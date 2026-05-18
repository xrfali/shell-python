from dataclasses import dataclass
import subprocess

from app.shell_context import ShellContext

@dataclass
class Job:
    job_no: int
    pid: int
    cmd: str
    status: str
    process: subprocess.Popen


def process_jobs_command(args, argl, ctx: ShellContext):

    to_remove = []
    jobs = ctx.jobs

    for idx, job in enumerate(jobs):
        marker = ' '
        if idx == len(jobs) - 1:
            marker = '+'
        elif idx == len(jobs) - 2:
            marker = '-'
        
        status = job.status
        cmd = job.cmd

        if job.process.poll() != None:
            status = "Done"
            cmd =  job.cmd[:-1]
            to_remove.append(idx)
        print(f"{[job.job_no]}{marker}  {status:<24}{cmd}")

    for idx in reversed(to_remove):
        jobs.pop(idx)
    
    return None

def reap_bg_jobs(ctx: ShellContext):
    jobs = ctx.jobs

    to_remove = []
    for idx, job in enumerate(jobs):
        cmd = job.cmd

        if job.process.poll() != None:
            status = "Done"
            cmd =  job.cmd[:-1]
            to_remove.append(idx)
            print(f"{[job.job_no]}+  {status:<24}{cmd}")
    
    for idx in reversed(to_remove):
        jobs.pop(idx)

def next_job_number(ctx: ShellContext) -> int:
    jobs = ctx.jobs

    job_nos = [job.job_no for job in jobs]
    job_no = 1

    while job_no in job_nos:
        job_no += 1
    
    return job_no


def is_bg_job(args):
    if args[-1] == "&":
        return args[:-1], True

    return args, False

