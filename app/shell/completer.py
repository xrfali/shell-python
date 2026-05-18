import os
import readline
import subprocess
from typing import List

from app.shell_context import ShellContext
BUILT_INS = ['echo', 'exit', 'type', 'pwd', 'complete', 'jobs', 'history', 'declare']

matches = []
lcp = ""

def is_registred_completer(command, ctx: ShellContext):
    completions = ctx.completions
    return completions.get(command) != None

def find_executable_paths(arg, tab_completion = True):
    path_list = os.environ['PATH'].split(os.pathsep)
    all_paths = []

    for path in path_list:
        try:
            all_files = os.listdir(path)
        except:
            continue

        #if exact file names are requires
        if not tab_completion:
            all_files = [os.path.join(path, af) for af in all_files if af == arg and is_executable_v2(os.path.join(path, af))]

        #if paths for tab completion is required
        elif tab_completion:
            all_files = [os.path.join(path, af) for af in all_files if af.startswith(arg) and is_executable_v2(os.path.join(path, af))]

        all_paths.extend(all_files)
    return all_paths

def is_executable_v2(file_path):
    return os.path.isfile(file_path) and os.access(file_path, os.X_OK)


def run_complete_process(args, env):
    try:
        op = subprocess.run(args, capture_output=True, text=True, env=env)
        stripped_op = op.stdout.strip()
        if stripped_op:
            op_list = op.stdout.strip().split('\n')
            op_list = [f"{op} " for op in op_list] 
            return op_list
    except Exception as e:
        print(f"error: {type(e).__name__}: {e}")
        return []

    return []

#Not used anywhere
def find_longest_common_prefix(arr: List[str]):
    if not arr : return ""
    if len(arr) == 1: return arr[0]

    first_word = arr[0]

    for idx, char in enumerate(first_word):
        for item in arr:
            if idx >= len(item) or item[idx] != char:
                return first_word[:idx]
    
    
    return first_word

def get_file_or_dir_matches(text = '', dir_path = '.'):

    res = [fn for fn in os.listdir(dir_path) if fn.startswith(text)]
    
    dirs = [dir for dir in res if os.path.isdir(os.path.join(dir_path, dir))]
    files = [file for file in res if os.path.isfile(os.path.join(dir_path, file))]

    if len(dirs) == 1 and not files:
        return [f"{dirs[0]}{os.sep}"]
    
    if len(files) == 1 and not dirs:
        return [f"{files[0]} "]

    dirs = [f"{dir}{os.sep}" for dir in dirs]
    files = [f"{file} " for file in files]    
    return dirs + files

def get_env_for_completion(input_line):
    byte_len = len(input_line.encode('utf-8'))
    env = os.environ.copy()
    env["COMP_LINE"] = input_line
    env["COMP_POINT"] = f"{byte_len}"

    return env

def auto_complete(text, state, ctx: ShellContext):
    global matches
    global lcp

    if state == 0:
        line = readline.get_line_buffer() 
        ll = line.split()
        if len(ll) == 1:
            if ctx.completions.get(ll[0]):
                cmd = ctx.completions.get(ll[0])
                env = get_env_for_completion(line)
                matches = run_complete_process([cmd], env)
            else:
                if text:
                    matches = [f"{bi} " for bi in BUILT_INS if bi.startswith(text)] or \
                        [f"{os.path.basename(ex)} " for ex in find_executable_paths(text)]
                else:
                    matches = get_file_or_dir_matches()
        elif len(ll) > 1:
            if is_registred_completer(ll[0], ctx):
                env = get_env_for_completion(line)
                args = []
                args.append(ctx.completions.get(ll[0]))
                args.append(ll[0])
                args.append(ll[-1])
                args.append(ll[-2])
                matches = run_complete_process(args, env)
            else:
                p = os.path.dirname(line.split()[-1]) if "/" in line.split()[-1] else '.'
                matches = get_file_or_dir_matches(text, p)

        if not matches: 
            print('\x07', end='')
            return None

    try:
        return matches[state]
    except IndexError:
        matches = []
        return None
 