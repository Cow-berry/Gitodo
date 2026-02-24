import git

import json
from pprint import pprint
from dataclasses import dataclass, field
from itertools import chain, cycle
from more_itertools import unzip, split_into, flatten, zip_offset
from typing import Any




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

class DB:
    cats_name: dict[str, Cat]
    cats: dict[str, Cat]
    steps: dict[str, Step]
    projects: dict[str, Project]
    
    def __init__(self):
        self.cats = dict()
        self.cats_name = dict()
        self.steps = dict()
        self.projects = dict()
        self.precompute()

    def precompute(self):
        # :Categories:
        
        cat_hashes, archcat_hashes = [
            x.split(' ')[1:]
            for x in git.show(['categories', 'archived-categories']).split('\n\n')]
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
        
        project_hashes, archproject_hashes = [x.split(' ')[1:] for x in git.show(['projects', 'archived-projects']).split('\n\n')]
        # roots_fl, steps_list = unzip([list(split_into(x.split(' '), [1, None])) for x in git.show(project_hashes + archproject_hashes).split('\n') if x != ''])
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
            cat.projects.append(project)

db = DB()




    
    
    
