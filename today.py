from typing import LiteralString, override
from commit import ListCommit, ListBranch, rb
from task import Project, Task, Mark, generate_note
from pretty import rainbow, rgb, endl
from commit import rbl
import git

from colorama import Fore as f
from colorama import Style as s

class Day(ListCommit):
    TAB: LiteralString = ' '*2
    BRANCH: str = rb.CRAWL
    
    def __init__(self, mut_hash: str):
        super().__init__(mut_hash)

    @property
    def date(self) -> str:
        return self.subject.split(' ')[1]

    def get_task_hashes(self) -> list[str]:
        return self.parents[1:]
        # return [git.get_parents(task)[1] for task in self.parents[1:]]


    def get_tasks(self) -> list[Task]:
        # h = self.get_task_hashes()
        # print('-'*50)
        # print('CREATING TASK')
        # print('-'*50)
        # test_result = [Task(h[0])]
        # print('-'*50)
        # print('FINISHED CREATING TASK')
        # print('-'*50)
        # return test_result
        return [Task(hash) for hash in self.get_task_hashes()]
        # return Project.get_by_roots(self.get_task_hashes())

    def get_task_by_num(self, n: int) -> Task:
        return self.get_tasks()[n]

    @staticmethod
    def get(date: str) -> Day | None:
        day_hashes = rbl.days.items
        days = [Day(hash) for hash in day_hashes]
        days = [day for day in days if day.date == date]
        return days[0] if days else None

    @classmethod
    def create_or_get(cls, date: str) -> Day:
        day = cls.get(date)
        if day: return day
        
        git.switch_reset(cls.BRANCH, rb.DAYS_STORAGE)
        git.commit(f"[i] {date}")
        hash = git.commit_hash(f"[m] {date}")
        rbl.days.append(cls.BRANCH)
        return Day(hash)

    def create_task(self, proj: Project) -> None:
        date = self.date
        const_day = self.parents[0]
        old_day = self.hash
        
        # git.switch(rb.CRAWL)
        # git.reset(self.parents[0])
        task = git.merge_pick(
            self.branch,
            [self.parents[0], proj.project_root],
            f"@ {self.date} {proj.name}",
            False)
        git.notes_add(task, generate_note(mark=Mark.NotDone.name))
        new_day = self.append(task)
        rbl.days.replace(self.hash, new_day)
        # new_today = rbl.today.append(task)
        # rbl.days.replace(old_today, new_today)

    def remove_task(self, hash: str) -> None:
        new_self = self.remove(hash)
        rbl.days.replace(self.hash, new_self)

    def __contains__(self, item: str) -> bool:
        return item in self.get_task_hashes()        

    # formats the list for `today` command
    @override
    def __str__(self) -> str:
        tasks: list[Task] = self.get_tasks() # raw projects without steps
        task_roots = [task.root for task in tasks]
        task_projects = Project.get_by_roots(task_roots)
        
        
        done_count = len([t for t in tasks if t.mark == Mark.Done])
        dots = ''.join([f"{t.mark.colour}●{s.RESET_ALL}" for t in tasks])
        res = rainbow(f"Agenda @ {self.date}") +  f"[{s.BRIGHT}{f.LIGHTGREEN_EX}{done_count}{s.RESET_ALL}/{len(tasks)}]:{dots}\n"
        ln = len(str(len(tasks)-1))
        for i, (task, project) in enumerate(zip(tasks, task_projects)):
            task.project = project
            res += f"{task.mark.emoji()}{task.mark.colour}[{i:>{ln}}] {task.name} {rgb(*[160]*3)}({task.category}){s.RESET_ALL}{s.BRIGHT}{f.LIGHTRED_EX}{'' if not task.project.archived else " ARCHIVED "}{s.RESET_ALL}:{endl}"
            steps = task.get_steps()
            override_mark = None
            if task.mark == Mark.Done:
                override_mark = Mark.Done
            for j, step in enumerate(steps):
                res += f"{self.TAB}{ (override_mark or step.mark).colour}{s.DIM}{j}. {s.NORMAL}{s.BRIGHT}{step.name}{endl}"
        return res
            
        


class Today(Day, ListBranch):
    BRANCH: str = rb.TODAY
    
    def __init__(self) -> None:
        super().__init__(rb.TODAY)

    def reset(self, other: Day):
        git.switch_reset(self.branch, other.hash)
        
        
