class App(GitUtils):
    def show_day(self, date="today"):
        branch_name = self.get_date(date)
        print(branch_name)
        added_tasks = git.show('main').split()[1:]
        added_tasks = [(git.show(task).split()[1], self.check_belongs(task, 'done')) for task in added_tasks]
        added_tasks = [(self.get_branches(task)[0], is_done) for task, is_done in added_tasks]
        print(added_tasks)
    
    def end_day(self):
        today = self.get_date()
        main_day = (self.get_branches('main') + [None])[0]
        if today != main_day:
            print(f"Already on day {today}")
            return

        git.branch(today, 'days')
        git.switch(today)
        git.commit(f'Start of {today} agenda')
        git.commit(f'End of {today} agenda')
        git.switch('main')
        git.reset(today)

    def add_task_today(self, task: str):
        today = self.get_date()
        git.switch('main')
        agenda_start = git.log('days', today).split('\n')[-1]
        git.reset(agenda_start)
        git.merge_pick(task, ['main', task], f'Add task {task}')
        parents = git.show(today).split()
        git.merge_pick(agenda_start, [*parents, 'main'], f'End of {today} agenda')
        git.switch(today)
        git.reset('main')
    
    def add_task_kind(self, task: str, parent: str = 'tasks'):
        if not task.startswith('|'):
            task = f'{parent}.{task}'
        
        git.branch(task, parent)
        git.switch(task)
        git.commit(f'Setup for {task}')

    def add_task_kind_step(self, step: str, parent: str):
        self.add_task_kind('||'+step, parent)

    def mark_task_todo(self, task: str):
        task_hash = git.log(task, 'main').split('\n')[-1]
        git.switch('done')
        git.merge_pick('done', ['done', task_hash], f'DONE: {task}')

    def browse(self, parent: str = 'tasks'):
        git.switch('last-parent')
        git.reset(parent)
        children = git.get_children(parent)
        for i, child in enumerate(children):
            child = self.get_branches(child)[0]
            print(f"{i}: {child}")

app = App()
