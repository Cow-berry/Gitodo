import git
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date, e, Result
from pretty import *
from commit import Commit
import commit
import task


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
    def run(cls, args: argparse.Namespace) -> Result[None]:
        return e.Error()

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

    @staticmethod
    @e.effect.result[None, str]()
    def create_category(args: argparse.Namespace) -> Result[None]:
        existing_categories: list[task.Category] = yield from task.get_existing_categories()
        existing_path_names = dict([(cat.path_name, cat) for cat in existing_categories])

        category_names: list[str] = args.name.split('.')
        path_names = ['.'.join(category_names[:(i+1)]) for i in range(len(category_names))]
        path_names = [path_name for path_name in path_names if path_name not in existing_path_names]

        if not path_names: return None
        if '.' not in path_names[0]:
            yield from git.switch('task-storage')
        else:
            parent_path_name = path_names[0][::-1].split('.', 1)[1][::-1]
            parent_cat = existing_path_names.get(parent_path_name)
            if not parent_cat: return e.Error(f"Unreachable: Could not find category {parent_path_name}")
            yield from git.switch(parent_cat.hash)
        
        for path_name in path_names:
            

            
            # yield from git.commit(path_name)\
            #     .bind(lambda _: git.show('HEAD', '%H'))\
            #     .map(lambda hash: [hash, task.Category(hash, path_name)])\
            #     .bind(lambda hash_cat: git.notes_add(hash_cat[0], hash_cat[1].generate_note()))\
            #     .map(lambda _: git.switch('categories'))
            # head = git.show('HEAD', '%H%n%s%n%P')
            # yield from git.reset('HEAD~1')\
            #     .bind(lambda _: head.map(lambda s: s.split('\n')))\
            #     .bind(lambda hash, subject, parents: git.merge_pick(hash, parents.split(), subject))\
            #     .map(lambda: git.switch('-'))
            

        return e.Ok(None)
            
            
    @classmethod
    def run(cls, args: argparse.Namespace) -> Result[None]:
        task_type: str = args.task_type
        print(f"{args = }")
        if task_type.startswith('c'):
            return cls.create_category(args)
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
    
