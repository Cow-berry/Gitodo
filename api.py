import git
import task
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from pretty import *
from commit import Commit
import commit


import argparse
from colorama import Fore as f
from colorama import Style as s


class Command:
    command = ""
    help = ""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        pass
        

def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:])
        cls.setup_parser(cls_parser)
    
    return parser
    
