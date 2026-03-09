from pathlib import Path
from colorama import Fore as f
from colorama import Style as s

import os
import tomllib
import subprocess
from datetime import datetime, timedelta

RUN_CMD_DEBUG = False
# RUN_CMD_DEBUG = True

LINUX = os.name == "posix"
WINDOWS = os.name == "nt"
if LINUX:
    GITODO_DIRECTORY = Path('/home/cowberry/Projects/Gitodo/test/')
    IMAGE_DIRECTORY = Path('/home/cowberry/Projects/Gitodo/img/')
elif WINDOWS:
    GITODO_DIRECTORY = Path(r'C:\Users\Anatoly\Test\Gitodo\test')
    IMAGE_DIRECTORY = Path(r'C:\Users\Anatoly\Test\Gitodo\img')
    
    
SAD_IMAGE_DIRECTORY = IMAGE_DIRECTORY / 'sad'
os.chdir(GITODO_DIRECTORY)
INSTALLED = os.path.isdir(GITODO_DIRECTORY / ".git")

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
    # if cmd[0] == 'git':
        # cmd += ['-C', ]
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

def windows_date(date: str) -> datetime | None:
    today = datetime.today()
    match date:
        case "today": return today
        case "tomorrow": return today + timedelta(days=1)
        case "yesterday": return today - timedelta(days=1)
        case _: pass

    date_split: list[str] = []
    
    for c in r"./\-":
        if c in date:
            date_split = date.split(c)
            break
    else:
        return None
    if len(date_split) != 3: return None
    if not all(x.isdecimal() for x in date_split): return None
    ymd = [int(x) for x in date_split]
    if ymd[0] > 31:
        y, m, d = ymd
    else:
        d, m, y = ymd
    return datetime(year=y, month=m, day=d)

def get_date(date_s: str="today", do_raise: bool=True) -> str:
    if WINDOWS:
        date = windows_date(date_s)
        if date is None:
            raise Exception(f"Invalid date: {date_s}")
        return f"{date.day:02}.{date.month:02}.{date.year:04}"
    return run_cmd(['date', '--date', date_s, '+%x'], do_raise)

def get_date_proc(date_s: str="today", do_raise: bool=True) -> subprocess.CompletedProcess[str]:
    if WINDOWS:
        date = windows_date(date_s)
        if date is None:
            return subprocess.CompletedProcess([], returncode=67, stdout="", stderr=f"Invalid date: {date_s}")
        date_str = f"{date.day}.{date.month}.{date.year}"
        return subprocess.CompletedProcess([], returncode=0, stdout=date_str, stderr="")
    return run_cmd_proc(['date', '--date', date_s, '+%x'], do_raise)
