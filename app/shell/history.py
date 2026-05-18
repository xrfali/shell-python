
from app.shell_context import ShellContext


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
