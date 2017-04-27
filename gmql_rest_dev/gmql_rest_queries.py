#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Galaxy plugin to REST access to the GMQL services
# (Queries)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

from rest_api_calls import read_token, auth_url_get, auth_url_post
from gmql_rest_datasets import list_samples, get_sample

import argparse
import json
import sys, os
from time import sleep
import tempfile
import csv
from pprint import pprint

GMQL_URL = "http://genomic.elet.polimi.it/gmql-rest"

# Default Execution type for now is spark
execution = "spark"


def save_query(user, filename, query, log_file, jobid='null'):
    """Save a query given its fileName, the query, and its jobid (when it is an already existing file)"""

    # Jobid is null for new queries; otherwise use the existing ones
    # TODO: save a pre-loaded query

    jobid = save(user, filename, query)

    with open(log_file, 'w') as f:
        f.write("{file} has been  saved.\n Jobid = {job}".format(file=filename, job=jobid))
    f.close()

    # TODO: Update queries history

    return jobid


def save(user, filename, query, jobid='null'):
    """Helper function that saves a query and returns its jobid
    (but without additional operations like logging or updating queries history"""

    url = "{gmql}/queries/save/{file}/{jobid}".format(gmql=GMQL_URL,file=filename,jobid=jobid)

    query = query.replace('__dq__', '"')
    query = query.replace('__sq__', "'")
    query = query.replace('__cn__', '\n')

    # A successful saving return the jobid
    jobid = auth_url_post(user, url, query, 'text/plain')

    return jobid.read()


def compile_query(user, filename, query, log_file):
    """Compile the given query"""

    # First save the query
    jobid = save(user, filename, query)

    # Then ask it to be compiled
    url = "{gmql}/queries/compilev2/{jobid}/{execution}".format(gmql=GMQL_URL,jobid=jobid,execution=execution)

    # Compilation returns the result dataset name.
    # The actual outcome and eventual error message must be retrieved from the job log
    response = auth_url_get(user, url)
    target_ds = response.read().decode('utf8')
    log = read_status(user, target_ds)

    status = log['gmqlJobStatusXML']['status']
    message = log['gmqlJobStatusXML']['message']

    if status == 'COMPILE_SUCCESS':
        with open(log_file, 'w') as f:
            f.write("{status}\n{dataset}".format(status=status, dataset=target_ds))
        f.close()
    if status == 'COMPILE_FAILED':
        with open(log_file, 'w') as f:
            f.write("{status}\n{message}".format(status=status, message=message))
        f.close()
        stop_err("Compilation failed.\nSee log for details.")


def run_query(user, filename, query, log_file, rs_format):
    """Run the given query. It returns an execution log and the resulting dataset."""

    # First save the query
    jobid = save(user, filename, query)

    # Then ask it to be executed
    if rs_format == "gtf":
        is_gtf = "true"
    else:
        is_gtf = "false"

    status = "NEW"

    url = "{gmql}/queries/runv2/{jobid}/{output}/{execution}".format(gmql=GMQL_URL,jobid=jobid,output=is_gtf,execution=execution)
    response = auth_url_get(user, url)
    target_ds = response.read().decode('utf8')

    while status != "SUCCESS" and status != "EXEC_FAILED" and status != "DS_CREATION_FAILED":
        log = read_status(user, target_ds)
        status = log['gmqlJobStatusXML']['status']
        sleep(5)

    message = log['gmqlJobStatusXML']['message']
    time = log['gmqlJobStatusXML']['execTime']

    if status == "EXEC_FAILED" or status == "DS_CREATION_FAILED":
        with open(log_file, 'w') as f:
            f.write("{status}\n{message}\n{execTime}".format(status=status, message=message, execTime=time))
        f.close()
        stop_err("Execution failed.\nSee log for details")

    if status == "SUCCESS":
        ext_log = read_complete_log(user, target_ds)
        job_list = ext_log['jobList']['jobs']
        jobs = ""
        for j in job_list:
            jobs = "{j_list}{j}\n".format(j_list=jobs, j=j)

        with open(log_file, 'w') as f:
            f.write("{status}\n"
                    "{message}\n"
                    "{execTime}\n"
                    "\n"
                    "{jobs}\n".format(status=status, message=message, execTime=time, jobs=jobs))
        f.close()

        ds = log['gmqlJobStatusXML']['datasetNames']

        # Retrieve the list of the samples in the resulting dataset
        # The list is stored in a temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        list_samples(user,temp.name,ds)

        # Create a list of the samples
        samples = list()
        with open(temp.name,"r") as t :
            dic = csv.DictReader(t,delimiter="\t")
            for item in dic:
                samples.append(item.get("sample"))
        t.close()

        for s in samples :
            # Get the sample
            get_sample(user,"{name}".format(name=s), ds, s)
            # Get its metadata
            get_sample(user,"{name}.meta".format(name=s), ds, s,"true")

        os.remove(temp.name)


def read_status(user, target):
    """Given the resulting dataset name, it retrieves the status of the current operation
    (as a JSON file)"""
    url = "{gmql}/jobs/{target_ds}/trace".format(gmql=GMQL_URL,target_ds=target)

    stat_obj = auth_url_get(user, url)
    decoder = json.JSONDecoder()
    stat = decoder.decode(stat_obj.read())

    return stat


def read_complete_log(user, target):
    """Given the resulting dataset name, it retrieves the complete log of the latest operation
    (as a JSON file)"""
    url = "{gmql}/jobs/{target_ds}/log".format(gmql=GMQL_URL,target_ds=target)

    log_obj = auth_url_get(user, url)
    decoder = json.JSONDecoder()
    log = decoder.decode(log_obj.read())

    return log


def show_jobs(user, output):
    """Retrieve the list of the user's jobs"""

    url = "{gmql}/jobs".format(gmql=GMQL_URL)
    job_obj = auth_url_get(user, url)
    decoder = json.JSONDecoder()
    job_js = decoder.decode(job_obj.read())

    job_list = job_js['jobList']['jobs']
    job_out = list()

    # For each job in the list retrieve the relative status info
    for j in job_list:
        job = dict()
        job.update(id=j)
        status = read_status(user, j)
        job.update(message=status['gmqlJobStatusXML']['message'],
                   status=status['gmqlJobStatusXML']['status'],
                   ds=status['gmqlJobStatusXML']['datasetNames'],
                   time=status['gmqlJobStatusXML']['execTime'])
        job_out.append(job)

    with open(output, 'w') as f:
        for j in job_out:
            f.write("{jobid}\t"
                    "{status}\t"
                    "{message}\t"
                    "{ds}\t"
                    "{time}\n".format(jobid=j.get('id'), status=j.get('status'), message=j.get('message'),
                                      ds=j.get('ds'), time=j.get('time')))
    f.close()


def stop_err(msg):
    sys.stderr.write("%s\n" % msg)


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-name")
    parser.add_argument("-value")
    parser.add_argument("-log")
    parser.add_argument("-format")
    parser.add_argument("-result_dir")


    args = parser.parse_args()

    if args.cmd == 'save':
        save_query(args.user, args.name, args.value, args.log)
    if args.cmd == 'compile':
        compile_query(args.user, args.name, args.value, args.log)
    if args.cmd == 'execute':
        run_query(args.user, args.name, args.value, args.log, args.format)
    if args.cmd == 'jobs':
        show_jobs(args.user, args.log)


if __name__ == "__main__":
    __main__()
