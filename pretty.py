from colorama import Fore as f
from colorama import Style as s

DONE = f"{f.GREEN} ✔ {s.RESET_ALL}"
IN_PROGRESS = f"{f.LIGHTBLUE_EX} ● {s.RESET_ALL}"
NOT_DONE = f"{f.RED} ■ {s.RESET_ALL}"

def date(d: str) -> str:
    return f"{f.LIGHTMAGENTA_EX}{d}{s.RESET_ALL}"

