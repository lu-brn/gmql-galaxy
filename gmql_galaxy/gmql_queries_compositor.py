#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Compositor
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import sys, argparse, json, logging
from itertools import chain
from gmql_queries_statements import *

def read_new_query(query_data):

    # Create new Query object and read JSON file
    query = dict ()

    with open(query_data, 'r') as f_in :
        qd = json.loads(f_in.read())

    query.update(name=qd['query_name'])

    # A list of statements objects is created from the list of operations and added to the query
    statements = map(lambda x: read_statement(x['operation']), qd['operations'])

    # Check if the user asked for materialize the final result and in case add a materialize statement
    # for the last variable defined

    if qd['materialize']['materialize_result'] :
        var = statements[-1][0].variables['output']
        mat_stm = Materialize(qd['materialize']['file_name'],var)
        statements.append((mat_stm,))

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
    stm.set_input_ds(x['input_ds'])

    #Check if there's metadata predicates and set it up
    mp_data = x['metadata_predicates']

    # If the condition of the first predicate is None, it means the user hasn't added any
    if mp_data['condition'] is not None :
        # Metadata predicates are well formed logical formulas. Create a new one and add the first
        # predicate. Negate it if it's the case.

        mp = WellFormedFormula(MetaPredicate(mp_data['attribute'], mp_data['value'],mp_data['condition']))
        if mp_data['negate'] :
            mp.negate()

        # Check if there are further predicates
        for pa in mp_data['pm_additional'] :

            mp1 = WellFormedFormula(MetaPredicate(pa['attribute'],pa['value'],pa['condition']))
            if pa['negate']:
                mp1.negate()

            if pa['logCon'] == 'AND':
                mp.and_(mp1)
            if pa['logCon'] == 'OR':
                mp.or_(mp1)

        stm.set_param(mp, 'metadata')

    # Similar applies with Region Predicates (if they are present)
    rp_data = x['region_predicates']

    if rp_data['condition'] is not None:
        rp_s = RegionPredicate(rp_data['attribute'],rp_data['value'],rp_data['condition'])
        rp_s.set_value_type()
        rp = WellFormedFormula(rp_s)
        if rp_data['negate'] :
            rp.negate()

        # Check if there are further predicates
        for pa in rp_data['pr_additional'] :
            rp1_s = RegionPredicate(rp_data['attribute'], rp_data['value'], rp_data['condition'])
            rp1_s.set_value_type()
            rp1 = WellFormedFormula(rp1_s)

            if pa['negate']:
                rp1.negate()

            if pa['logCon'] == 'AND':
                rp.and_(rp1)
            if pa['logCon'] == 'OR':
                rp.or_(rp1)

        stm.set_param(rp, 'region')

    # Check if there is a semijoin predicate. If it does, collect the attributes and the external ds to confront with.

    sj_data = x['semijoin_predicate']

    if sj_data['sj_attributes'] :
        sj = SemiJoinPredicate(sj_data['sj_attributes'],sj_data['ds_ext'],sj_data['condition'])

        stm.set_param(sj, 'semijoin')

    return stm

def read_saved_query():
    pass

def save(query, output):
    pass

def compile():
    pass

def run():
    pass

def stop_err(msg):
    sys.stderr.write("%s\n" % msg)

def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("-user")
    parser.add_argument("-query_params")
    parser.add_argument("-query_output")
    parser.add_argument("-query_log")
    parser.add_argument("-updated_ds_list")

    args = parser.parse_args()

    query = read_new_query(args.query_params)

    save(query, args.query_output)

if __name__ == "__main__":
    __main__()
