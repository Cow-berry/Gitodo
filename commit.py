import git
from pretty import *
from run import INSTALLED, run_cmd, get_date
from git import get_hash

from typing import Optional, Callable, Self

TAB = ' '*3

# SPECIAL_BRANCHES = ['done', 'finished', 'days', 'last-parent', 'today', 'main', get_date()]

def install():
    run_cmd(['rm', '-rf', '.git/'])
    run_cmd(["git",  "init"])
    git.commit("Initial commit")
    git.branch(rb.CRAWL, rb.MAIN)
    for name in [rb.TASK_STORAGE, rb.DAYS_STORAGE]:
        print(f"{name = }")
        git.branch_switch(name, 'main')
        git.commit(f"{name.capitalize()} start")

    git.switch(rb.DAYS_STORAGE)
    git.branch_switch(rb.TODAY, rb.DAYS_STORAGE)
    git.commit(f"[i] {get_date()}")
    git.commit(f"[m] {get_date()}")
    git.branch_switch(rb.DAYS, rb.TODAY)
    git.merge_pick(rb.DAYS, [rb.DAYS_STORAGE, rb.TODAY], "All days")

    git.switch(rb.TASK_STORAGE)
    for name in [rb.CATEGORIES, rb.PROJECTS]:
        print(f"{name = }")
        git.branch_switch(name, rb.TASK_STORAGE)
        git.commit(f"All {name}")


class Commit:
    hash: str
    subject: str
    parents: list[str]
    
    def __init__(self, commit_hash: str):
        commit_hash = get_hash(commit_hash)
        self.hash = commit_hash
        self.subject = git.show(self.hash, pretty="%s")
        self.parents = git.get_parents(self.hash)


class ListCommit(Commit):
    branch: str
    
    def __init__(self, commit_hash: str):
        super().__init__(commit_hash)
        self.branch = rb.CRAWL
    
    def update(self, upd: Callable[[list[str]], list[str]]) -> str:
        return git.merge_pick(self.hash, upd(self.parents), self.subject, merge=False)
        
    def append(self, hash: str) -> str:
        return self.update(lambda l: l + [hash])

    def remove(self, hash: str) -> str:
        return self.update(lambda l: l.remove(hash) or l) # type: ignore

    def replace(self, old_hash: str, new_hash: str) -> str:
        return self.update(lambda l: [new_hash if x == old_hash else x for x in l])

class ListBranch(ListCommit):
    def __init__(self, branch_name: str):
        super().__init__(branch_name)
        self.branch = branch_name

    def update(self, upd: Callable[[list[str]], list[str]]) -> str:
        # git.reset(git.get_parents(self.branch)[0])
        # git.reset(f'{self.branch}~1')
        new_hash = git.merge_pick(self.hash, upd(self.parents), self.subject, merge=False)
        git.switch(self.branch)
        git.reset(new_hash)
        return new_hash
    
        
        
class ReservedBranches:
    MAIN = 'main'
    TASK_STORAGE = 'task-storage'
    CATEGORIES = 'categories'
    CRAWL = 'crawl'
    PROJECTS = 'projects'
    DONE = 'done'
    DAYS_STORAGE = 'days-storage'
    DAYS = 'days'
    TODAY = 'today'

rb = ReservedBranches

class ReservedBrancheLists:
    categories: ListBranch
    projects: ListBranch
    days: ListBranch
    today: ListBranch
    def __getattr__(self, name: str) -> ListBranch:
        return ListBranch(name)

rbl = ReservedBrancheLists()
