import git
from run import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from commit import Commit, rb, rbl, ListCommit
from task import Category, Project, Step
from today import Day, Today
import commit
import task


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

        today_commit = Commit(rb.TODAY)
        date = today_commit.subject.split(' ')[-1]
        const_today = today_commit.parents[0]
        old_today = today_commit.hash
        
        git.switch(rb.CRAWL)
        git.reset(const_today)
        task = git.merge_pick(
            rb.TODAY,
            [const_today, proj.project_root],
            f"@ {date} {proj.name}")
        new_today = rbl.today.append(task)
        rbl.days.replace(old_today, new_today)
        
class TodayCommand(Command):
    command = ["today"]
    help = "Show today's agenda"
    TAB = " "*3

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        print(Today())
        
        # tasks = git.get_parents(rb.TODAY)[1:]
        # tasks = [git.get_parents(task)[1] for task in tasks]
        # projects = Project.get_by_hashes(tasks)
        # for i, proj in enumerate(projects):
        #     print(f"[{i}] {f.RED}{proj.name}{s.RESET_ALL}")
        #     for j, step in enumerate(proj.get_steps()):
        #         print(f"{cls.TAB}{f.LIGHTRED_EX}{j}. {step.name}{s.RESET_ALL}")
        
                
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    debug_parser = argparse.ArgumentParser(add_help=False)
    debug_parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:], parents=[debug_parser])
        cls.setup_parser(cls_parser)
    
    return parser
    
