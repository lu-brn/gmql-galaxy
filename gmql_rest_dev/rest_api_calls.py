#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Helper functions to perform REST calls on the GMQL server. 
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import sys
import urllib2
import json


def read_token(user):
    """It takes the file with json object containing the user authToken and returns its value as a string. """

    with open(user, 'r') as f_in:
        try:
            user_json = json.load(f_in)
        except ValueError:
            stop_err("The token is not a valid json file")
    f_in.close

    user_token = json.loads(user_json)['authToken']

    return user_token


def auth_url_get(user, url):
    """GET authenticated requests to fetch remote data."""

    req_out = urllib2.Request(url)
    req_out.add_header('X-Auth-Token', read_token(user))

    try:
        res_out = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err(e.reason)
        elif hasattr(e, 'code'):
            if (e.code == 401):
                stop_err("You are not authorized to do this. \nPlease login first.")
            else:
                stop_err("The server cannot be reached. Code: " + e.code)

    return res_out


def auth_url_post(user, url, content, content_type):
    """POST authenticated request."""

    req_out = urllib2.Request(url)

    req_out.add_header('X-Auth-Token', read_token(user))
    req_out.add_header('Content-Type', content_type)

    try:
        res_out = urllib2.urlopen(req_out, content)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err(e.reason)
        elif hasattr(e, 'code'):
            if e.code == 401:
                stop_err("You are not authorized to do this. \nPlease login first.")
            else:
                stop_err("The server cannot be reached. Code: " + e.code)

    return res_out


def auth_url_delete(user, url):
    """DELETE authenticated request to delete remote data."""

    req_out = urllib2.Request(url)

    req_out.get_method = lambda: "DELETE"

    req_out.add_header('X-Auth-Token', read_token(user))

    try:
        res_out = urllib2.urlopen(req_out)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err(e.reason)
        elif hasattr(e, 'code'):
            if e.code == 401:
                stop_err("You are not authorized to do this. \nPlease login first.")
            else:
                stop_err("The server cannot be reached. Code: " + e.code)

    response = res_out.read()

    return response


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()
