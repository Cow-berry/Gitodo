import git
from run import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from commit import Commit, rb, rbl, ListCommit
from task import Category, Project, Step, Task
from today import Day, Today
import commit
import task
from task import Mark


import argparse
import os
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
        
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task_type: str = args.task_type
        print(f"{args = }")
        if task_type.startswith('c'):
            Category.create(args.name)
        elif task_type.startswith('p'):
            Project.create(args.name, args.parent)
        elif task_type.startswith('s'):
            Step.create(args.name, args.parent)

# Todo better formatting
# Todo grep feature
# Todo show only children of one categorie
# Todo show just one project (possibly a separate command)
class BrowseCommand(Command):
    command = ["browse", 'b']
    help = "show all stored tasks"
    TAB = ' '*2

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        projects: list[Project] = Project.get_existing()
        projects.sort(key=lambda p: p.path)
        prev = None
        for proj in projects:
            if prev is None or proj.category != prev:
                cat_name = proj.category.replace('.', ' > ')
                print(f"{f.LIGHTMAGENTA_EX}{cat_name}{s.RESET_ALL}")
                prev = proj.category
            print(f"{cls.TAB}{f.LIGHTCYAN_EX}{proj.name}{s.RESET_ALL}")
            for i, step in enumerate(proj.get_steps()):
                print(f"{cls.TAB*2}{f.CYAN}{i}. {step.name}{s.RESET_ALL}")

class AssignCommand(Command):
    command = ["assign"]
    help = "Assign a task to today's agenda"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('name', type=str)

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        proj = Project.pick_project(args.name)
        if proj is None:
            print(f"Project {args.name} doesn't exist")
            return

        Task.create(proj)

class TodayCommand(Command):
    command = ["today", 't']
    help = "Show today's agenda"
    TAB = " "*3


    
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        today_date = Today().date
        actual_date = get_date()

        print(Today())
        
        if today_date != actual_date:
            print(f"Current agenda points to {f.LIGHTRED_EX}{today_date}{s.RESET_ALL}")
            print(f"But the actual date is {f.LIGHTGREEN_EX}{actual_date}{s.RESET_ALL}")
            print(f"To switch use the `{f.LIGHTMAGENTA_EX}wake up{s.RESET_ALL}` subcommand")
            
class WakeUpCommand(Command):
    command = ["wakeup"]
    help = "Update the agenda to show the curret day"

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        date = get_date()
        prev_date = Today().date
        if date == prev_date:
            print(f"Already on {date}")
            return
        git.switch_reset(rb.TODAY, rb.DAYS_STORAGE)
        git.commit(f"[i] {date}")
        git.commit(f"[m] {date}")
        rbl.days.append(rb.TODAY)
        
    
class MarkCommand(Command):
    command = ["mark", 'm']
    help = "Mark the progress of a task from agenda"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('mark_type', choices=['done', 'inprogress', 'undone', *'diu'])
        parser.add_argument('task_id', type=int)
        parser.add_argument('-s', type=int, required=False, dest='step_id')

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.mark_type.startswith('d'):
            mark = Mark.Done
        elif args.mark_type.startswith('i'):
            mark = Mark.InProgress
        else:
            mark = Mark.NotDone

        task = Today().get_task_by_num(args.task_id)
        if args.step_id is None:
            task.set_mark(mark)
            return

        step = task.get_steps()[args.step_id]
        step.set_mark(mark)
    # think where to store the mark (note on the task?)
    # also steps.. are not int, more like 1.3 or something
    # actually do we really need a done branch... i feel like it's a limitation more than anything
    # without the done branch, you can jst edit any day, by moving the `today` branch to different days and not worry about their order
    # upd: yes, but also having one list commit as undo can help for statistics, so we're doing that too
        
                
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
