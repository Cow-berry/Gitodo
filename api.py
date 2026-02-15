from typing import LiteralString, override
import git
from run import run_cmd, run_cmd_if, GITODO_DIRECTORY, get_date
from commit import Commit, rb, rbl, ListCommit
from task import Category, Project, Step, Task, TaskStep
from today import Day, Today
import commit
import task
from task import Mark


import argparse
import os
from colorama import Fore as f
from colorama import Style as s

def add_fuzzy_option(parser: argparse.ArgumentParser, option: str) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--fuzzy', '-r', type=str)
    group.add_argument(f'--{option}', f'-{option[0]}', type=str)

def process_fuzzy_option[T: Category](args: argparse.Namespace, cls: type[T], option: str) -> T | None:
    task = cls.full_pick(args.__getattribute__(option), args.fuzzy)
    if task is not None:
        return task
    if args.fuzzy:
        print(f"No {cls.__name__.lower()} with name containing {cls.COLOUR}{args.fuzzy}{s.RESET_ALL} found")
    else:
        print(f"No {cls.__name__.lower()} named exactly {cls.COLOUR}{args.__getattribute__(option)}{s.RESET_ALL} found")
    return None
    
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
        subcmds = parser.add_subparsers(dest='task_type')

        category = subcmds.add_parser('category', aliases=['c'])
        category.add_argument('name', type=str)

        project = subcmds.add_parser('project', aliases=['p'])
        project.add_argument('name', type=str)
        add_fuzzy_option(project, 'parent')
        # project.add_argument('--parent', '-p', type=str, required=True)

        step = subcmds.add_parser('step', aliases=['s'])
        step.add_argument('name', type=str)
        add_fuzzy_option(step, 'parent')
        
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
        subcmds = parser.add_subparsers(dest='task_type')

        category = subcmds.add_parser('category', aliases=['cat', 'c'])
        category.add_argument('name', type=str)

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
        rbl.archived_projects.append(proj.hash)
        rbl.projects.remove(proj.hash)
        print(f"removed {Project.COLOUR}{proj.name}{s.RESET_ALL}")

    @classmethod
    def remove_category(cls, name: str) -> None:
        cat = Category.get_by_name(name)
        if cat is None:
            print(f"No category named {name} exists")
            return
        
        all_projects = Project.get_existing()

        subcats = {p.category for p in all_projects if Category.is_subcat(p.category, cat.path)}
        for subcat in subcats:
            cls.remove_category(subcat)

        projects = [p for p in all_projects if p.category == cat.path]
        for project in projects:
            cls.remove_project(project)


        rbl.archived_categories.append(cat.hash)
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
            proj = process_fuzzy_option(args, Project, 'parent')
            if proj is None: return
            cls.remove_step(proj, args.step_id)
        elif task_type == 'project':
            proj = process_fuzzy_option(args, Project, 'name')
            if proj is None: return
            cls.remove_project(proj)
        else:
            cls.remove_category(args.name)
        

class RestoreCommand(Command):
    command: list[str] = ['restore']
    help: str = "Remove a task"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        subcmds = parser.add_subparsers(dest='task_type')

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
        print(args)
        if args.task_type.startswith('p'):
            project = process_fuzzy_option(args, Project, 'name')
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
        parser.add_argument('--all', '-a', dest='all', action='store_true')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        projects: list[Project] = Project.get_existing()
        if args.all:
            projects += Project.get_existing(rb.ARCHIVED_PROJECTS)
        projects.sort(key=lambda p: p.category)
        prev = None
        for proj in projects:
            if prev is None or proj.category != prev:
                cat_name = proj.category.replace('.', ' -> ')
                print(f"{Category.COLOUR}{cat_name}{s.RESET_ALL}")
                prev = proj.category
            print(f"{cls.TAB}{Project.COLOUR}{proj.name}{s.RESET_ALL}")
            for i, step in enumerate(proj.get_steps()):
                print(f"{cls.TAB*2}{Step.COLOUR}{i}. {step.name}{s.RESET_ALL}")

class AssignCommand(Command):
    command: list[str] = ["assign", 'a']
    help: str = "Assign a task to today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        # parser.add_argument('name', type=str)
        add_fuzzy_option(parser, 'name')
        parser.add_argument('--show', action='store_true')

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        proj = process_fuzzy_option(args, Project, 'name')
        if proj is None: return
        Task.create(proj)
        if args.show:
            TodayCommand.run_()

class UnassignCommand(Command):
    command: list[str] = ["unassign", 'una']
    help: str = "Unassign a task from today's agenda"

    @override
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('task_id', type=int)

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        task = Today().get_task_by_num(args.task_id)
        parents = git.get_parents(rb.TODAY)
        if task.hash not in parents[1:] and task.hash != parents[0]:
            return
        rbl.today.remove(task.hash)        
    
class TodayCommand(Command):
    command: list[str] = ["today", 't']
    help: str = "Show today's agenda"

    TAB: LiteralString = " "*3

    @override
    @classmethod
    def run_(cls) -> None:
        today_date = Today().date
        actual_date = get_date()

        print(Today())
        
        if today_date != actual_date:
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
        prev_date = Today().date
        if date == prev_date:
            print(f"Already on {date}")
            return
        git.switch_reset(rb.TODAY, rb.DAYS_STORAGE)
        git.commit(f"[i] {date}")
        git.commit(f"[m] {date}")
        rbl.days.append(rb.TODAY)
        

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
        parser.add_argument('-s', type=int, required=False, dest='step_id')
        parser.add_argument('--show', action='store_true')

    @override
    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        if args.mark_type.startswith('d'):
            mark = Mark.Done
        elif args.mark_type.startswith('i'):
            mark = Mark.InProgress
        else:
            mark = Mark.NotDone

        if mark == Mark.InProgress:
            UnfocusCommand.run_()
           
            
        task = Today().get_task_by_num(args.task_id)
        if args.step_id is None:
            task.set_mark(mark)
        else:
            if mark == Mark.InProgress and task.mark == Mark.NotDone:
                task.set_mark(Mark.InProgress)
            step: TaskStep = task.get_steps()[int(args.step_id)]
            step.set_mark(mark)

            

        if args.show:
            TodayCommand.run_()


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
    
