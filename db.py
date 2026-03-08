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
from collections.abc import Sequence
from enum import Flag, StrEnum, Enum, auto
from colorama import Fore as f
from colorama import Style as s




# information needed:
# all projects (+archived) (+their parent root nodes, may be accomplished in a single show)
# all categories (+archived)
# ~

def install() -> None:
    run.run_cmd(['rm', '-rf', '.git/'])
    run.run_cmd(["git",  "init"])
    git.commit("Initial commit")
    git.branch(rb.CRAWL, rb.MAIN)
    for name in [rb.TASK_STORAGE, rb.DAYS_STORAGE]:
        print(f"{name = }")
        git.branch_switch(name, 'main')
        git.commit(f"{name.capitalize()} start")

    git.switch(rb.DAYS_STORAGE)
    git.branch_switch(rb.TODAY, rb.DAYS_STORAGE)
    git.commit(f"[i] {run.get_date()}")
    git.commit(f"[m] {run.get_date()}")
    git.branch_switch(rb.DAYS, rb.TODAY)
    git.merge_pick(rb.DAYS, [rb.DAYS_STORAGE, rb.TODAY], "All days")

    git.switch(rb.TASK_STORAGE)
    for name in [rb.CATEGORIES, rb.PROJECTS, rb.ARCHIVED_CATEGORIES, rb.ARCHIVED_PROJECTS]:
        print(f"{name = }")
        git.branch_switch(name, rb.TASK_STORAGE)
        git.commit(f"All {name}")

def date_to_datetime(date: str) -> datetime.datetime:
    components: list[str] = []
    component: str = ""
    for c in date:
        if c.isdecimal():
            component += c
        else:
            if len(component) == 0: continue
            components.append(component)
            component = ""
    year, month, day = [int(x) for x in components]
    return datetime.datetime(year, month, day)
            

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

CREATING: str = green("Creating")
REMOVING: str = red("Removing")
ARCHIVING: str = yellow("Archiving")
RESTORING: str = paint("Restoring", '\x1b[103m' + rgb(0,0,0))
MARKING: str = "Marking"
SETTING: str = "Setting"
UNSETTING: str = "Unsetting"
ASSIGNING: str = green("Assigning")
UNASSIGNING: str = red("Unassigning")


class StepFTag(Flag):
    MUST = auto()

@dataclass
class Step:
    hash: str
    name: str
    ftag: StepFTag = field(default=StepFTag(0))

    COLOR: ClassVar[str] = rgb(70, 165, 200)

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, ftag=self.ftag.value)
        git.notes_add(self.hash, note)

    def detailed_name(self) -> str:
        return paint(self.name, self.COLOR)

class ProjectFTag(Flag):
    WAKEUP = auto()
    AGO = auto()
    BAD = auto()
    
@dataclass
class Project:
    hash: str
    root: str
    name: str
    cat: Cat
    mtime: str
    archived: bool = field(default=False)
    steps: list[Step] = field(default_factory=lambda: [])
    last_done: str | None = field(default=None)
    ftag: ProjectFTag = field(default=ProjectFTag(0))

    COLOR: ClassVar[str] = rgb(90, 205, 250)


    def update_last_done(self, date: str) -> None:
        if self.last_done is None: self.last_done = date
        self.last_done = max(self.last_done, date)

    def fetch_last_done(self) -> None:
        self.last_done = None
        for day in db.days.values():
            for task in day.tasks:
                if task.project != self: continue
                if task.mark != Mark.Done: continue
                self.update_last_done(day.date)

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name, archived=self.archived, category=self.cat.hash, ftag=self.ftag.value)
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
        return f"[m] {self.name} << {'.'.join(self.cat.path)}"

    def detailed_name(self) -> str:
        return f"{paint(self.name, self.COLOR)} ({self.cat.detailed_path()})"

@dataclass
class Cat:
    hash: str
    name: str
    parent: str
    archived: bool=field(default=False)
    subcats: list[Cat] = field(default_factory=lambda: [])
    projects: list[Project] = field(default_factory=lambda: [])

    COLOR: ClassVar[str] = rgb(245, 170, 185)

    def sync(self) -> None:
        note = generate_note(hash=self.hash, name=self.name.split('.')[-1], archived=self.archived)
        git.notes_add(self.hash, note)

    @property
    def parent_cat(self) -> Cat | None:
        return db.cats.get(self.parent)

    @property
    def path(self) -> tuple[str, ...]:
        parent = self.parent_cat
        if parent is None: return (self.name,)
        result = (*parent.path, self.name)
        return result

    @classmethod
    def get_list_merge(cls) -> tuple[str, list[str], str]:
        cat_hashes = [cat.hash for cat in db.all_cats]
        parents = [rb.TASK_STORAGE] + cat_hashes
        message = 'All categories'
        return rb.CATEGORIES, parents, message

    def is_subcat(self, other: Cat) -> bool:
        a = self.path
        b = other.path
        if len(a) < len(b):
            return False
        return all([ax == bx for ax, bx in zip(a, b)])

    def detailed_name(self) -> str:
        return paint(f"{self.name} ({' -> '.join(self.path)})", self.COLOR)

    def detailed_path(self) -> str:
        return paint(' -> '.join(self.path), self.COLOR)

type TaskType = Cat | Project | Step
type TaskTypeList = list[Cat] | list[Project]
    
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
            case Mark.NotDone:    return rgb(255, 50, 50)
            case Mark.InProgress: return rgb(0, 255, 255)
            case Mark.Done:       return rgb(50, 255, 50)



        
@dataclass
class Task:
    hash: str
    project: Project | None
    mark: Mark = field(default=Mark.NotDone)
    step_marks: dict[str, Mark] = field(default_factory=lambda: dict())

    def detailed_name(self) -> str:
        if self.project is None: return paint("Deleted Project", f.LIGHTRED_EX, s.BRIGHT)
        return self.project.detailed_name()

    def sync(self) -> None:
        note = generate_note(mark=self.mark, step_marks=self.step_marks)
        git.notes_add(self.hash, note)

    def get_steps(self) -> list[Step]:
        if self.project is None: return []
        return self.project.steps
        
        
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

    @property
    def active_task(self) -> Task | None:
        for task in self.tasks:
            if task.mark == Mark.InProgress:
                return task
        return None

    def agenda(self) -> str:
        result: list[str] = []
        dots = ''.join([paint('●', task.mark.colour) for task in self.tasks])
        task_count = len(self.tasks)
        done_count = sum([1 for task in self.tasks if task.mark == Mark.Done])
        plus_one = paint("+1", f.LIGHTCYAN_EX) if self.active_task is not None else ""
        if plus_one:
            done_count += 1
            task_count += 1
        if len(self.tasks) == 0:
            done_colour = rgb(255, 255, 255)
        else:
            t = done_count/task_count
            r = int(255*min(1, (1-t)*2))
            g = int(255*min(1, t*2))
            done_colour = rgb(r, g, 0)
        result.append(rainbow(f'Agenda @ {self.date}') + dots + paint(f"[{done_count}{plus_one}{done_colour}/{len(self.tasks)}]", done_colour) + ":")
        if len(self.tasks) == 0:
            result.append(f'--- No tasks are added yet --- ')
            return '\n'.join(result)
        
        
        ln = len(str(len(self.tasks)-1))
        for i, task in enumerate(self.tasks):
            project = task.project
            archived_text = red("DELETED") if project is None else (red("ARCHIVED") if project.archived else "")
            task_name = "Deleted Project" if project is None else f"{project.name} {paint(f"({project.cat.name})", Cat.COLOR)}"
            result.append(f'{task.mark.emoji()}' + paint(f'[{i:>{ln}}] {task_name} ', task.mark.colour + s.BRIGHT) + archived_text + f" last done: {project and project.last_done and rainbow(str(date_to_datetime(project.last_done)))}")
            if project is None: continue
            mark_override = task.mark if task.mark == Mark.Done else None
            for j, step in enumerate(project.steps):
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
    cats_path: dict[tuple[str, ...], Cat]
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

    
    def __init__(self) -> None:
        self.cats = dict()
        self.cats_path = dict()
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
        result.sort(key=lambda project: project.cat.path)
        return result
        

    @property
    def all_cats(self) -> list[Cat]:
        result = list(self.cats.values())
        result.sort(key=lambda cat: cat.path)
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
        self.cats_path[cat.path] = cat
        self.cats[cat.hash] = cat
        if cat.parent in self.cats:
            self.cats[cat.parent].subcats.append(cat)
        
    def _unstore_cat(self, cat: Cat) -> None:
        self.cats_path.pop(cat.path)
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

    def create_multiple_categories(self, path_str: str) -> int:
        parts = path_str.split('.')
        i = 1
        while i <= len(parts):
            part_path = parts[:i]
            if tuple(part_path) not in self.cats_path:
                break
            i += 1

        if i == len(parts) + 1: return 0
        
        if i == 1:
            parent = rb.TASK_STORAGE
        else:
            parent = self.cats_path[tuple(parts[:(i-1)])].hash        
        git.switch_reset(rb.CRAWL, parent)

        result = 0
        for cutoff in range(i, len(parts)+1):
            path = tuple(parts[:cutoff])
            hash = git.commit_hash('.'.join(path))
            cat = Cat(hash, path[-1], parent)
            print(f"{CREATING} category {cat.detailed_name()}")
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

        print(f"{REMOVING} category " + cat.detailed_name())
        self._unstore_cat(cat)
        upd_categories = git.merge_pick(*Cat.get_list_merge(), False)
        git.switch_reset(rb.CATEGORIES, upd_categories)

    def archive_cat(self, cat: Cat) -> None:
        for subcat in cat.subcats:
            self.archive_cat(subcat)
        
        for project in cat.projects:
            self.archive_project(project)

        print(f"{ARCHIVING} category " + cat.detailed_name())
        cat.archived = True
        cat.sync()

    def restore_cat(self, cat: Cat) -> None:
        for subcat in cat.subcats:
            self.restore_cat(subcat)
        
        for project in cat.projects:
            self.restore_project(project)

        print(f"{RESTORING} category " + cat.detailed_name())
        cat.archived = False
        cat.sync()

    def create_project(self, name: str, parent: Cat) -> tuple[Project, bool]:
        preexisting = self.projects_name.get(name)
        if preexisting is not None:
            for project in preexisting:
                if project.cat == parent:
                    return project, False
        
        commit_name = f"{name} <<< {parent.name}"
        git.switch_reset(rb.CRAWL, parent.hash)
        const_hash = git.commit_hash(f"[i] {commit_name}")
        mut_hash = git.commit_hash(f"[m] {commit_name}")
        project = Project(mut_hash, const_hash, name, parent, datetime.datetime.now().isoformat())
        print(f"{CREATING} project " + project.detailed_name())
        project.sync()
        self._store_project(project)
        upd_projects = git.merge_pick(*Project.get_list_merge())
        git.switch_reset(rb.PROJECTS, upd_projects)
        return project, True

    def remove_project(self, project: Project) -> None:
        print(f"{REMOVING} project " + project.detailed_name())
        self._unstore_project(project)
        upd_projects = git.merge_pick(*Project.get_list_merge(), False)
        git.switch_reset(rb.PROJECTS, upd_projects)

    def archive_project(self, project: Project) -> None:
        print(f"{ARCHIVING} project " + project.detailed_name())
        project.archived = True
        project.sync()

    def restore_project(self, project: Project) -> None:
        print(f"{RESTORING} project " + project.detailed_name())
        project.archived = False
        project.sync()

    def ftag_project(self, project: Project, ftag: ProjectFTag, unset: bool = False) -> None:
        print(f"{UNSETTING if unset else SETTING} ftag {ftag.name} to project " + project.detailed_name())
        if unset:
            project.ftag &= ~ftag
        else:
            project.ftag |= ftag
        project.sync()

    def create_step(self, name: str, parent: Project) -> None:
        git.switch_reset(rb.CRAWL, parent.hash)
        hash = git.commit_hash(name)
        step = Step(hash, name)
        print(f"{CREATING} step " + step.detailed_name())
        step.sync()
        self._store_step(step, parent)
        
        upd_project = git.merge_pick(*parent.get_merge())
        parent.hash = upd_project
        parent.mtime = datetime.datetime.now().isoformat()

        upd_projects = git.merge_pick(*Project.get_list_merge())
        git.switch_reset(rb.PROJECTS, upd_projects)
        
    def remove_step(self, step: Step, parent: Project) -> None:
        print(f"{REMOVING} step " + step.detailed_name() )
        self._unstore_step(step, parent)

        upd_project = git.merge_pick(*parent.get_merge(), False)
        parent.hash = upd_project
        parent.mtime = datetime.datetime.now().isoformat()

        upd_projects = git.merge_pick(*Project.get_list_merge(), False)
        git.switch_reset(rb.PROJECTS, upd_projects)

    def reorder_steps(self, parent: Project, nums: list[int]) -> None:
        old_steps = parent.steps
        new_steps = [old_steps[i] for i in nums]
        parent.steps = new_steps

        upd_project = git.merge_pick(*parent.get_merge(), False)
        parent.hash = upd_project
        parent.mtime = datetime.datetime.now().isoformat()

        upd_projects = git.merge_pick(*Project.get_list_merge(), False)
        git.switch_reset(rb.PROJECTS, upd_projects)

    def ftag_step(self, step: Step, project: Project, ftag: StepFTag, unset: bool = False) -> None:
        print(f"{UNSETTING if unset else SETTING} ftag {ftag.name} to step " + step.detailed_name() )
        if unset:
            step.ftag &= ~ftag
        else:
            step.ftag |= ftag
        step.sync()

    def rename(self, name: str, task: Cat | Project | Step, parent: Project | None = None) -> None:
        step_text = f" from project {paint(parent.detailed_name(), Project.COLOR)}" if parent is not None else ""
        cls = task.__class__
        cls_name = "category" if cls == Cat else cls.__name__.lower()
        task_name = task.detailed_name() if not isinstance(task, Step) else task.name
        print(f"Renaming {cls_name} {paint(task_name, cls.COLOR)}{step_text} to {name}")
        task.name = name
        task.sync()

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
        return None

    def assign_task(self, day: Day, project: Project) -> None:
        print(f"{ASSIGNING} {project.detailed_name()} to {rainbow(day.date)}")
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
        project_name = "Deleted Project" if task.project is None else task.project.detailed_name()
        print(f"{UNASSIGNING} {project_name} from {rainbow(day.date)}")
        self._unstore_task(task, day)
        upd_day = git.merge_pick(*day.get_merge(), False)
        day.hash = upd_day
        upd_days = git.merge_pick(*Day.get_list_merge(), False)
        git.switch_reset(rb.DAYS, upd_days)
        
    def mark_task(self, day: Day, task: Task, mark: Mark) -> None:
        print(f"{MARKING} task {task.detailed_name()} as {paint(mark.name, mark.colour)}")
        prev_mark = task.mark
        task.mark = mark
        task.sync()
        project = task.project
        if project is None: return
        if mark == Mark.Done:
            project.update_last_done(day.date)
        elif mark == Mark.NotDone and prev_mark == Mark.Done:
            project.fetch_last_done()

    def mark_task_step(self, day: Day, task: Task, step: Step, mark: Mark) -> None:
        print(f"{MARKING} step {step.detailed_name()} from task {task.detailed_name()} as {paint(mark.name, mark.colour)}")
        task.step_marks[step.hash] = mark
        task.sync()



    def pick[T: Project | Cat](self, t_list: Sequence[T], name: str | None, fuzzy: str | None, force_menu: bool = False) -> tuple[T | None, bool]:
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
            inp = input(f"Enter number in [0, {len(t_list)-1}] or q(uit): ").lower()
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
        
        

    def precompute(self) -> None:
        branch_names = [
            'categories',
            'projects',
            'days',
            'today']
        hashes = git.show(branch_names, pretty="%H %P").split('\n\n')
        
        cat_hashes, project_hashes, day_hashes, today_list = [x.split(' ') for x in hashes]

        self.task_storage = cat_hashes[1]
        cat_hashes = cat_hashes[2:]
        project_hashes = project_hashes[2:]
        day_hashes = day_hashes[2:]
        today = today_list[0]


        self.actual_date = run.get_date()

        # :Categories:
        

        parent_names = [x.split(' ', 1) for x in git.show(cat_hashes, pretty="%P %N").split('\n\n')]
        
        offset = len(cat_hashes)
        cats = zip(cat_hashes, parent_names)
        
        for hash, parent_name in cats:
            parent_hash, name_json = parent_name
            info = json.loads(name_json)
            archived = info.get('archived', False)
            name = info.get('name', Error)
            cat = Cat(hash, name, parent_hash, archived)
            self.cats[hash] = cat

        for cat in self.cats.values():
            parent_hash = cat.parent
            if parent_hash not in self.cats: continue
            self.cats[parent_hash].subcats.append(cat)

        for cat in self.cats.values():
            path = [cat.name]
            parent_hash = cat.parent
            while parent_hash in self.cats:
                parent = self.cats[parent_hash]
                parent_hash = parent.parent
                path.append(parent.name)
            
            self.cats_path[tuple(path[::-1])] = cat
            
        
        # :Projects:
        
        root_step = [x.split(' ') for x in git.show(project_hashes, pretty="%aI %P").split('\n') if x != '']
        mtimes = [x[0] for x in root_step]
        steps_list = [x[2:] for x in root_step]
        
        # :Steps:

        steps = list(flatten(steps_list))
        infos = git.notes_show_list(steps)
        for hash, name_json in zip(steps, infos):
            info = json.loads(name_json)
            name = info.get('name') or Error
            ftag = info.get('ftag', 0)
            step = Step(hash, name, StepFTag(ftag))
            self.steps[hash] = step


        # :Projects: again
        
        roots = [x[1] for x in root_step]
        notes = git.notes_show_list(list(roots))

        projects = zip(project_hashes, roots, notes, steps_list, mtimes)
        for hash, root, note, steps, mtime in projects:
            info = json.loads(note)
            name = info.get('name') or Error
            cat_name = info.get('category')
            archived = info.get('archived', False)
            ftag = info.get('ftag', 0)
            cat = self.cats[cat_name]
            project_steps = [self.steps[hash] for hash in steps]
            project = Project(hash, root, name, cat, mtime, archived, project_steps, ftag=ProjectFTag(ftag))
            self.projects[project.hash] = project
            self.projects_root[project.root] = project
            if project.name not in self.projects_name:
                self.projects_name[project.name] = [project]
            else:
                self.projects_name[project.name].append(project)
            cat.projects.append(project)
            

        # :Days:
        day_tasks_str = [x.split(":") for x in git.show(day_hashes, pretty="%H:%s:%P").split('\n') if x != '']

        # :Tasks:
        task_hashes = list(flatten([x[2].split(' ')[1:] for x in day_tasks_str]))
        tasks = [x.split('\n', 1) for x in git.show(task_hashes, pretty="%P%n%N").split('\n\n\n')]
        for hash, (parents, info_json) in zip(task_hashes, tasks):
            info = json.loads(info_json)
            mark = Mark[info.get('mark')] or Mark.NotDone
            step_marks_str: dict[str, str] = info.get('step_marks') or dict()
            step_marks = {k: Mark[v] for k, v in step_marks_str.items()}
            project_hash = parents.split(' ')[1]
            task_project = self.projects_root.get(project_hash)
            task = Task(hash, task_project, mark, step_marks)
            self.tasks[hash] = task

        # :Days: again

        for hash, subject, parents_str in day_tasks_str:
            day_parents = parents_str.split(' ')
            root = day_parents[0]
            date = subject[4:]
            day_tasks = [self.tasks[hash] for hash in day_parents[1:]]
            day = Day(hash, root, date, day_tasks)
            for task in day_tasks:
                task_project = task.project
                if task.mark != Mark.Done or task_project is None: continue
                task_project.update_last_done(date)
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

