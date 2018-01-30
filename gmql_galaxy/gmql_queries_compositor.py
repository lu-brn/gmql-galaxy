#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Compositor
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import os, sys, argparse, json, logging
from itertools import chain
from gmql_queries_statements import *
from gmql_rest_queries import compile_query, run_query

def read_new_query(query_data):

    # Create new Query object and read JSON file
    query = dict ()

    with open(query_data, 'r') as f_in :
        qd = json.loads(f_in.read())

    query.update(name=qd['query_name'])

    # A list of statements objects is created from the list of operations and added to the query
    statements = map(lambda x: read_statement(x['operation']), qd['operations'])

    # Check if the user asked for materialize the final result and in case add a materialize statement
    # for the last variable defined.

    if qd['materialize']['materialize_result'] :
        var = statements[-1][0].variables['output']
        mat_stm = Materialize(qd['materialize']['file_name'],var)
        statements.append((mat_stm,))

        # Also save info about the desired output format
        out_format = qd['materialize']['choose_op']['out_format']
        query.update(out_format=out_format)

    # Add statements list to query, flattening list elements if needed (in case there's some intermediate
    # materialize)

    query.update(statements=[x for x in chain.from_iterable(statements)])


    return query


def read_statement(x):

    if x['operator'] == 'SELECT' :
        stm = create_select(x)

    # If the user asked to materialize the current statement, add a MATERIALIZE statement; otherwise return
    # only the current statement

    if x['m_stm']['materialize_stm'] :
        mat_stm = Materialize(x['m_stm']['file_name'],stm.variables['output'])
        return (stm, mat_stm)
    else:
        return (stm,)

def create_select(x) :

    stm = Select()

    # Set output and input variables
    stm.set_output_var(x['output_var'])
    #stm.set_input_ds(x['input_ds'])

    if x['input']['input_type'] == 'i_ds' :
         input_ds = x['input']['input_ds']
    if x['input']['input_type'] == 'i_var':
         input_ds = x['input']['input_var']

    stm.set_input_ds(input_ds)

    #Check if there's metadata predicates and set it up
    mp_data = x['metadata_predicates']

    if mp_data['condition'] != 'None':
        meta_pred = _metadata_predicate(mp_data)

        # If there are further blocks
        for ma in mp_data['add_meta_blocks']:
            if meta_pred.__len__() > 1 :
                meta_pred = [meta_pred, 'BLOCK']
            mp = _metadata_predicate(ma)

            if ma['block_logCon']['negate']:
                mp = [mp, 'NOT']

            if ma['block_logCon']['logCon'] == 'AND':
                meta_pred = [meta_pred, mp, 'AND']
            if ma['block_logCon']['logCon'] == 'OR':
                meta_pred = [meta_pred, mp, 'OR']

        stm.set_param(meta_pred, 'metadata')

    # Similar applies with Region Predicates (if they are present)
    rp_data = x['region_predicates']

    if rp_data['condition'] != 'None':
        reg_pred = _region_predicate(rp_data)

        # If there are further blocks
        for ra in rp_data['add_region_blocks'] :
            if reg_pred.__len__() > 1 :
                reg_pred = [reg_pred, 'BLOCK']
            rp = _region_predicate(ra)

            if ra['block_logCon']['negate']:
                # rp.negate()
                rp = [rp, 'NOT']

            if ra['block_logCon']['logCon'] == 'AND':
                #reg_pred.and_(rp)
                reg_pred = [reg_pred, rp, 'AND']
            if ra['block_logCon']['logCon'] == 'OR':
                #reg_pred.or_(rp)
                reg_pred = [reg_pred, rp, 'OR']

        stm.set_param(reg_pred, 'region')

    # Check if there is a semijoin predicate. If it does, collect the attributes and the external ds to confront with.

    sj_data = x['semijoin_predicate']

    if sj_data['sj_attributes'] :
        sj_attr = map(lambda x: x['sj_att'], sj_data['sj_attributes'])
        sj = SemiJoinPredicate(sj_attr,sj_data['ds_ext'],sj_data['condition'])

        stm.set_param(sj, 'semijoin')

    return stm

def _metadata_predicate(mp_data):
    # Metadata predicates are well formed logical formulas. Create a new one and add the first
    # predicate. Negate it if it's the case.

    mp = MetaPredicate(mp_data['attribute'], mp_data['value'], mp_data['condition'])
    if mp_data['negate']:
        mp = [mp, 'NOT']

    # Check if there are further predicates
    for pa in mp_data['pm_additional']:

        mp1 = MetaPredicate(pa['attribute'], pa['value'], pa['condition'])
        if pa['negate']:
            mp1 = [mp1, 'AND']

        if pa['logCon'] == 'AND':
            mp = [mp, mp1, 'AND']
        if pa['logCon'] == 'OR':
            mp = [mp, mp1, 'OR']

    return mp

def _region_predicate(rp_data):

    rp_s = RegionPredicate(rp_data['attribute'], rp_data['value'], rp_data['condition'])
    if rp_data['is_meta_value']:
        rp_s.set_value_type('meta')
    else:
        rp_s.set_value_type()
    #rp = WellFormedFormula(rp_s)
    rp = rp_s
    if rp_data['negate']:
        #rp.negate()
        rp = [rp, 'NOT']

    # Check if there are further predicates
    for pa in rp_data['pr_additional']:
        rp1_s = RegionPredicate(pa['attribute'], pa['value'], pa['condition'])
        if pa['is_meta_value']:
            rp1_s.set_value_type('meta')
        else:
            rp1_s.set_value_type()
        #rp1 = WellFormedFormula(rp1_s)
        rp1 = rp1_s

        if pa['negate']:
            #rp1.negate()
            rp1 = [rp1, 'NOT']

        if pa['logCon'] == 'AND':
            #rp.and_(rp1)
            rp = [rp, rp1, 'AND']
        if pa['logCon'] == 'OR':
            #rp.or_(rp1)
            rp = [rp, rp1, 'OR']

    return rp

def save(query, output):

    #Set the config files where to look for the actual syntax to use
    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmql_syntax.yaml')

    with open(y_path, 'r') as yamlf:
        syntax = yaml.load(yamlf)


    with open(output, 'w') as f_out:

        for s in query['statements'] :
             f_out.write('{stm}\n'.format(stm=s.save(syntax)))


def compile(user, query_name, query_file, log):
    # Call the service in gmql_rest_queries to send the query to the GMQL server to compile.

    compile_query(user, query_name, query_file, log)


def run(user, query_name, query, log, out_format, updated_ds_list):
    # Call the service in gmql_rest_queries to send the query to the GMQL server to be executed.

    run_query(user, query_name, query, log, out_format, updated_ds_list)

def stop_err(msg):
    sys.stderr.write("%s\n" % msg)

def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-query_params")
    parser.add_argument("-query_output")
    parser.add_argument("-query_log")
    parser.add_argument("-updated_ds_list")

    args = parser.parse_args()

    query = read_new_query(args.query_params)
    save(query, args.query_output)

    if(args.cmd == 'compile'):
        compile(args.user, query['name'], args.query_output, args.query_log)

    if(args.cmd == 'run'):
        run(args.user, query['name'], args.query_output, args.query_log, query['out_format'], args.updated_ds_list)


if __name__ == "__main__":
    __main__()