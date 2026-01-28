import git
from pretty import *
from cmd import INSTALLED, run_cmd, get_date
from git import get_hash

from typing import Optional

TAB = ' '*3

# SPECIAL_BRANCHES = ['done', 'finished', 'days', 'last-parent', 'today', 'main', get_date()]

class ReservedBranches:
    TASK_STORAGE = 'task-storage'
    CATEGORIES = 'categories'
    CRAWL = 'crawl'
    PROJECTS = 'projects'

rb = ReservedBranches

def install():
    run_cmd(["git",  "init"])
    git.commit("Initial commit")
    for name in ['task-storage', 'categories', 'projects', 'done', 'day-storage', 'days']:
        print(f"{name = }")
        git.branch_switch(name, 'main')
        git.commit(f"{name.capitalize()} parent")

class Commit:
    hash: str
    subject: str
    parents: list[str]
    
    def __init__(self, commit_hash: str):
        commit_hash = get_hash(commit_hash)
        self.hash = commit_hash
        self.subject = git.show(self.hash, pretty="%s")
        self.parents = git.get_parents(self.hash)


