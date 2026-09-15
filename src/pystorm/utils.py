import re


# this function was (mostly) written by Gemini
def processMolang(expression: str):
# 1. Remove C-style single-line (//) and multi-line (/* */) comments.
    # We use a regex that matches strings first (to avoid removing comment characters inside strings)
    # Group 1: Strings | Group 2: Comments
    def remove_comments(match):
        if match.group(1): 
            return match.group(1) # Keep string as is
        return ""                 # Remove comment

    # remove comments only if there are multiple lines (in case this string isn't molang)
    if "\n" in expression or "\r" in expression:
        # Matches "...", '...', /*...*/, and //...
        pattern = r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')|(/\*.*?\*/|//[^\r\n]*)'
        expression = re.sub(pattern, remove_comments, expression, flags=re.DOTALL)

        # 2. Remove all newlines and carriage returns
        expression = expression.replace('\n', '').replace('\r', '')

    # 3. Replace double quotes with single quotes, and tabs with spaces
    expression = expression.replace('"', "'").replace('\t', ' ')

    # 4. Remove double spaces not contained in quotes
    parts = re.split(r"('[^'\\]*(?:\\.[^'\\]*)*')", expression)
    
    for i in range(len(parts)):
        if i % 2 == 0:  # Even index = outside of quotes
            while '  ' in parts[i]:
                parts[i] = parts[i].replace('  ', ' ')
                
    return "".join(parts).strip()