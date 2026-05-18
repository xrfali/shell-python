import os
import subprocess
import readline
import sys
import re
from app.shell.parser import parse_args
from app.shell.jobs import process_jobs_command, reap_bg_jobs, next_job_number, is_bg_job, Job
from app.shell.completer import is_registred_completer, find_executable_paths, auto_complete, BUILT_INS
from app.shell.io_utils import write_output_to_file, redirect_write, clear_redirect
from app.shell.history import read_history_from_file, write_history_to_file
from app.shell_context import ShellContext

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
