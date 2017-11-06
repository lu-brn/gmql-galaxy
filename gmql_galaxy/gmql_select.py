# GMQL Editor: composition of a new SELECT statement.
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

from datamng import *

import argparse
import json
import sys

def meta_predicates(meta_list) :
    """Parsing and creation of the Metadata Predicates.
    Expression whose atomic predicates are in the form: attribute-name (== | > | < | >= | <=) (value | decimalNumber).
    Atomic predicates are concatenated by means of the OR, AND and NOT operators."""

    plist = list()

    # Ignore logical operator before first predicate
    meta_list[0]['log_op'] = 'none'

    for p in meta_list:

        if p['log_op'] == 'none':
            log_op = ''
        else:
            log_op = p['log_op']

        exp_s = p['exp']

        if exp_s == 'eq':
            exp = '=='
        if exp_s == 'gt':
            exp = '>'
        if exp_s == 'lt':
            exp = '<'
        if exp_s == 'ge':
            exp = '>='
        if exp_s == 'le':
            exp = '<='

        att = p['attribute']
        value = p['value']

        if p['neg'] == True:
            predicate = '{log} NOT ( {att} {exp} {value} ) '.format(log=log_op, att=att, exp=exp, value=value)
        else:
            predicate = '{log} {att} {exp} {value} '.format(log=log_op, att=att, exp=exp, value=value)

        plist.append(predicate)

    pm = ''.join(plist)

    return pm

def region_predicates(region_list):
    """Parsing and creation of the Region Predicates.
    Expression whose atomic predicates are in the form: attribute-name (== | > | < | >= | <=) (value | decimalNumber).
    Atomic predicates are concatenated by means of the OR, AND and NOT operators."""

    plist = list()

    # Ignore logical operator before first predicate
    region_list[0]['log_op'] = 'none'

    for p in region_list:

        if p['log_op'] == 'none':
            log_op = ''
        else:
            log_op = p['log_op']

        exp_s = p['exp']

        if exp_s == 'eq':
            exp = '=='
        if exp_s == 'gt':
            exp = '>'
        if exp_s == 'lt':
            exp = '<'
        if exp_s == 'ge':
            exp = '>='
        if exp_s == 'le':
            exp = '<='

        att = p['field']
        value = p['value']

        if p['neg'] == True:
            predicate = '{log} NOT ( {att} {exp} {value} ) '.format(log=log_op, att=att, exp=exp, value=value)
        else:
            predicate = '{log} {att} {exp} {value} '.format(log=log_op, att=att, exp=exp, value=value)

        plist.append(predicate)

    pr = ''.join(plist)
    if pr :
        pr = 'region: {pr}'.format(pr=pr)

    return pr


def create_select(source,params,target_q) :
    """ Create a gmql SELECT statement starting from the given params
    The result structure serves as the actual query skeleton and it's so formed: 
        - target_ds : a runtime generated identifier for the target dataset 
        - query body: type of statement and its parameters
        - sources_ds: reference to the file containing the info about the source dataset collection. """

    # Open param file

    with open(params, 'r') as f_in:
        try:
            params_json = json.load(f_in)
        except ValueError:
            stop_err("An error occurred with the parameters parsing")
    f_in.close

    query = dict()

    # Reference to the target

    create_new_target(query)

    # Add reference to source
    in_mode = params_json['input']['in_mode']
    ref_unary_input(source, in_mode, target_q, query)

    # Parse predicates

    meta_list = params_json['meta_pred']['predicates_list']
    region_list = params_json['region_pred']['predicates_list']

    if meta_list :
        pm = meta_predicates(meta_list)
    else :
        pm = ''

    if region_list :
        pr = region_predicates(region_list)
    else :
        pr = ''


    # Compose query body

    mix_pred = list( filter( lambda x: x, [pm,pr]))
    mix_pred = ' ; '.join(mix_pred)

    query.update(target_q = 'SELECT\t{predicates}'.format(predicates=mix_pred))

    # Save the result query

    if in_mode == 'q' :
        save_result_1(target_q, query, source=source)
    else :
        save_result_1(target_q, query)

    # TODO: temporary here; will be moved in a specific module

    materialize = params_json['materialize']

   #TODO

def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("params")
    parser.add_argument("query")

    args = parser.parse_args()

    create_select(args.source,args.params,args.query)

if __name__ == "__main__":
    __main__()

def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()

