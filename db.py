import git
from pretty import rainbow
import run

import json
import datetime
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
    mtime: str
    archived: bool = field(default=False)
    steps: list[Step] = field(default_factory=lambda: [])

    COLOR: ClassVar[str] = f.LIGHTCYAN_EX

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived, category=self.cat.hash)
        git.notes_add(self.root, note)

    def get_merge(self) -> tuple[str, list[str], str]:
        hash = self.hash
        parents = [self.root] + [step.hash for step in self.steps]
        message = self.commit_name
        return hash, parents, message

    @classmethod
    def get_list_merge(cls) -> tuple[str, list[str], str]:
        project_hashes = [project.hash for project in db.all_projects]
        parents = [rb.TASK_STORAGE] + project_hashes
        message = 'All projects'
        return rb.PROJECTS, parents, message

    @property
    def commit_name(self) -> str:
        return f"[m] {self.name} << {self.cat.name}"

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


    @classmethod
    def get_list_merge(cls) -> tuple[str, list[str], str]:
        cat_hashes = [cat.hash for cat in db.all_cats]
        parents = [rb.TASK_STORAGE] + cat_hashes
        message = 'All categories'
        return rb.CATEGORIES, parents, message

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
    NotDone = 'NotDone'
    InProgress = 'InProgress'
    Done = 'Done'

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
    project: Project | None
    mark: Mark = field(default=Mark.NotDone)
    step_marks: dict[str, Mark] = field(default_factory=lambda: dict())

    def sync(self) -> None:
        note = generate_note(mark=self.mark)
        git.notes_add(self.hash, note)

        
@dataclass
class Day:
    hash: str
    root: str
    date: str
    tasks: list[Task] = field(default_factory=lambda: [])

    TAB: ClassVar[str] = ' '*4

    def get_merge(self) -> tuple[str, list[str], str]:
        hash = self.hash
        parents = [self.root] + [task.hash for task in self.tasks]
        message =  f"[m] {self.date}"
        return hash, parents, message

    @classmethod
    def get_list_merge(cls) -> tuple[str, list[str], str]:
        hash = rb.DAYS
        parent_hashes = [day.hash for day in db.days.values()]
        parents = [rb.DAYS_STORAGE] + parent_hashes
        message = 'All days'
        return hash, parents, message

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

# *ALLL* git calls will be always here
# Everything on the levels above has to interface with this class for git (and date) calls
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

    # It's actually not costly to compute these every time now
        
    @property
    def all_projects(self) -> list[Project]:
        result = list(self.projects.values())
        result.sort(key=lambda project: project.mtime)
        result.sort(key=lambda project: project.cat.name)
        return result
        

    @property
    def all_cats(self) -> list[Cat]:
        result = list(self.cats.values())
        result.sort(key=lambda cat: cat.name)
        return result

    @property
    def arch_projects(self) -> list[Project]:
        return [proj for proj in self.all_projects if proj.archived]

    @property
    def narch_projects(self) -> list[Project]:
        return [proj for proj in self.all_projects if not proj.archived]

    @property
    def arch_cats(self) -> list[Cat]:
        return [cat for cat in self.all_cats if cat.archived]

    @property
    def narch_cats(self) -> list[Cat]:
        return [cat for cat in self.all_cats if not cat.archived]

    def _store_cat(self, cat: Cat) -> None:
        self.cats_name[cat.name] = cat
        self.cats[cat.hash] = cat
        if cat.parent in self.cats:
            self.cats[cat.parent].subcats.append(cat)
        
    def _unstore_cat(self, cat: Cat) -> None:
        self.cats_name.pop(cat.name)
        self.cats.pop(cat.hash)
        if cat.parent in self.cats:
            self.cats[cat.parent].subcats.remove(cat)
        
    def _store_project(self, project: Project) -> None:
        self.projects[project.hash] = project
        self.projects_root[project.root] = project
        if project.name not in self.projects_name:
            self.projects_name[project.name] = [project]
        else:
            self.projects_name[project.name].append(project)
        project.cat.projects.append(project)

    def _unstore_project(self, project: Project) -> None:
        self.projects.pop(project.hash)
        self.projects_root.pop(project.root)
        name_list = self.projects_name.get(project.name)
        if name_list is not None and len(name_list) == 1:
            self.projects_name.pop(project.name)
        elif name_list is not None:
            self.projects_name[project.name].remove(project)
        project.cat.projects.remove(project)

    def _store_step(self, step: Step, parent: Project) -> None:
        self.steps[step.hash] = step
        parent.steps.append(step)

    def _unstore_step(self, step: Step, parent: Project) -> None:
        self.steps.pop(step.hash)
        parent.steps.remove(step)

    def _store_day(self, day: Day) -> None:
        self.days[day.date] = day

    def _unstore_day(self, day: Day) -> None:
        self.days.pop(day.date)

    def _store_task(self, task: Task, day: Day) -> None:
        self.tasks[task.hash] = task
        day.tasks.append(task)
        
    def _unstore_task(self, task: Task, day: Day) -> None:
        self.tasks.pop(task.hash)
        day.tasks.remove(task)



    
        
    def call_date(self, date: str) -> str:
        return run.get_date(date)

    def call_date_maybe(self, date: str) -> tuple[str | None, str]:
        proc = run.get_date_proc(date, False)
        if proc.returncode != 0:
            return None, proc.stderr
        return proc.stdout, ""

    def create_multiple_categories(self, path: str) -> int:
        parts = path.split('.')
        i = 1
        while i <= len(parts):
            path = '.'.join(parts[:i])
            if path not in self.cats_name:
                break
            i += 1

        if i == len(parts) + 1: return 0
        
        if i == 1:
            parent = rb.TASK_STORAGE
        else:
            parent = self.cats_name['.'.join(parts[:(i-1)])].hash        
        git.switch_reset(rb.CRAWL, parent)

        result = 0
        for cutoff in range(i, len(parts)+1):
            path = '.'.join(parts[:cutoff])
            hash = git.commit_hash(path)
            cat = Cat(hash, path, parent)
            cat.sync()
            self._store_cat(cat)
            parent = hash
            result += 1

        upd_cats = git.merge_pick(*Cat.get_list_merge())
        git.switch_reset(rb.CATEGORIES, upd_cats)
        return result

    def remove_category(self, cat: Cat) -> None:
        for subcat in cat.subcats[:]:
            self.remove_category(subcat)

        for project in cat.projects[:]:
            self.remove_project(project)

        print("Removing category " + paint(cat.name, Cat.COLOR))
        self._unstore_cat(cat)
        upd_categories = git.merge_pick(*Cat.get_list_merge(), False)
        git.switch_reset(rb.CATEGORIES, upd_categories)

    def archive_cat(self, cat: Cat) -> None:
        for subcat in cat.subcats:
            self.archive_cat(subcat)
        
        for project in cat.projects:
            self.archive_project(project)

        print("Archiving category " + paint(cat.name, Cat.COLOR))
        cat.archived = True
        cat.sync()

    def restore_cat(self, cat: Cat) -> None:
        for subcat in cat.subcats:
            self.restore_cat(subcat)
        
        for project in cat.projects:
            self.restore_project(project)

        print("Restoring category " + paint(cat.name, Cat.COLOR))
        cat.archived = False
        cat.sync()

    def create_project(self, name: str, parent: Cat) -> Project | None:
        preexisting = self.projects_name.get(name)
        if preexisting is not None:
            for project in preexisting:
                if project.cat == parent:
                    return project
        
        commit_name = f"{name} <<< {parent.name}"
        git.switch_reset(rb.CRAWL, parent.hash)
        const_hash = git.commit_hash(f"[i] {commit_name}")
        mut_hash = git.commit_hash(f"[m] {commit_name}")
        project = Project(mut_hash, const_hash, name, parent, datetime.datetime.now().isoformat())
        project.sync()
        self._store_project(project)
        upd_projects = git.merge_pick(*Project.get_list_merge())
        git.switch_reset(rb.PROJECTS, upd_projects)
        return None

        

    def remove_project(self, project: Project) -> None:
        print("Removing project " + paint(project.name, Project.COLOR))
        self._unstore_project(project)
        upd_projects = git.merge_pick(*Project.get_list_merge(), False)
        git.switch_reset(rb.PROJECTS, upd_projects)

    def archive_project(self, project: Project) -> None:
        print("Archiving project " + paint(project.name, Project.COLOR))
        project.archived = True
        project.sync()

    def restore_project(self, project: Project) -> None:
        print("Restoring project " + paint(project.name, Project.COLOR))
        project.archived = False
        project.sync()
        

    def create_step(self, name: str, parent: Project) -> None:
        git.switch_reset(rb.CRAWL, parent.hash)
        hash = git.commit_hash(name)
        step = Step(hash, name)
        step.sync()
        self._store_step(step, parent)
        
        upd_project = git.merge_pick(*parent.get_merge())
        parent.hash = upd_project
        parent.mtime = datetime.datetime.now().isoformat()

        upd_projects = git.merge_pick(*Project.get_list_merge())
        git.switch_reset(rb.PROJECTS, upd_projects)
        
    def remove_step(self, step: Step, parent: Project) -> None:
        print("Removing step " + paint(step.name, Step.COLOR) )
        self._unstore_step(step, parent)

        upd_project = git.merge_pick(*parent.get_merge(), False)
        parent.hash = upd_project
        parent.mtime = datetime.datetime.now().isoformat()

        upd_projects = git.merge_pick(*Project.get_list_merge(), False)
        git.switch_reset(rb.PROJECTS, upd_projects)

    def create_day(self, date: str) -> Day:
        day = self.days.get(date)
        if day is not None: return day
        git.switch_reset(rb.CRAWL, rb.DAYS_STORAGE)
        root = git.commit_hash(f"[i] {date}")
        hash = git.commit_hash(f"[m] {date}")
        day = Day(hash, root, date)
        self._store_day(day)
        upd_days = git.merge_pick(*Day.get_list_merge())
        git.switch_reset(rb.DAYS, upd_days)
        return day

    def create_today(self, date: str) -> Day | None:
        if self.today.date == date: return self.today
        day = self.days.get(date)
        if day is None:
            day = self.create_day(date)
        git.switch_reset(rb.TODAY, day.root)
        self.today = day

    def assign_task(self, day: Day, project: Project) -> None:
        git.switch_reset(rb.CRAWL, day.root)
        task_hash = git.merge_pick(project.root, [day.root, project.root], f"@ {day.date} {project.name}")
        task = Task(task_hash, project)
        task.sync()
        self._store_task(task, day)
        upd_day = git.merge_pick(*day.get_merge())
        day.hash = upd_day
        upd_days = git.merge_pick(*Day.get_list_merge(), False)
        git.switch_reset(rb.DAYS, upd_days)

    def unassign_task(self, day: Day, task: Task) -> None:
        self._unstore_task(task, day)
        upd_day = git.merge_pick(*day.get_merge(), False)
        day.hash = upd_day
        upd_days = git.merge_pick(*Day.get_list_merge(), False)
        git.switch_reset(rb.DAYS, upd_days)
        
        
        


    def pick[T: Project | Cat](self, t_list: list[T], name: str | None, fuzzy: str | None, force_menu: bool = False) -> tuple[T | None, bool]:
        if name is None and fuzzy is None: return None, False
        if fuzzy:
            t_list = [t for t in t_list if fuzzy in t.name]
        else:
            t_list = [t for t in t_list if name == t.name]

        if len(t_list) == 0: return None, False
        if len(t_list) == 1 and not force_menu: return t_list[0], True

        print("Please choose from this list:")
        for i, t in enumerate(t_list):
            print("- " + paint(f"[{i}] {t.detailed_name()}", f.LIGHTYELLOW_EX))

        while True:
            inp = input(f"Enter number in [0, {len(t_list)-1}] or q(uit): ")
            if inp == 'q' or inp == 'quit':
                print("Exiting")
                return None, True
            if not inp.isdecimal():
                print("Not a number")
                continue
            index = int(inp)
            if index < 0 or index >= len(t_list):
                print("Out of range")
                continue
            break
        print()
        return t_list[index], True
        
        

    def precompute(self):
        branch_names = [
            'categories',
            'projects',
            'days',
            'today']
        hashes = git.show(branch_names, pretty="%H %P").split('\n\n')
        
        cat_hashes, project_hashes, day_hashes, today = [x.split(' ') for x in hashes]

        self.task_storage = cat_hashes[1]
        cat_hashes = cat_hashes[2:]
        project_hashes = project_hashes[2:]
        day_hashes = day_hashes[2:]
        today = today[0]


        self.actual_date = run.get_date()

        # :Categories:
        

        parent_names = [x.split(' ', 1) for x in git.show(cat_hashes, pretty="%P %N").split('\n\n')]
        
        offset = len(cat_hashes)
        cats = zip(cat_hashes, parent_names)
        
        for hash, parent_name in cats:
            parent, name_json = parent_name
            info = json.loads(name_json)
            archived = info.get('archived', False)
            name = info.get('path') or info.get('name') or Error
            cat = Cat(hash, name, parent, archived)
            self.cats_name[name] = cat
            self.cats[hash] = cat

        for cat in self.cats.values():
            parent = cat.parent
            if parent not in self.cats: continue
            self.cats[parent].subcats.append(cat)
            
        
        # :Projects:
        
        root_step = [x.split(' ') for x in git.show(project_hashes, pretty="%aI %P").split('\n') if x != '']
        mtimes = [x[0] for x in root_step]
        steps_list = [x[2:] for x in root_step]
        
        # :Steps:

        steps = list(flatten(steps_list))
        infos = git.notes_show_list(steps)
        for hash, name_json in zip(steps, infos):
            info = json.loads(name_json)
            name: str = info.get('name') or Error
            step = Step(hash, name)
            self.steps[hash] = step


        # :Projects: again
        
        roots = [x[1] for x in root_step]
        notes = git.notes_show_list(list(roots))

        offset: int = len(project_hashes)
        projects = zip(project_hashes, roots, notes, steps_list, mtimes)
        for hash, root, note, steps, mtime in projects:
            info = json.loads(note)
            name = info.get('name') or Error
            cat_name = info.get('category')
            archived = info.get('archived', False)
            cat = self.cats[cat_name]
            steps = [self.steps[hash] for hash in steps]
            project = Project(hash, root, name, cat, mtime, archived, steps)
            self.projects[project.hash] = project
            self.projects_root[project.root] = project
            if project.name not in self.projects_name:
                self.projects_name[project.name] = [project]
            else:
                self.projects_name[project.name].append(project)
            cat.projects.append(project)
            

        # :Days:
        day_tasks = [x.split(":") for x in git.show(day_hashes, pretty="%H:%s:%P").split('\n') if x != '']

        # :Tasks:
        task_hashes = list(flatten([x[2].split(' ')[1:] for x in day_tasks]))
        tasks = [x.split('\n', 1) for x in git.show(task_hashes, pretty="%P%n%N").split('\n\n\n')]
        for hash, (parents, info_json) in zip(task_hashes, tasks):
            info = json.loads(info_json)
            mark = Mark[info.get('mark')] or Mark.NotDone
            step_marks_str: dict[str, str] = info.get('step_marks') or dict()
            step_marks = {k: Mark[v] for k, v in step_marks_str.items()}
            project_hash = parents.split(' ')[1]
            project = self.projects_root.get(project_hash)
            task = Task(hash, project, mark, step_marks)
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
# print(f"{[p.hash for p in db.arch_cats] = }")
# print(f"{[p.hash for p in db.all_cats] = }")
# upd_cats = git.merge_pick(*Cat.get_list_merge(rb.CATEGORIES, db.all_cats), False)
# git.switch_reset(rb.CATEGORIES, upd_cats)
# pprint(db.days)

# print(f"[DB] Number of calls: {f.LIGHTRED_EX}{run.number_of_calls}{s.RESET_ALL}")

