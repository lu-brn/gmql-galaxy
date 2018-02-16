#!/usr/bin/env python
# --------------------------------------------------------------------------------
# Class for the dynamic options in the GMQL Queries Compositor tools
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import logging
import os, imp


def get_metadata_attr(user, ds, ds_list) :

    options = []

    owner = ''

    with open(ds_list, 'r') as f:
        for d in f.readlines():
            if d.split('\t')[0] == ds:
                owner = d.split('\t')[1].rstrip('\n')
    f.close()

    attr_list = get_metadata(user, ds, str(owner))

    for i, att in enumerate( attr_list['attributes'] ):
        options.append( ( att.get('key', ' '), att.get('key', ' '), i==0 ) )


    return options


def get_metadata(user, ds, owner=''):
    """Return the metadata attributes names for the given dataset"""

    utilities = imp.load_source('gmql', os.getcwd()+'/tools/gmql/utilities.py')

    call = 'list'
    url = utilities.compose_url('metadata', call)

    # Format url
    if (owner == 'public'):
        url = url.format(datasetName='public.' + ds)
    else:
        url = url.format(datasetName=ds)

    content = dict()
    content.update(attributes=[])

    metadata = utilities.post(url, content, user=user)

    return metadata



