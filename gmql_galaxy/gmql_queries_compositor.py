#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Compositor
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import os, sys, argparse, json
from itertools import chain
from gmql_queries_statements import *
from gmql_rest_queries import compile_query, run_query, check_input
from gmql_rest_datasets import list_datasets
from gmql_queries_constants import *

def read_query(query_data):

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

        # Also save info about the desired output format (if available)
        out_format = qd['materialize']['choose_op'].get('out_format',None)
        if out_format:
            query.update(out_format=out_format)

        #Check if the user wants to import results into Galaxy already
        importFlag = qd['materialize']['choose_op'].get('import', None)
        if importFlag is not None:
            query.update(importFlag=importFlag)

    # Add statements list to query, flattening list elements if needed (in case there's some intermediate
    # materialize)

    query.update(statements=[x for x in chain.from_iterable(statements)])


    return query


def read_statement(x):

    op = x['operator']

    if op == 'SELECT' :
        stm = create_select(x)
    if op == 'MAP' :
        stm = create_map(x)
    if op == 'ORDER' :
        stm = create_order(x)
    if op == 'JOIN' :
        stm = create_join(x)

    # If the user asked to materialize the current statement, add a MATERIALIZE statement; otherwise return
    # only the current statement

    if x['m_stm']['materialize_stm'] :
        mat_stm = Materialize(x['m_stm']['file_name'],stm.variables['output'])
        return (stm, mat_stm)
    else:
        return (stm,)


def create_join(x) :
    stm = Join()

    # Set output and input variables
    stm.set_output_var(x['output_var'])
    stm.set_anchor_var(x['input_var_anchor'])
    stm.set_experiment_var(x['input_var_experiment'])

    # Look for conditions over regions distances and attributes values.

    conds = x['conditions_section']['conditions']

    if conds['c_type'] == 'distance' :
        pred = _genomic_predicate(conds.get('distance_conditions'))
        stm.set_genomic_predicate(pred)
    if conds['c_type'] == 'attributes' :
        pred = _equi_conditions(conds.get('region_attributes'))
        stm.set_equi_conditions(pred)
    else:
        pred1 = _genomic_predicate(conds.get('distance_conditions'))
        pred2 = _equi_conditions(conds.get('region_attributes'))
        stm.set_genomic_predicate(pred1)
        stm.set_equi_conditions(pred2)

    # Set the output preference
    stm.set_output_opt(conds.get('output_opt'))


    # Check if there are joinby conditions and set them up

    join_data = x['joinby']['joinby_clause']
    join_data = filter(lambda x: x['j_att'], join_data)
    join_data = map(lambda x: (x['j_att'], x['metajoin_match']), join_data)

    if join_data.__len__() > 0:
        jc = JoinbyClause(join_data)
        stm.set_joinby_clause(jc)


    return stm


def _genomic_predicate(pred):

    gp = GenomicPredicate()

    # Loop over the distal predicates and distinguish between distal conditions and stream directions.
    for x in pred:
        x = x.get('type_dc')
        if x.get('type_dc_value') == 'dist' :
            gp.add_distal_condition(x.get('dc'), x.get('n'))
        else:
            gp.add_distal_stream(x.get('ds'))

    return gp


def _equi_conditions(pred):

    atts = map(lambda x: x.get('attribute'), pred)
    ec = AttributesList(atts)

    return ec


def create_order(x):
     stm = Order()

     # Set output and input variables
     stm.set_output_var(x['output_var'])
     stm.set_input_var(x['input_var_ordering_ds'])

     # Collects ordering attributes and set them up, according also to their type (metadata or region)

     # Divide metadata attributes from region ones
     atts = x['ordering_attributes']['attributes']

     meta_att = filter(lambda att: att['att_type'] == 'metadata', atts)
     region_att = filter(lambda att: att['att_type'] == 'region', atts)

     # Collect attributes info from the two lists and add them to the ORDER parameters

     if meta_att:
         o_att_meta = OrderingAttributes()
         map(lambda att: o_att_meta.add_attribute(att['attribute_name'],att['order_type']), meta_att)
         stm.set_ordering_attributes(o_att_meta, 'metadata')

     if region_att:
         o_att_region = OrderingAttributes()
         map(lambda att: o_att_region.add_attribute(att['attribute_name'], att['order_type']), region_att)
         stm.set_ordering_attributes(o_att_region, 'region')

     # Check if there are constraints over the number of samples to extract and set them up

     top_opts = x['top_options']['to']

     if top_opts:
         topts = list()
         for to in top_opts:
             topts.append((to['type'],to['opt']['k_type'],to['opt']['k']))
         stm.set_top_options(topts)

     return stm


def create_map(x):
    stm = Map()

    # Set output and input variables
    stm.set_output_var(x['output_var'])
    stm.set_reference_var(x['input_var_reference'])
    stm.set_experiment_var(x['input_var_experiment'])

    # Check if the user has given an alternative name to the default one for the counting result

    if x['count_result']:
        stm.set_count_attribute(x['count_result'])

    # Check if there are additional region attributes definition and set them up

    nr_data = x['new_regions_attributes']['new_regions']

    new_regions = filter(lambda x: x['new_name'] and (x['function'] != 'None') and x['argument'], nr_data)
    new_regions = map(lambda x: RegionGenerator(newRegion=x['new_name'],
                                   function=RegFunction(x['function']),
                                   argRegion=x['argument']), new_regions)

    if new_regions.__len__() > 0 :
        stm.set_new_regions(new_regions)

    # Check if there are joinby conditions and set them up

    join_data = x['joinby']['joinby_clause']
    join_data = filter(lambda x: x['j_att'], join_data)
    join_data = map(lambda x: (x['j_att'], x['metajoin_match']), join_data)

    if join_data.__len__() > 0:
        jc = JoinbyClause(join_data)
        stm.set_joinby_clause(jc)

    return stm


def create_select(x) :

    stm = Select()

    # Set output and input variables
    stm.set_output_var(x['output_var'])

    input_data = x['input']

    if x['input']['input_type'] == 'i_ds' :
         input_var = input_data['input_ds']
         stm.set_input_var(input_var)
    if x['input']['input_type'] == 'i_var':
         input_var = input_data['input_var']
         stm.set_input_var(input_var)

    # Check if there's metadata predicates and set them up
    # They can be given as built step by step or directly as a text line.
    # Check the type and parse the appropriate data

    mp_data = input_data['metadata_predicates']['conditions']
    if mp_data['ad_flag'] == 'steps' :

        if mp_data['condition'] != 'None':
            meta_pred = _metadata_predicate(mp_data)

            # If there are further blocks
            for ma in mp_data['add_meta_blocks']:
                if meta_pred.__len__() > 1 :
                    meta_pred = [meta_pred, Wff.BLOCK]
                mp = _metadata_predicate(ma)

                if ma['block_logCon']['negate']:
                    mp = [mp, Wff.NOT]

                meta_pred = [meta_pred, mp, Wff(ma['block_logCon']['logCon'])]

            stm.set_param(meta_pred, 'metadata')
    else :
        meta_pred = check_input(mp_data['conditions_string'])
        stm.set_param(meta_pred, 'metadata')

    # Similar applies with Region Predicates (if they are present)
    rp_data = input_data['region_predicates']['conditions']
    if rp_data['ad_flag'] == 'steps' :

        if rp_data['condition'] != 'None':
            reg_pred = _region_predicate(rp_data)

            # If there are further blocks
            for ra in rp_data['add_region_blocks']:
                if reg_pred.__len__() > 1:
                    reg_pred = [reg_pred, Wff.BLOCK]
                rp = _region_predicate(ra)

                if ra['block_logCon']['negate']:
                    rp = [rp, Wff.NOT]

                reg_pred = [reg_pred, rp, Wff(ra['block_logCon']['logCon'])]


            stm.set_param(reg_pred, 'region')
    else:
        reg_pred = check_input(rp_data['conditions_string'])
        stm.set_param(reg_pred, 'region')



    # Check if there is a semijoin predicate. If it does, collect the attributes and the external ds to confront with.

    sj_data = input_data['semijoin_predicate']

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
        mp = [mp, Wff.NOT]

    # Check if there are further predicates
    for pa in mp_data['pm_additional']:

        mp1 = MetaPredicate(pa['attribute'], pa['value'], pa['condition'])
        if pa['negate']:
            mp1 = [mp1, Wff.NOT]

        if pa['logCon'] == 'AND':
            mp = [mp, mp1, Wff.AND]
        if pa['logCon'] == 'OR':
            mp = [mp, mp1, Wff.OR]

    return mp

def _region_predicate(rp_data):

    rp_s = RegionPredicate(rp_data['attribute'], rp_data['value'], rp_data['condition'])
    if rp_data['is_meta_value']:
        rp_s.set_value_type('meta')
    else:
        rp_s.set_value_type()
    rp = rp_s
    if rp_data['negate']:
        rp = [rp, Wff.NOT]

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
            rp1 = [rp1, Wff.NOT]

        if pa['logCon'] == 'AND':
            rp = [rp, rp1, Wff.AND]
        if pa['logCon'] == 'OR':
            rp = [rp, rp1, Wff.OR]

    return rp

def save(query, output, query_source):

    # Set the config files where to look for the actual syntax to use
    y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmql_syntax.yaml')

    with open(y_path, 'r') as yamlf:
        syntax = yaml.load(yamlf)

    # If I am continuing a local query, first copy the older statements
    if query_source:
        with open(output, 'w') as f_out:
            with open(query_source, 'r') as f_in:
                f_out.writelines(f_in.readlines())


    with open(output, 'a') as f_out:

        for s in query['statements'] :
             f_out.write('{stm}\n'.format(stm=s.save(syntax)))


def compile(user, query_name, query_file, log):
    # Call the service in gmql_rest_queries to send the query to the GMQL server to compile.

    compile_query(user, query_name, query_file, log)


def run(user, query_name, query, log, out_format, importFlag, updated_ds_list):
    # Call the service in gmql_rest_queries to send the query to the GMQL server to be executed.

    run_query(user, query_name, query, log, out_format, importFlag)

    #Save updated list of datasets
    list_datasets(user, updated_ds_list)


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)

def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-query_params")
    parser.add_argument("-query_output")
    parser.add_argument("-query_source")
    parser.add_argument("-query_log")
    parser.add_argument("-updated_ds_list")

    args = parser.parse_args()

    query = read_query(args.query_params)
    save(query, args.query_output, args.query_source)

    if(args.cmd == 'compile'):
        compile(args.user, query['name'], args.query_output, args.query_log)

    if(args.cmd == 'run'):
        run(args.user, query['name'], args.query_output, args.query_log, query['out_format'], query['importFlag'], args.updated_ds_list)


if __name__ == "__main__":
    __main__()
