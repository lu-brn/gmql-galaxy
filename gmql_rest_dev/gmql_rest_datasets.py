#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Galaxy plugin to REST access to the GMQL services
# (Datasets)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse

import validators
from galaxy.datatypes import sniff

from rest_api_calls import *

import logging

module = 'repository'


def list_datasets(user, output):
    """Retrieve the list of available datasets"""

    call = 'list_datasets'
    url = compose_url(module,call)

    response = auth_url_get(url, user)

    decoder = json.JSONDecoder()
    datasets = decoder.decode(response.read())

    list_datasets = datasets['datasets']

    with open(output,'w') as f:
        for ds in list_datasets:
            f.write("{name}\t{owner}\n".format(name=ds['name'],owner=ds['owner']))
    f.close()


def list_samples(user, output, ds, owner=''):
    """List the samples of a given dataset"""

    call = 'list_samples'
    url = compose_url(module,call)

    # Specify for which dataset.
    # If it's a public dataset, the 'public.' prefix must be added to the dataset name
    if (owner=='public'):
        url = url.format(datasetName='public.'+ ds)
    else :
        url = url.format(datasetName=ds)

    response = auth_url_get(url, user)

    decoder = json.JSONDecoder()
    samples = decoder.decode(response.read())

    list_s = samples['samples']

    with open(output, 'w') as f_out:
        for s in list_s:
            f_out.write("{id}\t{name}\n".format(id=s['id'], name=s['name']))
    f_out.close



def delete_dataset(user, output, ds):
    """Delete a dataset from the user's private space"""

    call = 'delete_dataset'
    url = compose_url(module,call)
    url = url.format(datasetName=ds)

    response = auth_url_delete(user, url)


    decoder = json.JSONDecoder()
    outcome = decoder.decode(response)

    with open(output, 'w') as f_out:
        f_out.write("Outcome: {result}".format(result=outcome['result']))
    f_out.close


def upload_samples_url(user, output, dataset, schema, samples):
    """Upload a dataset given the urls of the samples and their schema"""

    #Compose the url for the REST call
    call = 'upload_url'
    url = compose_url(module,call)
    url = url.format(datasetName=dataset)

    content = dict()

    # If schema type is given, add the option to the url. Otherwise, it check if the provided schema is a valid url.

    if schema in ['bed','bedGraph','gtf','tab','NarrowPeak','BroadPeak','vcf'] :
        url = add_url_param(url, module, call, schema)
    else:
        check_schema = validators.url(schema)
        if isinstance(check_schema, validators.utils.ValidationFailure): stop_err("Schema URL not valid")
        content.update(schema_file=schema)

    # Samples are listed one per line. It lists them looking for the new line marker ('__cn__')
    samples_list = samples.split('__cn__')

    # The regexp in input can allow a final empty string. The following removes it if present.
    if not samples_list[-1]:
        samples_list.remove("")

    # For each sample url, check if it is valid. If at least ones is not, upload fails
    # and which one is saved in the outcome.
    for s in samples_list:
        check_url = validators.url(s)
        if isinstance(check_url, validators.utils.ValidationFailure):
            with open(output, 'w') as f_out:
                f_out.write("This resource couldn't be loaded (invalid url)\n")
                f_out.write("Line %d: %s" % (samples_list.index(s) + 1, s))
            f_out.close
            stop_err("Some URLs are not valid.\nCheck the output file for details.")

    content.update(data_files=samples_list)
    content = json.dumps(content)

    response = auth_url_post(user, url, content)

    #TODO: unfold result and read what has been imported

    with open(output, 'w') as f_out:
        f_out.write(response.read())
    f_out.close

def upload_samples(user, output, dataset, schema, samples):
    """Upload a dataset from the local instance"""

    #Compose the url for the REST call
    call = 'upload_data'
    url = compose_url(module, call)
    url = url.format(datasetName=dataset)

    # Create a new instance of a MultiPartForm object
    form = MultiPartForm()

    # If the schema type is give, add the option to the url.

    if schema in ['bed','bedGraph','gtf','tab','NarrowPeak','BroadPeak','vcf'] :
        url = add_url_param(url, module, call, schema)
    else :
        # Prepare the schema given to be sent in the request
        form.add_file('schemaFile','schema', open(schema))

    # Read samples file path and add them to the form object
    # The structure is
    #   FILENAME    PATH

    with open(samples, "r") as file:
        s = map(lambda x: x.split('\t'), file)
        s.pop() # I need to get rid of list element, which is empty
        map(lambda x: form.add_file('file%d' % (s.index(x) + 1), x[0], open(x[1].rstrip('\n'))), s)

    # Post call

    body = str(form)
    response = auth_url_post(user, url, body, form.get_content_type())

    # Write output
    # TODO: unfold result and read what has been imported

    with open(output, 'w') as f_out:
        f_out.write(response.read())


def download_samples(user, output, dataset):
    """ Download the samples of the given dataset in form of a compressed zip archive."""

    call = 'download_zip'

    url = compose_url(module, call)
    url = url.format(datasetName=dataset)

    # Fetch the archive.
    data = auth_url_get(url, user)

    try:
        result, is_multi_byte = sniff.stream_to_open_named_file(data, os.open(output, os.O_WRONLY), output)
    except Exception as e:
        stop_err('Unable to fetch :\n%s' % (e))

    return result


def get_sample(user, output, dataset, name):
    """Retrieve a sample given its name and the dataset it belongs to"""

    call = 'download_sample'

    url = compose_url(module,call)
    url = url.format(datasetName=dataset,sample=name)

    data = auth_url_get(url, user, 'file')

    try:
        result, is_multi_byte = sniff.stream_to_open_named_file(data, os.open(output, os.O_WRONLY | os.O_CREAT), output)
    except Exception as e:
        stop_err('Unable to fetch :\n%s' % (e))


def get_sample_meta(user, output, dataset, name):
    """Retrieve a sample metadata given its name and the dataset it belongs to"""

    call = 'download_meta'

    url = compose_url(module, call)
    url = url.format(datasetName=dataset, sample=name)

    data = auth_url_get(url, user, 'file')

    try:
        result, is_multi_byte = sniff.stream_to_open_named_file(data, os.open(output, os.O_WRONLY | os.O_CREAT), output)
    except Exception as e:
        stop_err('Unable to fetch :\n%s' % (e))



def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()


def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-dataset")
    parser.add_argument("-owner")
    parser.add_argument("-schema")
    parser.add_argument("-samples")

    args = parser.parse_args()

    if args.cmd == 'list':
        list_datasets(args.user, args.output)
    if args.cmd == 'samples':
        list_samples(args.user, args.output, args.dataset, args.owner)
    if args.cmd == 'upload_url':
        upload_samples_url(args.user, args.output, args.dataset, args.schema, args.samples)
    if args.cmd == 'upload' :
        upload_samples(args.user, args.output, args.dataset, args.schema, args.samples)
    if args.cmd == 'download':
        download_samples(args.user, args.output, args.dataset)
    if args.cmd == 'delete':
        delete_dataset(args.user, args.output, args.dataset)


if __name__ == "__main__":
    __main__()
