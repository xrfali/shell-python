def parse_args(args):
    is_in_quotes = False
    is_in_double_quotes = False
    output = []
    curr = ""
    is_escaped = False
    o_file_name = ""
    idx = 0
    while idx < len(args):
        char = args[idx]
        if char == '1' and idx+2 < len(args) and args[idx+1] ==">" and args[idx+2] ==">" \
            and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 3
            o_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            if curr: output.append(curr)
            return output, o_file_name, None, 'a'
        
        elif char == '>' and idx+1 < len(args) and args[idx+1] ==">" \
            and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 2
            o_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            if curr: output.append(curr)
            return output, o_file_name, None, 'a'


        if char == '2' and idx+2 < len(args) and args[idx+1] == ">" and args[idx+2] == ">" \
            and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 3
            err_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            return output, None, err_file_name, 'a'

        if char == '2' and idx+1 < len(args) and args[idx +1] == ">" \
            and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 2
            err_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            return output, None, err_file_name, 'w'

        if char == '1' and idx + 1 < len(args) and args[idx + 1] == ">" \
            and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 2
            o_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            if curr: output.append(curr)
            return output, o_file_name, None, 'w'
        
        elif char == ">" and not is_escaped and not is_in_quotes and not is_in_double_quotes:
            idx = idx + 1
            o_file_name = "".join([arg for arg in args[idx:].strip() if arg != '"'])
            if curr: output.append(curr)
            return output, o_file_name, None, 'w'

        if char == '\\' and not is_escaped and not is_in_quotes:
            is_escaped = not is_escaped
            idx+=1 
            continue
        
        if not is_escaped:
            if char == '"' and not is_in_quotes:
                is_in_double_quotes = not is_in_double_quotes
                idx+=1 
                continue

            if char == "'" and not is_in_double_quotes:
                is_in_quotes = not is_in_quotes
                idx+=1 
                continue

            if char == " " and not is_in_quotes and not is_in_double_quotes:
                if curr:
                    output.append(curr)
                    curr = ""
                idx+=1 
                continue
        else:
            is_escaped = not is_escaped

        curr += char
        idx += 1
    
    output.append(curr)

    return output, o_file_name, None, 'w'
