import api
import run

import colorama
import os
import sys
import subprocess
from typing import Optional, Callable
            

def maybe_lock_in() -> None:
    if sys.argv[1:3] == ['lock', 'in']:
        os.chdir('/home/cowberry/Projects/Gitodo')
        subprocess.Popen(['emacs'])
        print("Locked In Successfully")
        exit(0)
    
def main() -> None:
    maybe_lock_in()
    parser = api.setup_parser()
    
    if len(sys.argv) == 1:
        api.TodayCommand.run(None)

    args = parser.parse_args(sys.argv[1:])

    cmd_cls: type[api.Command] | None = ([cls for cls in api.Command.__subclasses__() if args.command in cls.command] + [None])[0]
    
    if 'debug' in args and args.debug:
        print(f"{sys.argv[1:] = }")
        # run.RUN_CMD_DEBUG = True
        print(f"{args = }")    
        print(f"{cmd_cls = }")
    
    if not cmd_cls:
        print("No command was provided (how did you get here)")
        exit(1)
    
    cmd_cls.run(args)
    print(f'\nTOTAL NUMBER OF CALLS: {colorama.Fore.LIGHTRED_EX}{run.number_of_calls}{colorama.Style.RESET_ALL}')
    
if __name__ == "__main__":
    main()
    os.chdir(run.GITODO_DIRECTORY)
    
