import git
import pretty
from pretty import *

from typing import Self, override
from dataclasses import dataclass
from commit import rb, rbl, ListCommit, Commit
from pprint import pprint
from enum import Enum
import json

def generate_note(**kwargs) -> str:
    return json.dumps(kwargs)




@dataclass
class Category:
    hash: str
    path: str
    name: str

    COLOUR = f.LIGHTMAGENTA_EX
    LIST_BRANCH = rb.CATEGORIES

    def __init__(self, hash: str, path: str, **kwargs):
        self.hash = hash
        self.path = path
        self.name = self.path.split('.')[-1]

    def __str__(self) -> str:
        return f"{f.LIGHTYELLOW_EX}{self.name} ({self.path}) {s.DIM}[{self.hash[:8]}]{s.RESET_ALL}"

    @property
    def display(self) -> str:
        return f"{self.COLOUR}{self.name} ({self.path.replace('.', ' -> ')})"

    @staticmethod
    def is_subcat(a_str: str, b_str: str) -> bool:
        a = a_str.split('.')
        b = b_str.split('.')
        if len(a) <= len(b):
            return False
        return all([ax == bx for ax, bx in zip(a, b)])
        
    
    @classmethod
    def process_note(cls, hash: str, note: str) -> Self:
        args = json.loads(note)
        args.update({'hash': hash})
        return cls(**args)

    @classmethod
    def get_by_hashes(cls, hashes: list[str]) -> list[Self]:
        return [cls.process_note(hash, note) for hash, note in zip(hashes, git.notes_show_list(hashes))]

    @classmethod
    def get_existing(cls, hash: str | None = None) -> list[Self]:
        tasks = git.get_parents(hash or cls.LIST_BRANCH)[1:]
        return cls.get_by_hashes(tasks)

    @classmethod
    def get_list_by_name(cls, path_name: str, cond: Callable[[str, str], true] = lambda a, b: a == b, hash: str | None = None) -> list[Self]:
        return [task for task in cls.get_existing(hash) if cond(path_name, task.path)]
    
    # supposes that tasks have unique names..
    # deprecated
    @classmethod
    def get_existing_dict(cls, **kwargs) -> dict[str, Self]:
        return {task.path: task for task in cls.get_existing(**kwargs)}

    # deprecated
    # category only, since they're unique
    # maybe rename appropriately
    @classmethod
    def get_by_name(cls, name: str, **kwargs) -> Self | None:
        return cls.get_existing_dict(**kwargs).get(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        return name in cls.get_existing_dict()

    @classmethod
    def pick(cls, name: str, **kwargs) -> Self | None:
        tasks: list[Self] = cls.get_list_by_name(name, **kwargs)
        if len(tasks) == 0:
            return None
        elif len(tasks) == 1:
            return tasks[0]
        
        print("Choose one from this list:")
        for i, p in enumerate(tasks):
            print(f"- [{cls.COLOUR}{i}{s.RESET_ALL}] {p}")
            
        while True:
            inp = input(f"Enter number in [0, {len(tasks)-1}] or q(uit): ")
            if inp == 'q' or inp == 'quit':
                print("Exiting")
                return None
            if not inp.isdecimal():
                print("Not a number")
                continue
            index = int(inp)
            if index < 0 or index >= len(tasks):
                print("Out of range")
                continue
            break
        return tasks[index]

    @classmethod
    def partial_pick(cls, search: str) -> Self | None:
        return cls.pick(search, cond=lambda search, path: search.lower() in path.lower())

    @classmethod
    def full_pick(cls, name: str | None, search: str | None) -> Self | None:
        if name is not None:
            return cls.pick(name)
        return cls.partial_pick(search)

    @classmethod
    def get_or_create(cls, name: str, *args) -> Self:
        existing_paths: dict[str, Self] = cls.get_existing_dict()
        if name in existing_paths:
            return existing_paths[name]

        cat_names: list[str] = name.split('.')
        cat_names = ['.'.join(cat_names[:(i+1)]) for i in range(len(cat_names))]
        cat_names_if = [(cat_name, cat_name in existing_paths) for cat_name in cat_names]
        reset_hash = ([rb.TASK_STORAGE] + [existing_paths[cat].hash for cat, exists in cat_names_if if exists])[-1]
        cat_names = [cat for cat, exists in cat_names_if if not exists]

        git.switch(rb.CRAWL)
        git.reset(reset_hash)

        for cat_name in cat_names:
            hash = git.commit_hash(cat_name)
            git.notes_add(hash, generate_note(path=cat_name))
            rbl.categories.append(hash)
            git.switch(rb.CRAWL)

        return cls.get_by_name(name)

    @classmethod
    def create(cls, name: str, *args) -> None:
        cls.get_or_create(name)
        


class Project(Category):
    steps: list[str]
    category: str
    archived: bool
    
    COLOUR = f.LIGHTCYAN_EX
    LIST_BRANCH = rb.PROJECTS
    DELIMITER = ""

    def __init__(self, hash: str, category: str="FALLBACK", name: str="FALLBACK", archived: bool = False, **kwargs):
        self.hash = hash
        self.category = category
        self.archived = archived
        self.name = name
        self.path = f"{category}>>>{name}"

    def __str__(self) -> str:
        return f"{s.BRIGHT}{f.LIGHTYELLOW_EX}{self.name}{s.NORMAL} ({self.category}) {s.DIM}[{self.hash[:8]}]{s.RESET_ALL}"

    def get_steps(self) -> list[Step]:
        return Step.get_existing(self.hash)

    @property
    def project_root(self) -> str:
        return git.get_parents(self.hash)[0]

    @classmethod
    def get_list_by_name(cls, path_name: str, cond: Callable[[str, str], true] = lambda a, b: a == b, **kwargs) -> list[Self]:
        return [task for task in cls.get_existing(**kwargs) if cond(path_name, task.name)]
    
    @classmethod
    def get_by_root(cls, hash: str) -> Project:
        note = git.notes_show(hash)
        root = cls.process_note(hash, note)
        proj_list = cls.get_list_by_name(root.name)
        archived_proj_list = cls.get_list_by_name(root.name, hash=rb.ARCHIVED_PROJECTS)
        return [proj for proj in proj_list + archived_proj_list if proj.project_root == hash][0]

    # doesn't process archive yet
    @classmethod
    def get_by_roots(cls, hashes: list[str]) -> list[Project]:
        roots = [cls.process_note(hash, note) for hash, note in zip(hashes, git.notes_show_list_doubles(hashes))]
        name_proj = {proj.name: proj for proj in cls.get_existing()}
        return [name_proj[proj.name] for proj in roots]
        
        # name_root_dict = {proj.name: proj.hash for proj in roots}
        # return [proj for proj in cls.get_existing() if proj.name in name_root_dict and proj.project_root == name_root_dict[proj.name]]

    @classmethod
    def get_existing(cls, hash: str | None = None) -> list[Self]:
        tasks = git.get_parents(hash or cls.LIST_BRANCH)[1:]
        task_notes = [git.get_parents(task)[0] for task in tasks]
        return [cls.process_note(hash, note) for hash, note in zip(tasks, git.notes_show_list(task_notes))]

    # deprecated
    @classmethod
    def pick_project(cls, name: str) -> Project | None:
        projects: list[Project] = Project.get_list_by_name(name)
        if len(projects) == 0:
            return None
        elif len(projects) == 1:
            return  projects[0]
        
        print("Choose one of these projects:")
        for i, p in enumerate(projects):
            print(f"{i}. {p.path}")
            
        while True:
            inp = input(f"Enter number in [0, {len(projects)-1}]: ")
            if not inp.isdecimal():
                print("Not a number")
                continue
            index = int(inp)
            if index < 0 or index >= len(projects):
                print("Out of range")
                continue
            break
        return projects[index]

    @classmethod
    def create(cls, name: str, parent: str) -> None:
        parent_cat = Category.get_or_create(parent)
        commit_name = f"{name} <<< {parent}"
        git.switch(rb.CRAWL)
        git.reset(parent_cat.hash)
        const_hash = git.commit_hash(f'[i] {commit_name}')
        git.notes_add(const_hash, generate_note(category=parent, name=name))
        mut_hash = git.commit_hash(f'[m] {commit_name}')
        rbl.projects.append(mut_hash)

class Step(Category):
    category: str
    project: str
    name: str

    COLOUR = f.CYAN

    def __init__(self, hash: str, category: str, project: str, name: str, **kwargs):
        self.hash = hash
        self.category = category
        self.project = project
        self.name = name
        self.path = f"{category}>>>{project}>>{name}"
    
    @classmethod
    def create(cls, name: str, proj: Project) -> None:
        # proj = Project.pick_project(parent)
        # if proj is None: return
        git.switch(rb.CRAWL)
        git.reset(proj.project_root)
        step_hash = git.commit_hash(name)
        git.notes_add(step_hash, generate_note(category=proj.category, project=proj.name, name=name))
        new_proj_hash = ListCommit(proj.hash).append(step_hash)
        rbl.projects.replace(proj.hash, new_proj_hash)



class Mark(Enum):
    NotDone = 'not done'
    InProgress = 'in progress'
    Done = 'done'

    def emoji(self) -> str:
        match self:
            case Mark.NotDone:    return pretty.NOT_DONE
            case Mark.InProgress: return pretty.IN_PROGRESS
            case Mark.Done:       return pretty.DONE

    @property
    def colour(self) -> str:
        match self:
            case Mark.NotDone:    return rgb(200, 50, 50)
            case Mark.InProgress: return rgb(0, 255, 255)
            case Mark.Done:       return rgb(50, 255, 50)

class MarkedCommit(Commit):
    mark: Mark
    
    def __init__(self, commit_hash: str, mark: Mark):
        super().__init__(commit_hash)
        # self.mark = mark
        # git.notes_add(generate_note(mark))


# TODO: implement api command updating marks on tasks and steps
# make sure only one task can be in progress, but you can complete steps in any order
# NotDone project can have Done steps (maybe show percentage and/or progress bar)
@dataclass
class Task:
    hash: str
    project: Project
    mark: Mark
    step_marks: dict[str, Mark] # step hash -> mark
    
    def __init__(self, hash):
        self.hash = hash
        self.project = Project.get_by_root(git.get_parents(hash)[1])
        self.parse_note()

    def parse_note(self):
        args = json.loads(git.notes_show(self.hash) or '{}')
        mark_name = args.get('mark', Mark.NotDone.name)
        self.mark = Mark[mark_name]
        step_marks = args.get('step_marks', dict())
        self.step_marks = {hash: Mark[step_marks[hash]] for hash in step_marks}


    def update_note(self):
        git.notes_add(self.hash, generate_note(
            mark=self.mark.name,
            step_marks={hash: self.step_marks[hash].name for hash in self.step_marks}
        ))

    def set_mark(self, mark: Mark):
        self.mark = mark
        self.update_note()

    @property
    def name(self) -> str:
        return self.project.name

    @property
    def category(self) -> str:
        return self.project.category

    def get_steps(self) -> list[TaskStep]:
        steps: list[Step] = self.project.get_steps()
        return [TaskStep(self, step, self.step_marks.get(step.hash, Mark.NotDone)) for step in steps]
        

    
        
    @classmethod
    def create(cls, proj: Project) -> None:
        today_commit = Commit(rb.TODAY)
        date = today_commit.subject.split(' ')[-1]
        const_today = today_commit.parents[0]
        old_today = today_commit.hash
        
        git.switch(rb.CRAWL)
        git.reset(const_today)
        task = git.merge_pick(
            rb.TODAY,
            [const_today, proj.project_root],
            f"@ {date} {proj.name}")
        git.notes_add(task, generate_note(mark=Mark.NotDone.name))
        new_today = rbl.today.append(task)
        rbl.days.replace(old_today, new_today)

@dataclass
class TaskStep:
    task: Task
    step: Step
    mark: Mark
    
    def __init__(self, task: Task, step: Step, mark: Mark):
        self.task = task
        self.step = step
        self.mark = mark

    @property
    def name(self) -> str:
        return self.step.name

    def set_mark(self, mark: Mark):
        self.task.step_marks[self.step.hash] = mark
        self.task.update_note()

    
    
