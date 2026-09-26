import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"    unused_participants = \[p for p in all_participants if not p.get\('used'\)\]",
    '''    unused_participants = [p for p in all_participants if not p.get('used')]
    import random
    random.shuffle(unused_participants)''',
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)
