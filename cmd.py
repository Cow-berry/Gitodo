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
    print(f"stderr: {proc.stderr}")
    print('-'*line_lengh)
    return proc

class RunFailureException(Exception):
    def __init__(self, proc: subprocess.CompletedProcess):
        super().__init__('Failed to execute a command')
        self.proc = proc

def process_run_failure_exception(rfe: RunFailureException) -> None:
    proc = rfe.proc
    print(f"Failed to execute `{' '.join(proc.args)}`")
    print("Reason:")
    print(proc.stderr)

def run_except(function: Callable):
    def inner(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except RunFailureException as rfe:
            process_run_failure_exception(rfe)
    return inner


def run_cmd(cmd: list[str], debug=False, exception=True) -> subprocess.CompletedProcess:
    debug = debug or RUN_CMD_DEBUG
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.stdout = proc.stdout.decode('utf-8').strip()
    proc.stderr = proc.stderr.decode('utf-8').strip()
    if debug:
        debug_proc(proc)
    if proc.returncode != 0 and exception:
        raise RunFailureException(proc)
    return proc

def run_cmd_if(cmd: list[str], debug=False) -> bool:
    return run_cmd(cmd, debug, False).returncode == 0

def run_cmd_(cmd: str, *args,  **kwargs) -> subprocess.CompletedProcess:
    return run_cmd(cmd.split(), *args, **kwargs)
