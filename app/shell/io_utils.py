
import os
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
