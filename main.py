import colorama
import os
import sys
import subprocess
from typing import Optional

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

def run_cmd(cmd: list[str], debug=False) -> subprocess.CompletedProcess:
    debug = debug or RUN_CMD_DEBUG
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res.stdout = res.stdout.decode('utf-8').strip()
    res.stderr = res.stderr.decode('utf-8').strip()
    if not debug:
        return res
    return debug_proc(res)

def run_cmd_(cmd: str, *args,  **kwargs) -> subprocess.CompletedProcess:
    return run_cmd(cmd.split(), *args, **kwargs)


class GitUtils:
    def get_date(self, date: str="today") -> str:
        return run_cmd(['date', '--date', date, '+"%x"']).stdout.strip()[1:-1]

    def get_branches(self, commit_hash: str) -> list[str]:
        return run_cmd(['git', 'name-rev', commit_hash]).stdout.split()[1:]

    def merge_theirs(self, tree: str, parents: list[str], message: str):
        commit_hash = run_cmd(['git', 'commit-tree', '-m', message, *[x for parent in parents for x in ['-p', parent]], f'{tree}^{{tree}}']).stdout
        run_cmd(['git', 'merge', '--ff-only', commit_hash])

    def fix_name(self, name: str) -> str:
        return '-'.join(name.strip().split(' '))

class App(GitUtils):
    def show_day(self, date="today"):
        branch_name = self.get_date(date)
        print(branch_name)
        added_tasks = run_cmd(['git', 'show', '--pretty=%P', branch_name]).stdout.split()
        added_tasks = [run_cmd(['git', 'show', '--pretty=%P', task]).stdout.split()[1] for task in added_tasks]
        added_tasks = [self.get_branches(task_hash)[0] for task in added_tasks]

    def end_day(self):
        today = self.get_date()
        main_day = (self.get_branches('main') + [None])[0]
        if today == main_day:
            print(f"Already on day {today}")
            return
        run_cmd_(f'git branch {today} days')
        run_cmd_(f'git switch {today}')
        run_cmd('git commit --allow-empty -m'.split() + [f"Start of {today} agenda"])
        run_cmd('git commit --allow-empty -m'.split() + [f"End of {today} agenda"])
        run_cmd_('git switch main')
        run_cmd_(f'git reset --hard {today}')

    def add_task_today(self, task: str):
        today = self.get_date()
        run_cmd_('git switch main')
        agenda_start = run_cmd(['git', 'log', f'days..{today}', '--ancestry-path', '--pretty=%H']).stdout.split('\n')[-1]
        run_cmd_(f'git reset --hard {agenda_start}')
        self.merge_theirs(task, ['main', task], f'Add task {task}')
        # merging with the end of agenda
        parents = run_cmd(['git', 'show', today, '--pretty=%P']).stdout.split()
        self.merge_theirs(agenda_start, [*parents, 'main'], f'End of {today} agenda')
        run_cmd_(f'git switch {today}')
        run_cmd_('git reset main')

    def add_task_kind(self, task: str, parent: Optional[str] = None):
        task = self.fix_name(task)
        parent = parent or "tasks"
        parent = self.fix_name(parent)
        run_cmd_(f'git branch {task} {parent}')
        run_cmd_(f'git switch {task}')
        run_cmd('git commit --allow-empty -m'.split() + [f"Setup for {task}"])

    def mark_task_todo(self, task: str):
        todo()
        
        
        

os.chdir(GITODO_DIRECTORY)
app = App()
#app.end_day()
#app.add_task_today('adding-task-kind')
#app.add_task_today(sys.argv[1])
#app.add_task_kind('marking task as done', 'gitodo')
#app.add_task_kind(sys.argv[1], sys.argv[2])
app.mark_task_todo("a")
