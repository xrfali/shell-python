from app.shell.vars import process_arg_for_vars
from app.shell_context import ShellContext
import pytest

@pytest.fixture
def ctx():
    return ShellContext()

def test_process_arg_for_vars(ctx):
    ctx.shell_vars = {"VAR": "hello"}
    argl = process_arg_for_vars(["echo", "$VAR"], ctx)
    assert argl == ["echo", "hello"]

def test_process_arg_for_vars_curly_braces(ctx):
    ctx.shell_vars = {"VAR": "hello"}
    argl = process_arg_for_vars(["echo", "${VAR}"], ctx)
    assert argl == ["echo", "hello"]

def test_process_arg_for_vars_undefined(ctx):
    argl = process_arg_for_vars(["echo", "$UNDEFINED"], ctx)
    assert argl == ["echo"]

def test_process_arg_for_vars_no_var(ctx):
    argl = process_arg_for_vars(["echo", "VAR"], ctx)
    assert argl == ["echo", "VAR"]
