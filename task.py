import git

from typing import Self
from dataclasses import dataclass
import expression as e
from commit import rb
from pprint import pprint

class Colour:
    pass

@dataclass
class RGB(Colour):
    r: int
    g: int
    b: int

    def __str__(self) -> str:
        return f"{self.r},{self.g},{self.b}"

@dataclass
class Palette256(Colour):
    id: int

    def __str__(self) -> str:
        return f"{self.id}"

@dataclass
class UnknownColour(Colour):
    colour: str
    
    def __str__(self) -> str:
        return self.colour
  

@dataclass
class Category:
    hash: str
    path_name: str
    display_name: str
    display_colour: Colour

    DEFAULT_COLOUR = "99"
    LIST_BRANCH = rb.CATEGORIES

    def __init__(self, hash: str, path_name: str, display_name: str | None = None, display_colour: str | None = None, **kwargs):
        self.hash = hash
        self.path_name = path_name
        self.display_name = display_name or '.'.join([part.capitalize() for part in  path_name.split()])
        self.display_colour = process_colour(display_colour or self.DEFAULT_COLOUR)

    @property
    def name(self) -> str:
        return self.path_name.split('.')[-1]

    def generate_note(self) -> str:
        return f"""\
path_name: {self.path_name}
display_name: {self.display_name}
display_colour: {self.display_colour}
        """

    @classmethod
    def process_note(cls, hash: str, note: str) -> Self:
        lines = [line.split(':', 1) for line in note.split('\n') if ':' in line]
        args = {name.strip(): arg.strip() for name, arg in lines}
        args.update({'hash': hash})

        return cls(**args)

    @classmethod
    def get_existing(cls) -> list[Self]:
        tasks = git.get_parents(cls.LIST_BRANCH)[1:]
        pprint(tasks)
        return [cls.process_note(hash, note) for hash, note in zip(tasks, git.notes_show_list(tasks))]

    @classmethod
    def get_existing_dict(cls) -> dict[str, Self]:
        deb= {task.path_name: task for task in cls.get_existing()}
        pprint(deb)
        return deb

    @classmethod
    def maybe_get_by_name(cls, name: str) -> Self | None:
        return cls.get_existing_dict().get(name)


    @classmethod
    def get_by_name(cls, name: str) -> Self:
        return cls.get_existing_dict()[name]
        


class Project(Category):
    steps: list[str]
    
    DEFAULT_COLOUR = "100" #todo
    LIST_BRANCH = rb.PROJECTS

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.steps = git.get_parents(self.hash)

    @property
    def name(self) -> str:
        return self.path_name.split('|')[-1]

    @property
    def project_root(self) -> str:
        return git.get_parents(self.hash)[0]

    @classmethod
    def get_list_by_name(cls, name: str) -> list[Self]:
        return [proj for proj in Project.get_existing() if proj.name == name]

class Step(Category):
    pass
    

def process_colour(colour: str) -> Colour:
    args_str = colour.split(',')
    if not all([str.isdecimal(arg) for arg in args_str]):
        return UnknownColour(colour)
    args = [int(arg) for arg in args_str]
    
    if len(args) == 1:
        return Palette256(args[0])
    elif len(args) == 3:
        return RGB(*args)
    else:
        return UnknownColour(colour)

class ParsingException(Exception):
    pass

