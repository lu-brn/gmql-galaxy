#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Galaxy plugin to REST access to the GMQL services
# (Datasets)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import sys, os
import json
import argparse

import validators
from galaxy.datatypes import sniff

from rest_api_calls import auth_url_get, auth_url_post, auth_url_delete

from pprint import pprint


GMQL_URL = "http://genomic.elet.polimi.it/gmql-rest"


def list_datasets(user, output):
    """Retrieve the list of available datasets"""

    url = "{gmql}/dataSets".format(gmql=GMQL_URL)

    response = auth_url_get(user, url)

    decoder = json.JSONDecoder()
    datasets = decoder.decode(response.read())

    list_datasets = datasets['attributeList']['attribute']

    # Move the user private datasets to this list
    user_datasets = list()
    for ds in list_datasets:
        if not ds['name'].startswith("public."):
            user_datasets.append(ds)
            list_datasets.remove(ds)

    with open(output,'w') as f:
        for ds in user_datasets:
            f.write("{name}\n".format(name=ds['name']))
        for ds in list_datasets:
            f.write("{name}\n".format(name=ds['name'].strip("public.")))
    f.close()


def list_samples(user, output, ds):
    """List the samples of a given dataset"""

    url = "{gmql}/dataSets/{dataset}".format(gmql=GMQL_URL,dataset=ds)
    response = auth_url_get(user, url)

    decoder = json.JSONDecoder()
    samples = decoder.decode(response.read())

    list_s = samples['attributeList']['attribute']

    with open(output, 'w') as f_out:
        f_out.write("id\tsample\n")
        for s in list_s:
            name = s['name'].rsplit("/")
            f_out.write("{id}\t{name}\n".format(id=s['id'],name=name[-1]))
    f_out.close


def get_sample(user,output,ds,name,is_meta="false"):
    """Retrieve a sample or its metadata given its name and the dataset it belongs to"""
    # TODO: temporary version of the server on another port

    url = "http://genomic.elet.polimi.it:9997/gmql-rest/datasets/{ds}/{name}/{meta}".format(ds=ds,name=name,meta=is_meta)

    data = auth_url_get(user, url)

    try:
        result, is_multi_byte = sniff.stream_to_open_named_file(data, os.open(output, os.O_WRONLY | os.O_CREAT), output)
    except Exception as e:
        stop_err('Unable to fetch :\n%s' % (e))



def delete_dataset(user, output, ds):
    """Delete a dataset from the user's private space"""

    # Check if the given dataset is public. If it is, operation fails.
    if ds.startswith("public."):
        stop_err("Operation not allowed. This is a public dataset.")

    url = "{gmql}/dataSets/{dataset}".format(gmql=GMQL_URL,dataset=ds)

    response = auth_url_delete(user, url)

    with open(output, 'w') as f_out:
        f_out.write(response)
    f_out.close


def upload_samples(user, output, dataset, schema, samples):
    """Upload a dataset given the urls of the samples and their schema"""

    url = "{gmql}/dataSets/{dataset}/uploadSampleUrls".format(gmql=GMQL_URL,dataset=dataset)

    content = dict()

    # If schema type is given, add the option to the query. Otherwise, it check if the provided schema is a valid url.

    if schema == 'bed':
        url = url + '?schemaType=bed'
    elif schema == 'bedGraph':
        url = url + '?schemaType=bedGraph'
    elif schema == 'gtf':
        url = url + '?schemaType=gtf'
    elif schema == 'tab':
        url = url + '?schemaType=tab'
    elif schema == 'NarrowPeak':
        url = url + '?schemaType=NarrowPeak'
    elif schema == 'BroadPeak':
        url = url + '?schemaType=BroadPeak'
    elif schema == 'vcf':
        url = url + '?schemaType=vcf'
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

    response = auth_url_post(user, url, content, 'application/json')

    with open(output, 'w') as f_out:
        f_out.write(response.read())
    f_out.close


def download_samples(user, output, dataset, clean):
    """ Download the samples of the given dataset in form of a compressed zip archive.
    It first require the archive to be prepared. Note that :
    # clean = true: clean the previous folder if it exists and rebuild
    # clean = false: just send ready when it exists
    Then it requests the actual zip file. """

    # Check if the given dataset is public. If it is, operation fails.
    if dataset.startswith("public."):
        stop_err("Public datasets are not available to download.")

    url_prepare = "{gmql}/dataSets/{dataset}/preparaZip/{clean}".format(gmql=GMQL_URL,dataset=dataset,clean=clean)
    url_fetch = "{gmql}/dataSets/{dataset}/downloadZip".format(gmql=GMQL_URL, dataset=dataset)

    # Send request to prepare the dataset zip archive. If clean = 'false' and it already exists,
    # the outcome is 'oldZip'; 'ok' in any other positive case.
    auth_url_get(user, url_prepare)

    # Fetch the archive.
    data = auth_url_get(user, url_fetch)

    try:
        result, is_multi_byte = sniff.stream_to_open_named_file(data, os.open(output, os.O_WRONLY), output)
    except Exception as e:
        stop_err('Unable to fetch :\n%s' % (e))

    return result


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-dataset")
    parser.add_argument("-schema")
    parser.add_argument("-samples")
    parser.add_argument("-clean")

    args = parser.parse_args()

    if args.cmd == 'list':
        list_datasets(args.user, args.output)
    if args.cmd == 'samples':
        list_samples(args.user, args.output, args.dataset)
    if args.cmd == 'upload':
        upload_samples(args.user, args.output, args.dataset, args.schema, args.samples)
    if args.cmd == 'download':
        download_samples(args.user, args.output, args.dataset, args.clean)
    if args.cmd == 'delete':
        delete_dataset(args.user, args.output, args.dataset)


if __name__ == "__main__":
    __main__()
