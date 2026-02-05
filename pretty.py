from colorama import Fore as f
from colorama import Style as s
import colorama
import itertools

DONE = f"{f.GREEN} ✔ {s.RESET_ALL}"
IN_PROGRESS = f"{f.LIGHTBLUE_EX} ● {s.RESET_ALL}"
NOT_DONE = f"{f.RED} ■ {s.RESET_ALL}"

endl = f"{s.RESET_ALL}\n"

def rgb(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"

def date(d: str) -> str:
    return f"{f.LIGHTMAGENTA_EX}{d}{s.RESET_ALL}"

def rainbow(string: str) -> str:
    rainbow = [
        f.LIGHTRED_EX,
        rgb(255,91,0),
        f.LIGHTYELLOW_EX,
        f.LIGHTGREEN_EX,
        f.LIGHTCYAN_EX,
        f.LIGHTBLUE_EX,
        f.LIGHTMAGENTA_EX
    ]
    rainbow = [x for c in rainbow for x in [c]*2]

    return ''.join([f"{style}{ch}{s.RESET_ALL}" for ch, style in zip(string, itertools.cycle(rainbow))])

