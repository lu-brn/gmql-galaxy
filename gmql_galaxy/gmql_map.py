# GMQL Editor: composition of a new MAP statement.
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse
import json

import datamng


def create_map(source1, source2, params, target_q):
    """ Create a gmql MAP statement starting from the given params
        The result structure serves as the actual query skeleton and it's so formed: 
            - target_ds : a runtime generated identifier for the target dataset 
            - query body: type of statement and its attributes
            - sources_ds: reference to the files containing the info about the sources dataset collections. """

    # Open param file

    with open(params, 'r') as f_in:
        try:
            params_json = json.load(f_in)
        except ValueError:
            stop_err("An error occurred with the parameters parsing")
    f_in.close

    query = dict()

    # Reference to the target
    datamng.create_new_target(query)

    # See if inputs are collections or precompiled queries
    in_mode1 = params_json['input1']['in_mode']
    in_mode2 = params_json['input2']['in_mode']

    # Add reference to sources
    datamng.ref_binary_input(source1, in_mode1, source2, in_mode2, target_q, query)


    #TODO: predicates & query body


    #Save the result
    if in_mode1 == 'q' :
        if in_mode2 == 'q' :
            datamng.save_result_2(target_q, query, source1=source1, source2=source2)
        else :
            datamng.save_result_2(target_q, query, source1=source1)
    else :
        if in_mode2 == 'q' :
            datamng.save_result_2(target_q, query, source2=source2)
        else :
            datamng.save_result_2(target_q, query)



def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("source1")
    parser.add_argument("source2")
    parser.add_argument("params")
    parser.add_argument("query")

    args = parser.parse_args()

    create_map(args.source1, args.source2, args.params, args.query)

if __name__ == "__main__":
    __main__()

def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()