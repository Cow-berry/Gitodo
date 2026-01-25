import subprocess
import os
from typing import TypeAlias
import expression as e

RUN_CMD_DEBUG = False
# RUN_CMD_DEBUG = True

GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
os.chdir(GITODO_DIRECTORY)
INSTALLED = os.path.isdir(GITODO_DIRECTORY+".git")

type Error = str
type Result[T] = e.Result[T, Error]

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


def run_cmd_proc(cmd: list[str]) -> Result[subprocess.CompletedProcess]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.stdout = proc.stdout.decode('utf-8').strip()
    proc.stderr = proc.stderr.decode('utf-8').strip()
    if RUN_CMD_DEBUG:
        debug_proc(proc)
    if proc.returncode == 0:
        return e.Ok(proc)
    return e.Error(f"# Failed to execute {cmd}:\n{proc.stderr}")

def run_cmd(cmd: list[str]) -> Result[str]:
    return run_cmd_proc(cmd).map(lambda x: x.stdout)

def run_cmd_strip(cmd: list[str]) -> Result[None]:
    return run_cmd_proc(cmd).map(lambda _: None)

def run_cmd_if(cmd: list[str], *args, **kwargs) -> bool:
    return run_cmd_proc(cmd, *args, **kwargs).is_ok()
    
def run_cmd_(cmd: str, *args,  **kwargs) -> Result[str]:
    return run_cmd(cmd.split(), *args, **kwargs)

def get_date(date: str="today") -> Result[str]:
    return run_cmd(['date', '--date', date, '+"%x"'])


def sequence[T, U](results: list[e.Result[T, U]]) -> e.Result[list[T], U]:
    result = []
    for result in results:
        match result:
            case e.Ok(x):
                result.append(x)
            case e.Error(err):
                return e.Error(err)
    return e.Ok(result)
