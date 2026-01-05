Current plan:
- adding kinds of tasks
- marking tasks done
  - have a notion of a one-time task, completing which does't let you add them again
  -- also also ARCHIVE THEM so the names are available again (or/and fix subtasks)
  - mark start of day as done when creating the agenda
- displaying current tasks with done marks
- browse all/topic tasks and mass-add them 
- switch to a current task (switch main, switch main back to end when needed)
- make internal branches obscurely-names to not interfere with user input
- do something with subtasks
- polish the app
  - check the current agenda exists
  - check the task exists
  - add colours to everything


# adding a task to today:
- checks that there is a today's agenda (today ends at 4am)
- git-merge-theirs the task to the agenda where
```git-merge-theirs() { git merge --ff-only $(git commit-tree -m "Add task $2" -p $1 -p $2 $2^{tree}); }```
- checks that there's an end to today's agenda
- replaces end with a new end that includes the newly added task
- reset --hard back to the start of agenda

# completing a task for today:
- merges the tasks adding commit to the done branch with -s ours from done side

# showing today's tasks:
- does
```getGitChildren(){     git rev-list --all --parents | grep "^.\{40\}.*${1}.*" | awk '{print $1}' | xargs -I commit git log -1 --oneline commit | cat -; }```
to the start of today's agenda
- then formats it in some way


# showing stats for a day
you can use something like -date="two days ago"
and it will pass it to `date` that can work with it and you can get that day's agenda
