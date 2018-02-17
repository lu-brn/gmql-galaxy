#!/usr/bin/env python
# --------------------------------------------------------------------------------
# Class for the dynamic options in the GMQL Queries Compositor tools
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import logging
import os, imp


def validate_user(user):
    """Check if the user is a valid one"""

    #value = incoming.get('authToken', None)

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



def get_metadata(user, ds, owner=''):
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

    content = dict()
    content.update(attributes=[])

    metadata = utilities.post(url, content, user=user)

    return metadata