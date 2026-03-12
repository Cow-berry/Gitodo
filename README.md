Gitodo README
===============

A fully functional terminal/cmd todo app, that stores all of its data inside git.

Originally a Git + Python exercise, it grew into full-fledged todo app the author is using every day. 

Main philosophy of the app can be expressed in two points:
- You can only focus on a single thing at any moment
- Keeping track of tasks should be a fun convenience, not a chore

Table of contents:
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Reference](#reference)

# Installation
## Windows
Dependencies:
* [Git](https://git-scm.com/install/windows)
* [Image-magick](https://imagemagick.org/script/download.php)
* [Uv](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)

In command line:

0. Go into a directory you want the code to be in  
(skip this step to store in a folder inside C:\Users\\\<username\>)
```
cd Your\Preferrable\Directory\For\Source
```
1. Clone the repo
```
git clone https://github.com/Cow-berry/Gitodo
```
2. Run the install script
```
cd Gitodo && INSTALL_WINDOWS.bat
```
## Linux
Dependencies:
* git
* image-magick (specifically `convert` command)
* uv

```bash
git clone https://github.com/Cow-berry/Gitodo
cd Gitodo && ./INSTALL_LINUX.sh
```

# Usage Guide
> You can get a help for any command by putting -h at the end. including `gd -h` to list all available commands

First command must be [`install`](#install-comand)
```
gd install
```
It sets up the internal storage


To verify tha it worked run
```
gd t
gd today
```
to show today's (empty for now) agenda

> Notice how `today` can be shortened to `t`,   most of the commands can be shortened to 1-3 letters this way. I'll be providing all the options in this document.

### # Creating and Assigning
There are 3 kinds of tasks:
* Categories - used to organise projects
* Projects - the main unit, the tasks themselves
* Steps - numbered list of steps required to complete a project

All of these can be created with the [`create`](#create-command) command:

1) Categories
```
gd create category name
gd c c name
```

Let's create our first category
```
gd c c chores
```

2) Projects
```
gd create project parent name
gd c p parent name
```

Let's create our first project
```
gd c p cho "cook breakfast"
```
> Notice two things:
> 1) just cho was enough because it's a substring of the name. If there are multiple result that fit substring search, you will be given a menu to choose from.
> 2) it a name contains a whitespace, it should be quoted like "cook breafast" here. Otherwise the program will think cook and breakfast are separate arguments.

3) Steps
```
gd create step parent name
gd c s parent name
```
Let's create several steps (you might want to alter the specifics):
```
gd c s bre "make oatmeal"
gd c s bre "turn off the stove"
```
We don't want to forget turning off the stove, so we'll mark that too.

Now let's see what we just created with [`browse`](#browse-command) command
```
gd browse
gd b
```
You should now see that we have:
- category chores
- project cook breakfast
- 2 steps

Suppose we now want to add another step in the middle between the two. You can do it either with a flag to [`create`](#create-command) command or with [`reorder`](#reorder-command) command
```
gd c s bre "make a snack"
gd ord p bre
[enter 0 2 1 in the prompt]

gd c s bre "make another snack" -i 2
```
> Notice how all the counts start with 0. At this moment we have four steps, numbered 0, 1, 2 and 3

Another way to view created tasks is with [`show`](#show-command) command
```
gd s c cho
gd s p bre
```

Finally the main way you interact with projects is through assigning them to a day's agenda. Let's assign our project to today with [`asssign`](#assign-command) command.
```
gd a bre
```

### # Marking tasks off in a fun way
You can see it immeditely showed the updated output of [`today`](#today-command) command as well.
In the agenda you can see it's red, because it's marked as NotDone by deault. To change that we can use [`mark`](#mark-command) command

This will mark the task 0, step 0 in that task, as inprogress.  
Notice how both the step and the project are blue now.

```
gd m i 0 0
```
And this marks it done (green)
```
gd m d 0 0
```
And this marks the task itself done
```
gd m d 0
```

At this point you should actually get a warning saying that there aren't any .png images in a specific folder. I recommend putting several .png images that bring you joy in there. If you need one for test, you can use [this one](https://hololive.hololivepro.com/wp-content/uploads/2020/07/Mori-Calliope_pr-img_03.png).  
Place the image in the folder.
And then do the command again
```
gd m d 0
```
You should see that image along with a congratulatory text


Now there's a useful feautre called ftag (function tag). It's assigned with the [`ftag`](#ftag-command) command
```
gd ftag s must bre 3
gd m n 0
gd m d 0
[enter y in the prompt]
```

We can tag the step 2 of project breakfast (the one about turning off the stove) as the `must` step.  
And now if we mark the task as not done, and then attempt to mark it as done, it will prompt you to confirm that you've completed all the `must` steps.
You can unset it with the same command and --unset (-u) flag
```
gd ftag s must bre 3 -u
```

For steps currently `must` is the only ftag.  
For projects there are three:

- `ago` makes it so you see how many days ago the specific task was completed last
- `bad` switches the folder for congratulatory images to the sad_image one. Meant for negative things you do like aimlessly scrolling social media ^-^
- `wakeup` adds the task to agenda every time you invoke [`wakeup`](#wakeup-command) command (basically making it a daily task)

What is [`wakeup`](#wakeup-command) command? It's the only way to advance to the next day. When today's agenda doesn't correspond to the actual current date, you'll get a warning telling you to switch to the next day using this command

### # Undoing and Fixing Mistakes
In making all these tasks and assignments, you might make a mistake, or otherwise want to change things.

If you want to change the wording of something you have [`rename`](#rename-command) command (a.k.a. `reword` a.k.a `mv`, pick your poison).

```
gd reword s bre 0
[enter cook eggs in the prompt]
```
Check `gd b` and `gd t` to check that the name changed both in the global list and agenda.


You can [`unassign`](#unassign-command) any task by mentioning its number in the agenda.

`gd una 0`
would unassign the cooking task we used throughout this guide.

Finally you can archived a task with [`remove`](#remove-command) and return it back with [`restore`](#restore-command) command.

```
gd r p bre
gd restore p bre
```

Why [`remove`](#remove-command) command isn't called "archive"? Well, because it can also permanently remove a task if you specify --purge flag (except steps are purged always)

```
gd r s bre 2
gd r p bre --purge
gd r c cho --purge
```

And with this, the cycle is finished and you have an empty storage.  
If you are reading this, I hope you may find this app useful.  
If you wish something be added or changed, feel free to open a github issue or otherwise contact me.





--------------------------------------------

# Reference


## Install command
Does the initialisation for the internal git repository used for storage
```
gd install
```

## Create command
#### Categories
Creates a nested category, making parents if needed
```
gd create category path.to.subcategory
gd c c path.to.subcategory
```

```
gd c c a.b.c
```
will create categories with names:
- a
- b (child of a)
- c (child of b)
#### Projects
Creates a project in the specified category
```
gd create project ("category substring" | --name "exact category name") "project" [--assign [--schedule date]]
gd c p ("category substr"| -n "exact category name") "project" [-a [-d date]]
```
Without `--name` assumes search by a substring  
Flag `--assign` immediately  assign the project to today  
Flag `--schedule` makes `-a` assign to the specified date

#### Step
Creates a step in the specified project
```
gd create step ("project substring" | --name "exact project name") [--insert integer_place]
gd c s ("project substr" | -n "exact project name") [-i integer_place]
```
Without `--name` assumes search by a substring  
If `-i` is not specified, appends the new step to the end of the list  
If `-i` is specified, inserts the new step in the specified position

## Rename command
Rename a specific task
`rename`, `reword`, `mv` are equivalent ways to invoke this command.
```
gd rename (category|project|step) ("partial name" | --name "full_name") [step_id] --archived [new_name]
gd mv (c|p|s) ("partial", -n "full") [step_id] -a [new_name]
```
Without `--name` assumes search by a substring  
`step_id` is only needed for `rename step`  
Flag `--archived` searches in archived as well  
`new_name` is the new name of the task. If not provided, you are prompted to enter it.



## Browse command
View and search through all tasks
```
gd browse --archived --cat-name "category substring" --project_name "project substring"
gd b -a -c "cat substr" -p "project substr"
```
Without arguments shows all (unarchived unless `--archived`) **projects** (skips categories with no projects)  
Flag `--cat-name` filters categories by substring  
Flag `--project-name` filters projects by substring

## Show command
Shows details of specified task
```
gd show category --archived --steps ("cat substring" | -n "exact cat name")
gd s c -a -s name ("cat substr" | -n "exact")

gd show project --archived ("project substring" | -n "exact project name")
gd s p -a name ("project substr" | -n "exact")

gd show day date
gd s d date

gd show ftag name --archived --steps
gs s f -a -s name
```
#### Category
Shows specified category with its project  
Flag `--archived` searches in archived as well  
Flag `--steps` shows steps of the projects (hidden by default)

#### Project
Shows specified project with its steps  
Flag `--archived` searches in archived as well

#### Day
Show specified day with its tasks

#### Ftag
Shows all projects having the specified ftag  
Flag `--archived` searches in archived as well  
Flag `--steps` shows steps of the projects (hidden by default)

## Ftag command
(Un)sets ftag on project or step
```
ftag project tag_name ("project substring" | -n "exact project name") --archived --unset
ftag p tag_name ("project substr" | -n "exact") -a -u

ftag step tag_name ("project substring" | -n "exact project name") step_id --archived --unset
ftag s tag_name ("project substr" | -n "exact") step_if -a -u
```
Flag `--archived` searches in archived as well  
Flag `--unset` changes the bahvious to unset the ftag

 


## Assign command
Assign a project as a task to a day's agenda
```
gd assign ("project substring" | -n "exact project name") --silent --schedule date --insert position
gd a ("project substr" | -n "exact") -s -d date -i pos
```
Flag `--silent` doesn't print the updated agenda in the end (printed by default)  
Flag `--schedule` allows to change the date (today by default)  
Flag `--insert` inserts the new task in the specified position (last by default)

## Unassign command
Unassign a specific assigned task
```
gd unassign task_id --silent --schedule date
gd una task_id -s -d date
```
task_id is the number you see tasks listed under in `gd t`  
Flag `--silent` doesn't print the updated agenda in the end (printed by default)  
Flag `--schedule` allows to change the date (today by default)

## Mark command
Marks the specified task with specified mark
```
gd mark (done | ingprogress | notdone) task_id [step_id] --silent --archive --schedule date
gd m (d|i|n) task_id [step_id] -s -a -d date
```
If step_id provided, marks the step. Otherwise marks the task as a whole  
Flag `--silent` doesn't print updated agenda (printed by default)  
Flag `--archive` additionally archived the corresponding project (untouched by default)  
Flag `--schedule` allows to operate on specified day (today by default)


## Reorder command
Reorder positions of lists
```
gd reorder (project --archived ("project substring" | --name "exact project name") | day [date])
gd r (p -a ("project substr" | -n "exact") | d [date])
```
if project is chosen, searches in (un)archived projects and gives you a way to enter the positions of steps.
If day is chosen, picks today (or the date specified) and gives you a way to enter the positions of tasks.

## Remove command
Archives/removes a task.
#### Category
Archiving/removing a category also does to all subcategories and all projects under them
```
gd remove category ("category substring" | --name "exact category name") --silent --purge --archived
gd r c ("cat" | -n "exact name") -s --purge -a
```
Flag `--silent` doesn't print the just archived category (printed by default)  
Flag `--purge` permanently removes the category  
Flag `--archive` seacrhes in the archived as well

#### Project
```
gd remove project ("project substring" | --name "exact project name")  --silent --purge --archived
gd r p ("project substr" | -n "exact") -s --purge -a
```
Flag `--silent` doesn't print the just archived project (printed by default)  
Flag `--purge` permanently removes the category  
Flag `--archive` seacrhes in the archived as well

#### Step
Removing steps actually permanently removes. There isn't an option not to.
```
gd remove step ("project substring" | --name "exact project name") step_id --silent --archived
gd r s ("project substr" | -n "exact") step_id -s -a
```
Flag `--silent` doesn't print the updated project (printed by default)  
Flag `--archive` seacrhes for the parent project in the archived as well


## Restore command
Undoes the archiving by `remove` command (without `--purge`)
```
gd restore (category|project) --silent ("partial name" | -n "full name")
gd unarch (c|p) -s ("part" | -n "full")
```
Flag `--silent` doesn't print the just unarchived task (printed by default)  



## Wakeup command
Switches to the current day's agenda.  
Shows a warning if it's already the case.
```
gd wakeup
```
