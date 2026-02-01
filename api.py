import git
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from pretty import *
from commit import Commit, rb
import commit
import task
from task import Category, Project, Step


import argparse
from colorama import Fore as f
from colorama import Style as s


class Command:
    command: list[str] = []
    help = ""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        pass

class InstallCommand(Command):
    command = ['install', 'nuke']
    help = "Sets up the git environment"

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        commit.install()


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
        project.add_argument('--parent', '-p', type=str, required=True)

        step = subcmds.add_parser('step', aliases=['s'])
        step.add_argument('name', type=str)
        step.add_argument('--parent', '-p', type=str, required=True)
        
        # parser.add_argument('task_type', choices=['category', 'c', 'project', 'p', 'step', 's'])
        # parser.add_argument('name', type=str)
        # parser.add_argument('--short-name', '-s', type=str, dest='short_name')
        # parser.add_argument('--parent', '-p', type=str, dest='parent')
        # parser.add_argument('--focus', '-f', action="store_true", dest='focus')

    @staticmethod
    def create_category(name: str, silent: bool=False) -> Category:
        existing_path_names: dict[str, Category] = Category.get_existing_dict()

        category_names: list[str] = name.split('.')
        category_names = ['.'.join(category_names[:(i+1)]) for i in range(len(category_names))]

        git.switch(rb.CRAWL)
        prev = None
        for i, cat in enumerate(category_names):
            if cat not in existing_path_names:
                git.reset(prev or rb.TASK_STORAGE)
                break
            prev = existing_path_names[cat].hash
        else:
            if not silent:
                print(f"{name} already exists")
            return existing_path_names[name]

        for category_name in category_names[i:]:
            hash = git.commit_hash(category_name)
            git.notes_add(hash, Category(hash, category_name).generate_note())
            commit.branch_list_append(rb.CATEGORIES, hash)
            git.switch(rb.CRAWL)

        return Category.get_by_name(name)

    

    @staticmethod
    def create_project(args: argparse.Namespace) -> None:
        CreateCommand.create_category(args.parent, silent=True)
        path_name = f'{args.parent}|{args.name}'
        cat: Category = Category.get_by_name(args.parent)

        git.switch(rb.CRAWL)
        git.reset(cat.hash)
        git.commit(f'[i] {path_name}')
        hash = git.commit_hash(f"[t] {path_name}")
        git.notes_add(hash, Project(hash, path_name).generate_note())

        commit.branch_list_append(rb.PROJECTS, hash)
        
    @staticmethod
    def create_step(args: argparse.Namespace) -> None:
        projects: Project | None = Project.get_list_by_name(args.parent)
        if len(projects) == 0:
            print(f"Project {args.parent} doesn't exist")
            return
        elif len(projects) == 1:
            proj = projects[0]
        else:
            print("Choose one of these projects:")
            for i, p in enumerate(projects):
                print(f"{i}. {p.path_name}")
            while True:
                i = input(f"Enter number in [0, {len(projects)-1}]: ")
                if not i.isdecimal():
                    print("Not a number")
                    continue
                i = int(i)
                if i < 0 or i >= len(projects):
                    print("Out of range")
                    continue
                break
            proj = projects[i]

        git.switch(rb.CRAWL)
        git.reset(proj.project_root)
        step_hash = git.commit_hash(args.name)
        new_proj_hash = commit.branch_list_append(proj.hash, step_hash, is_branch=False)
        commit.branch_list_replace(rb.PROJECTS, proj.hash, new_proj_hash)
        
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        print(f"{args = }")
        if task_type.startswith('c'):
            cls.create_category(args.name)
        elif task_type.startswith('p'):
            cls.create_project(args)
        elif task_type.startswith('s'):
            cls.create_step(args)

def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
