import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"        try:\s*with open\('participants.json', 'r', encoding='utf-8'\) as f:\s*all_participants = json.load\(f\)\s*except:\s*all_participants = \[\]",
    '''    try:
        with open('participants.json', 'r', encoding='utf-8') as f:
            all_participants = json.load(f)
    except:
        all_participants = []''',
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Formatting fixed for try block")
