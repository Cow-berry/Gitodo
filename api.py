import git
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from pretty import *
from commit import Commit, rb
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
    def run(cls, args: argparse.Namespace) -> None:
        return e.Error()

class CreateCommand(Command):
    command = ['create', 'c']
    help = "Creates a task"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type')

        category = subcmds.add_parser('category', aliases=['c'])
        category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        project.add_argument('name', type=str)
        project.add_argument('--parent', '-p', type=str)
        
        # parser.add_argument('task_type', choices=['category', 'c', 'project', 'p', 'step', 's'])
        # parser.add_argument('name', type=str)
        # parser.add_argument('--short-name', '-s', type=str, dest='short_name')
        # parser.add_argument('--parent', '-p', type=str, dest='parent')
        # parser.add_argument('--focus', '-f', action="store_true", dest='focus')

    @staticmethod
    def create_category(name: str, silent: bool=False) -> None:
        
        existing_categories: list[task.Category] = task.get_existing_categories()
        existing_path_names = {cat.path_name: cat for cat in existing_categories}

        category_names: list[str] = name.split('.')
        path_names = [(i, join_name)
                      for i in range(len(category_names))
                      if (join_name:='.'.join(category_names[:(i+1)])) not in existing_path_names]

        if len(path_names) == 0:
            if not silent:
                print(f"{name} already exists")
            return

        git.switch('crawl')
        i, path_name = path_names[0]
        if i == 0:
            git.reset('task-storage')
        else:
            name = '.'.join(category_names[:i])
            cat = existing_path_names[name]
            git.reset(cat.hash)

        for _, path_name in path_names:
            hash = git.commit_hash(path_name)
            git.notes_add(hash, task.Category(hash, path_name).generate_note())

            git.switch(rb.CATEGORIES)
            prev = Commit(rb.CATEGORIES)
            git.reset(rb.TASK_STORAGE)
            git.merge_pick(prev.hash, prev.parents + [hash], prev.subject)
            git.switch(rb.CRAWL)


    @staticmethod
    def create_project(args: argparse.Namespace) -> None:
        path_name = f'{args.parent}|{args.name}'
        cat = args.parent
        cat = task.get_category_by_name(cat)
        CreateCommand.create_category(cat.path_name, silent=True)

        git.switch('crawl')
        git.reset(cat.hash)
        git.commit(f'{path_name} parent ')
        hash = git.commit_hash(path_name)
        git.notes_add(hash, task.Project(hash, path_name).generate_note())
        
        git.switch(rb.PROJECTS)
        prev = Commit(rb.PROJECTS)
        git.reset(rb.TASK_STORAGE)
        git.merge_pick(prev.hash, prev.parents + [hash], prev.subject)

    @staticmethod
    def create_step(args: argparse.Namespace) -> None: # PROTOTYPE
        proj = task.get_project_by_name(args.parent)
        prev = Commit(proj.hash)

        git.switch('crawl')
        git.reset(prev.parents[0])
        hash = git.commit(args.name)
        new_hash = git.merge_pick(prev.hash, prev.parents + [hash], prev.subject)

        prev = Commit(rb.PROJECTS)
        parents = prev.parents
        parents[parents.index(hash)] = new_hash
        git.merge_pick(prev.hash, parents)
        
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        print(f"{args = }")
        if task_type.startswith('c'):
            cls.create_category(args.name)
        elif task_type.startswith('p'):
            cls.create_project(args)
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
    
