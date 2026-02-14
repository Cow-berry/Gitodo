import subprocess
import os
from typing import TypeAlias

RUN_CMD_DEBUG = False
# RUN_CMD_DEBUG = True

GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
os.chdir(GITODO_DIRECTORY)
INSTALLED = os.path.isdir(GITODO_DIRECTORY+".git")


def debug_proc(proc: subprocess.CompletedProcess[str]) -> subprocess.CompletedProcess[str]:
    code = proc.returncode
    code_msg = "SUCESS" if code == 0 else "FAILURE"
    line_lengh = os.get_terminal_size().columns
    print(f"{code_msg}:".ljust(line_lengh, '-'))
    print(f"cmd: '{' '.join(proc.args)}'")
    print(f"stdout: '{proc.stdout}'")
    print(f"stderr: '{proc.stderr}'")
    print('-'*line_lengh)
    return proc

class RunException(Exception):
    pass

def run_cmd_proc(cmd: list[str], do_raise: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    proc.stdout = proc.stdout.strip()
    proc.stderr = proc.stderr.strip()
    if RUN_CMD_DEBUG:
        debug_proc(proc)
    if proc.returncode != 0 and do_raise:
        raise RunException(f"# Failed to execute {cmd}:\n{proc.stderr}")
    return proc

def run_cmd(cmd: list[str], do_raise: bool = True) -> str:
    return run_cmd_proc(cmd, do_raise).stdout

def run_cmd_if(cmd: list[str], do_raise: bool = True) -> bool:
    return run_cmd_proc(cmd, do_raise).returncode == 0
    
def run_cmd_(cmd: str, do_raise: bool = True) -> str:
    return run_cmd(cmd.split(), do_raise)

def get_date(date: str="today") -> str:
    return run_cmd(['date', '--date', date, '+%x'])
