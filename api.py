import git
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from pretty import *
from commit import Commit
import commit


import argparse
from colorama import Fore as f
from colorama import Style as s


class Command:
    command = []
    help = ""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        pass

class CreateCommand(Command):
    command = ['create', 'c']
    help = "Creates a task"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('task_type', choices=['category', 'c', 'project', 'p', 'step', 's'])
        parser.add_argument('name', type=str)
        parser.add_argument('--short-name', '-s', type=str, dest='short_name')
        parser.add_argument('--parent', '-p', type=str, dest='parent')
        parser.add_argument('--focus', '-f', action="store_true", dest='focus')

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        print(f"{args = }")
        if task_type.startswith('c'):
            print("Adding a category")
        elif task_type.startswith('p'):
            print("Adding a project")
        elif task_type.startswith('s'):
            print("Adding a step")

    @staticmethod
    def add_category(args: argparse.Namespace) -> None:
        pass
        
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
