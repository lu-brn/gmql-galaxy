#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Galaxy plugin to REST access to the GMQL services
# (Authentication module)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse

from rest_api_calls import *
import logging

module = 'access'


def guest_login(output):
    """In order to call any of the services, a user must be logged at least as a guest.
    It returns the authToken to be used later and the relative validity flag"""

    call = 'guest'
    url = compose_url(module, call)

    response = url_get(url)

    user = json.load(response)

    user.update(valid=True)

    with open(output, 'w') as f_out:
        json.dump(user, f_out)


def login(output, username, password) :
    """In order to call any of the services, a user must be logged.
    Given credentials it attempts to login the user into the gmql system """

    call = 'login'

    url = compose_url(module, call)

    user_data = dict ()
    user_data.update(username=username,password=password)
    request = json.dumps(user_data)

    response = url_post(url, request)

    user = json.load(response)

    # The returned JSON only contains authToken. Add Validity flag and username
    user.update(username=username,valid=True)

    with open(output,'w') as f_out :
        json.dump(user, f_out)


def logout(user, output):
    """Logout from the system """

    call = 'logout'

    url = compose_url(module, call)
    response = auth_url_get(url, user)

    with open(output, 'w') as f_out:
        f_out.write(response.read())

    # Flag the token as invalid and save back the user json

    with open(user,'r') as f_in :
        user_js = json.load(f_in)

    user_js['valid'] = False

    with open(user,'w') as f_out :
        json.dump(user_js, f_out)


    #delete_user_token()


def register(new_user, output) :

    logging.basicConfig(filename='/home/luana/gmql-galaxy/auth.log',level=logging.DEBUG, filemode='w')

    call = 'register'

    url = compose_url(module, call)

    with open(new_user,'r') as f_in :
        nu = json.loads(f_in.read())

    request = json.dumps(nu)

    #logging.debug('%s\n'%(json.dumps(nu)))

    response = url_post(url, request)

    # The registration call returns a valid token and some info about the new user. Add
    # the validity flag and create the new user file in galaxy

    user = json.load(response)
    user.update(valid=True)

    with open(output,'w') as f_out :
        json.dump(user, f_out)



def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("-output")
    parser.add_argument("-cmd")
    parser.add_argument("-login_type")
    parser.add_argument("-user")
    parser.add_argument("-username")
    parser.add_argument("-password")
    parser.add_argument("-new_user")

    args = parser.parse_args()

    if args.cmd == 'login':
        if args.login_type == 'guest':
            guest_login(args.output)
        else :
            login(args.output, args.username, args.password)
    if args.cmd == 'logout':
        logout(args.user, args.output)
    if args.cmd == 'register' :
        register(args.new_user, args.output)


if __name__ == "__main__":
    __main__()
