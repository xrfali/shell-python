from app.shell.parser import parse_args

def test_simple_command():
    tokens, outfile, err_file, mode = parse_args("echo hello")
    assert tokens == ["echo", "hello"]
    assert outfile == ""
    assert err_file is None
    assert mode == 'w'

def test_single_quote_echo_command():
    tokens, outfile, err_file, mode = parse_args("echo 'hello world'")
    assert tokens == ["echo", "hello world"]
    assert outfile == ""
    assert err_file is None
    assert mode == 'w'

def test_echo_redirect_command():
    tokens, outfile, err_file, mode = parse_args("echo hi > out.txt")
    assert tokens == ["echo", "hi"]
    assert outfile == "out.txt"
    assert err_file is None
    assert mode == 'w'

def test_echo_append_redirect_command():
    tokens, outfile, err_file, mode = parse_args("echo hi >> out.txt")
    assert tokens == ["echo", "hi"]
    assert outfile == "out.txt"
    assert err_file is None
    assert mode == 'a'

def test_echo_error_redirect_command():
    tokens, outfile, err_file, mode = parse_args("ls 2> err.txt")
    assert tokens == ["ls"]
    assert outfile is None
    assert err_file == "err.txt"
    assert mode == 'w'