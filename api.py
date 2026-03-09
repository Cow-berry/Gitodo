from db import Cat, Project, Step, Day, Mark, ProjectFTag, StepFTag, paint, red, yellow, green
from db import db, install
from grats import pick_grats
from pretty import rainbow, rainbowb, rgbb, rgb

import os
import random
import argparse
from datetime import datetime
from colorama import Fore as f
from colorama import Back as b
from colorama import Style as s
from typing import Callable, ClassVar, LiteralString, override
from enum import StrEnum
from collections.abc import Sequence

from run import IMAGE_DIRECTORY

def parse_image(imgf: list[bytes]) -> list[str]:
    w, h = [int(x) for x in imgf[1].decode('utf-8').split()]
    maxcol = int(imgf[2].decode('utf-8'))
    img =  (imgf[3]) #list(imgf[3])
    for x in imgf[4:]:
        img += x
    img_str = ''
    buffer: list[int] = []
    for i, c in enumerate(img):
        buffer.append(c)
        if len(buffer) != 3: continue
        r, g, b = buffer
        buffer=[]
        img_str += f"\x1b[48;2;{r};{g};{b}m \x1b[0m"
        if (i // 3 + 1) % w == 0:
            img_str += '\n'
            
    return img_str.split('\n')

def add_fuzzy_option(parser: argparse.ArgumentParser, option: str, required: bool=True, dash_n: bool=False): # type: ignore
    group = parser.add_mutually_exclusive_group(required=required)
    # default behaviour is fuzzy unless a flag is provided
    group.add_argument(f'fuzzy', type=str, default=None, nargs="?", metavar='fuzzy')
    group.add_argument('--fuzzy', '-r', type=str, dest='fuzzy_flag')
    group.add_argument(f'--{option}', f'-{option[0]}', *(['-n'] if dash_n else []), type=str)
    return group

def process_fuzzy_option(args: argparse.Namespace,  option: str) -> tuple[str | None, str | None]:
    fuzzy = args.fuzzy_flag or args.fuzzy
    option_arg = args.__getattribute__(option)
    return option_arg, fuzzy


def args_to_chosen[T: Cat | Project](cls: type[T], all_list: list[T], narch_list: list[T], args: argparse.Namespace, option: str, all: bool = True) -> T | None:
    name, fuzzy = process_fuzzy_option(args, option)
    choose_list = all_list if all else narch_list
    chosen, found = db.pick(choose_list, name, fuzzy)
    if chosen is None:
        if not found: report_fuzzy(error, cls, rd.NotFound, name, fuzzy)
    return chosen


def args_to_cat(args: argparse.Namespace, option: str, all: bool = True) -> Cat | None:
    return args_to_chosen(Cat, db.all_cats, db.narch_cats, args, option, all)

def args_to_project(args: argparse.Namespace, option: str, all: bool = True) -> Project | None:
    return args_to_chosen(Project, db.all_projects, db.narch_projects, args, option, all)


def args_to_step(args: argparse.Namespace, option: str, all: bool = True) -> tuple[Step, Project] | tuple[None, None]:
    parent = args_to_project(args, option, all)
    if parent is None: return None, None
    step_count = len(parent.steps)
    step_id: int = args.step_id
    if step_id < 0 or step_id >= step_count:
        report_out_of_bounds(step_id, step_count, 'step', f"Project {parent.detailed_name()}")
        return None, None
    return parent.steps[step_id], parent
    

    


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

def report_out_of_bounds(id: int, count: int, var_name: str, text: str, id_name: str | None = None) -> None:
    if id_name is None:
        id_name = f"{var_name}_id"
    error(f"{id} is out of bounds. {text} has {count} {var_name}s. {id_name} should be in [0, {count-1}]")
    
    
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
        group = project.add_argument_group('assign group')
        group.add_argument('-a', '--assign', action='store_true')
        group.add_argument('-d', '--schedule', type=str)
        add_fuzzy_option(project, 'parent')
        project.add_argument('name', type=str)

        
        step = subcmds.add_parser('step', aliases=['s'])
        add_fuzzy_option(step, 'name')
        step.add_argument('step_name', type=str)
        step.add_argument('--insert', '-i', type=int)
        
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
            project, created = db.create_project(args.name, cat)
            if not created:
                report(error, Project, rd.AlreadyExists, f"{paint(args.name, Project.COLOR)} under category {cat.detailed_name()}")
                print()
                ShowCommand.show_project(project)
                return
            if args.assign:
                day = db.today
                if args.schedule:
                    date, error_ = db.call_date_maybe(args.schedule)
                    if date is None:
                        error(error_)
                        return
                    day = db.create_day(date)
                db.assign_task(day, project)
        else:
            name, fuzzy = process_fuzzy_option(args, 'name')
            parent, found = db.pick(db.narch_projects, name, fuzzy)
            if parent is None:
                if not found: report_fuzzy(error, Project, rd.NotFound, name, fuzzy)
                return
            insert: int | None = args.insert
            if insert is not None and (insert < 0 or insert > len(parent.steps)):
                report_out_of_bounds(insert, len(parent.steps), 'steps', parent.detailed_name(), 'insert')
                return
            db.create_step(args.step_name, parent)
            if insert is not None:
                db.reorder_steps(parent, list(range(insert)) + [len(parent.steps)-1] + list(range(insert, len(parent.steps)-1)))
            ShowCommand.show_project(parent)

class RemoveCommand(Command):
    command: list[str] = ['remove', 'r', 'arch']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        add_fuzzy_option(category, 'name')
        category.add_argument('--purge', required=False, action='store_true')
        category.add_argument('--silent', '-s', action='store_true')
        category.add_argument('--archived', '-a', dest='all', action='store_true')

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')
        project.add_argument('--purge', required=False, action='store_true')
        project.add_argument('--silent', '-s', action='store_true')
        project.add_argument('--archived', '-a', dest='all', action='store_true')
        
        step = subcmds.add_parser('step', aliases=['s'])
        add_fuzzy_option(step, 'parent', dash_n=True)
        step.add_argument('step_id', type=int)
        step.add_argument('--silent', '-s', action='store_true')
        step.add_argument('--archived', '-a', dest='all', action='store_true')
        


    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type.startswith('s'):
            step, project = args_to_step(args, 'step_id', args.all)
            if step is None or project is None: return
            db.remove_step(step, project)
            if not args.silent: ShowCommand.show_project(project)
        elif task_type.startswith('p'):
            purge: bool = args.purge
            project = args_to_project(args, 'name', args.all)
            if project is None: return
            if not purge:
                db.archive_project(project)
                if not args.silent: ShowCommand.show_project(project)
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
            purge = args.purge
            cat = args_to_cat(args, 'name', args.all)
            if cat is None: return
            if not purge:
                db.archive_cat(cat)
                if not args.silent: ShowCommand.show_category(cat)
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
    command: list[str] = ['restore', 'unarch']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        category.add_argument('--silent', '-s', action='store_true')
        add_fuzzy_option(category, 'name')

        project = subcmds.add_parser('project', aliases=['p'])
        project.add_argument('--silent', '-s', action='store_true')
        add_fuzzy_option(project, 'name')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        if task_type.startswith('p'):
            project = args_to_chosen(Project, db.arch_projects, [], args, 'name', True)
            if project is None: return
            existing = db.projects_name[project.name]
            if any([not p.archived for p in existing]):
                error("Restoring is impossible. Project with this name already exists. Rename or archive it first.")
                return
            db.restore_project(project)
            if not args.silent: ShowCommand.show_project(project)
        elif task_type.startswith('c'):
            cat = args_to_chosen(Cat, db.arch_cats, [], args, 'name', True)
            if cat is None: return
            
            db.restore_cat(cat)
            if not args.silent: ShowCommand.show_category(cat)
        
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

        for project in db.all_projects:
            if ProjectFTag.WAKEUP in project.ftag:
                db.assign_task(db.today, project)

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
        project = args_to_project(args, 'name', False)
        if project is None: return
        
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
        parser.add_argument('--archive', '-a',  action='store_true')
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
        if project is None:
            error("The referred project was previously deleted.")
            return
            
        if step_id is not None:
            if project is None:
                error(f"This project was permanently {red("deleted")}. Steps can't be picked.")
                return
            step_count = len(project.steps)
            if step_count == 0:
                error(f"Project {project.detailed_name()} has {red('0')} step.")
                return
            if step_id < 0 or step_id >= step_count:
                report_out_of_bounds(step_id, step_count, 'step', 'Project ' + project.detailed_name_str())
                return
            step = project.steps[step_id]
            if mark == Mark.InProgress: UnfocusCommand.unfocus()
            db.mark_task_step(day, task, step, mark)
            if mark == Mark.InProgress and task.mark != Mark.Done:
                db.mark_task(day, task, mark)
            if not silent: print(day.agenda())
            return

        if mark == Mark.Done:
            must_steps = [s for s in project.steps if StepFTag.MUST in s.ftag and task.step_marks.get(s.hash, Mark.NotDone) != Mark.Done]
            for must_step in must_steps:
                print("Have you completed this step: " + must_step.detailed_name() + "[y/N]: ", end='')
                answer = input()
                if answer.lower() != 'y':
                    print('Abort.')
                    return
                db.mark_task_step(day, task, must_step, mark)
        
        if mark == Mark.InProgress: UnfocusCommand.unfocus()
        db.mark_task(day, task, mark)
        if archive:
            # if project is None: warning("This project is already permanently deleted.")
            db.archive_project(project)
        if not silent: print(day.agenda())
        if mark != Mark.Done: return
        
        bad = ProjectFTag.BAD in project.ftag
        img = pick_grats(bad)

        congrats = [rainbow(''.join("CONGRATS ON COMPLETING:")), project.detailed_name()]
        img[len(img)//2-1] += "   " + congrats[0]
        img[len(img)//2] += "   " + congrats[1]

        print('\n'.join(img))
                


class UnfocusCommand(Command):
    command: list[str] = ["unfocus"]
    help: str = "mark everything inprogress back to not done"

    @staticmethod
    def unfocus() -> None:
        tasks = db.today.tasks
        day = db.today
        for task in tasks:
            for step in task.get_steps():
                if task.step_marks.get(step.hash) == Mark.InProgress:
                    db.mark_task_step(day, task, step, Mark.NotDone)
            if task.mark == Mark.InProgress:
                db.mark_task(day, task, Mark.NotDone)
    @override
    @classmethod
    def run_(cls) -> None:
        cls.unfocus()
        print(db.today.agenda())
    
class RenameCommand(Command):
    command: list[str] = ["rename", "reword", "mv"]
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
        chosen: Cat | Project | Step | None
        parent: Project | None
        if task_type.startswith('c'):
            chosen = args_to_cat(args, 'name', args.all)
            parent = None
        elif task_type.startswith('p'):
            chosen = args_to_project(args, 'name', args.all)
            parent = None
        else:
            chosen, parent = args_to_step(args, 'parent', args.all)

        if chosen is None: return

        new_name: str | None = args.new_name
        if new_name is None:
            print(f"Enter the new name for {chosen.detailed_name()}: ", end='')
            new_name = input()
        db.rename(new_name, chosen, parent)

        project = parent or chosen
        if isinstance(chosen, Cat): ShowCommand.show_category
        elif isinstance(project, Project): ShowCommand.show_project(project)


class ReorderCommand(Command):
    command: list[str] = ["reorder", 'ord']
    help: str = "reorder steps in a project"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='list_type', required=True)
        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')
        project.add_argument('--archived', '-a', dest='all', action='store_true')

        day = subcmds.add_parser('day', aliases=['d'])
        day.add_argument('schedule', default=None, type=str, nargs="?")

    @classmethod
    def input_sequence(cls, count: int) -> list[int] | None:
        print(f"Enter numbers 0 through {count-1} or q(uit):")
        
        while True:
            inp = input().lower()
            if inp == 'q' or inp == 'quit':
                print('Exiting.')
                return None
            nums_str = inp.split()
            print('\x1b[1A\r', end='')
            nums: list[int] = []
            not_mentioned = list(range(count))
            out_of_bounds: list[int] = []
            repeated: list[int] = []
            not_numbers: list[str] = []
            for x in inp.split(' '):
                if len(x.strip()) == 0:
                    print(x, end=' ')
                    continue
                if not x.isdecimal() and not (x[0] == '-' and x[1:].isdecimal()):
                    not_numbers.append(x.strip())
                    print(red(x), end=' ')
                    continue
                n = int(x)
                if n < 0 or n >= count:
                    out_of_bounds.append(n)
                    print(red(x), end =' ')
                    continue
                if n not in not_mentioned:
                    repeated.append(n)
                    print(red(x), end=' ')
                    continue
                not_mentioned.remove(n)
                nums.append(n)
                print(green(x), end=' ')
            print()

            if not_numbers: print(f"Not numbers: {red(' '.join(not_numbers))}")
            if not_mentioned: print(f"Not mentioned: {green(' '.join(map(str, not_mentioned)))}")
            if out_of_bounds: print(f"Out of bounds: {red(' '.join(map(str, out_of_bounds)))}")
            if repeated: print(f"Repeated: {red(' '.join(map(str, repeated)))}")

            if len(not_numbers + not_mentioned + out_of_bounds + repeated) == 0:
                return nums
        

    @classmethod
    def handle_day(cls, args: argparse.Namespace) -> None:
        day = db.today
        if args.schedule:
            date, error_ = db.call_date_maybe(args.schedule)
            if date is None:
                error(error_)
                return
            if date not in db.days:
                error(f"Agenda for {date} doesn't yet exist")
                return
            day = db.days[date]

        print(day.agenda())

        tasks = day.tasks
        task_count = len(tasks)
        if task_count == 0:
            warning("No tasks assigned. Nothing to reorder")
            return

        nums = cls.input_sequence(task_count)
        if nums is None: return

        db.reorder_day(day, nums)
        print(day.agenda())

    @classmethod
    def handle_project(cls, args: argparse.Namespace) -> None:
        project = args_to_project(args, 'name', args.all)
        if project is None: return
        ShowCommand.show_project(project)
        steps = project.steps
        step_count = len(steps)
        if step_count == 0:
            warning("No steps. Nothing to reorder.")
            return
            
        nums = cls.input_sequence(step_count)
        if nums is None: return
    
        db.reorder_steps(project, nums)
        ShowCommand.show_project(project)
            
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.list_type.startswith('d'): cls.handle_day(args)
        else: cls.handle_project(args)
        

            
class FtagCommand(Command):
    command: list[str] = ['ftag']
    help: str = "(Un)Set a function tag to a project"
    

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)
        
        project = subcmds.add_parser('project', aliases=['p'])
        project.add_argument('ftag_name',  type=str, choices=[ftag_name.lower() for ftag_name in ProjectFTag._member_names_])
        add_fuzzy_option(project, 'name')
        project.add_argument('--archived', '-a', dest='all', action='store_true')
        project.add_argument('--unset', '-u', action='store_true')
 
        step = subcmds.add_parser('step', aliases=['s'])
        step.add_argument('ftag_name', type=str, choices=[ftag_name.lower() for ftag_name in StepFTag._member_names_])
        add_fuzzy_option(step, 'parent', dash_n=True)
        step.add_argument('step_id', type=int)
        step.add_argument('--archived', '-a', dest='all', action='store_true')
        step.add_argument('--unset', '-u', action='store_true')
 
     
    @classmethod
    @override
    def run(cls, args: argparse.Namespace) -> None:
        if args.task_type.startswith('p'):
            project = args_to_project(args, 'name', args.all)
            if project is None: return
            db.ftag_project(project, ProjectFTag[args.ftag_name.upper()], args.unset)
        else:
            step, project = args_to_step(args, 'parent', args.all)
            if step is None or project is None: return
            db.ftag_step(step, project, StepFTag[args.ftag_name.upper()], args.unset)
    
            
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
    def show_multiple_projects_with_cats(cls, projects: list[Project], reasons: str = "") -> None:
        if len(projects) == 0:
            warning(f"No {paint("projects", Project.COLOR)} found" + reasons)
            return
        cat: Cat | None = None
        for project in projects:
            if project.cat != cat:
                cat = project.cat
                print(f"{cat.detailed_path()}{red(':') if cat.archived else paint(':', Cat.COLOR)}")
            print(f"{paint("一", Cat.COLOR + s.DIM if not project.archived else f.LIGHTRED_EX)} {project.detailed_name(cat=False)}")
            for i, step in enumerate(project.steps):
                if not project.archived:
                    print(paint(f"{cls.TAB}{cls.TAB}{i}. {step.detailed_name_str()}", step.COLOR))
                else:
                    print(red(f"{cls.TAB}{cls.TAB}{i}. {step.detailed_name_str()}"))
                    
        
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        projects = db.all_projects if args.all else db.narch_projects

        if args.cat_name is None and args.project_name is None:
            cls.show_multiple_projects_with_cats(projects)
            return

        reasons: str = ""
        if args.cat_name is not None:
            projects = [p for p in projects if args.cat_name in '.'.join(p.cat.path)]
            reasons += f' in {paint("categories", Cat.COLOR)} containing "{paint(args.cat_name, Cat.COLOR)}"'
        if args.project_name is not None:
            projects = [p for p in projects if args.project_name in p.name]
            reasons += f' with {paint("names", Project.COLOR)} containing "{paint(args.project_name, Project.COLOR)}"'

        cls.show_multiple_projects_with_cats(projects, reasons)



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

        ftag = subcmd.add_parser('ftag', aliases=['f'])
        ftag.add_argument('name', type=str, choices=[x.lower() for x in ProjectFTag._member_names_])
        ftag.add_argument('--archived', '-a', dest='all', action='store_true')
        ftag.add_argument('--steps', '-s', dest='show_steps', action='store_true', default=False)

    @classmethod
    def show_project(cls, project: Project) -> None:
        print("Showing project", end = ' ')
        print(f"{paint(project.detailed_name(), project.COLOR)}:")
        if len(project.steps) == 0:
            print('--- no steps in this project ---')
            return
        for i, step in enumerate(project.steps):
            print(paint(f"{cls.TAB}{i}. {step.detailed_name_str()}", step.COLOR))

    @classmethod
    def show_category(cls, cat: Cat, archived: bool=False, steps: bool=True, silent: bool=False) -> None:
        if not silent: print(f"Showing category {cat.detailed_name()}:")
        print(f"{cat.detailed_path()}:")
        cls.show_multiple_projects(cat.projects, archived, steps, show_cat=False)

        for subcat in cat.subcats:
            cls.show_category(subcat, archived, steps, True)

    @classmethod
    def show_multiple_projects(cls, projects: list[Project], archived: bool= False, steps: bool=True, show_cat: bool=True) -> None:
        for project in projects:
            if not archived and project.archived: continue
            print(f"{paint("一", Cat.COLOR)} {project.detailed_name(show_cat)}")
            if not steps: continue
            for i, step in enumerate(project.steps):
                print(paint(f"{cls.TAB}{i}. {step.detailed_name_str()}", step.COLOR))
            
    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.kind.startswith('p'):
            project = args_to_project(args, 'name', args.all)
            if project is None: return
            cls.show_project(project)
        elif args.kind.startswith('d'):
            date = db.call_date(args.date)
            day = db.days.get(date)
            if day is None:
                print(f"There are {red('no')} records about {rainbow(date)}")
                return
            print(day.agenda())
        elif args.kind.startswith('c'):
            show_steps: bool = args.show_steps
            cat = args_to_cat(args, 'name', args.all)
            if cat is None: return
            cls.show_category(cat, args.all, show_steps, False)
        elif args.kind.startswith('f'):
            name: str = args.name
            show_steps = args.show_steps
            ftag = ProjectFTag[name.upper()]
            proj_list = db.all_projects if args.all else db.narch_projects
            projects = [proj for proj in proj_list if ftag in proj.ftag]
            cls.show_multiple_projects(projects, args.all, show_steps)
            
                
            
class InstallCommand(Command):
    command: list[str] = ['install', 'nuke']
    help: str = "Sets up the git environment"

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        install()


class DebugCommand(Command):
    command: list[str] = ["debug"]
    help: str = "Show all field of a chosen object"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type', required=True)

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        add_fuzzy_option(category, 'name')
        category.add_argument('--archived', '-a', dest='all', action='store_true')

        project = subcmds.add_parser('project', aliases=['p'])
        add_fuzzy_option(project, 'name')
        project.add_argument('--archived', '-a', dest='all', action='store_true')
        
        step = subcmds.add_parser('step', aliases=['s'])
        add_fuzzy_option(step, 'parent', dash_n=True)
        step.add_argument('step_id', type=int)
        step.add_argument('--archived', '-a', dest='all', action='store_true')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type

        if task_type.startswith('c'):
            cat = args_to_cat(args, 'name', args.all)
            if cat is None: return
            print(cat.debug())
        elif task_type.startswith('p'):
            project = args_to_project(args, 'name', args.all)
            if project is None: return
            print(project.debug())
        elif task_type.startswith('s'):
            step, project = args_to_step(args, 'parent', args.all)
            if step is None or project is None: return
            print(project.debug())
            print()
            print(step.debug())

    
 
        
                
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command', required=True)
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
