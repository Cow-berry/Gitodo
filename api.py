import git
import task
from cmd import run_cmd, run_cmd_if, GITODO_DIRECTORY
from pretty import *
from commit import Commit


import argparse
from colorama import Fore as f
from colorama import Style as s

def get_date(date: str="today") -> str:
    return run_cmd(['date', '--date', date, '+"%x"']).stdout.strip()[1:-1]


class Command:
    command = ""
    help = ""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        pass
        

class AddCommand(Command):
    command = ["add", 'a']
    help = "Add a task to the general pull"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name", type=str)
        parser.add_argument("-i", "--index", dest='parent', type=int, help="Specify the parent")
        
        kind = parser.add_mutually_exclusive_group(required=True)
        for name in ['category', 'project', 'step']:
            kind.add_argument(f'-{name[0]}', f"--{name}", dest='kind', action='store_const', const=name, help=f"Add a {name}")

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        parent = task.index_through(args.parent) if args.parent is not None else 'last-parent'
        name: str = git.get_branches(parent, exclude=['last-parent', 'main'])[0]
        name = name[::-1].split('--', 1)[1][::-1]
        name = f"{name}.{args.name}--{args.kind}"
        # if args.kind == "category":
        #     name = f"{name}.{args.name}"
        # elif args.kind == "project":
        #     name = f"{name}.{args.name}|"
        # elif args.kind == "step":
        #     name = f"{name}||{args.name}"

        git.branch(name, parent)
        git.switch(name)
        git.commit(f'{args.name}')
        if args.kind != "step":
            git.switch('last-parent')
            git.reset(name)
        

class BrowseCommand(Command):
    command = ["browse", 'b']
    help = "Browse the pull of projects"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--all", dest='all', action="store_true", required=False)

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        git.switch('main')
        git.reset('tasks')
        hash = git.show('main', pretty='%H')
        res: Task = task.traverse_hash(hash)
        print(res)
        

        
        # git.switch('last-parent')

        # branch = 'last-parent'
        # if args.choice is not None:
        #     branch = git.get_children('last-parent')[args.choice]
        #     git.reset(branch)

        # for i, child in enumerate(git.get_children(branch)):
        #     name = git.get_branches(child)[0]
        #     print(f"{i}: {name}")


class BeginCommand(Command):
    command = ["begin"]
    help = "reset the curretn day"

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace, silent=False) -> None:
        today = get_date()
        prev_today = (git.get_branches('today') + [None])[0]
        if today == prev_today:
            if not silent:
                print(f"\n{IN_PROGRESS}Already on day {today}\n")
            return

        if run_cmd_if(['git', 'show-ref', '--quiet', f'refs/heads/{today}']):
            git.switch('today')
            git.reset(today)
            if not silent:
                print(f"\n{IN_PROGRESS}Moved back on day {today}\n")
            return

        git.branch(today, 'days')
        git.switch(today)
        git.commit(f'Agenda start: {today}')
        git.commit(f'Agenda end: {today}')
        git.switch('today')
        git.reset(today)
        print(f"\n{DONE}Successfully switched to {f.LIGHTMAGENTA_EX}{today}{s.RESET_ALL}\n")


class PickCommand(Command):
    command = ["pick"]

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-i", "--index", dest='parent', type=int, help="Specify the parent")

    @staticmethod
    def print_today() -> None:
        for i, (pick, task_hash) in enumerate(zip(task.get_picks(), task.get_tasks())):
            is_done = git.check_belongs(pick, 'done')
            mark = DONE if is_done else NOT_DONE
            subject = git.show(task_hash, pretty="%s")
            print(f"{mark}{i}. {subject}")
         
        
    @staticmethod
    def add_to_today(task_hash: str) -> None:
        git.switch('today')
        end = Commit('today')
        start = end.parents[0]
        git.reset(start)
        pick = git.merge_pick(task_hash, [start, task_hash], f'Pick: {Commit(task_hash).subject}')
        git.merge_pick(start, [*end.parents, pick], end.subject)
        git.reset_branch(get_date(), 'today')
        
        [PickCommand.add_to_today(subtask) for subtask in git.get_children(task_hash, exclude=[pick])]
    

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        BeginCommand.run(args, silent=True)

        if args.parent is None:
           cls.print_today()
           return
       
        parent = task.index_through(args.parent)
        cls.add_to_today(parent)
        
        
        # for subtask in git.get_children(new_task)[1:]:
        #     PickCommand.run(args, hash=subtask)


class UnpickCommand(Command):
    command = ['unpick']

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-i", dest='index', type=int, help="")
        

    @classmethod
    def run(cls, args: argparse.Namespace, hash: Optional[str] = None) -> None:
        today = Commit('today')
        today.parents.pop(args.index + 1)
        new_today = git.merge_pick('today', today.parents, today.subject, False)

        git.reset_branch('today', new_today)
        git.reset_branch(get_date(), new_today)
        
class DoneCommand(Command):
    command = ["done"]

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-i", dest='index', type=int, help="")

    @classmethod
    def run(cls, args: argparse.Namespace, hash: Optional[str] = None) -> None:
        git.switch('done')
        done_task = Commit(Commit('today').parents[args.index + 1])
        git.merge_pick('done', ['done', done_task.hash], f"Done: {done_task.subject}")
        PickCommand.print_today()
        
        
class EvalCommad(Command):
    command = ["eval"]

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("code", type=str, help="Specify the code to eval")

    @classmethod
    def run(cls, args: argparse.Namespace, hash: Optional[str] = None) -> None:
        print(eval(args.code))

class Install(Command):
    command = ["install"]

    # done days tasks 
    @classmethod
    def run(cls, args: argparse.Namespace, hash: Optional[str] = None) -> None:
        run_cmd(["git",  "init"])
        git.commit("Initial commit")
        for name in ['done', 'days', 'tasks']:
            git.branch_(name, 'main')
            git.commit(f"{name.capitalize()} parent")

        git.branch('last-parent', 'tasks')
        git.branch('today', 'days')
        

def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:])
        cls.setup_parser(cls_parser)
    
    return parser
    
