from cmd import run_cmd, run_cmd_, run_cmd_strip, Result, e

def _fix_name(name: str) -> str:
    return '-'.join(name.strip().split(' '))

def log(parent: str, child: str, pretty: str = "%H", ancestry_path: bool = True) -> Result[str]:
    child = _fix_name(child)
    parent = _fix_name(parent)

    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')
    if ancestry_path:
        flags.append('--ancestry-path')
            
    return run_cmd(['git', 'log', f'{parent}..{child}'] + flags)

def show(node: str, pretty: str = "%P") -> Result[str]:
    node = _fix_name(node)
    
    flags = []
    if pretty:
        flags.append(f'--pretty={pretty}')
        
    return run_cmd(['git', 'show', *flags, node])

def normalise(hash: str) -> Result[str]:
    return show(hash, pretty="%H")

def switch(node: str) -> Result[None]:
    node = _fix_name(node)
    
    return run_cmd_strip(['git', 'switch', node])

def branch(child: str, parent: str) -> Result[None]:
    child = _fix_name(child)
    parent = _fix_name(parent)
    
    return run_cmd_strip(['git', 'branch', child, parent])

@e.effect.result[None, str]
def branch_switch(child: str, parent: str):
    yield from branch(child, parent)
    yield from switch(child)

def reset(node: str, mode: str = '--mixed') -> Result[None]:
    node = _fix_name(node)
    
    return run_cmd_strip(['git', 'reset', mode, node])

@e.effect.result[None, str]
def reset_branch(b_from: str, b_to: str, *args, **kwargs):
    yield from switch(b_from)
    yield from reset(b_to, *args, **kwargs)
    
def commit(msg: str) -> Result[None]:
    return run_cmd_strip(['git', 'commit', '--allow-empty', '-m', msg])

@e.effect.result[str, str]()
def merge_pick(tree: str, parents: list[str], message: str, merge=True):
    tree = _fix_name(tree)
    parents = [_fix_name(parent) for parent in parents ]
    parents = [x for parent in parents for x in ['-p', parent]]
    commit_cmd = ['git', 'commit-tree', '-m', message, *parents, f'{tree}^{{tree}}']

    commit_hash = yield from run_cmd(commi_cmd).
    if merge:
        merge_cmd = ['git', 'merge', '--ff-only', commit_hash]
        yield from run_cmd_proc(merge_cmd)
    return commit_hash

@e.effect.result[list[str], str]()
def get_children(parent: str, exclude: list[str] = []):
    parent = show(parent, pretty="%H")
    cmd = ['git', 'rev-list', '--all', '--parents']
    families = (yield from run_cmd(cmd)).split('\n')
    children = []
    for family in families:
        child, *parents = family.split(' ')
        if parent in parents and child not in exclude:
            children.append(child)
    return children

def get_parents(commit_hash: str, exclude: list[str] = []) -> Result[list[str]]:
    return show(commit_hash)\
        .map(lambda s: s.split(' '))\
        .map(lambda l: list(filter(lambda x: x not in exclude, l)))    
    
def get_branches(commit_hash: str, exclude: list[str] = []) -> Result[list[str]]:
    return run_cmd(['git', 'branch', '--points-at', commit_hash, '--format=%(refname:lstrip=2)'])\
        .map(s: s.split(' '))\
        .map(lambda l: list(filter(lambda x: x not in exclude, l)))   

def check_belongs(child: str, parent: str) -> bool:
    return run_cmd_(f'git log {parent}..{child} --ancestry-path').map(bool).default_value(False)

def show_debug(hashes: list[str]):
    print([show(hash, pretty='%h:%s') for hash in hashes])
    return hashes
