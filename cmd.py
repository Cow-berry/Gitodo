import subprocess
import os

RUN_CMD_DEBUG = False
# RUN_CMD_DEBUG = True

GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
os.chdir(GITODO_DIRECTORY)
INSTALLED = os.path.isdir(GITODO_DIRECTORY+".git")

def debug_proc(proc: subprocess.CompletedProcess):
    code = proc.returncode
    code_msg = "SUCESS" if code == 0 else "FAILURE"
    line_lengh = os.get_terminal_size().columns
    print(f"{code_msg}:".ljust(line_lengh, '-'))
    print(f"cmd: '{' '.join(proc.args)}'")
    print(f"stdout: '{proc.stdout}'")
    print(f"stderr: '{proc.stderr}'")
    print('-'*line_lengh)
    return proc

def run_cmd(cmd: list[str], ok=True) -> (subprocess.CompletedProcess | tuple[subprocess.CompletedProcess, bool]):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.stdout = proc.stdout.decode('utf-8').strip()
    proc.stderr = proc.stderr.decode('utf-8').strip()
    if RUN_CMD_DEBUG:
        debug_proc(proc)
    if ok:
        return proc, proc.returncode == 0
    return proc

def run_cmd_if(cmd: list[str], *args, **kwargs) -> bool:
    _, ok = run_cmd(cmd, *args, **kwargs, ok=True)
    return ok

def run_cmd_(cmd: str, *args,  **kwargs) -> (subprocess.CompletedProcess | tuple[subprocess.CompletedProcess, bool]):
    return run_cmd(cmd.split(), *args, **kwargs)

def get_date(date: str="today") -> str:
     result, ok = run_cmd(['date', '--date', date, '+"%x"'])
     if not ok: # user input if any must be checked first
         print(f"Could not get date `{date}`")
     return result.stdout.strip()[1:-1]
