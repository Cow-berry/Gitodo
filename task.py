import git

from colorama import Fore as f
from colorama import Style as s

TAB = "  "

class Task:
    title = "DEAULT_TITLE"
    children: list[Task] = []
    color = ""
    number = 0
    
    def __init__(self, hash: str):
        self.hash = hash
        self.branch = git.get_branches(self.hash)[-1]
        self.subject = git.show(self.hash, pretty="%s")
        self.children = []
        self.number = 0

    def number_through(self) -> Task:
        self.number_through_(0)
        return self
        
    def number_through_(self, number: int) -> int:
        self.number = number
        
        for child in self.children:
            number = child.number_through_(number + 1)

        return number

    def flatten(self) -> list[Task]:
        return [self] + [flattened for child in self.children for flattened in child.flatten()]

    def to_str(self) -> str:
        return f"{self.color}{self.title}:{s.RESET_ALL} {self.subject}"

    def __str__(self) -> str:
        # print(f"{self.subject} -> {','.join(x.subject for x in self.children)}")
        
        current = ''
        if 'last-parent' in git.get_branches(self.hash):
            current = f"  {f.LIGHTGREEN_EX}<- *CURRENT*{s.RESET_ALL}"
        
        res = f"{self.color}{self.number} {self.title}:{s.RESET_ALL} {self.subject}{current}\n"

        if not self.children:
            return res

        for i, child in enumerate(self.children):
            debug = f"{self.number}.{i}"
            if not child.children:
                res += TAB + str(child)
            else:
                res += ''.join([TAB + line + '\n' for line in str(child).split('\n')[:-1]])

        return res


class Step(Task):
    title = "Step"
    color = f.LIGHTCYAN_EX

    
class Project(Task):
    title = "Project"
    color = f.LIGHTMAGENTA_EX

    def __init__(self, hash: str, children: list[Task]):
        super().__init__(hash)
        self.children = children
        for i, child in enumerate(self.children):
            child.number = i

        
class Category(Project):
    title = "Category"
    color = f.LIGHTRED_EX

    
def traverse_hash(hash: str) -> Task:
    hash = git.normalise(hash)
    branch = git.get_branches(hash)[-1]

    cls = Task
    if branch.endswith('|'):
        cls = Project
    elif '|' in branch:
        cls = Step
        return cls(hash)
    else:
        cls = Category

    children: list[Task] = [traverse_hash(ch_hash) for ch_hash in git.get_children(hash)]
    res = cls(hash, children)
    res.number_through()
    return res

numbered_through: list[Task] = traverse_hash('tasks').number_through().flatten()
numbered_through.sort(key=lambda task: task.number)

def index_through(i: int) -> str:
    return numbered_through[i].hash

def index(hash: str, i: int) -> str:
    return traverse_hash(hash).children[i].hash

def get_tasks(day: str = 'today') -> list[str]:
    agenda_start = git.log('days', day).split('\n')[-1]
    return [git.get_parents(parent, exclude=[agenda_start])[0] for parent in git.get_parents(day, exclude=[agenda_start])]

def get_picks(day: str = 'today') -> list[str]:
    agenda_start = git.log('days', day).split('\n')[-1]
    return git.get_parents(day, exclude=[agenda_start])

