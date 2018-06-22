#!/usr/bin/env python
# --------------------------------------------------------------------------------
# Class for the dynamic options in the GMQL tools
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import sys, requests


def validate(request_context, error_map, params, inputs):
    """Generic validate function, it checks if the user is valid."""

    user = params.get('authToken', '')

    if user:
        try:
            validate_user(user.file_name)
        except:
            error_msg = 'User has expired'
            error_map['authToken'] = error_msg


def validate_upload(request_context, error_map, params, inputs):
    """Validate function for uploading tool. It also checks the chosen ds name does not exists already."""

    validate(request_context, error_map, params, inputs)

    name = params.get('name')

    user = params.get('authToken')

    #This MUST be changed in the future to a parametric solution. Hopefully in the future Galaxy will allow
    #validation without external scripts

    url = 'http://genomic.elet.polimi.it/gmql-rest/datasets'

    datasets = get(url, user=user.file_name)
    list_datasets = [x['name'] for x in datasets['datasets']]

    if name in list_datasets:
        error_msg = 'Dataset already exists. Choose another name.'
        error_map['name'] = error_msg


def validate_variables(request_context, error_map, params, inputs):
    """Validate function for gmql_compositor. It checks that all queries input variables
    have been previously defined. """

    validate(request_context, error_map, params, inputs)

    output_vars = set([])

    # TODO: Include in the check output variables eventually defined previously in another query

    for op in params.get('operations'):
        op_curr = op.get('operation')
        if op_curr.get('input', ''):
            input_var = op_curr.get('input').get('input_var', '')
            if input_var:
                if input_var not in output_vars:
                    error_msg = '%s has not been defined yet\n' % (input_var)
                    name = '|'.join(['operations_%d' % (op.get('__index__')), 'operation', 'input', 'input_var'])
                    error_map[name] = error_msg
        else:
            for key in op_curr.keys():
                if key.startswith('input_var'):
                    input_var = op_curr.get(key)
                    if input_var:
                        if input_var not in output_vars:
                            error_msg = '%s has not been defined yet\n' % (input_var)
                            name = '|'.join(['operations_%d' % (op.get('__index__')), 'operation', key])
                            error_map[name] = error_msg

        # Update output_vars with the result of current operation
        output_vars.add(op_curr.get('output_var'))


def validate_user(user):
    """Check if the user is a valid one"""

    if user:
        with open(user, 'r') as f:
            valid = f.readline().rstrip('\n').split('\t')[2]
            if valid == 'False':
                raise Exception, "User has expired"


def get_metadata_attr(user, ds, ds_list):
    options = []

    try:
        validate_user(user)
        if ds_list:

            owner = ''

            with open(ds_list, 'r') as f:
                for d in f.readlines():
                    if d.split('\t')[0] == ds:
                        owner = d.split('\t')[1].rstrip('\n')
            f.close()

            attr_list = get_metadata(user, ds, str(owner))

            for i, att in enumerate(attr_list['attributes']):
                options.append((att.get('key', ' '), att.get('key', ' '), i == 0))

            return options

        else:
            return options
    except:
        return options


def get_metadata_values(user, ds, ds_list, att):
    options = []

    try:
        validate_user(user)
        if ds_list:

            owner = ''

            with open(ds_list, 'r') as f:
                for d in f.readlines():
                    if d.split('\t')[0] == ds:
                        owner = d.split('\t')[1].rstrip('\n')
            f.close()

            attr_list = get_metadata(user, ds, str(owner), att)

            # By default first option is '*' i.e. any value
            options.append(('any value', '*', 0))

            for i, att in enumerate(attr_list['values']):
                options.append(('%s (%d)' % (att.get('text', ' '), att.get('count', 0)), att.get('text', ' '), i == 0))

            return options

        else:
            return options
    except:
        return options


def get_metadata(user, ds, owner='', att_name=''):
    """Return the metadata attributes names for the given dataset"""

    url = 'http://genomic.elet.polimi.it/gmql-rest/metadata/{datasetName}/filter'

    # Format url
    if (owner == 'public'):
        url = url.format(datasetName='public.' + ds)
    else:
        url = url.format(datasetName=ds)

    if att_name:
        url = '{url}/{att}'.format(url=url, att=att_name)

    content = dict()
    content.update(attributes=[])

    metadata = post(url, content, user=user)

    return metadata


def read_token(input):
    """It takes the tabular file with the information over the user
     name   authToken   valid_flag
     It checks if the user is still valid and extract the authToken for the REST calls"""

    with open(input, 'r') as f_in:
        user = f_in.readline().rstrip('\n').split('\t')

    if user[2]:
        token = user[1]
    else:
        stop_err("This session is no longer valid")

    return token


def get(url, user=None, response_type='json'):
    """GET Request
    :param url: url where to fetch the requested resource
    :param user: for authenticated requests; if not provided make an unauthenticated request (es. for login)
    :param response_type: type of the fetched response.
        JSON ( Default )
        TEXT
        ZIP
        FILE
    """

    # Set request headers
    headers = dict()

    if user:
        headers.update({'X-AUTH-TOKEN': read_token(user)})

    if response_type == 'text':
        headers.update({'Accept': 'text/plain'})
    elif response_type == 'zip':
        pass
    elif response_type == 'file':
        headers.update({'Accept': 'file'})
    else:
        headers.update({'Accept': 'application/json'})

    # Make the request
    response = requests.get(url, headers=headers)

    # Check returned server status
    status_code = response.status_code

    # Read result. If Server OK, read according to response_type. Raise an error otherwise.
    if status_code == requests.codes.ok:
        if response_type == 'json':
            return response.json()
        elif response_type == 'text':
            return response.text
        else:
            return response
    elif status_code == requests.codes.unauthorized:
        #expire_user(user)
        stop_err("You are not authorized to do this. \nPlease login first.")
    elif status_code == requests.codes.not_found:
        stop_err("Resource not found for this user.")
    else:
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
       #expire_user(user)
       stop_err("You are not authorized to do this. \nPlease login first.")
    else :
        stop_err("Error {code}: {reason}\n{message}".format(code=status_code,
                                                 reason=response.reason,
                                                 message=response.content))


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()