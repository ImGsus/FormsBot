import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add import json at the top if it's not there, but remove it from the local scope first
code = code.replace('                        import json\n', '')

if 'import json' not in code:
    code = re.sub(r'import sys', 'import sys\nimport json', code)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)
