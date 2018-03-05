#!/usr/bin/env python
# --------------------------------------------------------------------------------
# Class for the dynamic options in the GMQL Queries Compositor tools
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import os, imp


def validate (request_context, error_map, params, inputs):
    """Generic validate function, it checks if the user is valid."""

    user = params.get('authToken', '')

    if user:
        try:
            validate_user(user.file_name)
        except:
            error_msg = 'User has expired'
            error_map['authToken'] = error_msg


def validate_variables(request_context, error_map, params, inputs):
    """Validate function for gmql_compositor. It checks that all queries input variables
    have been previously defined. """

    validate(request_context, error_map, params, inputs)

    output_vars = set([])

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
        with open(user, 'r') as f :
            valid = f.readline().rstrip('\n').split('\t')[2]
            if valid == 'False' :
                raise Exception, "User has expired"


def get_metadata_attr(user, ds, ds_list) :

    options = []

    try :
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
    except :
        return options

def get_metadata_values(user, ds, ds_list, att) :

    options = []

    try :
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
                options.append(('%s (%d)'%(att.get('text', ' '),att.get('count',0)), att.get('text', ' '), i == 0))

            return options

        else:
            return options
    except :
        return options


def get_metadata(user, ds, owner='', att_name=''):
    """Return the metadata attributes names for the given dataset"""

    utilities = imp.load_source('gmql', os.getcwd()+'/tools/gmql/utilities.py')

    module = 'metadata'
    call = 'list'
    url = utilities.compose_url(module, call)

    # Format url
    if (owner == 'public'):
        url = url.format(datasetName='public.' + ds)
    else:
        url = url.format(datasetName=ds)

    if att_name:
        url = '{url}/{att}'.format(url=url,att=att_name)

    content = dict()
    content.update(attributes=[])

    metadata = utilities.post(url, content, user=user)

    return metadata