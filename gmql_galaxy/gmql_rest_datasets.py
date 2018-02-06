# Galaxy plugin to REST access to the GMQL services
# (Datasets)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse

import validators
import tempfile

from utilities import *

import logging

module = 'repository'


def list_datasets(user, output, saveResult=True):
    """Retrieve the list of available datasets"""

    call = 'list_datasets'
    url = compose_url(module,call)

    datasets = get(url, user=user)
    list_datasets = datasets['datasets']

    if saveResult:
        with open(output,'w') as f:
            for ds in list_datasets:
                f.write("{name}\t{owner}\n".format(name=ds['name'],owner=ds['owner']))
        f.close()
    else:
        return list_datasets


def list_samples(user, output, ds):
    """List the samples of a given dataset"""

    call = 'list_samples'
    url = compose_url(module,call)

    # Specify for which dataset.
    # If it's a public dataset, the 'public.' prefix must be added to the dataset name

    # Check if the ds is public or not
    owner = ''
    for d in list_datasets(user, '', False):
        if d['name'] == ds :
            owner = d['owner']

    if (owner=='public'):
        url = url.format(datasetName='public.'+ ds)
    else :
        url = url.format(datasetName=ds)

    samples = get(url, user=user)
    list_s = samples['samples']

    with open(output, 'w') as f_out:
        for s in list_s:
            f_out.write("{id}\t{name}\t{ext}\n".format(id=s['id'], name=s['name'],ext=s['path'].rsplit('.',1)[1]))


def rename_dataset(user, output, ds, new):
    """Rename a dataset from the user's private space"""

    call = 'rename_dataset'
    url = compose_url(module,call)
    url = url.format(datasetName=ds, newDatasetName=new)

    outcome = get(url, user=user)

    # Return the updated list of user's datasets
    list_datasets(user, output)

    # Write on stdout the operation outcome
    sys.stdout.write("Rename: {result}".format(result=outcome['result']))


def delete_dataset(user, output, ds):
    """Delete a dataset from the user's private space"""

    call = 'delete_dataset'
    url = compose_url(module,call)
    url = url.format(datasetName=ds)

    outcome = delete(url, user=user)

    #Return the updated list of user's datasets
    list_datasets(user, output)

    #Write on stdout the operation outcome
    sys.stdout.write("Delete: {result}".format(result=outcome['result']))


def upload_samples_url(user, output, dataset, schema, samples, updatedDsList):
    """Upload a dataset given the urls of the samples and their schema"""

    #Compose the url for the REST call
    call = 'upload_url'
    url = compose_url(module,call)
    url = url.format(datasetName=dataset)

    content = dict()

    # Put back escaped '&'
    samples = samples.replace('__amp__', '&')
    schema = schema.replace('__amp__', '&')

    # If schema type is given, add the option to the url. Otherwise, it check if the provided schema is a valid url.

    params = dict ()

    if schema in ['bed','bedGraph','NarrowPeak','BroadPeak','vcf'] :
        params = add_url_param(params, module, call, schema)
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
            stop_err("Some URLs are not valid.\nCheck the output file for details.")

    content.update(data_files=samples_list)

    result = post(url, content, user=user, params=params)

    #Return the list of updated samples
    list_imported(result, output)

    #Return the updated list of samples
    list_datasets(user, updatedDsList)


def upload_samples(user, output, dataset, schema, samples, updatedDsList):
    """Upload a dataset from the local instance"""


    #Compose the url for the REST call
    call = 'upload_data'
    url = compose_url(module, call)
    url = url.format(datasetName=dataset)

    #Files dict for payload
    files = dict ()

    # If the schema type is give, add the option to the url.
    params = dict ()


    if schema in ['bed','bedGraph','NarrowPeak','BroadPeak','vcf'] :
        params = add_url_param(params, module, call, schema)
    else :
        # Add the schema given to the payload dictionary
        files.update({'schema' : ('{ds}.xml'.format(ds=dataset), open(schema, 'rb'))})

    # Read samples file path and add them to the form object
    # The structure is
    #   FILENAME    PATH

    with open(samples, "r") as file:
        s = map(lambda x: x.split('\t'), file)
        s.pop() # I need to get rid of last element, which is empty
        map(lambda x: files.update({'file%d' % (s.index(x) + 1) : (x[0], open(x[1].rstrip('\n'), 'rb'))}), s)

    # Post call

    result = post(url, files, user=user, params=params, content_type='multiform')

    #Return the list of updated samples
    list_imported(result, output)


    #Return the updated list of samples
    list_datasets(user, updatedDsList)



def list_imported(result, output) :
    """When uploading a ds, the server returns a json object describing what has been imported
    INPUT JSON FIELDS -
    imported: samples imported with their metadata
    autoMetadata: samples imported without metadata (those have been auto generated) """

    samples = list ()

    if 'imported' in result :
        imported = result.get('imported')
        if imported:
            samples.append(result.get('imported'))
    if 'autoMetadata' in result :
        am = result.get('autoMetadata')
        if am :
            samples.append(result.get('autoMetadata'))


    with open(output, 'w') as f_out:
        for l in samples:
            for s in l :
                if 'id' in s and s['id']:
                    id = s['id']
                else :
                    id = l.index(s) + 1
                if 'path' in s :
                    ext = s['path'].rsplit('.')[1]
                else :
                    n = s['name'].rsplit('.')
                    if n.__len__()>1 :
                        ext = n[1]
                    else :
                        ext = ''

                name = s['name']

                f_out.write("{id}\t{name}\t{ext}\n".format(id=id, name=name,ext=ext))


def download_samples(user, output, dataset):
    """ Download the samples of the given dataset in form of a compressed zip archive."""

    call = 'download_zip'

    url = compose_url(module, call)
    url = url.format(datasetName=dataset)

    # Fetch the archive.

    data = get(url, user=user, response_type='zip')

    with open(output, 'wb') as fd:
        for chunk in data.iter_content(chunk_size=128):
            fd.write(chunk)

def get_sample(user, output, dataset, name):
    """Retrieve a sample given its name and the dataset it belongs to"""

    call = 'download_sample'

    url = compose_url(module,call)
    url = url.format(datasetName=dataset,sample=name)

    data = get(url, user=user, response_type='file')

    with open(output, 'wb') as fd:
        for chunk in data.iter_content(chunk_size=128):
            fd.write(chunk)


def get_sample_meta(user, output, dataset, name):
    """Retrieve a sample metadata given its name and the dataset it belongs to"""

    call = 'download_meta'

    url = compose_url(module, call)
    url = url.format(datasetName=dataset, sample=name)

    data = get(url, user=user, response_type='file')

    with open(output, 'wb') as fd:
        for chunk in data.iter_content(chunk_size=128):
            fd.write(chunk)

def import_samples(user, ds, isMulti=False) :


    # Retrieve the list of the samples in the resulting dataset
    # The list is stored in a temporary file
    temp = tempfile.NamedTemporaryFile(delete=False)
    list_samples(user, temp.name, ds)

    # Retrieve names and extensions of the samples
    with open(temp.name, "r") as t:
        samples = map(lambda x: helper_samples(x), t)
    t.close()

    if isMulti:
        #Prefix the file name with the dataset name
        for s in samples:
            # Get the sample
            get_sample(user, "{ds}#sample_{name}.{ext}".format(ds=ds,name=s['name'].replace('_', ''), ext=s['ext']), ds, s['name'])
            # Get its metadata
            get_sample_meta(user, "{ds}#metadata_{name}.meta".format(ds=ds,name=s['name'].replace('_', ''), ext=s['ext']), ds, s['name'])
    else:
        for s in samples:
            # Get the sample
            get_sample(user, "sample_{name}.{ext}".format(name=s['name'].replace('_',''), ext=s['ext']), ds, s['name'])
            # Get its metadata
            get_sample_meta(user,"metadata_{name}.meta".format(name=s['name'].replace('_',''),ext=s['ext']),ds,s['name'])

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

    logging.basicConfig(filename='/home/luana/gmql-galaxy/ds.log', level=logging.DEBUG, filemode='w')

    call = "schema"

    url = compose_url(module, call)

    # Check if the ds is public or not
    owner = ''
    for d in list_datasets(user, '', False):
        if d['name'] == ds :
            owner = d['owner']

    if (owner=='public'):
        url = url.format(datasetName='public.'+ ds)
    else :
        url = url.format(datasetName=ds)

    schema = get(url, user=user)


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
    parser.add_argument("-new_name")
    parser.add_argument("-schema")
    parser.add_argument("-samples")
    parser.add_argument("-add_output")

    args = parser.parse_args()

    if args.cmd == 'list':
        list_datasets(args.user, args.output)
    if args.cmd == 'samples':
        list_samples(args.user, args.output, args.dataset)
    if args.cmd == 'rename' :
        rename_dataset(args.user, args.output, args.dataset, args.new_name)
    if args.cmd == 'delete':
        delete_dataset(args.user, args.output, args.dataset)
    if args.cmd == 'schema' :
        get_schema(args.user, args.dataset, args.output)
    if args.cmd == 'upload_url':
        upload_samples_url(args.user, args.output, args.dataset, args.schema, args.samples, args.add_output)
    if args.cmd == 'upload' :
        upload_samples(args.user, args.output, args.dataset, args.schema, args.samples, args.add_output)
    if args.cmd == 'import':
        import_samples(args.user, args.dataset)
    if args.cmd == 'download' :
        download_samples(args.user,args.output,args.dataset)


if __name__ == "__main__":
    __main__()
