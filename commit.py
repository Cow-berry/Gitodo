import git

class Commit:
    hash: str
    subject: str
    branches: list[str]
    parents: list[str]
    children: list[str]
    
    def __init__(self, commit_hash: str):
        self.hash = commit_hash
        self.subject = git.show(self.hash, pretty="%s")
        self.braches = git.get_branches(self.hash)
        self.parents = git.get_parents(self.hash)
        self.children = git.get_children(self.hash)
