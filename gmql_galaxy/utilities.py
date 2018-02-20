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
import itertools
import requests

import logging


def load_parts(module, call) :
    """Given the module and the single operation, returns the fragments for the url to call"""

    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'gmql_rest.yaml')

    with open(y_path,'r') as yamlf :
        cfg = yaml.load(yamlf)

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

def add_url_param(params, module, op, value,) :
    """Given the params dict, add a new pair of key:value with the given value and the key set for given module and operation"""

    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmql_rest.yaml')

    with open(y_path, 'r') as yamlf:
        cfg = yaml.load(yamlf)
    yamlf.close()

    key = cfg[module]['params'][op]

    params.update({key : value})

    return params


def read_token(input):
    """It takes the tabular file with the information over the user
     name   authToken   valid_flag
     It checks if the user is still valid and extract the authToken for the REST calls"""

    with open(input,'r') as f_in :
        user = f_in.readline().rstrip('\n').split('\t')

    if user[2] :
        token = user[1]
    else :
        stop_err("This session is no longer valid")


    return token

def expire_user(input):
    """Set the validity flag of a user token to false"""

    with open(input,'r') as f:
        user = f.readline().rstrip('\n').split('\t')

    user[2] = False

    with open(input,'w') as f :
         f.write('{fullName}\t{token}\t{valid}\n'.format(fullName=user[0], token=user[1],
                                                            valid=user[2]))


def get(url, user=None, response_type='json') :
    """GET Request
    :param url: url where to fetch the requested resource
    :param user: for authenticated requests; if not provided make an unauthenticated request (es. for login)
    :param response_type: type of the fetched response.
        JSON ( Default )
        TEXT
        ZIP
        FILE
    """

    #Set request headers
    headers = dict ()

    if user :
        headers.update({'X-AUTH-TOKEN' : read_token(user)})

    if response_type == 'text' :
        headers.update({'Accept' : 'text/plain'})
    elif response_type == 'zip' :
        pass
    elif response_type == 'file' :
        headers.update({'Accept' : 'file'})
    else :
        headers.update({'Accept' : 'application/json'})

    logging.debug(headers)

    #Make the request
    response = requests.get(url, headers=headers)

    #Check returned server status
    status_code = response.status_code

    #Read result. If Server OK, read according to response_type. Raise an error otherwise.
    if status_code == requests.codes.ok :
        if response_type == 'json' :
            return response.json()
        elif response_type == 'text' :
            return response.text
        else :
            return response
    elif status_code == requests.codes.unauthorized :
        expire_user(user)
        stop_err("You are not authorized to do this. \nPlease login first.")
    elif status_code == requests.codes.not_found :
        stop_err("Resource not found for this user.")
    else :
        stop_err("Error {code}: {reason}\n{message}".format(code=status_code,
                                                            reason=response.reason,
                                                            message=response.content))


def post(url, payload, user=None, params=None, content_type='json', response_type='json') :
    """ POST Request
    :param url: url where to post data
    :param payload: payload for the post request. Type is specified by content_type.
    :param user:  for authenticated requests; if not provided make an unauthenticated request (es. for registration)
    :param params: optional query parameters
    :param content_type
    :param response_type: Default is json
    """

    # Set request headers
    headers = dict()

    if user:
        headers.update({'X-AUTH-TOKEN': read_token(user)})

    headers.update({'Accept': 'application/json'})

    if content_type == 'text' :
        headers.update({'Content-Type' : 'text/plain'})
        response = requests.post(url, params=params, headers=headers, data=payload)
    elif content_type == 'multiform' :
        response = requests.post(url, params=params, headers=headers, files=payload)
    else :
        headers.update({'Content-Type': 'application/json'})
        response = requests.post(url, params=params, headers=headers, json=payload)

    # Check returned server status
    status_code = response.status_code

    if status_code == requests.codes.ok :
        return response.json()
    elif status_code == requests.codes.unauthorized :
        expire_user(user)
        stop_err("You are not authorized to do this. \nPlease login first.")
    else :
        stop_err("Error {code}: {reason}\n{message}".format(code=status_code,
                                                 reason=response.reason,
                                                 message=response.content))



def delete(url, user=None, response_type='json') :
    """DELETE request
    :param url: url where to post data
    :param user:  for authenticated requests; if not provided make an unauthenticated request (es. for registration)
    :param response_type: Default is json
    """

    # Set request headers
    headers = dict()

    if user:
        headers.update({'X-AUTH-TOKEN': read_token(user)})

    headers.update({'Accept': 'application/json'})

    #Make the request
    response = requests.delete(url, headers=headers)

    #Check returned server status
    status_code = response.status_code


    #If Server OK, read result. Raise an error otherwise.
    if status_code == requests.codes.ok :
            return response.json()
    elif status_code == requests.codes.unauthorized :
        expire_user(user)
        stop_err("You are not authorized to do this. \nPlease login first.")
    elif status_code == requests.codes.not_found :
        stop_err("Resource not found for this user.")
    else :
        stop_err("Error {code}: {reason}".format(code=status_code,
                                                 reason=response.reason))



def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()
