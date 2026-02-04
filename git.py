from run import run_cmd, run_cmd_

from typing import Callable

def _fix_name(name: str) -> str:
    return '-'.join(name.strip().split(' '))

def log(parent: str, child: str, pretty: str = "%H", ancestry_path: bool = True) -> str:
    child = _fix_name(child)
    parent = _fix_name(parent)

    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')
    if ancestry_path:
        flags.append('--ancestry-path')
            
    return run_cmd(['git', 'log', f'{parent}..{child}'] + flags)

def show(nodes: list[str] | str | None = None, pretty: str = "%P") -> str:
    if isinstance(nodes, str):
        nodes = [nodes]
    elif nodes is None:
        nodes = []
    nodes = [_fix_name(node) for node in nodes]
    
    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')

    cmd = ['git', 'show', *flags, *nodes]
        
    return run_cmd(cmd)

def get_hash(hash: str) -> str:
    return show(hash, pretty="%H")

def switch(node: str) -> None:
    node = _fix_name(node)
    
    run_cmd(['git', 'switch', node])

def branch(child: str, parent: str) -> None:
    child = _fix_name(child)
    parent = _fix_name(parent)
    
    run_cmd(['git', 'branch', child, parent])

def branch_switch(child: str, parent: str) -> None:
    branch(child, parent)
    switch(child)

def reset(node: str, mode: str = '--mixed') -> None:
    node = _fix_name(node)
    
    run_cmd(['git', 'reset', mode, node])

def reset_branch(b_from: str, b_to: str, *args, **kwargs) -> None:
    switch(b_from)
    reset(b_to, *args, **kwargs)
    
def commit(msg: str) -> None:
    run_cmd(['git', 'commit', '--allow-empty', '-m', msg])

def commit_hash(msg: str) -> str:
    commit(msg)
    return show(pretty="%H")

def merge_pick(tree: str, parents: list[str], message: str, merge=True) -> str:
    tree = _fix_name(tree)
    parents = [_fix_name(parent) for parent in parents ]
    parents = [x for parent in parents for x in ['-p', parent]]
    
    commit_cmd = ['git', 'commit-tree', '-m', message, *parents, f'{tree}^{{tree}}']
    commit_hash = run_cmd(commit_cmd)

    if merge:
        merge_cmd = ['git', 'merge', '--ff-only', commit_hash]
        run_cmd(merge_cmd)
    return commit_hash

    

def get_children(parent: str, exclude: list[str] = []) -> list[str]:
    parent = show(parent, pretty="%H")
    cmd = ['git', 'rev-list', '--all', '--parents']
    families = [family.split(' ') for family in run_cmd(cmd).split('\n')]
    return [child
            for child, *parents in families
            if parent in parents
            and child not in exclude]

def get_parents(commit_hash: str, exclude: list[str] = []) -> list[str]:
    return [parent
            for parent in show(commit_hash).split(' ')
            if parent not in exclude]
    
def get_branches(commit_hash: str, exclude: list[str] = []) -> list[str]:
    branch_cmd = ['git', 'branch', '--points-at', commit_hash, '--format=%(refname:lstrip=2)']
    return [branch
            for branch in run_cmd(branch_cmd).split(' ')
            if branch not in exclude]

def check_belongs(child: str, parent: str) -> bool:
    return len(run_cmd_(f'git log {parent}..{child} --ancestry-path')) == 0

def show_debug(hashes: list[str]) -> list[str]:
    print([show(hash, pretty='%h:%s') for hash in hashes])
    return hashes

def notes_show(hash: str) -> str:
    return run_cmd(['git', 'notes', 'show', hash])

def notes_show_list(hashes: list[str]) -> list[str]:
    if not hashes: return []
    return show(hashes, pretty="%N").split('\n\n')

def notes_add(hash: str, note: str) -> None:
    run_cmd(['git', 'notes', 'add', '-fm', note, hash])

def notes_copy(hash_from: str, hash_to: str) -> None:
    run_cmd(['git', 'notes', 'copy', hash_from, hash_to])

