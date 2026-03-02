from pretty import rainbow
from run import get_date
from commit import rb, rbl, ListCommit
import commit

from db import Cat, Project, Day, Mark, TaskType, TaskTypeList, paint, red, yellow, green
from db import db


import argparse
from colorama import Fore as f
from colorama import Back as b
from colorama import Style as s
from typing import Callable, ClassVar, LiteralString, override
from enum import StrEnum
from collections.abc import Sequence

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

def report_out_of_bounds(id: int, count: int, var_name: str, text: str) -> None:
    error(f"{id} is out of bounds. {text} has {count} {var_name}s. {var_name}_id should be in [0, {count-1}]")
    
    
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
                report(warning, Cat, rd.AlreadyExists, paint(args.name, Cat.COLOR))
                return
        elif task_type.startswith('p'):
            name, fuzzy = process_fuzzy_option(args, 'parent')
            cat, found = db.pick(db.narch_cats, name, fuzzy)
            if cat is None:
                if not found: report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            existing_project = db.create_project(args.name, cat)
            if existing_project is not None:
                report(error, Project, rd.AlreadyExists, f"{paint(args.name, Project.COLOR)} under category {cat.detailed_name()}")
                print()
                ShowCommand.show_project(existing_project)
        else:
            name, fuzzy = process_fuzzy_option(args, 'parent')
            project, found = db.pick(db.narch_projects, name, fuzzy)
            if project is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
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
        category.add_argument('--purge', required=False, action='store_true')
        # category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')
        project.add_argument('--purge', required=False, action='store_true')
        
        step = subcmds.add_parser('step', aliases=['s'])
        step.add_argument('step_id', type=int)
        add_fuzzy_option(step, 'parent')


    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type.startswith('s'):
            name, fuzzy = process_fuzzy_option(args, 'parent')
            project, found = db.pick(db.narch_projects, name, fuzzy)
            if project is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            steps_count = len(project.steps)
            step_id: int = args.step_id
            if step_id < 0 or step_id >= steps_count:
                error(f"{step_id} is out of bounds. Project {paint(project.name, Project.COLOR)} has {steps_count} steps. step_id should be in [0, {steps_count-1}]")
                return
            db.remove_step(project.steps[step_id], project)
        elif task_type.startswith('p'):
            purge: bool = args.purge
            name, fuzzy = process_fuzzy_option(args, 'name')
            projects = db.all_projects if purge else db.narch_projects
            project, found = db.pick(projects, name, fuzzy)
            if project is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            if not purge:
                db.archive_project(project)
                return
            print(f"The following project will be {paint("PERMANENTLY deleted", f.LIGHTRED_EX)}:")
            ShowCommand.show_project(project)
            print("Do you want to continue? [y/N] ", end = '')
            yes = input()
            if yes.lower() != 'y':
                print("Abort.")
                return
            db.remove_project(project)
        elif task_type.startswith('c'):
            purge: bool = args.purge
            name, fuzzy = process_fuzzy_option(args, 'name')
            cats = db.all_cats if purge else db.narch_cats
            cat, found = db.pick(cats, name, fuzzy)
            if cat is None:
                if not found: report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            if not purge:
                db.archive_cat(cat)
                return
            print(f"The following projects and categories will be {paint("PERMANENTLY deleted", f.LIGHTRED_EX)}:")
            ShowCommand.show_category(cat)
            print("Do you want to continue? [y/N] ", end = '')
            yes = input()
            if yes.lower() != 'y':
                print("Abort.")
                return
            db.remove_category(cat)
            
                
class RestoreCommand(Command):
    command: list[str] = ['restore']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        add_fuzzy_option(category, 'name')

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type.startswith('p'):
            name, fuzzy = process_fuzzy_option(args, 'name')
            project, found = db.pick(db.arch_projects, name, fuzzy)
            if project is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            db.restore_project(project)
        elif task_type.startswith('c'):
            name, fuzzy = process_fuzzy_option(args, 'name')
            cat, found = db.pick(db.arch_cats, name, fuzzy)
            if cat is None:
                if not found: report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            db.restore_cat(cat)
        
class WakeUpCommand(Command):
    command: list[str] = ["wakeup"]
    help: str = "Update the agenda to show the curret day"

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        today_date = db.call_date('today')
        if today_date in db.days:
            report(warning, Day, rd.AlreadyExists, rainbow(today_date))
        
        db.create_today(today_date)

        print(db.today.agenda())


class AssignCommand(Command):
    command: list[str] = ["assign", 'a']
    help: str = "Assign a task to today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        add_fuzzy_option(parser, 'name')
        parser.add_argument('--silent', action='store_true')
        parser.add_argument('--schedule', '-d', type=str)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        name, fuzzy = process_fuzzy_option(args, 'name')
        project, found = db.pick(db.narch_projects, name, fuzzy)
        if project is None:
            if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
            return
            
        day = db.today
        if args.schedule:
            date, error_ = db.call_date_maybe(args.schedule)
            if date is None:
                error(error_)
                return
            day = db.create_day(date)

        db.assign_task(day, project)

        if not args.silent:
            print(day.agenda())

            
class UnassignCommand(Command):
    command: list[str] = ["unassign", 'una']
    help: str = "Unassign a task from today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('task_id', type=int)
        parser.add_argument('--silent', action='store_true')
        parser.add_argument('--schedule', '-d', type=str)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        day = db.today
        if args.schedule:
            date, error_ = db.call_date_maybe(args.schedule)
            if date is None:
                error(error_)
                return
            day = db.create_day(date)

        task_id: int = args.task_id
        task_count = len(day.tasks)
        if task_id < 0 or task_id >= task_count:
            error(f"{task_id} is out of bounds. Day {rainbow(day.date)} has {task_count} steps. step_id should be in [0, {task_count-1}]")
            return
        task = day.tasks[task_id]
        db.unassign_task(day, task)

        if not args.silent:
            print(day.agenda())

class MarkCommand(Command):
    command: list[str] = ["mark", 'm']
    help: str = "Mark the progress of a task from agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('mark_type', choices=['done', 'inprogress', 'notdone', *'din'])
        parser.add_argument('task_id', type=int)
        parser.add_argument('step_id', type=int, default=None, nargs='?')
        parser.add_argument('--silent', '-s', action='store_true')
        parser.add_argument('--archive', action='store_true')
        parser.add_argument('--schedule', '-d', type=str)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        silent: bool = args.silent
        archive: bool = args.archive
        mark_type: str = args.mark_type
        mark: Mark
        match mark_type[0]:
            case 'd': mark = Mark.Done
            case 'i': mark = Mark.InProgress
            case _  : mark = Mark.NotDone
        task_id: int = args.task_id
        step_id: int | None = args.step_id
        day = db.today
        if args.schedule:
            date, error_ = db.call_date_maybe(args.schedule)
            if date is None:
                error(error_)
                return
            day = db.create_day(date)
        task_count = len(day.tasks)
        if task_id < 0 or task_id >= task_count:
            report_out_of_bounds(task_id, task_count, 'task', "Day " + rainbow(day.date))
            return
        
        task = day.tasks[task_id]
        project = task.project
        if step_id is not None:
            if project is None:
                error(f"This project was permanently {red("deleted")}. Steps can't be picked.")
                return
            step_count = len(project.steps)
            if step_id < 0 or step_id >= step_count:
                report_out_of_bounds(step_id, step_count, 'step', 'Project ' + paint(project.name, Project.COLOR))
                return
            step = project.steps[step_id]
            if mark == Mark.InProgress: UnfocusCommand.unfocus()
            db.mark_task_step(task, step, mark)
            if mark == Mark.InProgress and task.mark != Mark.Done:
                db.mark_task(task, mark)
            if not silent: print(day.agenda())
            return

        if mark != Mark.NotDone: UnfocusCommand.unfocus()
        db.mark_task(task, mark)
        if archive:
            if project is None: warning("This project is already permanently deleted")
            else: db.archive_project(project)
        if not silent: print(day.agenda())
        


class UnfocusCommand(Command):
    command: list[str] = ["unfocus"]
    help: str = "mark everything inprogress back to not done"

    @staticmethod
    def unfocus() -> None:
        tasks = db.today.tasks
        for task in tasks:
            for step in task.get_steps():
                if task.step_marks.get(step.hash) == Mark.InProgress:
                    db.mark_task_step(task, step, Mark.NotDone)
            if task.mark == Mark.InProgress:
                db.mark_task(task, Mark.NotDone)
    @override
    @classmethod
    def run_(cls) -> None:
        cls.unfocus()
        print(db.today.agenda())
    
class RenameCommand(Command):
    command: list[str] = ["mv"]
    help: str = "rename anything inside task"

    
    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        add_fuzzy_option(category, 'name')
        category.add_argument('new_name', type=str, default=None, nargs='?')
        category.add_argument('--archived', '-a', dest='all', action='store_true')

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')
        project.add_argument('new_name', type=str, default=None, nargs='?')
        project.add_argument('--archived', '-a', dest='all', action='store_true')
        
        step = subcmds.add_parser('step', aliases=['s'])
        add_fuzzy_option(step, 'parent')
        step.add_argument('step_id', type=int)
        step.add_argument('new_name', type=str, default=None, nargs='?')
        step.add_argument('--archived', '-a', dest='all', action='store_true')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        name, fuzzy = process_fuzzy_option(args, 'name' if task_type[0] != 's' else 'parent')
        all: bool = args.all
        match task_type[0]:
            case 'c':
                tasks = db.all_cats if all else db.narch_cats
                cls = Cat
            case _:
                tasks = db.all_projects if all else db.narch_projects
                cls = Project
        task, found = db.pick(tasks, name, fuzzy)
        if task is None:
            if not found: report_fuzzy(error, cls, rd.NotFound, name, fuzzy)
            return

        parent: Project | None = None
        if task_type[0] == 's' and args.step_id is not None and isinstance(task, Project):
            step_id: int = args.step_id
            parent = task
            step_count = len(parent.steps)
            if step_id < 0 or step_id >= step_count:
                report_out_of_bounds(step_id, step_count, 'step', f"Project {parent.detailed_name()}")
                return
            task = parent.steps[step_id]
        new_name: str | None = args.new_name
        if new_name is None:
            print(f"Enter the new name for {task.detailed_name()}: ", end='')
            new_name = input()
        db.rename(new_name, task, parent)

        if isinstance(task, Cat):
            ShowCommand.show_category(task)
            return
        project = parent or task
        if isinstance(project, Project):
            ShowCommand.show_project(project)
        

class ReorderCommand(Command):
    command: list[str] = ["reorder"]
    help: str = "reorder steps in a project"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        add_fuzzy_option(parser, 'name')
        parser.add_argument('--archived', '-a', dest='all', action='store_true')
        

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        name, fuzzy = process_fuzzy_option(args, 'name')
        project_list = db.all_projects if args.all else db.narch_projects
        project, found = db.pick(project_list, name, fuzzy)
        if project is None:
            if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
            return
        ShowCommand.show_project(project)
        steps = project.steps
        step_count = len(steps)
        print(f"Enter numbers 0 through {step_count-1} or q(uit)")
        while True:
            inp = input().lower()
            if inp == 'q' or inp == 'quit':
                print('Exiting.')
                return
            nums_str = inp.split()
            if not all(x.isdecimal() for x in nums_str):
                print("Not numbers: ", ' '.join([x for x in nums_str if not x.isdecimal()]))
                continue
            nums = [int(x) for x in nums_str]
            if min(nums) < 0 or max(nums) >= step_count:
                print('\x1b[1A', end='')
                print("Out of range: " + ' '.join([str(x) for x in nums if x < 0 or x >= step_count]))
                continue
            if len(nums) != len(set(nums)):
                print("Numbers reapeated: " + ' '.join([str(x) for x in nums if nums.count(x) > 1]))
                continue
            if len(nums) < step_count:
                print("Number not mentioned: " + ' '.join([str(i) for i in range(step_count) if i not in nums]))
                continue
            break
        db.reorder_steps(project, nums)
        ShowCommand.show_project(project)
            
            
        
    
            
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

    @classmethod
    def show_multiple_projects(cls, projects: list[Project], reasons: str = "") -> None:
        if len(projects) == 0:
            warning(f"No {paint("projects", Project.COLOR)} found" + reasons)
            return
        cat: Cat | None = None
        for project in projects:
            if project.cat != cat:
                cat = project.cat
                print(f"{paint(cat.detailed_path(), cat.COLOR)}:")
            print(f"{paint("一", Cat.COLOR + s.DIM)} {paint(project.name, project.COLOR)}")
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
            projects = [p for p in projects if args.cat_name in '.'.join(p.cat.path)]
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

    TAB: ClassVar[str] = '  '

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmd = parser.add_subparsers(dest='kind', required=True)

        category = subcmd.add_parser('category', aliases=['c'])
        category.add_argument('--archived', '-a', dest='all', action='store_true')
        category.add_argument('--steps', '-s', dest='show_steps', action='store_true', default=False)
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
    def show_category(cls, cat: Cat, archived: bool=False, steps: bool=True, silent: bool=False) -> None:
        if not silent: print(f"Showing category {cat.detailed_name()}:")
        print(f"{paint(cat.detailed_path(), Cat.COLOR)}:")
        for project in cat.projects:
            if not archived and project.archived: continue
            print(f"{paint("一", Cat.COLOR)} {paint(project.name, project.COLOR)}")
            if not steps: continue
            for i, step in enumerate(project.steps):
                print(paint(f"{cls.TAB}{i}. {step.name}", step.COLOR))

        for subcat in cat.subcats:
            cls.show_category(subcat, archived, steps, True)
            
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.kind.startswith('p'):
            name, fuzzy = process_fuzzy_option(args, 'name')
            proj_list = db.all_projects if args.all else db.narch_projects
            project, found = db.pick(proj_list, name, fuzzy)
            if project is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
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
            show_steps: bool = args.show_steps
            name, fuzzy = process_fuzzy_option(args, 'name')
            cat_list = db.all_cats if args.all else db.narch_cats
            cat, found = db.pick(cat_list, name, fuzzy)
            if cat is None:
                if not found: report_fuzzy(error, Cat, rd.NotFound, name, fuzzy)
                return
            cls.show_category(cat, args.all, show_steps, False)
                
            
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
    
