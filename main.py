import api
import cmd
from cmd import Result

import colorama
import os
import sys
import subprocess
from typing import Optional, Callable
import expression as e
            

def maybe_lock_in() -> None | NoReturn:
    if sys.argv[1:3] == ['lock', 'in']:
        os.chdir('/home/cowberry/Projects/Gitodo')
        subprocess.Popen(['emacs'])
        print("Locked In Successfully")
        exit(0)
    
def main() -> None:
    maybe_lock_in()
    
    parser = api.setup_parser()
    args = parser.parse_args(sys.argv[1:])

    cmd_cls: api.Command = ([cls for cls in api.Command.__subclasses__() if args.command in cls.command] + [None])[0]
        
    if args.debug:
        print(f"{sys.argv[1:] = }")
        cmd.RUN_CMD_DEBUG = True
        print(f"{args = }")    
        print(f"{cmd_cls = }")
    
    if not cmd_cls:
        print("No command was provided")
        exit(1)
    
    run = cmd_cls.run(args)
    if run.is_error():
        print(f"# Error occured:\n{run.error}")

    
if __name__ == "__main__":
    main()
    os.chdir(cmd.GITODO_DIRECTORY)
    
