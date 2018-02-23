# Galaxy plugin to REST access to the GMQL services
# (Queries)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse
import tempfile
from time import sleep

from gmql_rest_datasets import list_datasets, import_samples
from utilities import *

module_execution = 'query_exec'
module_monitor = 'query_monitor'


def check_input(query):

    # Clean the input from Galaxy escape characters.

    query = query.replace('__dq__', '"')
    query = query.replace('__sq__', "'")
    query = query.replace('__gt__', ">")
    query = query.replace('__lt__', "<")
    query = query.replace('__cn__', '\n')


    return query


def compile_query(user, filename, query, log_file):
    """Compile the given query"""

    call = 'compile'

    #Read query from file
    with open(query, 'r') as f_in:
        query_text = f_in.read()

    #Check the input
    query_cl = check_input(query_text)


    # Then ask it to be compiled
    url = compose_url(module_execution, call)

    outcome = post(url, query_cl, user=user, content_type='text')

    status = outcome['status']
    message = outcome['message']
    target_ds = outcome['id']

    if status == 'COMPILE_SUCCESS':
        with open(log_file, 'w') as f:
            f.write("{status}\n{dataset}".format(status=status, dataset=target_ds))
        f.close()
    if status == 'COMPILE_FAILED':
        with open(log_file, 'w') as f:
            f.write("{status}\n{message}".format(status=status, message=message))
        f.close()
        stop_err("Compilation failed.\nSee log for details.")


def run_query(user, filename, query, log_file, rs_format, importResult=True):
    """Run the given query. It returns an execution log and the resulting dataset."""


    call = 'run'

    # Read query from file
    with open(query, 'r') as f_in:
        query_text = f_in.read()

    # Check the input
    query_cl = check_input(query_text)

    # Then ask it to be executed

    status = "NEW"

    url = compose_url(module_execution, call)
    url = url.format(name=filename,output=rs_format)

    outcome = post(url, query_cl, user=user, content_type='text')

    jobid = outcome['id']

    while status != "SUCCESS" and status != "EXEC_FAILED" and status != "DS_CREATION_FAILED":
        log = read_status(user, jobid)
        status = log['status']
        sleep(5)

    message = log['message']
    time = log['executionTime']

    if status == "EXEC_FAILED" or status == "DS_CREATION_FAILED":
        with open(log_file, 'w') as f:
            f.write("{status}\n{message}\n{execTime}".format(status=status, message=message, execTime=time))
        f.close()
        stop_err("Execution failed.\nSee log for details")

    if status == "SUCCESS":
        ext_log = read_complete_log(user, jobid)
        job_list = ext_log['log']
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

        importResult = bool(importResult)

        if importResult:
            # For now, it gets only the final result (it's easier to deal later with simple collections
            # than a nested ones)

            ds = log['datasets'][-1]
            ds_name = ds.get('name')
            import_samples(user, ds_name)


def read_status(user, jobid):
    """Given the job id, it retrieves the status of the current operation
    (as a JSON file)"""

    call = 'status'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    status = get(url, user=user, response_type='json')

    return status



def read_complete_log(user, jobid):
    """Given the jobid, it retrieves the complete log of the latest operation
    (as a JSON file)"""

    call = 'log'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    log = get(url, user=user, response_type='json')

    return log


def show_jobs(user, output):
    """Retrieve the list of the user's jobs"""

    call = 'jobs'

    url = compose_url(module_monitor, call)

    jobs = get(url, user=user, response_type='json')

    jobs_list = jobs['jobs']
    jobs_out = list()

    # For each job in the list retrieve the relative status info
    for j in jobs_list:
        job = dict()
        j_id = j['id']
        job.update(id=j_id)
        trace = read_status(user, j_id)

        status = trace['status']
        if status == 'SUCCESS' :
            job.update(message=trace['message'],
                       status=status,
                       ds=trace['datasets'][0]['name'],
                       time=trace['executionTime'])
        else :
            job.update(message=trace['message'],
                       status=status,
                       ds=trace['datasets'][0]['name'])

        jobs_out.append(job)

    with open(output, 'w') as f:
        for j in jobs_out:
            f.write("{jobid}\t"
                    "{status}\t"
                    "{message}\t"
                    "{ds}\t"
                    "{time}\n".format(jobid=j.get('id'), status=j.get('status'), message=j.get('message'),
                                      ds=j.get('ds'),time=j.get('time')))
    f.close()

def stop_query(user,jobid,output) :
    """Stop the execution of the given job"""

    call = 'stop'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    outcome = get(url, user=user, response_type='json')

    with open(output,'w') as f_out :
        json.dump(outcome, f_out)



def stop_err(msg):
    sys.stderr.write("%s\n" % msg)


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("-user")
    parser.add_argument("-cmd")
    parser.add_argument("-name")
    parser.add_argument("-query")
    parser.add_argument("-queryNew")
    parser.add_argument("-queryLocal")
    parser.add_argument("-log")
    parser.add_argument("-job")
    parser.add_argument("-format")
    parser.add_argument("-importFlag")
    parser.add_argument("-add_output")


    args = parser.parse_args()

    if args.cmd == 'compile':
        compile_query(args.user, args.name, args.query, args.log)
    if args.cmd == 'execute':
        run_query(args.user, args.name, args.query, args.log, args.format, args.importFlag)
        list_datasets(args.user,args.add_output)
    if args.cmd == 'jobs':
        show_jobs(args.user, args.log)
    if args.cmd == 'stop' :
        stop_query(args.user, args.job, args.log)


if __name__ == "__main__":
    __main__()
