#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Helper functions to perform REST calls on the GMQL server. 
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import sys
import os
import urllib2
import json
import yaml
import mimetypes
import mimetools
import itertools

import logging

def load_parts(module, call) :
    """Given the module and the single operation, returns the fragments for the url to call"""

    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'gmql_rest.yaml')

    with open(y_path,'r') as yamlf :
        cfg = yaml.load(yamlf)
    yamlf.close()

    parts = list ()

    gmql = cfg['GMQL_URL']
    prefix = cfg[module]['prefix']
    op = cfg[module]['operations'][call]

    parts.append(gmql)
    if prefix :
        parts.append(prefix)

    for p in op :
        parts.append(p)

    return parts

def compose_url(module, call) :
    """Given the fragments of a url, return the composite one"""

    parts = load_parts(module,call)
    url = '/'.join(parts)

    return url

def add_url_param(baseurl, module, op, value) :
    """Given a base url, add the given query param"""

    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmql_rest.yaml')

    with open(y_path, 'r') as yamlf:
        cfg = yaml.load(yamlf)
    yamlf.close()

    param = cfg[module]['params'][op]

    url = '{url}?{param}={value}'.format(url=baseurl, param=param, value=value)

    return url


def read_token(input):
    """It takes the file with json object containing an user valid authToken and returns its value as a simple string. """

    with open(input, 'r') as f_in:
        try:
            user = json.load(f_in)
        except ValueError:
            stop_err("The token is not a valid json file")

    if user['valid'] :
        token = user['authToken']
    else:
        stop_err("This session is no longer valid")

    return token


def url_get(url, response_type='application/json') :
    """GET request without user token"""

    req_out = urllib2.Request(url)
    req_out.add_header('Accept', response_type)

    try:
        response = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err('{code}: {reason}'.format(code=e.code, reason=e.reason))
        elif hasattr(e, 'code'):
            stop_err("The server cannot be reached. \nCode: {code}".format(code=e.code))

    return response


def auth_url_get(url, user, response_type='application/json'):
    """GET authenticated requests to fetch remote data.
    If not specified otherwise, the response is expected to be a json"""

    req_out = urllib2.Request(url)
    req_out.add_header('X-Auth-Token', read_token(user))
    req_out.add_header('Accept', response_type)

    try:
        res_out = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err('{code}: {reason}'.format(code=e.code, reason=e.reason))
        elif hasattr(e, 'code'):
            if (e.code == 401):
                stop_err("You are not authorized to do this. \nPlease login first.")
            else:
                stop_err("The server cannot be reached. \nCode: {code}".format(code=e.code))

    return res_out

def url_post(url, content, content_type='application/json', response_type='application/json') :
    """POST request without user token.
    For login and register operations. """

    req_out = urllib2.Request(url)

    req_out.add_header('Content-Type', content_type)
    req_out.add_header('Accept',response_type)
    req_out.add_data(content)

    try:
        response = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err('{code}: {reason}'.format(code=e.code, reason=e.reason))
        elif hasattr(e, 'code'):
            stop_err("The server cannot be reached. \nCode: {code}".format(code=e.code))

    return response



def auth_url_post(user, url, content, content_type='application/json', response_type='application/json'):
    """POST authenticated request.
    If not specified otherwise, the response is expected to be a json."""

    logging.basicConfig(filename='/home/luana/gmql-galaxy/post.log',level=logging.DEBUG, filemode='w')
    logging.debug('Starting Logger\n')
    logging.debug('Content Type %s\n' %(content_type))
    logging.debug('Accept: %s\n' % (response_type))
    logging.debug(('Content: %s\n' %(content)))


    req_out = urllib2.Request(url)

    req_out.add_header('X-Auth-Token', read_token(user))
    req_out.add_header('Content-Type', content_type)
    req_out.add_header('Accept', response_type)
    req_out.add_data(content)



    try:
        res_out = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err('{code}: {reason}'.format(code=e.code,reason=e.reason))
        elif hasattr(e, 'code'):
            if e.code == 401:
                stop_err("You are not authorized to do this. \nPlease login first.")
            else:
                stop_err("The server cannot be reached. \nCode: {code}".format(code=e.code))

    return res_out


def auth_url_delete(user, url, response_type='application/json'):
    """DELETE authenticated request to delete remote data.
    If not specified otherwise, the response is expected to be a json"""

    req_out = urllib2.Request(url)

    req_out.get_method = lambda: "DELETE"

    req_out.add_header('X-Auth-Token', read_token(user))
    req_out.add_header('Accept',response_type)

    try:
        res_out = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err('{code}: {reason}'.format(code=e.code, reason=e.reason))
        elif hasattr(e, 'code'):
            if e.code == 401:
                stop_err("You are not authorized to do this. \nPlease login first.")
            else :
                stop_err("The server cannot be reached. \nCode: {code}".format(code=e.code))


    response = res_out.read()

    return response


class MultiPartForm(object) :
    """Manage multiple files forms for POST requests """

    def __init__(self):

        self.files = []
        self.boundary = mimetools.choose_boundary()

        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):

        body = fileHandle.read()
        if mimetype is None :
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        self.files.append((fieldname,filename, mimetype, body))

        return


    def __str__(self) :

        parts = []
        boundary = '--------------------------' + self.boundary

        parts.extend(
            [boundary,
             'Content-Disposition: form-data: name="%s"; filename="%s"' % (field_name, filename),
             'Content-Type: %s' % content_type,
             '',
             body,
             ]
            for field_name, filename, content_type, body in self.files
        )

        flattened = list(itertools.chain(*parts))
        flattened.append('--------------------------' + self.boundary)
        flattened.append('')

        return '\r\n'.join(flattened)





def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()
