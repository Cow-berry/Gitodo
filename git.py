from cmd import run_cmd, run_cmd_

class Git:
    def _fix_name(self, name: str) -> str:
        return '-'.join(name.strip().split(' '))

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

    def get_children(self, parent: str):
        parent = self.show(parent, pretty="%H")
        families = run_cmd_("git rev-list --all --parents").stdout.split('\n')
        children = []
        for family in families:
            child, *parents = family.split(' ')
            if parent in parents:
                children.append(child)
        return children
            
    def get_branches(self, commit_hash: str) -> list[str]:
        return run_cmd(['git', 'branch', '--points-at', commit_hash, '--format=%(refname:lstrip=2)']).stdout.split('\n')
        # return run_cmd(['git', 'name-rev', commit_hash]).stdout.split()[1:]



    def check_belongs(self, child: str, parent: str):
        return run_cmd_(f'git log {child}..{parent} --ancestry-path').stdout != ''

git = Git()
