# Galaxy plugin to REST access to the GMQL services
# (Authentication module)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse, json

from utilities import *

module = 'access'


def guest_login(output):
    """In order to call any of the services, a user must be logged at least as a guest.
    It returns the authToken to be used later and the relative validity flag"""

    call = 'guest'
    url = compose_url(module, call)

    user = get(url)

    # Set the user as valid
    user.update(valid=True)
    user.update(name='Guest')

    with open(output, 'w') as f_out :
        f_out.write('{name}\t{token}\t{valid}\n'.format(name=user['name'],token=user['authToken'],valid=user['valid']))


def login(output, username, password) :
    """In order to call any of the services, a user must be logged.
    Given credentials it attempts to login the user into the gmql system """

    call = 'login'

    url = compose_url(module, call)

    user_data = dict ()
    user_data.update(username=username,password=password)

    user = post(url, user_data)

    user.update(valid=True)

    with open(output, 'w') as f_out :
        f_out.write('{name}\t{token}\t{valid}\n'.format(name=user['fullName'],token=user['authToken'],valid=user['valid']))

def logout(user,output):
    """Logout from the system """

    call = 'logout'

    url = compose_url(module, call)
    response = get(url, user, response_type='text')

    with open(output, 'w') as f_out:
         f_out.write(response)

    # Flag the token as invalid and save back the user

    expire_user(user)


def register(new_user, output) :

    call = 'register'
    url = compose_url(module, call)

    with open(new_user,'r') as f_in :
        nu = json.loads(f_in.read())

    # The registration call returns a valid token and some info about the new user. Add
    # the validity flag and create the new user file in galaxy

    user = post(url, nu)

    user.update(valid=True)

    with open(output, 'w') as f_out :
        f_out.write('{name}\t{token}\t{valid}\n'.format(name=user['fullName'],token=user['authToken'],valid=user['valid']))


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
