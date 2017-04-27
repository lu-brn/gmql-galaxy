#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Galaxy plugin to REST access to the GMQL services
# (Authentication module)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import sys, os
import urllib2
import json
import argparse

from galaxy_api import *
from rest_api_calls import auth_url_get

GMQL_URL = "http://genomic.elet.polimi.it/gmql-rest"


def guest_login(output):
    """In order to call any of the services, a user must be logged at least as a guest.
    This function logs the user and return an authToken to be used later"""

    url = "{gmql}/guest".format(gmql=GMQL_URL)
    req = urllib2.Request(url)
    req.add_header('Accept', 'application/json')

    try:
        res = urllib2.urlopen(req)
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            stop_err("An error has occurred. Reason : " + e.reason)
        elif hasattr(e, 'code'):
            stop_err("The server cannot be reached. Code: " + e.code)

    res_str = res.read().decode('utf8')


    with open(output, 'w') as f_out:
        json.dump(res_str, f_out)
    f_out.close


def logout(user, output):
    """Logout from the system """

    url = "{gmql}/logout".format(gmql=GMQL_URL)
    response = auth_url_get(user,url)

    with open(output, 'w') as f_out:
        f_out.write(response.read())
    f_out.close

    # Remove the token from dataset
    delete_user_token()


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("-cmd")
    parser.add_argument("-login_type")
    parser.add_argument("-user")

    args = parser.parse_args()

    if args.cmd == 'login':
        if args.login_type == 'guest': guest_login(args.output)
    if args.cmd == 'logout':
        logout(args.user, args.output)


if __name__ == "__main__":
    __main__()
