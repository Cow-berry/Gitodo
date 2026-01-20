import git
from pretty import *
from cmd import INSTALLED, run_cmd, get_date

from typing import Optional

TAB = ' '*3

# SPECIAL_BRANCHES = ['done', 'finished', 'days', 'last-parent', 'today', 'main', get_date()]

def install():
    # run_cmd(["git",  "init"])
    # git.commit("Initial commit")
    # for name in ['done', 'finished', 'days', 'tasks']:
    #     git.branch_(name, 'main')
    #     git.commit(f"{name.capitalize()} parent")

    # git.branch('last-parent', 'tasks')
    # git.branch('today', 'days')


class Commit:
    hash: str
    subject: str
    branches: list[str]
    parents: list[str]
    # children: list[str]
    
    def __init__(self, commit_hash: str):
        self.hash = commit_hash
        self.subject = git.show(self.hash, pretty="%s")
        self.branches = git.get_branches(self.hash, exclude=SPECIAL_BRANCHES)
        self.parents = git.get_parents(self.hash)
        # self.children = git.get_children(self.hash)


tasks = []
if INSTALLED:
    tasks: TaskCommit = TaskCommit('tasks').traverse()


