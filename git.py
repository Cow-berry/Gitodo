from cmd import run_cmd, run_cmd_

def _fix_name(name: str) -> str:
    return '-'.join(name.strip().split(' '))

def log(child: str, parent: str, pretty: str = "%H", ancestry_path: bool = True) -> str:
    child = _fix_name(child)
    parent = _fix_name(parent)

    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')
    if ancestry_path:
        flags.append('--ancestry-path')
            
    return run_cmd(['git', 'log', f'{child}..{parent}'] + flags).stdout

def show(node: str, pretty: str = "%P") -> str:
    node = _fix_name(node)
    
    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')
        
    return run_cmd(['git', 'show', *flags, node]).stdout

def normalise(hash: str) -> str:
    return show(hash, pretty="%H")

def switch(node: str) -> None:
    node = _fix_name(node)
    
    run_cmd(['git', 'switch', node])

def branch(child: str, parent: str) -> None:
    child = _fix_name(child)
    parent = _fix_name(parent)
    
    run_cmd(['git', 'branch', child, parent])

def branch_(child: str, parent: str) -> None:
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

def merge_pick(tree: str, parents: list[str], message: str, merge=True) -> str:
    tree = _fix_name(tree)
    parents = [_fix_name(parent) for parent in parents ]
    
    parents = [x for parent in parents for x in ['-p', parent]]
    commit_hash = run_cmd(['git', 'commit-tree', '-m', message, *parents, f'{tree}^{{tree}}']).stdout
    if merge:
        run_cmd(['git', 'merge', '--ff-only', commit_hash])
    return commit_hash

def get_children(parent: str, exclude: list[str] = []):
    parent = show(parent, pretty="%H")
    families = run_cmd_("git rev-list --all --parents").stdout.split('\n')
    children = []
    for family in families:
        child, *parents = family.split(' ')
        if parent in parents and child not in exclude:
            children.append(child)
    return children

def get_parents(commit_hash: str, exclude: list[str] = []) -> list[str]:
    res = show(commit_hash).split(' ')
    return [x for x in res if x not in exclude]
    
    
def get_branches(commit_hash: str, exclude: list[str] = []) -> list[str]:
    res = run_cmd(['git', 'branch', '--points-at', commit_hash, '--format=%(refname:lstrip=2)']).stdout.split('\n')
    return [x for x in res if x not in exclude]
    # return run_cmd(['git', 'name-rev', commit_hash]).stdout.split()[1:]



def check_belongs(child: str, parent: str):
    return run_cmd_(f'git log {child}..{parent} --ancestry-path').stdout != ''

def show_debug(hashes: list[str]):
    print([show(hash, pretty='%h:%s') for hash in hashes])
    return hashes
