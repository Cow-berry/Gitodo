import git
from pretty import *
from cmd import INSTALLED, run_cmd, get_date
from git import get_hash

from typing import Optional, Callable

TAB = ' '*3

# SPECIAL_BRANCHES = ['done', 'finished', 'days', 'last-parent', 'today', 'main', get_date()]

class ReservedBranches:
    MAIN = 'main'
    TASK_STORAGE = 'task-storage'
    CATEGORIES = 'categories'
    CRAWL = 'crawl'
    PROJECTS = 'projects'
    DONE = 'done'

rb = ReservedBranches

def install():
    run_cmd(['rm', '-rf', '.git/'])
    run_cmd(["git",  "init"])
    git.commit("Initial commit")
    git.branch(rb.CRAWL, rb.MAIN)
    for name in [rb.TASK_STORAGE]:
        print(f"{name = }")
        git.branch_switch(name, 'main')
        git.commit(f"{name.capitalize()} start")

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


# TODO: add note to arguments
def branch_list_update(branch: str, upd: Callable[[list[str]], list[str]], is_branch: bool=True) -> str:
    prev_parents = upd(git.get_parents(branch))
    prev_hash = git.get_hash(branch)
    prev_subject = git.show(branch, pretty='%s')

    if is_branch:
        git.switch(branch)
    else:
        git.switch(rb.CRAWL)
    git.reset(f'{branch}~1')
    new_hash = git.merge_pick(prev_hash, prev_parents, prev_subject)
    if not is_branch:
        git.notes_copy(prev_hash, new_hash)
    return new_hash

def branch_list_append(branch: str, hash: str, **kwargs) -> str:
    return branch_list_update(branch, lambda l: l + [hash], **kwargs)

def branch_list_replace(branch: str, before: str, after: str, **kwargs) -> str:
    def replace(l: list[str]) -> list[str]:
        print(f"Replacing in {l}\n{before} -> {after}")
        l[l.index(before)] = after
        return l
    return branch_list_update(branch, replace, **kwargs)
