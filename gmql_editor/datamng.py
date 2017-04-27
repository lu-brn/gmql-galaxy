#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL editor: local management of the input and output of the query compositors.
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import time
import os
import errno
import shutil

def create_new_target(query) :
    """Create a new identifier and add to the query dictionary
    The name is build over the current time and hour"""

    current_time = '{date}_{hour}'.format(date=time.strftime('%Y%m%d'), hour=time.strftime("%H%M"))
    result = 'result_{time}'.format(time=current_time)
    query.update(target_ds=result)


def ref_single_input(source, target_q, in_mode, query):
    """Manage the input for unary operations. 
    This can be a collection of dataset or the result of a previous query """

    # Create a folder to collect references to collections files. (If this does not exist already)
    dst = os.path.join(os.path.split(target_q)[0], 'collection_refs')

    try:
        os.makedirs(dst)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    if in_mode == 'c':

        # Read the identifier of the collection

        with open(source, 'r') as f_in:
            c = f_in.readline().rstrip()
        f_in.close

        # Copy the temp files with references to the input collection in that folder
        dst = os.path.join(dst, c)
        shutil.copy(source, dst)
        query.update(source_ds=dst)

    else:

        # Read the path to the query data

        with open(source, 'r') as f_in:
            q = f_in.readline().rstrip('\n')
        f_in.close

        # Reach the query data and retrieve the input name

        with open(q, 'r') as f_in:
            stms = f_in.readlines()
            q_data = stms[-1].rstrip('\n')
            in_ds = q_data.split('\t')[0]
        f_in.close

        query.update(source_ds=in_ds)

def save_result (source, target_q, in_mode, query):
    """ Save the result query.
    If the input is another query, this is updated """

    if in_mode == 'q' :

        with open(source, 'r') as f_in:
            q = f_in.readline().rstrip('\n')
        f_in.close

        shutil.copy(q, target_q)

    with open(target_q, 'a') as f_out:
        f_out.write('{target}\t{query}\t{source}\n'.format(target=query['target_ds'], query=query['target_q'],
                                                           source=query['source_ds']))
    f_out.close