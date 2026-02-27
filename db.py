import git
from pretty import rainbow
import run

import json
from pprint import pprint
from dataclasses import dataclass, field
from itertools import chain, cycle
from more_itertools import unzip, split_into, flatten, zip_offset
from typing import Any, ClassVar
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

def paint(text: Any, *fores: str) -> str:
    return f"{''.join(fores)}{str(text)}{s.RESET_ALL}"

def red(text: str) -> str:
    return paint(text, f.LIGHTRED_EX)

def yellow(text: str) -> str:
    return paint(text, f.LIGHTYELLOW_EX)

def green(text: str) -> str:
    return paint(text, f.LIGHTGREEN_EX)

def rgb(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"

@dataclass
class Step:
    hash: str
    name: str

    COLOR: ClassVar[str] = s.BRIGHT + s.DIM + f.CYAN

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

    i = 20
    COLOR: ClassVar[str] = f.LIGHTCYAN_EX

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived, category=self.cat.hash)
        git.notes_add(self.root, note)

    def detailed_name(self) -> str:
        return f"{self.name} ({self.cat.name})"

@dataclass
class Cat:
    hash: str
    name: str
    parent: str
    archived: bool=field(default=False)
    subcats: list[Cat] = field(default_factory=lambda: [])
    projects: list[Project] = field(default_factory=lambda: [])

    COLOR: ClassVar[str] = f.LIGHTMAGENTA_EX

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived)
        git.notes_add(self.hash, note)

    def is_subcat(self, other: Cat) -> bool:
        a = self.name.split('.')
        b = other.name.split('.')
        if len(a) < len(b):
            return False
        return all([ax == bx for ax, bx in zip(a, b)])

    def detailed_name(self) -> str:
        if '.' not in self.name: return self.name
        name = self.name.rsplit('.', 1)[-1]
        return f"{name} ({self.name.replace('.', ' -> ')})"

class Mark(StrEnum):
    NotDone = 'not done'
    InProgress = 'in progress'
    Done = 'done'

    def emoji(self) -> str:
        match self:
            case Mark.NotDone:    return paint(' ■ ', rgb(255,0,0))
            case Mark.InProgress: return paint(' ● ', rgb(0,0,255))
            case Mark.Done:       return paint(' ✔ ', rgb(0,255,0))

    @property
    def colour(self) -> str:
        match self:
            case Mark.NotDone:    return rgb(200, 50, 50)
            case Mark.InProgress: return rgb(0, 255, 255)
            case Mark.Done:       return rgb(50, 255, 50)        

        
@dataclass
class Task:
    hash: str
    mark: Mark
    project: Project
    step_marks: dict[str, Mark] = field(default_factory=lambda: dict())

        
@dataclass
class Day:
    hash: str
    root: str
    date: str
    tasks: list[Task] = field(default_factory=lambda: [])

    TAB: ClassVar[str] = ' '*4

    def agenda(self) -> str:
        result: list[str] = []
        dots = ''.join([paint('●', task.mark.colour) for task in self.tasks])
        done_count = sum([1 for task in self.tasks if task.mark == Mark.Done])
        if len(self.tasks) == 0:
            done_colour = rgb(255, 255, 255)
        else:
            t = done_count/len(self.tasks)
            r = int(255*min(1, (1-t)*2))
            g = int(255*min(1, t*2))
            done_colour = rgb(r, g, 0)
        result.append(rainbow(f'Agenda @ {self.date}') + dots + paint(f"[{done_count}/{len(self.tasks)}]", done_colour) + ":")
        if len(self.tasks) == 0:
            result.append(f'--- No tasks are added yet --- ')
            return '\n'.join(result)
        
        ln = len(str(len(self.tasks)-1))
        for i, task in enumerate(self.tasks):
            result.append(f'{task.mark.emoji()}' + paint(f'[{i:>{ln}}] {task.project.detailed_name()}', task.mark.colour))
            mark_override = task.mark if task.mark == Mark.Done else None
            for j, step in enumerate(task.project.steps):
                mark = mark_override or task.step_marks.get(step.hash, Mark.NotDone)
                result.append(self.TAB + paint(f"{s.DIM}{j}. {s.NORMAL}{s.BRIGHT}{step.name}", mark.colour))
        return '\n'.join(result)

class ReservedBranches:
    MAIN: str = 'main'
    TASK_STORAGE: str = 'task-storage'
    CATEGORIES: str = 'categories'
    PROJECTS: str = 'projects'
    ARCHIVED_CATEGORIES: str = 'archived-categories'
    ARCHIVED_PROJECTS: str = 'archived-projects'
    CRAWL: str = 'crawl'
    DONE: str = 'done'
    DAYS_STORAGE: str = 'days-storage'
    DAYS: str = 'days'
    TODAY: str = 'today'

rb = ReservedBranches
    
class DB:
    cats_name: dict[str, Cat]
    cats: dict[str, Cat]
    steps: dict[str, Step]
    projects: dict[str, Project]
    projects_root: dict[str, Project]
    projects_name: dict[str, list[Project]]
    tasks: dict[str, Task]
    days: dict[str, Day]
    today: Day
    actual_date: str
    task_storage: str

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
        self.projects_name = dict()
        self.tasks = dict()
        self.days = dict()
        
        self.precompute()

        self.all_cats = list(self.cats.values())
        self.arch_cats = [cat for cat in self.all_cats if cat.archived]
        self.narch_cats = [cat for cat in self.all_cats if not cat.archived]
        
        self.all_projects = list(self.projects.values())
        self.arch_projects = [proj for proj in self.all_projects if proj.archived]
        self.narch_projects = [proj for proj in self.all_projects if not proj.archived]

    def call_date(self, date: str) -> str:
        return run.get_date(date)

    def create_multiple_categories(self, path: str) -> int:
        parts = path.split('.')
        i = 1
        while i <= len(parts):
            path = '.'.join(parts[:i])
            if path not in self.cats_name:
                break
            i += 1

        if i == len(parts) + 1: return 0
        
        git.switch(rb.CRAWL)
        if i == 1:
            parent = rb.TASK_STORAGE
        else:
            parent = self.cats_name['.'.join(parts[:(i-1)])].hash
        git.reset(parent)

        result = 0
        for cutoff in range(i, len(parts)+1):
            path = '.'.join(parts[:cutoff])
            hash = git.commit_hash(path)
            cat = Cat(hash, path, parent)
            cat.sync()
            self.cats[hash] = cat
            self.cats_name[path] = cat
            self.all_cats.append(cat)
            self.narch_cats.append(cat)
            parent = hash
            result += 1

        old_cats = [cat.hash for cat in self.narch_cats]
        
        hash = git.merge_pick(rb.CATEGORIES, [self.task_storage] + old_cats + [self.all_cats[-1].hash], 'All categories')
        git.switch(rb.CATEGORIES)
        git.reset(hash)
        return result

    def create_project(self, name: str, parent: Cat) -> Project | None:
        preexisting = self.projects_name.get(name)
        if preexisting is not None:
            for project in preexisting:
                if project.cat == parent:
                    return project
        
        commit_name = f"{name} <<< {parent.name}"
        git.switch(rb.CRAWL)
        git.reset(parent.hash)
        const_hash = git.commit_hash(f"[i] {commit_name}")
        mut_hash = git.commit_hash(f"[m] {commit_name}")
        project = Project(mut_hash, const_hash, name, parent)
        project.sync()
        self.projects[project.hash] = project
        self.projects_root[project.root] = project
        if name not in self.projects_name:
            self.projects_name[name] = [project]
        else:
            self.projects_name[name].append(project)
        
        old_projects = [project.hash for project in self.narch_projects]
        hash = git.merge_pick(rb.PROJECTS, [self.task_storage] + old_projects + [mut_hash], 'All projects')
        git.switch(rb.PROJECTS)
        git.reset(hash)
        return None

    def create_step(self, name: str, parent: Project) -> None:
        git.switch(rb.CRAWL)
        git.reset(parent.hash)
        hash = git.commit_hash(name)
        step = Step(hash, name)
        step.sync()
        upd_parent = git.merge_pick(parent.hash, [parent.root] + [step.hash for step in parent.steps] + [step.hash], f"[m] {parent.name} <<< {parent.cat.name}")
        parent.steps.append(step)

        old_projects = [project.hash for project in self.narch_projects]
        old_projects.remove(parent.hash)
        upd_projects = git.merge_pick(rb.PROJECTS, [self.task_storage] + old_projects + [upd_parent], 'All projects')
        git.switch(rb.PROJECTS)
        git.reset(upd_projects)
        
    def create_day(self, date: str) -> Day:
        git.switch(rb.CRAWL)
        git.reset(rb.DAYS_STORAGE)
        root = git.commit_hash(f"[i] {date}")
        hash = git.commit_hash(f"[m] {date}")
        day = Day(hash, root, date)
        old_days = [day.hash for day in self.days.values()]
        upd_days = git.merge_pick(rb.DAYS, [rb.DAYS_STORAGE] + old_days + [hash], 'All days')
        git.switch(rb.DAYS)
        git.reset(upd_days)
        return day

    def create_today(self, date: str) -> Day | None:
        day = self.create_day(date)
        git.switch(rb.TODAY)
        git.reset(day.root)


    def pick[T: Project | Cat](self, t_list: list[T], name: str | None, fuzzy: str | None, force_menu: bool = False) -> T | None:
        if name is None and fuzzy is None: return None
        if fuzzy:
            t_list = [t for t in t_list if fuzzy in t.name]
        else:
            t_list = [t for t in t_list if name == t.name]

        if len(t_list) == 0: return None
        if len(t_list) == 1 and not force_menu: return t_list[0]

        print("Please choose from this list:")
        for i, t in enumerate(t_list):
            print("- " + paint(f"[{i}] {t.detailed_name()}", f.LIGHTYELLOW_EX))

        while True:
            inp = input(f"Enter number in [0, {len(t_list)-1}] or q(uit): ")
            if inp == 'q' or inp == 'quit':
                print("Exiting")
                return None
            if not inp.isdecimal():
                print("Not a number")
                continue
            index = int(inp)
            if index < 0 or index >= len(t_list):
                print("Out of range")
                continue
            break
        print()
        return t_list[index]
        
        

    def precompute(self):
        branch_names = [
            'categories',
            'archived-categories',
            'projects',
            'archived-projects',
            'days',
            'today']
        hashes = git.show(branch_names, pretty="%H %P").split('\n\n')
        
        cat_hashes, archcat_hashes, project_hashes, archproject_hashes, day_hashes, today = [x.split(' ') for x in hashes]

        self.task_storage = cat_hashes[1]
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
            if name not in self.projects_name:
                self.projects_name[name] = [project]
            else:
                self.projects_name[name].append(project)
            cat.projects.append(project)
            

        # :Days:
        day_tasks = [x.split(":") for x in git.show(day_hashes, pretty="%H:%s:%P").split('\n\n')]

        # :Tasks:
        task_hashes = list(flatten([x[2].split(' ')[1:] for x in day_tasks]))
        tasks = [x.split('\n', 1) for x in git.show(task_hashes, pretty="%P%n%N").split('\n\n\n')]
        for hash, (parents, info_json) in zip(task_hashes, tasks):
            info = json.loads(info_json)
            mark = Mark[info.get('mark')] or Mark.NotDone
            step_marks_str: dict[str, str] = info.get('step_marks') or dict()
            step_marks = {k: Mark[v] for k, v in step_marks_str.items()}
            project_hash = parents.split(' ')[1]
            project = self.projects_root[project_hash]
            task = Task(hash, mark, project, step_marks)
            self.tasks[hash] = task

        # :Days: again

        for hash, subject, parents_str in day_tasks:
            parents = parents_str.split(' ')
            root = parents[0]
            date = subject[4:]
            tasks = [self.tasks[hash] for hash in parents[1:]]
            day = Day(hash, root, date, tasks)
            self.days[date] = day
            if root == today:
                self.today = day

        

db = DB()
# pprint(db.days)

# print(f"[DB] Number of calls: {f.LIGHTRED_EX}{run.number_of_calls}{s.RESET_ALL}")

