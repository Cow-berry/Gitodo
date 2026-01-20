General:
	- store changeable in notes
	- store debug in commit msg

Concrete steps:
	- update cmd to return ok flags
	- implement create
	- implement browse
	- implement (un)focus
	- implement browse


<USN> = unambiguous short name

--- PROJECT ARENA ------

# gd create (category|project|step) <name:str> [--short-name <short: str>] [--parent <p:USN>] [--focus]
	creates a task object with <p> parent
    --short-name creates a short name used for indexing
		*in case if none provided, it's reated from <name>
	--focus optionally focuses on the specified parent
	
# gd (un)focus <p:USN>
	makes the `gd create` parent <p> by default 
	
# gd edit <USN> [--name <name:str>] [--short-name <name: str>] ..
	by default just prints the values
	if values are provided updates the values
	
# gd browse <USN> [--regexp <regexp:str>]
	shows all projects
	--regexp optionally filters them by a regex

--- DAYS ARENA -------
	
# gd today
	shows current days agenda
	creates one if none present

# gd assign <task:USN>
	adds task to today
	
# gd done (index:int|<task:USN>)[.(index:int|<subtask:USN>)]
	marks a (sub)task as done by merging it with `done` branch
	
# gd undone --||--
	unmarks a (sub)task as done by rebasing `done` branch with a custom script that deletes an entry with the specific 
