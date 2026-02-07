from commit import ListCommit, ListBranch, rb
from task import Project
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
        return [git.get_parents(task)[1] for task in self.parents[1:]]


    def get_tasks(self) -> list[Project]:
        return Project.get_by_roots(self.get_task_hashes())

    def __contains__(self, item) -> bool:
        return item in self.get_task_hashes()        

    # formats the list for `today` command
    def __str__(self) -> str:
        tasks = self.get_tasks() # raw projects without steps
        res = rainbow(f"Agenda @ {self.date}:\n")
        ln = len(str(len(tasks)))
        for i, task in enumerate(tasks):
            res += f"{[IN_PROGRESS, DONE][1-i]}{f.LIGHTMAGENTA_EX}[{i:>{ln}}] {task.name} ({task.category}):{s.RESET_ALL}\n"
            steps = task.get_steps()
            for j, step in enumerate(steps):
                res += f"{self.TAB}{f.RED}{j}. {s.BRIGHT}{step.name}{s.RESET_ALL}\n"
        return res
            
        


class Today(Day, ListBranch):
    def __init__(self):
        super().__init__(rb.TODAY)
        
        
