import colorama
import os
import sys
import subprocess
from typing import Optional, Callable

GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
RUN_CMD_DEBUG = True

def todo():
    print("AHAHA YOU DIDN'T IMPLEMENT THIS")
    sys.exit(69)

def debug_proc(proc: subprocess.CompletedProcess):
    code = proc.returncode
    code_msg = "SUCESS" if code == 0 else "FAILURE"
    line_lengh = os.get_terminal_size().columns
    print(f"{code_msg}:".ljust(line_lengh, '-'))
    print(f"cmd: '{' '.join(proc.args)}'")
    print(f"stdout: {proc.stdout}")
    #print(f"stderr: {proc.stderr}")
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

def run_cmd(cmd: list[str], debug=False) -> subprocess.CompletedProcess:
    debug = debug or RUN_CMD_DEBUG
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.stdout = proc.stdout.decode('utf-8').strip()
    proc.stderr = proc.stderr.decode('utf-8').strip()
    if debug:
        debug_proc(proc)
    if proc.returncode != 0:
        raise RunFailureException(proc)
    return proc

def run_cmd_(cmd: str, *args,  **kwargs) -> subprocess.CompletedProcess:
    return run_cmd(cmd.split(), *args, **kwargs)

class GitPrivate:
    def _fix_name(self, name: str) -> str:
        return '-'.join(name.strip().split(' '))
        

class Git(GitPrivate):
    def log(self, child: str, parent: str, pretty: str = "%H", ancestry_path: bool = True) -> str:
        child = self._fix_name(child)
        parent = self._fix_name(parent)

        flags = []
        if pretty:
            flags.append(f'--pretty={pretty}')
        if ancestry_path:
            flags.append('--ancestry-path')
            
        return run_cmd(['git', 'log', f'{child}..{parent}'] + flags).stdout

    def show(self, node: str, pretty: str = "%P") -> str:
        node = self._fix_name(node)
        
        flags = []
        if pretty:
            flags.append(f'--pretty={pretty}')

        return run_cmd(['git', 'show', *flags, node]).stdout

    @run_except
    def branch(self, child: str, parent: str) -> None:
        child = self._fix_name(child)
        parent = self._fix_name(parent)
        
        run_cmd(['git', 'branch', child, parent])

    def switch(self, node: str) -> None:
        node = self._fix_name(node)
        
        run_cmd(['git', 'switch', node])

    def reset(self, node: str, mode: str = '--mixed') -> None:
        node = self._fix_name(node)
        
        run_cmd(['git', 'reset', mode, node])

    def commit(self, msg: str) -> None:
        run_cmd(['git', 'commit', '--allow-empty', '-m', msg])

    def merge_pick(self, tree: str, parents: list[str], message: str) -> None:
        tree = self._fix_name(tree)
        parents = [self._fix_name(parent) for parent in parents ]
        
        parents = [x for parent in parents for x in ['-p', parent]]
        commit_hash = run_cmd(['git', 'commit-tree', '-m', message, *parents, f'{tree}^{{tree}}']).stdout
        run_cmd(['git', 'merge', '--ff-only', commit_hash]) 
        
        

# Creating the git manager object
git = Git()


class GitUtils:
    def get_date(self, date: str="today") -> str:
        return run_cmd(['date', '--date', date, '+"%x"']).stdout.strip()[1:-1]

    def get_branches(self, commit_hash: str) -> list[str]:
        return run_cmd(['git', 'name-rev', commit_hash]).stdout.split()[1:]



    def check_belongs(self, child: str, parent: str):
        return run_cmd_(f'git log {child}..{parent} --ancestry-path').stdout != ''

class App(GitUtils):
    def show_day(self, date="today"):
        branch_name = self.get_date(date)
        print(branch_name)
        added_tasks = git.show('main').split()[1:]
        added_tasks = [(git.show(task).split()[1], self.check_belongs(task, 'done')) for task in added_tasks]
        added_tasks = [(self.get_branches(task)[0], is_done) for task, is_done in added_tasks]
        print(added_tasks)
    
    def end_day(self):
        today = self.get_date()
        main_day = (self.get_branches('main') + [None])[0]
        if today != main_day:
            print(f"Already on day {today}")
            return

        git.branch(today, 'days')
        git.switch(today)
        git.commit(f'Start of {today} agenda')
        git.commit(f'End of {today} agenda')
        git.switch('main')
        git.reset(today)

    def add_task_today(self, task: str):
        today = self.get_date()
        git.switch('main')
        agenda_start = git.log('days', today).split('\n')[-1]
        git.reset(agenda_start)
        git.merge_pick(task, ['main', task], f'Add task {task}')
        parents = git.show(today).split()
        git.merge_pick(agenda_start, [*parents, 'main'], f'End of {today} agenda')
        git.switch(today)
        git.reset('main')
    
    def add_task_kind(self, task: str, parent: Optional[str] = None):
        parent = parent or "tasks"

        git.branch(task, parent)
        git.switch(task)
        git.commit(f'Setup for {task}')

    def mark_task_todo(self, task: str):
        task_hash = git.log(task, 'main').split('\n')[-1]
        git.switch('done')
        git.merge_pick('done', ['done', task_hash], f'DONE: {task}')
        
@run_except
def main() -> None:
    os.chdir(GITODO_DIRECTORY)
    app = App()
    # app.end_day()
    # app.add_task_today('drink')
    # app.add_task_today(sys.argv[1])
    # app.add_task_kind('rewriting it with a Git class', 'gitodo')
    # app.add_task_kind(sys.argv[1], sys.argv[2])
    # app.mark_task_todo("drink")
    # app.show_day()
    # run_cmd_('git log 270qbbde..done --ancestry-path')

main()
