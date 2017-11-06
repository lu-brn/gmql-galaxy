# Galaxy plugin to REST access to the GMQL services
# (Queries)
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

import argparse
import tempfile
from time import sleep

from gmql_rest_datasets import list_samples, get_sample, get_sample_meta
from utilities import *
from gmql_compositor import *

module_execution = 'query_exec'
module_monitor = 'query_monitor'


def check_input(q_type, query):

    if q_type == 'local' :
        # Retrieve the query data and convert it in an actual one and then clean it
        cm = Compositor()
        query = cm.read_query(query)

    # Clean the input from Galaxy escape characters.

    query = query.replace('__dq__', '"')
    query = query.replace('__sq__', "'")
    query = query.replace('__cn__', '\n')


    return query


def compile_query(user, filename, q_type, query, log_file):
    """Compile the given query"""

    call = 'compile'

    #Check the input
    query_cl = check_input(q_type, query)

     # Then ask it to be compiled
    url = compose_url(module_execution, call)

    response = auth_url_post(user, url, query_cl, 'text/plain')

    decoder = json.JSONDecoder()
    outcome = decoder.decode(response.read())

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


def run_query(user, filename, q_type, query, log_file, rs_format):
    """Run the given query. It returns an execution log and the resulting dataset."""

    call = 'run'

    # First clean the input
    query_cl = check_input(query)

    # Then ask it to be executed

    status = "NEW"

    url = compose_url(module_execution, call)
    url = url.format(name=filename,output=rs_format)

    response = auth_url_post(user, url, query_cl,'text/plain')

    decoder = json.JSONDecoder()
    outcome = decoder.decode(response.read())

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

        ds = log['datasets'][0]['name']

        # Retrieve the list of the samples in the resulting dataset
        # The list is stored in a temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        list_samples(user,temp.name,ds)

        # Create a list of the samples
        with open(temp.name,"r") as t :
            #lines = t.readlines()
            samples = map(lambda x: x.split('\t')[1].rstrip('\n'), t)
        t.close()

        for s in samples :
            # Get the sample
            get_sample(user,"sample_{name}.{ext}".format(name=s.replace('_',''),ext=rs_format), ds, s)
            # Get its metadata
            get_sample_meta(user,"metadata_{name}.meta".format(name=s.replace('_',''),ext=rs_format), ds, s)

        os.remove(temp.name)



def read_status(user, jobid):
    """Given the job id, it retrieves the status of the current operation
    (as a JSON file)"""

    call = 'status'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    response = auth_url_get(url, user)

    decoder = json.JSONDecoder()
    status = decoder.decode(response.read())

    return status



def read_complete_log(user, jobid):
    """Given the jobid, it retrieves the complete log of the latest operation
    (as a JSON file)"""

    call = 'log'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    log_obj = auth_url_get(url, user)

    decoder = json.JSONDecoder()
    log = decoder.decode(log_obj.read())

    return log


def show_jobs(user, output):
    """Retrieve the list of the user's jobs"""

    call = 'jobs'

    url = compose_url(module_monitor, call)

    outcome = auth_url_get(url, user)
    decoder = json.JSONDecoder()
    jobs = decoder.decode(outcome.read())

    jobs_list = jobs['jobs']
    jobs_out = list()

    # For each job in the list retrieve the relative status info
    for j in jobs_list:
        job = dict()
        j_id = j['id']
        job.update(id=j_id)
        status = read_status(user, j_id)
        job.update(message=status['message'],
                   status=status['status'],
                   ds=status['datasets'][0]['name'],
                   time=status['executionTime'])
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

    logging.basicConfig(filename='/home/luana/gmql-galaxy/monitor.log', level=logging.DEBUG, filemode='a')

    call = 'stop'

    url = compose_url(module_monitor, call)
    url = url.format(jobid=jobid)

    logging.debug("jobid: %s"%(jobid))
    logging.debug("url: %s"%(url))

    outcome = auth_url_get(url, user)

    with open(output,'w') as f_out :
        f_out.write(outcome.read())



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
    parser.add_argument("-result_dir")


    args = parser.parse_args()

    if args.cmd == 'compile':
        if args.query == 'new' :
            compile_query(args.user, args.name, args.query, args.queryNew, args.log)
        else :
            compile_query(args.user, args.name, args.query, args.queryLocal, args.log)
    if args.cmd == 'execute':
        if args.query == 'new' :
            run_query(args.user, args.name, args.query, args.queryNew, args.log, args.format)
        else :
            run_query(args.user, args.name, args.query, args.queryLocal, args.log, args.format)
    if args.cmd == 'jobs':
        show_jobs(args.user, args.log)
    if args.cmd == 'stop' :
        stop_query(args.user, args.job, args.log)


if __name__ == "__main__":
    __main__()
