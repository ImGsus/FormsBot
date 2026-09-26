import sys
import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Import json
if 'import json' not in code:
    code = re.sub(r'import re', 'import re\nimport json', code)

# 2. Update classify
new_classify = '''
        if textareas or inputs:
            if 'gmail' in low or 'email' in low:
                return 'email', title
            if 'name' in low or 'participant' in low:
'''
code = re.sub(
    r"if textareas or inputs:\s*if 'name' in low or 'participant' in low:",
    new_classify.strip('\n'),
    code
)

# 3. Update answer_page definition
code = re.sub(
    r'def answer_page\(driver, stars, dry_run=False\):',
    'def answer_page(driver, stars, participant, dry_run=False):',
    code
)

# 4. Update answer_page name branch
new_name_branch = '''
        elif kind == 'name':
            value = participant['name'] if participant else random_name()
            if type_into(question, value, driver):
                answered += 1
            log.append(f\'      [name]   "{clean(title)}" -> "{value}"\')
        elif kind == 'email':
            value = participant['email'] if participant else "default@gmail.com"
            if type_into(question, value, driver):
                answered += 1
            log.append(f\'      [email]  "{clean(title)}" -> "{value}"\')
'''
code = re.sub(
    r"elif kind == 'name':\s*value = random_name\(\)\s*if type_into\(question, value, driver\):\s*answered \+= 1\s*log\.append\(f'      \[name\]   \"\{clean\(title\)\}\" -> \"\{value\}\"'\)",
    new_name_branch.strip('\n'),
    code
)

# 5. Update walk_form definition and call
code = re.sub(
    r'def walk_form\(driver, stars, dry_run=False\):',
    'def walk_form(driver, stars, participant, dry_run=False):',
    code
)
code = re.sub(
    r'answered, log = answer_page\(driver, stars, dry_run=dry_run\)',
    'answered, log = answer_page(driver, stars, participant, dry_run=dry_run)',
    code
)

# 6. Update submit_once definition and call
code = re.sub(
    r'def submit_once\(link, stars, driver, dry_run=False\):',
    'def submit_once(link, stars, participant, driver, dry_run=False):',
    code
)
code = re.sub(
    r'ok, reason, _pages = walk_form\(driver, stars, dry_run\)',
    'ok, reason, _pages = walk_form(driver, stars, participant, dry_run)',
    code
)

# 7. Update main loop
new_main_loop = '''
    try:
        with open('participants.json', 'r', encoding='utf-8') as f:
            all_participants = json.load(f)
    except:
        all_participants = []

    try:
        for index, profile in enumerate(plan, start=1):
            participant = all_participants[(index - 1) % len(all_participants)] if all_participants else None
            stars = RATING_PROFILE_MIX[profile]
            for attempt in range(1, MAX_RETRIES + 1):
                ok, reason, driver = submit_once(FORM_LINK, stars, participant, driver)
'''

code = re.sub(
    r"try:\s*for index, profile in enumerate\(plan, start=1\):\s*stars = RATING_PROFILE_MIX\[profile\]\s*for attempt in range\(1, MAX_RETRIES \+ 1\):\s*ok, reason, driver = submit_once\(FORM_LINK, stars, driver\)",
    new_main_loop.strip('\n'),
    code
)

# 8. Update inspect definition and call (for dry run compatibility)
code = re.sub(
    r'ok, reason, _pages = walk_form\(driver, 5, dry_run=True\)',
    'ok, reason, _pages = walk_form(driver, 5, None, dry_run=True)',
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied")
