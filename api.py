from typing import LiteralString, override
from run import get_date
from commit import rb, rbl, ListCommit
from task import Category, Project, Step, TaskStep, StoredTaskList
from today import Day, Today
import commit
from task import Mark

from db import db


import argparse
from colorama import Fore as f
from colorama import Back as b
from colorama import Style as s

def add_fuzzy_option(parser: argparse.ArgumentParser, option: str, required: bool=True): # type: ignore
    group = parser.add_mutually_exclusive_group(required=required)
    # default behaviour is fuzzy unless a flag is provided
    group.add_argument(f'fuzzy', type=str, default=None, nargs="?", metavar='fuzzy')
    group.add_argument('--fuzzy', '-r', type=str, dest='fuzzy_flag')
    group.add_argument(f'--{option}', f'-{option[0]}', type=str)
    return group

def process_fuzzy_option[T: StoredTaskList](args: argparse.Namespace, cls: type[T], option: str, force_menu: bool=False, hash: str | None = None) -> T | None:
    fuzzy = args.fuzzy_flag or args.fuzzy
    option_arg = args.__getattribute__(option)
    task = cls.full_pick(option_arg, fuzzy, hash, force_menu)
    if task is not None:
        return task
    if fuzzy:
        print(f"No {cls.__name__.lower()} with name containing {cls.COLOUR}{fuzzy}{s.RESET_ALL} found")
    else:
        print(f"No {cls.__name__.lower()} named exactly {cls.COLOUR}{option_arg}{s.RESET_ALL} found")
    return None

def process_fuzzy_optional[T: Category](args: argparse.Namespace, cls: type[T], option: str) -> tuple[T | None, bool]:
    if (args.fuzzy or args.fuzzy_flag or args.__getattribute__(option)) is None:
        return None, False
    obj = process_fuzzy_option(args, cls, option)
    not_found = obj is None
    return (obj, not_found)
    



    
class Command:
    command: list[str] = []
    help: str = ""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        cls.run_()

    @classmethod
    def run_(cls) -> None:
        pass

class InstallCommand(Command):
    command: list[str] = ['install', 'nuke']
    help: str = "Sets up the git environment"

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        commit.install()
 
        
                
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command', required=True)
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
