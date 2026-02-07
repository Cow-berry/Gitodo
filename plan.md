General:
	* store changeable in notes
	* store debug in commit msg

Concrete steps:
	~ update cmd&git to return a Result
	- implement create
	- implement browse
	- implement (un)focus
	- implement browse


<USN> = unambiguous short name

--- PROJECT ARENA ------

[d] # gd create (category|project|step) <name:str> [--short-name <short: str>] [--parent <p:USN>] [--focus]
	creates a task object with <p> parent
    --short-name creates a short name used for indexing
		*in case if none provided, it's reated from <name>
	--focus optionally focuses on the specified parent
	
[d] ### gd create category existing1.existing2.new3.new4
	- split by .
	- check in @categories branch for existing ones
	: for each
		- make commit in @task-storage
		- add notes for custom names and other fields
	- remerge-append the new branches into the @categories
	
[d] ### gd create project -p cat1.cat2.cat3 project

[d] ### gd create step -p cat1.cat2.cat3.project 

	
	
	
# gd edit <USN> [--name <name:str>] [--short-name <name: str>] ..
	by default just prints the values
	if values are provided updates the values
	
# gd browse <USN> [--regexp <regexp:str>]
	shows all projects
	--regexp optionally filters them by a regex

--Notes--
Category:
	hash: <str>
	name: <str>
	display\_name: <str>
	display\_colour: <int> | tuple[int, int, int]
	
Project:	
	hash: <str>
	name: <str>
	display\_name: <str>
	display\_colour: <int> | tuple[int, int, int]
	steps: list[str]
	
Step:
	hash: <str>
	name: <str>
	display\_name: <str>
	display\_colour: <int> | tuple[int, int, int]

--- DAYS ARENA -------
	
# gd today
	shows current days agenda
	~~creates one if none present~~ actually just create one immediately upon install

# gd assign <task:USN>
	adds task to today
	
### gd assign 
	
# gd done (index:int|<task:USN>)[.(index:int|<subtask:USN>)]
	marks a (sub)task as done by merging it with `done` branch
	
# gd undone --||--
	unmarks a (sub)task as done by rebasing `done` branch with a custom script that deletes an entry with the specific 
-------	
	
# gd start (starts a timer), allows to make splits at steps, allows to finish and compare time, allows to pause and cancel timer
	
--Notes--


    /- s1
proj -- s2
 |	\-  s3
 \--	
    \
day--task

how do i design task to be persistent to step transpositions
yet to have marks whether specific steps are done

step hashes are persistent enough

--
I should either
+ allow to add copies of the same task (and show them properly)
- disallow adding copies of the same task to the same day

allowing sounds more permissive, and I can actually think of usecases
that means I need to properly shows doubles [done]

{s1.hash: done, s2.hash: in_progress}
just add/modify marks. never assume the steps hash is already there, bc user can change the project structure mid-day and introduce new steps

