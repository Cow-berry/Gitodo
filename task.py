from functools import cache
import git
import pretty
from pretty import rgb

from colorama import Fore as f
from colorama import Style as s
from typing import Any, Self, final, override, Callable
from dataclasses import dataclass
from commit import rb, rbl, ListCommit, Commit
from pprint import pprint
from enum import Enum
import json

def generate_note(**kwargs: Any) -> str:
    return json.dumps(kwargs)

class StoredTask:
    hash: str
    path: str

    COLOUR: str
    LIST_BRANCH: str

    @classmethod
    @cache
    def get_existing(cls, hash: str | None = None, archived: bool=False) -> list[Self]:
        tasks = git.get_parents(hash or cls.LIST_BRANCH)[1:]
        return cls.get_by_hashes(tuple(tasks))

    @classmethod
    @cache
    def get_by_hashes(cls, hashes: list[str], archived: bool=False) -> list[Self]:
        # for hash, note in zip(hashes, git.notes_show_list(cls.get_notes_hashes(hashes))):
            # print("PROCESSING NOTE")
            # return [cls.process_note(hash, note, archived=archived)]
        return [cls.process_note(hash, note, archived=archived) for hash, note in zip(hashes, git.notes_show_list(cls.get_notes_hashes(hashes)))]

    @classmethod
    def get_notes_hashes(cls, hashes: list[str]) -> list[str]:
        return hashes

    @classmethod
    def process_note(cls, hash: str, note: str, **kwargs: Any) -> Self:
        args = json.loads(note)
        args.update({'hash': hash, **kwargs})
        return cls(**args)

    
class StoredTaskList(StoredTask):
    LIST_BRANCH: str
    

    @classmethod
    def get_list_by_name(cls, path_name: str, cond: Callable[[str, str], bool] = lambda a, b: a == b, hash: str | None = None, archived: bool=False) -> list[Self]:
        return [task for task in cls.get_existing(hash, archived) if cond(path_name, task.path)]

    @classmethod
    def pick(cls, name: str, cond: Callable[[str, str], bool] = lambda a, b: a == b, hash: str | None = None, force_menu: bool=False) -> Self | None:
        tasks: list[Self] = cls.get_list_by_name(name, cond, hash)
        if len(tasks) == 0:
            return None
        elif len(tasks) == 1 and not force_menu:
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
        print()
        return tasks[index]

    @classmethod
    def partial_pick(cls, search: str, hash: str | None = None, force_menu: bool=False) -> Self | None:
        return cls.pick(search, lambda search, path: search.lower() in path.lower(), hash, force_menu)

    @classmethod
    def full_pick(cls, name: str | None, search: str | None, hash: str | None = None, force_menu: bool = False) -> Self | None:
        if name is not None:
            return cls.pick(name, hash=hash)
        if search is None:
            return None
        return cls.partial_pick(search, hash=hash, force_menu=force_menu)


class Category(StoredTaskList):
    hash: str
    path: str
    name: str

    COLOUR: str = f.LIGHTMAGENTA_EX
    LIST_BRANCH: str = rb.CATEGORIES

    def __init__(self, hash: str, path: str, **_: dict[str, Any]) -> None:
        self.hash = hash
        self.path = path
        self.name = self.path.split('.')[-1]

    @override
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
    def get_existing_dict(cls, hash: str | None = None) -> dict[str, Self]:
        return {task.path: task for task in cls.get_existing(hash)}

    @classmethod
    def get_by_name(cls, name: str, hash: str | None = None) -> Self | None:
        return cls.get_existing_dict(hash).get(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        return name in cls.get_existing_dict()

    # @classmethod
    # def index_by_name(cls, name: str, hash: str| None = None) -> Self:
    #     obj = cls.get_by_name(name, hash)
    #     if obj is None:
    #         raise Exception("Unreachable")
    #     return obj
    

    @classmethod
    def create(cls, name: str) -> Self:
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

        hash: str = ''
        for cat_name in cat_names:
            hash = git.commit_hash(cat_name)
            git.notes_add(hash, generate_note(path=cat_name))
            rbl.categories.append(hash)
            git.switch(rb.CRAWL)

        return cls.process_note(hash, generate_note(path=name))

@final
class Project(StoredTaskList):
    category: str
    archived: bool
    
    COLOUR: str = f.LIGHTCYAN_EX
    LIST_BRANCH: str = rb.PROJECTS
    DELIMITER: str = ""

    def __init__(self, hash: str, category: str="FALLBACK", name: str="FALLBACK", archived: bool=False, **_: Any):
        self.hash = hash
        self.category = category
        self.name = name
        self.path = f"{category}>>>{name}"
        self.archived = archived

    @override
    def __str__(self) -> str:
        return f"{s.BRIGHT}{f.LIGHTYELLOW_EX}{self.name}{s.NORMAL} ({self.category}) {s.DIM}[{self.hash[:8]}]{s.RESET_ALL}"

    def get_steps(self) -> list[Step]:
        return Step.get_existing(self.hash)

    @property
    def project_root(self) -> str:
        return git.get_parents(self.hash)[0]

    
    @classmethod
    def get_by_root(cls, hash: str) -> Project:
        root = cls.process_note(hash, git.notes_show(hash))
        proj_list = cls.get_list_by_name(root.path)
        archived_proj_list = cls.get_list_by_name(root.path, hash=rb.ARCHIVED_PROJECTS, archived=True)
        return [proj for proj in proj_list + archived_proj_list if proj.project_root == hash][0]

    @classmethod
    def get_by_roots(cls, hashes: list[str]) -> list[Project]:
        doubles = len(set(hashes)) != len(hashes)
        if not doubles:
            notes = git.notes_show_list(hashes)
        else:
            notes = git.notes_show_list_doubles(hashes)
        roots = [cls.process_note(hash, note) for hash, note in zip(hashes, notes)]
        proj_list = cls.get_existing() + cls.get_existing(rb.ARCHIVED_PROJECTS, True)
        root_proj = {
            parents[0]: proj
            for proj, parents in zip(
                    proj_list,
                    git.get_parents_lists([proj.hash for proj in proj_list]))}
        return [root_proj[root.hash] for root in roots]

    @override
    @classmethod
    def get_notes_hashes(cls, hashes: list[str]) -> list[str]:
        return [parents[0] for parents in git.get_parents_lists(hashes)]
        # return [git.get_parents(hash)[0] for hash in hashes]


    @classmethod
    def create(cls, name: str, cat: Category) -> None: # type: ignore
        # parent_cat = Category.get_or_create(parent)
        commit_name = f"{name} <<< {cat.path}"
        git.switch(rb.CRAWL)
        git.reset(cat.hash)
        const_hash = git.commit_hash(f'[i] {commit_name}')
        git.notes_add(const_hash, generate_note(category=cat.path, name=name))
        mut_hash = git.commit_hash(f'[m] {commit_name}')
        rbl.projects.append(mut_hash)

@final
class Step(StoredTask):
    category: str
    project: str
    name: str

    COLOUR = f.CYAN

    def __init__(self, hash: str, category: str, project: str, name: str, **_: Any) -> None:
        self.hash = hash
        self.category = category
        self.project = project
        self.name = name
        self.path = f"{category}>>>{project}>>{name}"

    @classmethod
    def create(cls, name: str, proj: Project) -> None: # type: ignore
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


# TODO: implement api command updating marks on tasks and steps
# make sure only one task can be in progress, but you can complete steps in any order
# NotDone project can have Done steps (maybe show percentage and/or progress bar)
@dataclass
class Task:
    hash: str
    root: str
    project: Project
    mark: Mark
    step_marks: dict[str, Mark] # step hash -> mark
    
    def __init__(self, hash: str) -> None:
        self.hash = hash
        self.root = git.get_parents(hash)[1]
        # self.project = Project.get_by_root(git.get_parents(hash)[1])
        self.parse_note()

    def parse_note(self) -> None:
        args = json.loads(git.notes_show(self.hash) or '{}')
        mark_name = args.get('mark', Mark.NotDone.name)
        self.mark = Mark[mark_name]
        step_marks = args.get('step_marks', dict())
        self.step_marks = {hash: Mark[step_marks[hash]] for hash in step_marks}


    def update_note(self) -> None:
        git.notes_add(self.hash, generate_note(
            mark=self.mark.name,
            step_marks={hash: self.step_marks[hash].name for hash in self.step_marks}
        ))

    def set_mark(self, mark: Mark) -> None:
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


@dataclass
class TaskStep:
    task: Task
    step: Step
    mark: Mark
    
    def __init__(self, task: Task, step: Step, mark: Mark) -> None:
        self.task = task
        self.step = step
        self.mark = mark

    @property
    def name(self) -> str:
        return self.step.name

    def set_mark(self, mark: Mark) -> None:
        self.task.step_marks[self.step.hash] = mark
        self.task.update_note()

    
    
