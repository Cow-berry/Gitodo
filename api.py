from enum import StrEnum
from typing import Callable, ClassVar, LiteralString, override
from run import get_date
from commit import rb, rbl, ListCommit
import commit
from task import Category, Mark

from db import Cat, Project, Day, paint, red, yellow, green
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


def error(text: str) -> None:
    print(red(f"Error: ") + text)

def warning(text: str) -> None:
    print(yellow("Warning: ") + text)

def success(text: str) -> None:
    print(green("Success: ") + text)

class ReportDetail(StrEnum):
    NotFound = "not found"
    AlreadyExists = "already exists"

rd = ReportDetail

def report(func: Callable[[str], None], cls: type[object], detail: ReportDetail, text: str) -> None:
    kind = "Category" if cls == Cat else cls.__name__
    func(f"{kind} {text} {detail}")
    

def report_fuzzy[T: Cat | Project](func: Callable[[str], None], cls: type[T], detail: ReportDetail, name: str | None, fuzzy: str | None) -> None:
    search_spec = "contaning" if fuzzy is not None else "exactly"
    text = f"with name {search_spec} {paint(fuzzy or name, cls.COLOR)}"
    report(func, cls, detail, text)
    
    
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


class CreateCommand(Command):
    command: list[str] = ['create', 'c']
    help: str = "Creates a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['c'])
        category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'parent')
        project.add_argument('name', type=str)

        step = subcmds.add_parser('step', aliases=['s'])
        add_fuzzy_option(step, 'parent')
        step.add_argument('name', type=str)
        
    @classmethod
    @override
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type.startswith('c'):
            cats_created = db.create_multiple_categories(args.name)
            if cats_created == 0:
                report(warning, Category, rd.AlreadyExists, paint(args.name, Cat.COLOR))
                return
            [success(f"Created category {paint(cat.detailed_name(), Cat.COLOR)}") for cat in db.narch_cats[-cats_created:]]
        elif task_type.startswith('p'):
            name, fuzzy = process_fuzzy_option(args, 'parent')
            cat = db.pick(db.narch_cats, name, fuzzy)
            if cat is None:
                report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            existing_project = db.create_project(args.name, cat)
            if existing_project is not None:
                report(error, Project, rd.AlreadyExists, f"{paint(args.name, Project.COLOR)} under category {paint(cat.name, Cat.COLOR)}")
                print()
                ShowCommand.show_project(existing_project)
        else:
            name, fuzzy = process_fuzzy_option(args, 'parent')
            project = db.pick(db.narch_projects, name, fuzzy)
            if project is None:
                report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            db.create_step(args.name, project)

class RemoveCommand(Command):
    command: list[str] = ['remove', 'r']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        add_fuzzy_option(category, 'name')
        # category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')

        step = subcmds.add_parser('step', aliases=['s'])
        step.add_argument('step_id', type=int)
        add_fuzzy_option(step, 'parent')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.task_type.startswith('s'):
            name, fuzzy = process_fuzzy_option(args, 'parent')
            project = db.pick(db.narch_projects, name, fuzzy)
            if project is None:
                report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            steps_count = len(project.steps)
            if args.step_id < 0 or args.step_id >= steps_count:
                error(f"{args.step_id} is out of bounds. Project {paint(project.name, Project.COLOR)} has {steps_count} steps. step_id should be in [0, {steps_count-1}]")
                return
            db.remove_step(project, project.steps[args.steps_id])
            
        
class WakeUpCommand(Command):
    command: list[str] = ["wakeup"]
    help: str = "Update the agenda to show the curret day"

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        existing_day = db.create_day(db.call_date('today'))
        if existing_day is not None:
            # report_already_exists
            return


    

class BrowseCommand(Command):
    command: list[str] = ["browse", 'b']
    help: str = "show all stored tasks"
    
    TAB: ClassVar[str] = ' '*2

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--archived', '-a', dest='all', action='store_true')
        parser.add_argument('--cat-name', '-c', dest='cat_name', type=str, required=False)
        parser.add_argument('--project-name', '-p', dest='project_name', type=str, required=False)

    @staticmethod
    def get_projects(name: str | None, fuzzy: str | None, archived: bool) -> list[Project] | None:
        projects = db.all_projects if archived else db.narch_projects
        if name is None and fuzzy is None: return projects
        cats = db.all_cats if archived else db.narch_cats
        cat = db.pick(cats, name, fuzzy)
        if cat is None: return None
        return [project for project in projects if project.cat.is_subcat(cat)]

    @classmethod
    def show_multiple_projects(cls, projects: list[Project], reasons: str = "") -> None:
        if len(projects) == 0:
            warning(f"No {paint("projects", Project.COLOR)} found" + reasons)
            return
        cat: Cat | None = None
        for project in projects:
            if project.cat != cat:
                cat = project.cat
                print(f"{paint(cat.name.replace('.', ' > '), cat.COLOR)}:")
            print(f"{cls.TAB}{paint(project.name, project.COLOR)}")
            for i, step in enumerate(project.steps):
                print(paint(f"{cls.TAB}{cls.TAB}{i}. {step.name}", step.COLOR))
        
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        projects = db.all_projects if args.all else db.narch_projects

        if args.cat_name is None and args.project_name is None:
            cls.show_multiple_projects(projects)
            return

        reasons: str = ""
        if args.cat_name is not None:
            projects = [p for p in projects if args.cat_name in p.cat.name]
            reasons += f' in {paint("categories", Cat.COLOR)} containing "{paint(args.cat_name, Cat.COLOR)}"'
        if args.project_name is not None:
            projects = [p for p in projects if args.project_name in p.name]
            reasons += f' with {paint("names", Project.COLOR)} containing "{paint(args.project_name, Project.COLOR)}"'

        cls.show_multiple_projects(projects, reasons)



class TodayCommand(Command):
    command: list[str] = ["today", 't']
    help: str = "Show today's agenda"

    TAB: LiteralString = " "*3

    @override
    @classmethod
    def run_(cls) -> None:
        print(db.today.agenda())

        if db.today.date != db.actual_date:
            print()
            print(f"{s.BRIGHT}{f.LIGHTRED_EX}{"ACHTUNG:".center(38)}{s.RESET_ALL}")
            print(f"Current agenda points to {f.LIGHTRED_EX}{db.today.date}{s.RESET_ALL}")
            print(f"But the actual date is {f.LIGHTGREEN_EX}{db.actual_date}{s.RESET_ALL}")
            print(f"To switch use the `{f.LIGHTMAGENTA_EX}wakeup{s.RESET_ALL}` subcommand")
            print()


class ShowCommand(Command):
    command: list[str] = ['show', 's']
    help: str = "Show details"

    TAB: ClassVar[str] = ' '*2

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmd = parser.add_subparsers(dest='kind', required=True)

        category = subcmd.add_parser('category', aliases=['c'])
        category.add_argument('--archived', '-a', dest='all', action='store_true')
        add_fuzzy_option(category, 'name', False)
        
        project = subcmd.add_parser('project', aliases=['p'])
        parser.add_argument('--archived', '-a', dest='all', action='store_true')
        add_fuzzy_option(project, 'name')

        day = subcmd.add_parser('day', aliases=['d'])
        day.add_argument('date', type=str)

    @classmethod
    def show_project(cls, project: Project):
        print("Showing project", end = ' ')
        print(f"{paint(project.name, project.COLOR)}")
        for i, step in enumerate(project.steps):
            print(paint(f"{cls.TAB}{i}. {step.name}", step.COLOR))

    @classmethod
    def show_category(cls, cat: Cat) -> None:
        print("Showing category", end = ' ')
        print(f"{paint(cat.name, Cat.COLOR)}:")
        for project in cat.projects:
            print(f"- {paint(project.name, project.COLOR)}")
            for i, step in enumerate(project.steps):
                print(paint(f"{cls.TAB}{i}. {step.name}", step.COLOR))
            
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.kind.startswith('p'):
            name, fuzzy = process_fuzzy_option(args, 'name')
            proj_list = db.all_projects if args.all else db.narch_projects
            project = db.pick(proj_list, name, fuzzy)
            if project is None:
                search_spec = "contaning" if fuzzy else "exactly"
                print(f"Project with name {search_spec} {fuzzy or name} was not found")
                return
            cls.show_project(project)
        elif args.kind.startswith('d'):
            date = db.call_date(args.date)
            day = db.days.get(date)
            if day is None:
                print(f"There are no records about {date}")
                return
            print(day.agenda())
        elif args.kind.startswith('c'):
            name, fuzzy = process_fuzzy_option(args, 'name')
            cat_list = db.all_cats if args.all else db.narch_cats
            cat = db.pick(cat_list, name, fuzzy)
            if cat is None:
                report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            cls.show_category(cat)
                
            
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
    
