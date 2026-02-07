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
    print(f"{sys.argv[1:] = }")
    parser = api.setup_parser()
    args = parser.parse_args(sys.argv[1:])

    cmd_cls: type[api.Command] | None = ([cls for cls in api.Command.__subclasses__() if args.command in cls.command] + [None])[0]
    
    if 'debug' in args and args.debug:
        print(f"{sys.argv[1:] = }")
        # run.RUN_CMD_DEBUG = True
        print(f"{args = }")    
        print(f"{cmd_cls = }")
    
    if not cmd_cls:
        print("No command was provided")
        exit(1)
    
    cmd_cls.run(args)
    
if __name__ == "__main__":
    main()
    os.chdir(run.GITODO_DIRECTORY)
    
