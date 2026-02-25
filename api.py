from typing import LiteralString, override
from run import get_date
from commit import rb, rbl, ListCommit
import commit
from task import Mark

from db import Cat, Project
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

def process_fuzzy_option(args: argparse.Namespace,  option: str) -> tuple[str | None, str | None]:
    fuzzy = args.fuzzy_flag or args.fuzzy
    option_arg = args.__getattribute__(option)
    return option_arg, fuzzy 

    
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


class BrowseCommand(Command):
    command: list[str] = ["browse", 'b']
    help: str = "show all stored tasks"
    
    TAB: LiteralString = ' '*2

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--archived', '-a', dest='all', action='store_true')
        add_fuzzy_option(parser, 'name', False)

    @staticmethod
    def get_projects(name: str | None, fuzzy: str | None, archived: bool) -> list[Project] | None:
        projects = db.all_projects if archived else db.narch_projects
        if name is None and fuzzy is None: return projects
        cats = db.all_cats if archived else db.narch_cats
        cat = db.pick(cats, name, fuzzy)
        if cat is None: return None
        return [project for project in projects if project.cat == cat]
        
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        name, fuzzy = process_fuzzy_option(args, 'name')
        archived = args.all
        projects = cls.get_projects(name, fuzzy, archived)
        if projects is None:
            search_spec = "contaning" if fuzzy else "exactly"
            print(f"Category with name {search_spec} {fuzzy or name} was not found")
            return

        cat: Cat | None = None
        for project in projects:
            if project.cat != cat:
                cat = project.cat
                print(f"{cat.name.replace('.', ' > ')}:")
            print(f"{cls.TAB}{project.name}")
            for i, step in enumerate(project.steps):
                print(f"{cls.TAB}{cls.TAB}{i}. {step.name}")

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
    
