# Galaxy plugin to REST access to the GMQL services
# (Datasets)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse

import validators
from galaxy.datatypes import sniff
import tempfile

from utilities import *

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

    try :
        response = auth_url_get(url, user)
    except urllib2.URLError as e:
        stop_err("Dataset not found for this user.\nCheck if it is the owner of this dataset.")

    decoder = json.JSONDecoder()
    samples = decoder.decode(response.read())

    list_s = samples['samples']

    with open(output, 'w') as f_out:
        for s in list_s:
            f_out.write("{id}\t{name}\t{ext}\n".format(id=s['id'], name=s['name'],ext=s['path'].rsplit('.',1)[1]))
    f_out.close



def delete_dataset(user, output, ds):
    """Delete a dataset from the user's private space"""

    call = 'delete_dataset'
    url = compose_url(module,call)
    url = url.format(datasetName=ds)

    #logging.debug('%s\n'%(url))

    try:
        response = auth_url_delete(user, url)
    except urllib2.URLError as e:
        stop_err("Dataset not found for this user.\nCheck if it is the owner of this dataset.")


    decoder = json.JSONDecoder()
    outcome = decoder.decode(response)

    with open(output, 'w') as f_out:
        f_out.write("Outcome: {result}".format(result=outcome['result']))
    f_out.close


def upload_samples_url(user, output, output1, dataset, schema, samples):
    """Upload a dataset given the urls of the samples and their schema"""

    logging.basicConfig(filename='/home/luana/gmql-galaxy/ds.log', level=logging.DEBUG, filemode='w')

    #Compose the url for the REST call
    call = 'upload_url'
    url = compose_url(module,call)
    url = url.format(datasetName=dataset)

    content = dict()

    # Put back escaped '&'
    samples = samples.replace('__amp__', '&')
    schema = schema.replace('__amp__', '&')

    # If schema type is given, add the option to the url. Otherwise, it check if the provided schema is a valid url.

    if schema in ['bed','bedGraph','gtf','tab','NarrowPeak','BroadPeak','vcf'] :
        url = add_url_param(url, module, call, schema)
    else:
        check_schema = validators.url(schema)
        if isinstance(check_schema, validators.utils.ValidationFailure): stop_err("Schema URL not valid")
        content.update(schema_file=schema)


    logging.debug(samples)

    # Samples are listed one per line. It lists them looking for the new line marker ('__cn__')
    samples_list = samples.split('__cn__')

    logging.debug(samples_list)

    # The regexp in input can allow a final empty string. The following removes it if present.
    if not samples_list[-1]:
        samples_list.remove("")

    # For each sample url, check if it is valid. If at least ones is not, upload fails
    # and which one is saved in the outcome.
    for s in samples_list:
        logging.debug(s)
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

    #Return the list of updated samples
    list_samples(user,output1,dataset)

    #Return the new list of datasets
    list_datasets(user, output)


def upload_samples(user, output, output1, dataset, schema, samples):
    """Upload a dataset from the local instance"""

    logging.basicConfig(filename='/home/luana/gmql-galaxy/upload.log', level=logging.DEBUG, filemode='w')

    #Compose the url for the REST call
    call = 'upload_data'
    url = compose_url(module, call)
    url = url.format(datasetName=dataset)



    # Create a new instance of a MultiPartForm object
    form = MultiPartForm()

    # If the schema type is give, add the option to the url.

    logging.debug(schema)

    if schema in ['bed','bedGraph','gtf','tab','NarrowPeak','BroadPeak','vcf'] :
        url = add_url_param(url, module, call, schema)
    else :
        # Prepare the schema given to be sent in the request
        form.add_file('schema','{ds}.xml'.format(ds=dataset), open(schema))

    logging.debug(url)

    # Read samples file path and add them to the form object
    # The structure is
    #   FILENAME    PATH

    with open(samples, "r") as file:
        s = map(lambda x: x.split('\t'), file)
        logging.debug(s.__str__())
        s.pop() # I need to get rid of last element, which is empty
        map(lambda x: form.add_file('file%d' % (s.index(x) + 1), x[0], open(x[1].rstrip('\n'))), s)

    # Post call

    body = str(form)

    response = auth_url_post(user, url, body, form.get_content_type())

    #Return the list of updated samples
    list_samples(user,output1,dataset)

    #Return the new list of datasets
    list_datasets(user, output)


def download_samples(user, output, dataset):
    """ Download the samples of the given dataset in form of a compressed zip archive."""

    call = 'download_zip'

    url = compose_url(module, call)
    url = url.format(datasetName=dataset)

    # Fetch the archive.
    try :
        data = auth_url_get(url, user)
    except urllib2.URLError as e:
        stop_err("Dataset not found for this user.\nCheck if it is the owner of this dataset.")

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

def import_samples(user, ds) :

    logging.basicConfig(filename='/home/luana/gmql-galaxy/ds.log', level=logging.DEBUG, filemode='w')

    # Retrieve the list of the samples in the resulting dataset
    # The list is stored in a temporary file
    temp = tempfile.NamedTemporaryFile(delete=False)
    list_samples(user, temp.name, ds)

    # Retrieve names and extensions of the samples
    with open(temp.name, "r") as t:
        #samples = map(lambda x: x.split('\t')[1].rstrip('\n'), t)
        samples = map(lambda x: helper_samples(x), t)
        logging.debug(samples.__str__())
    t.close()

    for s in samples:
        # Get the sample
        #logging.debug(s)
        logging.debug("{name}.{ext}".format(name=s['name'],ext=s['ext']),ds,s['name'])
        get_sample(user,"{name}.{ext}".format(name=s['name'],ext=s['ext']),ds,s['name'])
        # Get its metadata
        #TODO: temporary don't get metadata
        #logging.debug("{name}.{ext}.meta".format(name=s['name'],ext=s['ext']),ds,s['name'])
        #get_sample_meta(user,"{name}.{ext}.meta".format(name=s['name'],ext=s['ext']),ds,s['name'])

    os.remove(temp.name)

def helper_samples(s):
    """From a list of samples retrieve name and extension"""
    split = s.split('\t')
    sample = dict()
    sample.update(name=split[1])
    sample.update(ext=split[2].rstrip('\n'))

    return sample

def get_schema(user, ds, file) :
    """Get the schema field of the input dataset and save it in file"""

    call = "schema"

    url = compose_url(module, call)
    url = url.format(datasetName=ds)

    response = auth_url_get(url, user)

    schema = json.load(response)

    with open(file,'w') as f_out:
        for f in schema['fields'] :
            f_out.write('{field}\t{type}\n'.format(field=f['name'],type=f['type']))



def stop_err(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()


def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("-opt_out1")
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
    if args.cmd == 'delete':
        delete_dataset(args.user, args.output, args.dataset)
    if args.cmd == 'upload_url':
        upload_samples_url(args.user, args.output, args.opt_out1, args.dataset, args.schema, args.samples)
    if args.cmd == 'upload' :
        upload_samples(args.user, args.output, args.opt_out1, args.dataset, args.schema, args.samples)
    if args.cmd == 'import':
        import_samples(args.user, args.dataset)
    if args.cmd == 'download' :
        download_samples(args.user,args.output,args.dataset)


if __name__ == "__main__":
    __main__()
