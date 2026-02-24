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
            # already handles check for no duplicates
            Category.create(args.name)
        elif task_type.startswith('p'):
            cat = process_fuzzy_option(args, Category, 'parent')
            if cat is None: return
            if any([p.category==cat.path for p in Project.get_list_by_name(args.name)]):
                print(f"Project {Project.COLOUR}{args.name}{s.RESET_ALL} under category {Category.COLOUR}{cat.path.replace('.', ' -> ')}{s.RESET_ALL} already exists")
                # TODO: show the project info
                return
            Project.create(args.name, cat)
        elif task_type.startswith('s'):
            proj = process_fuzzy_option(args, Project, 'parent')
            if proj is None: return
            Step.create(args.name, proj)

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

    @staticmethod
    def remove_step(proj: Project, id: int) -> None:
        step = proj.get_steps()[id]
        # steps go to valhalla forever
        new_proj_hash = ListCommit(proj.hash).remove(step.hash)
        rbl.projects.replace(proj.hash, new_proj_hash)

    @staticmethod
    def remove_project(proj: Project) -> None:
        print(f'removing project {proj.hash}')
        rbl.archived_projects.append(proj.hash)
        rbl.projects.remove(proj.hash)
        print(f"removed {Project.COLOUR}{proj.name}{s.RESET_ALL}")

    @classmethod
    def remove_category(cls, cat: Category) -> None:
        print(f"{f.GREEN}Removing cat {cat.path} {cat.hash}{s.RESET_ALL}")
        all_projects = Project.get_existing()

        subcats = {p.category for p in all_projects if Category.is_subcat(p.category, cat.path)}
        print(f"{cat.path} -> {subcats}")
        for subcat in subcats:
            subcat_obj = Category.get_by_name(subcat)
            if subcat_obj is None:
                print(f'skipped {subcat}')
                continue
            cls.remove_category(subcat_obj)

        projects = [p for p in all_projects if p.category == cat.path]
        print(f"CORRESPONDING PROJECT TO {cat.path} are {[p.hash for p in projects]}")
        for project in projects:
            cls.remove_project(project)


        rbl.archived_categories.append(cat.hash)
        print(f"Trying to remove {cat.hash}")
        rbl.categories.remove(cat.hash)
        print(f"removed {Category.COLOUR}{cat.display}{s.RESET_ALL}")
    
    # Removing a project should make it still readable, but archived (and maybe restorable)
    # Removing a category should be reflected in the browse command (project that are inside the removed category also need to removed (maybe with a warning)
    # Steps can go to hell
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type == 'c': task_type = 'category'
        if task_type == 'p': task_type = 'project'
        if task_type == 's': task_type = 'step'
        
        if task_type == 'step':
            proj = process_fuzzy_option(args, Project, 'parent', True)
            if proj is None: return
            cls.remove_step(proj, args.step_id)
        elif task_type == 'project':
            proj = process_fuzzy_option(args, Project, 'name', True)
            if proj is None: return
            cls.remove_project(proj)
        else:
            cat = process_fuzzy_option(args, Category, 'name', True)
            if cat is None: return
            cls.remove_category(cat)
            # TODO: category is trying to get removed twice, need debugging
        

class RestoreCommand(Command):
    command: list[str] = ['restore']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['c'])
        category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')

    @staticmethod
    def restore_project(proj: Project) -> None:
        rbl.projects.append(proj.hash)
        rbl.archived_projects.remove(proj.hash)
        print(f"restored {Project.COLOUR}{proj.name}{s.RESET_ALL}")

    @classmethod
    def restore_category(cls, name: str) -> None:
        cat = Category.get_by_name(name, hash=rb.ARCHIVED_CATEGORIES)
        ex_cat = Category.get_by_name(name)
        if cat and ex_cat:
            print("Category named {name} exists both in the data and archive.\nRestore is impossible")
            return
        if cat is None:
            print(f"No archived category named {name} exists")
            return
        all_projects = Project.get_existing(hash=rb.ARCHIVED_PROJECTS)

        subcats = {p.category for p in all_projects if Category.is_subcat(p.category, cat.path)}
        for subcat in subcats:
            cls.restore_category(subcat)

        projects = [p for p in all_projects if p.category == cat.path]
        for project in projects:
            cls.restore_project(project)


        rbl.categories.append(cat.hash)
        rbl.archived_categories.remove(cat.hash)
        print(f"restored {Category.COLOUR}{cat.display}{s.RESET_ALL}")
        
            
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.task_type.startswith('p'):
            project = process_fuzzy_option(args, Project, 'name', True, rb.ARCHIVED_PROJECTS)
            if not project: return
            cls.restore_project(project)
        else:
            cls.restore_category(args.name)
            



    
    

# Todo better formatting
# Todo grep feature
# Todo show only children of one categorie
# Todo show just one project (possibly a separate command)
class BrowseCommand(Command):
    command: list[str] = ["browse", 'b']
    help: str = "show all stored tasks"
    
    TAB: LiteralString = ' '*2

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--archived', '-a', dest='all', action='store_true')
        add_fuzzy_option(parser, 'category', False)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        cat, not_found = process_fuzzy_optional(args, Category, 'category')
        if cat is None and not_found: return
        projects: list[Project] = Project.get_existing()
        if args.all:
            projects += Project.get_existing(rb.ARCHIVED_PROJECTS, True)
        if cat is not None:
            projects = [p for p in projects if p.category == cat.path]
        projects.sort(key=lambda p: p.category)
        prev = None
        result: list[str] = []
        for proj in projects:
            if prev is None or proj.category != prev:
                cat_name = proj.category.replace('.', ' -> ')
                result.append(f"{Category.COLOUR}{cat_name}{s.RESET_ALL}")
                prev = proj.category
            result.append(f"{cls.TAB}{Project.COLOUR if not proj.archived else f.LIGHTRED_EX}{proj.name}{s.RESET_ALL}")
            for i, step in enumerate(proj.get_steps()):
                result.append(f"{cls.TAB*2}{Step.COLOUR}{i}. {step.name}{s.RESET_ALL}")
        print('\n'.join(result))

class AssignCommand(Command):
    command: list[str] = ["assign", 'a']
    help: str = "Assign a task to today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        # parser.add_argument('name', type=str)
        add_fuzzy_option(parser, 'name')
        parser.add_argument('--show', action='store_true')
        parser.add_argument('--schedule', '-d', type=str)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        proj = process_fuzzy_option(args, Project, 'name')
        if proj is None: return
        day: Day
        if args.schedule is None:
            day = Today()
        else:
            date = get_date(args.schedule)
            day = Day.create_or_get(date)
        day.create_task(proj)
        if args.show:
            TodayCommand.run_()

class UnassignCommand(Command):
    command: list[str] = ["unassign", 'una']
    help: str = "Unassign a task from today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('task_id', type=int)
        parser.add_argument('--schedule', '-d', type=str)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        day: Day
        if args.schedule is None:
            day = Today()
        else:
            date = get_date(args.schedule)
            day = Day.create_or_get(date)
        
        task = day.get_task_by_num(args.task_id)
        if task.hash not in day.items and task.hash != day.parents[0]:
            return
        day.remove_task(task.hash)        
    
class TodayCommand(Command):
    command: list[str] = ["today", 't']
    help: str = "Show today's agenda"

    TAB: LiteralString = " "*3

    @override
    @classmethod
    def run_(cls) -> None:
        today = Today()
        ShowCommand.show_day(today)
        today_date = today.date
        actual_date = get_date()

        if today_date != actual_date:
            print(f"{s.BRIGHT}{f.LIGHTRED_EX}{"ACHTUNG:".center(38)}{s.RESET_ALL}")
            print(f"Current agenda points to {f.LIGHTRED_EX}{today_date}{s.RESET_ALL}")
            print(f"But the actual date is {f.LIGHTGREEN_EX}{actual_date}{s.RESET_ALL}")
            print(f"To switch use the `{f.LIGHTMAGENTA_EX}wakeup{s.RESET_ALL}` subcommand")
            
class WakeUpCommand(Command):
    command: list[str] = ["wakeup"]
    help: str = "Update the agenda to show the curret day"

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        date = get_date()
        old_day = Today()
        prev_date = old_day.date
        if date == prev_date:
            print(f"Already on {date}")
            return
        new_day = Day.create_or_get(date)
        old_day.reset(new_day)
        

class UnfocusCommand(Command):
    command: list[str] = ["unfocus"]
    help: str = "mark the inprogress project back to not done"

    @override
    @classmethod
    def run_(cls) -> None:
        tasks = Today().get_tasks()
        for task in tasks:
            if task.mark == Mark.InProgress:
                task.set_mark(Mark.NotDone)
        
class MarkCommand(Command):
    command: list[str] = ["mark", 'm']
    help: str = "Mark the progress of a task from agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('mark_type', choices=['done', 'inprogress', 'undone', *'diu'])
        parser.add_argument('task_id', type=int)
        parser.add_argument('step_id', type=int, default=None, nargs='?')
        parser.add_argument('--show', '-s', action='store_true')
        parser.add_argument('--archive', action='store_true')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.mark_type.startswith('d'):
            mark = Mark.Done
        elif args.mark_type.startswith('i'):
            mark = Mark.InProgress
        else:
            mark = Mark.NotDone

        if mark == Mark.InProgress or args.step_id is not None:
            UnfocusCommand.run_()
           
            
        task = Today().get_task_by_num(args.task_id)
        if args.step_id is None:
            task.set_mark(mark)
        else:
            if task.mark != Mark.Done:
                task.set_mark(Mark.InProgress)
            step: TaskStep = task.get_steps()[int(args.step_id)]
            step.set_mark(mark)

        if args.archive:
            RemoveCommand.remove_project(task.project)

        if args.show:
            TodayCommand.run_()

class ShowCommand(Command):
    command: list[str] = ['show', 's']
    help: str = "Show details"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmd = parser.add_subparsers(dest='kind', required=True)
        
        project = subcmd.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')

        day = subcmd.add_parser('day', aliases=['d'])
        day.add_argument('date', type=str)

    @staticmethod
    def show_project(project: Project) -> None:
        print(project)

    @staticmethod
    def show_day(day: Day) -> None:
        print(day)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.kind == 'p':
            proj = process_fuzzy_option(args, Project, 'name')
            if proj is None: return
            cls.show_project(proj)
        elif args.kind == 'd':
            date = get_date(args.date)
            day = Day.get(date)
            if day is None:
                print(f"There are no records about {date}")
                return
            cls.show_day(day)
            
            
                
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command', required=True)
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
