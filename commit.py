import git
from pretty import *
from cmd import INSTALLED, run_cmd, get_date

from typing import Optional

TAB = ' '*3

SPECIAL_BRANCHES = ['done', 'finished', 'days', 'last-parent', 'today', 'main', get_date()]

def install():
    run_cmd(["git",  "init"])
    git.commit("Initial commit")
    for name in ['done', 'finished', 'days', 'tasks']:
        git.branch_(name, 'main')
        git.commit(f"{name.capitalize()} parent")

    git.branch('last-parent', 'tasks')
    git.branch('today', 'days')




class Commit:
    hash: str
    subject: str
    branches: list[str]
    parents: list[str]
    children: list[str]
    
    def __init__(self, commit_hash: str):
        self.hash = commit_hash
        self.subject = git.show(self.hash, pretty="%s")
        self.branches = git.get_branches(self.hash, exclude=SPECIAL_BRANCHES)
        self.parents = git.get_parents(self.hash)
        self.children = git.get_children(self.hash)


class TaskCommit(Commit):
    style: str = s.RESET_ALL
    task_children: list[TaskCommit]
    local_index: list[int]

    def __init__(self, commit_hash: str):
        super().__init__(commit_hash)
        self.task_children = []
        self.local_index = []

    def get_nested(self, indecies: list[int]):
        if indecies == []:
            return self
        return self.task_children[indecies[0]].get_nested(indecies[1:])
    
    def get_children(self) -> list[TaskCommit]:
        res = []
        for child in self.children:
            if git.check_belongs(child, 'days'):
                continue
            a = git.log(child, 'finished')
            if len(a) != 0 and a.count('\n') == 0:
                continue
            res.append(inspect_task(child))
        return res

    def get_local_index(self) -> str:
        return '' if not self.local_index else '(' + '.'.join([str(index)for index in self.local_index]) + ')'

    def __str__(self) -> str:
        return f"{self.style}{self.local_index[-1]:>2}. {self.subject} {self.get_local_index()}{s.RESET_ALL}\n"

    def traverse(self, index=[]) -> None:
        self.local_index = index
        self.task_children = self.get_children()
        # print(self.task_children)
        for i, child in enumerate(self.task_children):
            child.traverse(self.local_index + [i])
        
        return self
    
    def traverse_str(self, ident=0) -> str:
        result = TAB*ident + str(self)
        for child in self.task_children:
            result += child.traverse_str(ident+1)
        return result

class CategoryCommit(TaskCommit):
    style: str = rgb(85, 205, 252)

    # def get_local_index(self) -> str:
        # return ""

class StepCommit(TaskCommit):
    style: str = rgb(172, 117, 128)
    
    def get_children(self) -> list[TaskCommit]:
        return []

    def get_local_index(self) -> str:
        return ""

class ProjectCommit(TaskCommit):
    style: str = rgb(247, 168, 184)

def inspect_task(hash: str) -> Optional[TaskCommit]:
    branches = git.get_branches(hash)
    branches = [branch for branch in branches if '--' in branch]
    check = lambda name: any(map(lambda s: s.endswith(f'--{name}'), branches))
    
    if check("step"):
        return StepCommit(hash)
    elif check("project"):
        return ProjectCommit(hash)
    elif check("category"):
        return CategoryCommit(hash)
    else:
        #やべ
        return None

if INSTALLED:
    tasks: TaskCommit = TaskCommit('tasks').traverse()


