from colorama import Fore as f
from colorama import Style as s

import subprocess
import os
from typing import TypeAlias

# RUN_CMD_DEBUG = False
RUN_CMD_DEBUG = True

GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
os.chdir(GITODO_DIRECTORY)
INSTALLED = os.path.isdir(GITODO_DIRECTORY+".git")

number_of_calls: int = 0


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
    global number_of_calls
    number_of_calls += 1
    proc = subprocess.run(cmd, capture_output=True, text=True)
    proc.stdout = proc.stdout.strip()
    proc.stderr = proc.stderr.strip()
    if RUN_CMD_DEBUG: debug_proc(proc)
    if RUN_CMD_DEBUG and proc.returncode != 0 and do_raise:
        raise RunException(f"# Failed to execute {cmd}:\n{proc.stderr}")
    elif proc.returncode != 0 and do_raise:
        print(f"{f.LIGHTRED_EX}# Failed to execute {s.RESET_ALL}{cmd}:\n{f.LIGHTYELLOW_EX}{s.BRIGHT}{proc.stderr}{s.RESET_ALL}")
        exit(0)
    return proc;

def run_cmd(cmd: list[str], do_raise: bool = True) -> str:
    return run_cmd_proc(cmd, do_raise).stdout

def run_cmd_if(cmd: list[str], do_raise: bool = True) -> bool:
    return run_cmd_proc(cmd, do_raise).returncode == 0
    
def run_cmd_(cmd: str, do_raise: bool = True) -> str:
    return run_cmd(cmd.split(), do_raise)

def get_date(date: str="today", do_raise: bool=True) -> str:
    return run_cmd(['date', '--date', date, '+%x'], do_raise)
