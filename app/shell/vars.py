
import re
from app.shell_context import ShellContext

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
