import git

from dataclasses import dataclass
import expression as e

class Colour:
    pass

@dataclass
class RGB(Colour):
    r: int
    g: int
    b: int

    def __str__(self) -> str:
        return f"{r},{g},{b}"

@dataclass
class Palette256(Colour):
    id: int

    def __str__(self) -> str:
        return f"{self.id}"

@dataclass
class UnknownColour(Colour):
    colour: str
    
    def __str__(self) -> str:
        return colour
  

@dataclass
class Category:
    hash: str
    path_name: str
    display_name: str
    display_colour: Colour

    DEFAULT_COLOUR = "99"

    def __init__(self, hash: str, path_name: str | None = None, display_name: str | None = None, display_colour: str | None = None, **kwargs):
        self.hash = hash
        self.path_name = path_name
        self.display_name = display_name or '.'.join([part.capitalize() for part in  path_name.split()])
        self.display_colour = process_colour(display_colour or self.DEFAULT_COLOUR)

    @property
    def name(self) -> str:
        return self.path_name.split('.')[-1]

    def generate_note(self) -> str:
        return f"""\
hash: {self.hash}
path_name: {self.path_name}
display_name: {self.display_name}
display_colour: {self.display_colour}
        """


class Project(Category):
    DEFAULT_COLOUR = "100" #todo

    def name(self) -> str:
        return self.path_name.split
    
    
    

def process_colour(colour: str) -> Colour:
    args = colour.split(',')
    if not all([str.isdecimal(arg) for arg in args]):
        return UnknownColour(colour)
    args = [int(arg) for arg in args]
    
    if len(args) == 1:
        return Palette256(args[0])
    elif len(args) == 3:
        return RGB(*args)
    else:
        return UnknownColour(colour)

class ParsingException(Exception):
    pass

    
def process_category(note: str) -> Category:
    args = dict([
        tuple([s.strip() for s in line.split(':', 1)])
        for line in note.split('\n') if ':' in line])
    if not all([field in args for field in Category.__dataclass_fields__]):
        raise ParsingException(f"This is not a valid category:\n{note}")
    return Category(**args)


def get_existing_categories() -> list[Category]:
    categories = git.get_parents('categories')[1:]
    return [process_category(cat) for cat in git.notes_show_list(categories)]

def get_category_by_name(name: str) -> Category | None:
    return {cat.path_name: cat for cat in get_existing_categories()}.get(name)
