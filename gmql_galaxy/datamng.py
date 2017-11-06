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

def save_ref(source, in_mode, src_list, dst_path) :
    """A input can be:
     - A collection within the local instance of galaxy
     - A remote collection withing the GMQL Server
     - The result of a previous query """

    # Create a folder to collect references to collections files. (If this does not exist already)
    dst = os.path.join(os.path.split(dst_path)[0], 'collection_refs')

    try:
        os.makedirs(dst)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    if in_mode == 'c':

        # Read the identifier of the collection

        with open(source, 'r') as f_in:
            c = f_in.readline().rstrip('\n')


        # Copy the temp files with references to the input collection in that folder
        dst = os.path.join(dst, c)
        shutil.copy(source, dst)
        src_list.append(dst)

    elif in_mode == 'r' :
        #We only need to retrieve the collection name into the repository

        with open(source, 'r') as f_in:
            c = f_in.readline().rstrip('\n')

        src_list.append(c)

    else:

        # Read the path to the query data

        with open(source, 'r') as f_in:
            q = f_in.readline().rstrip('\n')


        # Reach the query data and retrieve the input name

        with open(q, 'r') as f_in:
            stms = f_in.readlines()
            q_data = stms[-1].rstrip('\n')
            in_ds = q_data.split('\t')[0]


        src_list.append(in_ds)

    return src_list

def ref_unary_input(source, in_mode, target_q, query):
    """Manage the input for unary operations."""

    src_list = list()
    #Calls the save_ref utility which returns a list with the references to sources
    src_list = save_ref(source, in_mode, src_list, target_q)

    #Save src_list in the query
    query.update(sources_ds=src_list[0])


def ref_binary_input(source1, in_mode1, source2, in_mode2, target_q, query):
    """Manage the input for binary operations.
    These can be a collection of datasets or the results of previous queries """

    src_list = list()
    # Calls the save_ref utility which returns a list with the references to sources
    src_list = save_ref(source1, in_mode1, src_list, target_q)
    src_list = save_ref(source2, in_mode2, src_list, target_q)

    src_str = '{s1}\t{s2}'.format(s1=src_list[0],s2=src_list[1])
    query.update(sources_ds=src_str)



def save_result_1 (target_q, query, *args, **kwargs):
    """ Save the result query for unary operations
    If the input is another query, this is updated """

    source_q = kwargs.get('source', None)

    if source_q :
        # Read the path of the source query and copy the content into target_q
        with open(source_q, 'r') as f_in:
            q = f_in.readline().rstrip('\n')


        shutil.copy(q, target_q)

    # Update with the new statement

    with open(target_q, 'a') as f_out:
        f_out.write('{target}\t{query}\t{source}\n'.format(target=query['target_ds'], query=query['target_q'],
                                                           source=query['sources_ds']))


def save_result_2 (target_q, query, *args, **kwargs):
    """ Save the result query for binary operations
    If the input are queries, these are merged and updated with the new statement """

    q1 = kwargs.get('source1', None)
    q2 = kwargs.get('source2', None)


    if q1 :

        if q2 :

            with open(q1,'r') as f_q1 :
                path_q1 = f_q1.readline().rstrip('\n')
            f_q1.close()

            shutil.copy(path_q1, target_q)

            with open(target_q,'a') as f_out :

                with open(q2, 'r') as f_q2:
                    path_q2 = f_q2.readline().rstrip('\n')
                f_q2.close()

                with open(path_q2,'r') as f_in :
                    f_out.write(f_in.read())
                f_in.close()

            f_out.close()

        else :
            with open(q1,'r') as f_q1 :
                path_q1 = f_q1.readline().rstrip('\n')
            f_q1.close()

            shutil.copy(path_q1, target_q)


    else :
        if q2 :
            with open(q2,'r') as f_q2 :
                path_q2 = f_q2.readline().rstrip('\n')
            f_q2.close()

            shutil.copy(path_q2, target_q)



    #TODO: change, now it's set to work only with MAP
    with open(target_q, 'a') as f_out:
        f_out.write('{target}\t{query}\t{source}\n'.format(target=query['target_ds'], query='MAP\t ',
                                                           source=query['sources_ds']))