import git
import task

import argparse


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
        parser.add_argument("name")
        parser.add_argument("-i", "--index", dest='parent', type=int, help="Specify the parent")
        
        kind = parser.add_mutually_exclusive_group(required=True)
        for name in ['category', 'project', 'step']:
            kind.add_argument(f'-{name[0]}', f"--{name}", dest='kind', action='store_const', const=name, help=f"Add a {name}")

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        parent = task.index_through(args.parent) if args.parent is not None else 'last-parent'
        names: list[str] = git.get_branches(parent)
        names = [name for name in names if name != "last-parent"]
        name = names[0]
        if args.kind == "category":
            name = f"{name}.{args.name}"
        elif args.kind == "project":
            name = f"{name}.{args.name}|"
        elif args.kind == "step":
            name = f"{name}||{args.name}"

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
    def run(cls, args: argparse.Namespace) -> None:
        today = get_date()
        prev_today = (git.get_branches('today') + [None])[0]
        if today == prev_today:
            print(f"Already on day {today}")
            return

        git.branch(today, 'days')
        git.switch(today)
        git.commit(f'Agenda start: {today}')
        git.commit(f'Agenda end: {today}')
        git.switch('today')
        git.reset(today)


class PickCommand(Command):
    command = ["pick"]

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> None:
        pass

def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='Gitodo')
    sub_parsers = parser.add_subparsers(dest='command')
    for cls in Command.__subclasses__():
        cls_parser = sub_parsers.add_parser(cls.command[0], help=cls.help, aliases=cls.command[1:])
        cls.setup_parser(cls_parser)
    
    return parser
    
