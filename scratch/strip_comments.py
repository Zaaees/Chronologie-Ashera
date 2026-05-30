import os
import re

def strip_js_ts_css_comments(content):
    out = []
    i = 0
    n = len(content)
    
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    escape = False
    
    while i < n:
        char = content[i]
        
        if escape:
            out.append(char)
            escape = False
            i += 1
            continue
            
        if char == '\\' and (in_single_quote or in_double_quote or in_backtick):
            out.append(char)
            escape = True
            i += 1
            continue
            
        if char == "'" and not in_double_quote and not in_backtick:
            in_single_quote = not in_single_quote
            out.append(char)
            i += 1
            continue
        elif char == '"' and not in_single_quote and not in_backtick:
            in_double_quote = not in_double_quote
            out.append(char)
            i += 1
            continue
        elif char == '`' and not in_single_quote and not in_double_quote:
            in_backtick = not in_backtick
            out.append(char)
            i += 1
            continue
            
        if not in_single_quote and not in_double_quote and not in_backtick:
            # JSX Comments: {/* ... */}
            if i + 3 < n and content[i:i+3] == '{/*':
                j = i + 3
                while j + 3 <= n and content[j:j+3] != '*/}':
                    j += 1
                j += 3
                
                # Clean preceding whitespace on this line
                back = len(out) - 1
                is_full_line_comment = True
                while back >= 0 and out[back] != '\n':
                    if out[back] not in (' ', '\t', '\r'):
                        is_full_line_comment = False
                        break
                    back -= 1
                    
                if is_full_line_comment:
                    while len(out) > 0 and out[-1] != '\n':
                        out.pop()
                    if j < n and content[j] == '\n':
                        j += 1
                else:
                    while len(out) > 0 and out[-1] in (' ', '\t'):
                        out.pop()
                        
                i = j
                continue
                
            # CSS/JS Multi-line Comments: /* ... */
            elif i + 2 < n and content[i:i+2] == '/*':
                j = i + 2
                while j + 2 <= n and content[j:j+2] != '*/':
                    j += 1
                j += 2
                
                back = len(out) - 1
                is_full_line_comment = True
                while back >= 0 and out[back] != '\n':
                    if out[back] not in (' ', '\t', '\r'):
                        is_full_line_comment = False
                        break
                    back -= 1
                    
                if is_full_line_comment:
                    while len(out) > 0 and out[-1] != '\n':
                        out.pop()
                    if j < n and content[j] == '\n':
                        j += 1
                else:
                    while len(out) > 0 and out[-1] in (' ', '\t'):
                        out.pop()
                        
                i = j
                continue
                
            # JS/TS Single-line Comments: // ...
            elif i + 2 < n and content[i:i+2] == '//':
                j = i + 2
                while j < n and content[j] != '\n':
                    j += 1
                
                back = len(out) - 1
                is_full_line_comment = True
                while back >= 0 and out[back] != '\n':
                    if out[back] not in (' ', '\t', '\r'):
                        is_full_line_comment = False
                        break
                    back -= 1
                    
                if is_full_line_comment:
                    while len(out) > 0 and out[-1] != '\n':
                        out.pop()
                    if j < n and content[j] == '\n':
                        j += 1
                else:
                    while len(out) > 0 and out[-1] in (' ', '\t'):
                        out.pop()
                        
                i = j
                continue
                
        out.append(char)
        i += 1
        
    return "".join(out)

def strip_trailing_python_comment(line):
    in_single_quote = False
    in_double_quote = False
    escape = False
    
    for i, char in enumerate(line):
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == '#' and not in_single_quote and not in_double_quote:
            return line[:i].rstrip()
    return line

def remove_python_docstrings_and_comments(content):
    lines = content.split('\n')
    cleaned_lines = []
    in_docstring_double = False
    in_docstring_single = False
    
    for line in lines:
        if in_docstring_double:
            if '"""' in line:
                parts = line.split('"""', 1)
                remainder = parts[1]
                in_docstring_double = False
                remainder_cleaned = strip_trailing_python_comment(remainder)
                if remainder_cleaned.strip():
                    cleaned_lines.append(remainder_cleaned)
            continue
            
        if in_docstring_single:
            if "'''" in line:
                parts = line.split("'''", 1)
                remainder = parts[1]
                in_docstring_single = False
                remainder_cleaned = strip_trailing_python_comment(remainder)
                if remainder_cleaned.strip():
                    cleaned_lines.append(remainder_cleaned)
            continue
            
        stripped = line.strip()
        
        if stripped.startswith('"""') and stripped.endswith('"""') and len(stripped) >= 6:
            continue
        if stripped.startswith("'''") and stripped.endswith("'''") and len(stripped) >= 6:
            continue
            
        if '"""' in line:
            parts = line.split('"""', 1)
            lead = parts[0]
            in_docstring_double = True
            lead_cleaned = strip_trailing_python_comment(lead)
            if lead_cleaned.strip():
                cleaned_lines.append(lead_cleaned)
            continue
            
        if "'''" in line:
            parts = line.split("'''", 1)
            lead = parts[0]
            in_docstring_single = True
            lead_cleaned = strip_trailing_python_comment(lead)
            if lead_cleaned.strip():
                cleaned_lines.append(lead_cleaned)
            continue
            
        cleaned = strip_trailing_python_comment(line)
        if line.strip() == '':
            cleaned_lines.append('')
        elif cleaned.strip() != '':
            cleaned_lines.append(cleaned)
            
    return '\n'.join(cleaned_lines)

def clean_file(file_path, strip_func):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found)")
        return
        
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    cleaned = strip_func(content)
    
    # Remove extra blank lines (more than 2 consecutive blank lines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
        
    print(f"Cleaned comments from {file_path}!")

def main():
    clean_file("src/App.tsx", strip_js_ts_css_comments)
    clean_file("src/index.css", strip_js_ts_css_comments)
    clean_file("src/data.ts", strip_js_ts_css_comments)
    clean_file("parser_html.py", remove_python_docstrings_and_comments)
    clean_file("parser.py", remove_python_docstrings_and_comments)

if __name__ == "__main__":
    main()
