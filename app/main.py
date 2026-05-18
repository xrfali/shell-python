import os
import subprocess
import readline
import sys
from typing import List
import re
from app.shell.parser import parse_args
from app.shell.jobs import process_jobs_command, reap_bg_jobs, next_job_number, is_bg_job, Job

from app.shell_context import ShellContext


BUILT_INS = ['echo', 'exit', 'type', 'pwd', 'complete', 'jobs', 'history', 'declare']

matches = []
lcp = ""

def is_registred_completer(command, ctx: ShellContext):
    completions = ctx.completions
    return completions.get(command) != None

def process_complete_command(args, argl, ctx: ShellContext):
    completions = ctx.completions

    if(len(argl) == 2 and argl[0] == '-p'):
        if not completions:
            print(f"complete: {argl[-1]}: no completion specification")
        else: 
            if is_registred_completer(argl[1], ctx):
                completion = completions.get(argl[1])
                print(f"complete -C '{completion}' {argl[1]}")
            else:
                print(f"complete: {argl[-1]}: no completion specification")
    
    if(len(argl) == 2 and argl[0] == "-r"):
        completions.pop(argl[1], None)

    if(len(argl) == 3 and argl[0] == "-C"):
        if not completions.get(argl[2]):
            completions[argl[2]] = argl[1] # e.g. (git, <PATH>)

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

def process_executable_request(command):
    file_paths = find_executable_paths(command, tab_completion=False)
    try:
        return file_paths[0]
    except:
        None

def process_type_command(args):
    args = args.split()
    for arg in args:
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

def write_output_to_file(file_name, output, file_mode = 'w'):
    with open(file_name, file_mode) as file:
        output += '\n' if output else ''
        file.write(output)

def redirect_write(w):
    saved_stdout = os.dup(1)
    os.dup2(w, 1)
    return saved_stdout

def clear_redirect(saved_stdout):
    if saved_stdout is not None:
        os.dup2(saved_stdout, 1)
        os.close(saved_stdout)

def read_history_from_file(path, ctx: ShellContext):
    commands_history = ctx.history
    try:
        with open(path, 'r') as f:
            h = f.read().splitlines()
            commands_history += h
    except FileNotFoundError:
        pass

def write_history_to_file(path, ctx: ShellContext, op = 'w'):
    commands_history = ctx.history
    last_history_idx = ctx.last_history_idx

    cmd_h = commands_history if last_history_idx == None else commands_history[last_history_idx:]
    ctx.last_history_idx = len(commands_history)
    try:
        with open(path, op) as f:
            f.writelines(cmd + '\n' for cmd in cmd_h)
    except FileNotFoundError:
        pass

def process_vars_with_braces(arg, ctx):
    def check_patter(match):
        return ctx.shell_vars.get(match.group(1), '')
        
    reg = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    return re.sub(reg, check_patter, arg)

def process_arg_for_vars(argl, ctx: ShellContext):
    new_argl = []
    for arg in argl:
        if "$" in arg and '{' in arg and '}' in arg:
            op = process_vars_with_braces(arg, ctx)
            new_argl.append(op)
            continue
        
        if "$" in arg:
            idx = arg.index('$')
            v = ctx.shell_vars.get(arg[idx+1:], '')
            op = arg[:idx] + v
            new_argl.append(op)
            continue

        new_argl.append(arg)
    
    new_argl = [arg for arg in new_argl if arg != '']
    return new_argl

def main():
    ctx = ShellContext()
    
    readline.set_completer(lambda text, state: auto_complete(text, state, ctx))
    if readline.__doc__ and 'libedit' in readline.__doc__:
        readline.parse_and_bind('bind ^I rl_complete')
    else:
        readline.parse_and_bind('tab: complete')

    hp = os.environ.get('HISTFILE')
    if hp:
        read_history_from_file(hp, ctx)
        ctx.last_history_idx = len(ctx.history)

    while True:
        reap_bg_jobs(ctx)
        user_input = input("$ ")
        
        parsed_input, op_file_name, err_file_name, file_mode = parse_args(user_input.strip())

        if err_file_name:
            write_output_to_file(err_file_name, "", file_mode)
        
        parsed_input, is_bg = is_bg_job(parsed_input)

        temp_input = parsed_input
        commands = []
        
        ctx.history.append(user_input.strip())

        while(True):
            if '|' in temp_input:
                pipeIdx = temp_input.index('|')
                commands.append(temp_input[:pipeIdx])
                if len(temp_input) > pipeIdx+1: 
                    temp_input = temp_input[pipeIdx+1:] 
                else:
                    break
            else:
                if len(temp_input) > 0:
                    commands.append(temp_input)
                break

        if not commands:
            commands = [parsed_input]

        prev_r = None
        processes = []
        for idx, cmd in enumerate(commands):
            command = cmd[0]
            argl = cmd[1:]

            new_argl = []
            
            argl = process_arg_for_vars(argl, ctx)

            args = " ".join(argl)

            r, w = None, None
            if len(commands) > 1 and idx < len(commands) - 1:
                r, w = os.pipe()
                                
            match command:
                case 'exit':
                    if hp:
                        write_history_to_file(hp, ctx, 'a')

                    sys.exit(0)
                case 'complete':
                    process_complete_command(args, argl, ctx)

                case 'declare':
                    if len(argl) == 2:
                        if argl[0] == '-p':
                            if ctx.shell_vars.get(argl[1]):
                                v = ctx.shell_vars.get(argl[1])
                                print(f"declare -- {argl[1]}=\"{v}\"")
                            else:
                                print(f"declare: {argl[1]}: not found")
                    elif len(argl) == 1 and '=' in argl[0]:
                            v = argl[0].split('=')
                            pattern = r'^[_a-zA-Z][a-zA-Z0-9_]*$'
                            if re.match(pattern, v[0]):
                                ctx.shell_vars[v[0]] = v[1]
                            else:
                                print(f"declare: `{argl[0]}': not a valid identifier")
                                
                case 'history':
                    if len(ctx.history) > 0:
                        idx = 0
                        if len(argl) > 0:
                            if argl[0].isdigit():
                                n = int(argl[0])
                                idx = len(ctx.history) - n  if len(ctx.history) >= n else 0
                            
                            if len(argl) == 2:
                                if argl[0] == '-r':
                                    read_history_from_file(argl[1], ctx)
                                    break
                                elif argl[0] == '-w' or argl[0] == '-a':
                                    write_history_to_file(argl[1], ctx, 'w' if argl[0] == '-w' else 'a')
                                    break

                        while idx < len(ctx.history):
                            print(f"{idx+1:>4}  {ctx.history[idx]}")
                            idx += 1

                case 'type':
                    if (output := process_type_command(args)) is not None:
                        saved_stdout = None
                        if w:
                            saved_stdout = redirect_write(w)
                        
                        file_name = op_file_name or err_file_name
                        write_output_to_file(file_name, output, file_mode) if file_name else print(output)

                        clear_redirect(saved_stdout)
                    
                        if w is not None:
                            os.close(w)
                            prev_r = r
                case 'echo':
                    saved_stdout = None
                    if w:
                        saved_stdout = redirect_write(w)

                    write_output_to_file(op_file_name, args, file_mode) if op_file_name else print(args)

                    clear_redirect(saved_stdout)
                    
                    if w is not None:
                        os.close(w)
                        prev_r = r
                case 'pwd':
                    output = os.getcwd()
                    file_name = op_file_name or err_file_name
                    write_output_to_file(file_name, output, file_mode) if file_name else print(output)
                case 'cd':
                    process_cd_command(args)  
                case 'jobs':
                    process_jobs_command(args, argl, ctx)
                case _:
                    command_path = process_executable_request(command)
                    if not command_path:
                        print(f"{user_input}: command not found")
                    else:  
                        if len(commands) > 1:
                            #piping

                            if prev_r:
                                if idx < len(commands) - 1:
                                    p = subprocess.Popen([command] + argl, stdout=w, stdin=prev_r)
                                    processes.append(p)
                                else:
                                    p = subprocess.Popen([command] + argl, stdin=prev_r)
                                    processes.append(p)
                                os.close(prev_r)
                            else:
                                p = subprocess.Popen([command] + argl, stdout=w)
                                processes.append(p)
                            
                            if idx < len(commands) - 1:
                                prev_r = r
                                os.close(w)
                        else: 
                            if is_bg:
                                process = subprocess.Popen([command] + argl)
                                job_no = next_job_number(ctx)
                                job = Job(job_no, process.pid, user_input, "Running", process)
                                ctx.jobs.append(job)
                                print(f"{[job_no]} {process.pid}")
                            else:
                                p = subprocess.run([command] + argl, capture_output=True, text=True)
                                
                                stripped_err = p.stderr.strip()
                                stripped_op = p.stdout.strip()
                                if stripped_err:
                                    if err_file_name:
                                        write_output_to_file(err_file_name, stripped_err, file_mode)
                                    
                                    elif op_file_name:
                                        write_output_to_file(op_file_name, '', file_mode)
                                        print(stripped_err)
                                    else:
                                        print(stripped_err)
                                    
                                if stripped_op:
                                    if op_file_name:
                                        write_output_to_file(op_file_name, stripped_op, file_mode)
                                    else:
                                        print(stripped_op)

        for p in processes:
            p.wait()      
       
    pass

if __name__ == "__main__":
    main()
