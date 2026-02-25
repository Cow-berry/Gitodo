import git
import run

import json
from pprint import pprint
from dataclasses import dataclass, field
from itertools import chain, cycle
from more_itertools import unzip, split_into, flatten, zip_offset
from typing import Any
from enum import StrEnum, Enum
from colorama import Fore as f
from colorama import Style as s




# information needed:
# all projects (+archived) (+their parent root nodes, may be accomplished in a single show)
# all categories (+archived)
# ~

Error = "Error"

def generate_note(**kwargs: Any) -> str:
    return json.dumps(kwargs)

@dataclass
class Step:
    hash: str
    name: str

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name)
        git.notes_add(self.hash, note)

@dataclass
class Project:
    hash: str
    root: str
    name: str
    cat: Cat
    archived: bool = field(default=False)
    steps: list[Step] = field(default_factory=lambda: [])

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived, category=self.cat.hash)
        git.notes_add(self.root, note)

@dataclass
class Cat:
    hash: str
    name: str
    parent: str
    archived: bool=field(default=False)
    subcats: list[Cat] = field(default_factory=lambda: [])
    projects: list[Project] = field(default_factory=lambda: [])

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived)
        git.notes_add(self.hash, note)

class Mark(StrEnum):
    NotDone = 'not done'
    InProgress = 'in progress'
    Done = 'done'

# print('NotDone' in Mark._member_names_, Mark['NotDone'])
        
@dataclass
class Task:
    hash: str
    mark: Mark
    project: Project
        
@dataclass
class Day:
    hash: str
    date: str
    tasks: list[Task]
        
class DB:
    actual_date: str
    cats_name: dict[str, Cat]
    cats: dict[str, Cat]
    steps: dict[str, Step]
    projects: dict[str, Project]
    projects_root: dict[str, Project]
    tasks: dict[str, Task]
    days: dict[str, Day]

    all_cats: list[Cat]
    arch_cats: list[Cat]
    narch_cats: list[Cat]
    
    all_projects: list[Project]
    arch_projects: list[Project]
    narch_projects: list[Project]
    
    def __init__(self):
        self.cats = dict()
        self.cats_name = dict()
        self.steps = dict()
        self.projects = dict()
        self.projects_root = dict()
        self.tasks = dict()
        self.days = dict()
        
        self.precompute()

        self.all_cats = list(self.cats.values())
        self.arch_cats = [cat for cat in self.all_cats if cat.archived]
        self.narch_cats = [cat for cat in self.all_cats if not cat.archived]
        
        self.all_projects = list(self.projects.values())
        self.arch_projects = [proj for proj in self.all_projects if proj.archived]
        self.narch_projects = [proj for proj in self.all_projects if not proj.archived]

    def pick[T: Project | Cat](self, t_list: list[T], name: str | None, fuzzy: str | None, force_menu: bool = False) -> T | None:
        if name is None and fuzzy is None: return None
        if fuzzy:
            t_list = [t for t in t_list if fuzzy in t.name]
        else:
            t_list = [t for t in t_list if name == t.name]
        ...
        
        

    def precompute(self):
        branch_names = ['categories', 'archived-categories', 'projects', 'archived-projects', 'days', 'today']
        hashes = git.show(branch_names, pretty="%H %P").split('\n\n')
        
        cat_hashes, archcat_hashes, project_hashes, archproject_hashes, day_hashes, today = [x.split(' ') for x in hashes]
        cat_hashes = cat_hashes[2:]
        archcat_hashes = archcat_hashes[2:]
        project_hashes = project_hashes[2:]
        archproject_hashes = archproject_hashes[2:]
        day_hashes = day_hashes[2:]
        today = today[0]


        self.actual_date = run.get_date()

        # :Categories:
        

        parent_names = [x.split(' ', 1) for x in git.show(cat_hashes + archcat_hashes, pretty="%P %N").split('\n\n')]
        
        offset = len(cat_hashes)
        cats = zip(cat_hashes, parent_names, cycle([False]))
        archcats = zip(archcat_hashes, parent_names[offset:], cycle([True]))
        
        for hash, parent_name, archived in chain(cats, archcats):
            parent, name_json = parent_name
            info = json.loads(name_json)
            name = info.get('path') or info.get('name') or Error
            cat = Cat(hash, name, parent, archived)
            self.cats_name[name] = cat
            self.cats[hash] = cat

        for cat in self.cats.values():
            parent = cat.parent
            if parent not in self.cats: continue
            self.cats[parent].subcats.append(cat)
            
        
        # :Projects:
        
        root_step = [x.split(' ') for x in git.show(project_hashes + archproject_hashes).split('\n') if x != '']
        steps_list = [x[1:] for x in root_step]
        # :Steps:

        steps = list(flatten(steps_list))
        infos = git.notes_show_list(steps)
        for hash, name_json in zip(steps, infos):
            info = json.loads(name_json)
            name: str = info.get('name') or Error
            step = Step(hash, name)
            self.steps[hash] = step


        # :Projects: again
        
        roots = [x[0] for x in root_step]
        notes = git.notes_show_list(list(roots))

        offset: int = len(project_hashes)
        # print(f"{project_hashes = }")
        # print(f"{roots = }")
        # print(f"{list(steps_list) = }")
        projects = zip(project_hashes, roots, notes, steps_list, cycle([False]))
        archprojects = zip(archproject_hashes, roots[offset:], notes[offset:], list(steps_list)[offset:], cycle([True]))
        for hash, root, note, steps, archived in chain(projects, archprojects):
            info = json.loads(note)
            name = info.get('name') or Error
            cat_name = info.get('category')
            cat = self.cats[cat_name]
            steps = [self.steps[hash] for hash in steps]
            project = Project(hash, root, name, cat, archived, steps)
            self.projects[hash] = project
            self.projects_root[root] = project
            cat.projects.append(project)
            

        # :Days:
        day_tasks = [x.split(":") for x in git.show(day_hashes, pretty="%H:%s:%P").split('\n\n')]

        # :Tasks:
        task_hashes = list(flatten([x[2].split(' ')[1:] for x in day_tasks]))
        tasks = [x.split('\n', 1) for x in git.show(task_hashes, pretty="%P%n%N").split('\n\n\n')]
        for hash, (parents, info_json) in zip(task_hashes, tasks):
            info = json.loads(info_json)
            mark = info.get('mark') or Mark.NotDone
            project_hash = parents.split(' ')[1]
            project = self.projects_root[project_hash]
            task = Task(hash, mark, project)
            self.tasks[hash] = task

        # :Days: again

        for hash, subject, parents in day_tasks:
            date = subject[4:]
            tasks = [self.tasks[hash] for hash in parents.split(' ')[1:]]
            day = Day(hash, date, tasks)
            self.days[date] = day
        

db = DB()
# pprint(db.days)

print(f"[DB] Number of calls: {f.LIGHTRED_EX}{run.number_of_calls}{s.RESET_ALL}")




    
    
    
