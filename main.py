import api
import cmd



import colorama
import os
import sys
import subprocess
from typing import Optional, Callable


GITODO_DIRECTORY = '/home/cowberry/Projects/Gitodo/test/'
            

def maybe_lock_in() -> None | NoReturn:
    if sys.argv[1:3] == ['lock', 'in']:
        os.chdir('/home/cowberry/Projects/Gitodo')
        subprocess.Popen(['emacs'])
        print("Locked In Successfully")
        exit(0)
    
@cmd.run_except
def main() -> None:
    maybe_lock_in()
   
    os.chdir(GITODO_DIRECTORY)
    
    parser = api.setup_parser()
    args = parser.parse_args(sys.argv[1:])
    cmd_cls: api.Command = [cls for cls in api.Command.__subclasses__() if args.command in cls.command][0]
    cmd_cls.run(args)

    # print(f"{args = }")
    # print(f"{cmd_cls = }")
    
if __name__ == "__main__":
    main()
