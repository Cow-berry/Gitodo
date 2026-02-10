from commit import ListCommit, ListBranch, rb
from task import Project, Task, Mark
from pretty import *
import git

class Day(ListCommit):
    TAB = ' '*2
    
    def __init__(self, hash):
        super().__init__(hash)

    @property
    def date(self) -> str:
        return self.subject.split(' ')[1]

    def get_task_hashes(self) -> list[str]:
        return self.parents[1:]
        # return [git.get_parents(task)[1] for task in self.parents[1:]]


    def get_tasks(self) -> list[Project]:
        return [Task(hash) for hash in self.get_task_hashes()]
        # return Project.get_by_roots(self.get_task_hashes())

    def get_task_by_num(self, n: int) -> Task:
        return self.get_tasks()[n]

    def __contains__(self, item) -> bool:
        return item in self.get_task_hashes()        

    # formats the list for `today` command
    def __str__(self) -> str:
        tasks: list[Task] = self.get_tasks() # raw projects without steps
        res = rainbow(f"Agenda @ {self.date}:\n")
        ln = len(str(len(tasks)-1))
        for i, task in enumerate(tasks):
            res += f"{task.mark.emoji()}{task.mark.colour}[{i:>{ln}}] {task.name} {rgb(*[160]*3)}({task.category}):{endl}"
            steps = task.get_steps()
            override_mark = None
            if task.mark == Mark.Done:
                override_mark = Mark.Done
            for j, step in enumerate(steps):
                res += f"{self.TAB}{ (override_mark or step.mark).colour}{s.DIM}{j}. {s.NORMAL}{s.BRIGHT}{step.name}{endl}"
        return res
            
        


class Today(Day, ListBranch):
    def __init__(self):
        super().__init__(rb.TODAY)
        
        
