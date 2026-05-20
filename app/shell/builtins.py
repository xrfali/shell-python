
from app.shell.completer import BUILT_INS, find_executable_paths, is_registered_completer
from app.shell_context import ShellContext
import os

def process_complete_command(argl, ctx: ShellContext):
    completions = ctx.completions

    if(len(argl) == 2 and argl[0] == '-p'):
        if not completions:
            print(f"complete: {argl[-1]}: no completion specification")
        else: 
            if is_registered_completer(argl[1], ctx):
                completion = completions.get(argl[1])
                print(f"complete -C '{completion}' {argl[1]}")
            else:
                print(f"complete: {argl[-1]}: no completion specification")
    
    if(len(argl) == 2 and argl[0] == "-r"):
        completions.pop(argl[1], None)

    if(len(argl) == 3 and argl[0] == "-C"):
        if not completions.get(argl[2]):
            completions[argl[2]] = argl[1] # e.g. (git, <PATH>)
 

def process_executable_request(command):
    file_paths = find_executable_paths(command, tab_completion=False)
    try:
        return file_paths[0]
    except IndexError:
        return None

def process_type_command(argl):
    for arg in argl:
        if arg in BUILT_INS:
            return f"{arg} is a shell builtin"
        else:
            file_path = process_executable_request(arg)
            if file_path:
                return f"{arg} is {file_path}"
            else:
                print(f"{arg}: not found")
                return None

def process_cd_command(arg):
    try:
        if arg == "~":
            os.chdir(os.environ['HOME'])
        else:
            os.chdir(arg)
    except FileNotFoundError:
        print(f"cd: {arg}: No such file or directory")
