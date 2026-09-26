import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Update the loop to use unused_participants and save state on OK
new_loop_logic = '''
    try:
        with open('participants.json', 'r', encoding='utf-8') as f:
            all_participants = json.load(f)
    except:
        all_participants = []

    unused_participants = [p for p in all_participants if not p.get('used')]

    try:
        for index, profile in enumerate(plan, start=1):
            if not unused_participants:
                print("No more unused participants available! Stopping early to avoid duplicates.")
                break
                
            participant = unused_participants[(index - 1) % len(unused_participants)]
            stars = profile
            for attempt in range(1, MAX_RETRIES + 1):
                ok, reason, driver = submit_once(FORM_LINK, stars, participant, driver)
                if driver is None:
                    print('  browser died, restarting it')
                    driver = make_driver()
                    continue
                if ok:
                    submitted += 1
                    participant['used'] = True
                    # Remove from unused list for subsequent iterations
                    unused_participants.remove(participant)
                    # Save back to file
                    with open('participants.json', 'w', encoding='utf-8') as f:
                        import json
                        json.dump(all_participants, f, indent=2)
                        
                    print(f'[{index}/{TOTAL_RESPONDENTS}] OK  '
                          f'profile={profile} ({stars} stars) -> Marked {participant.get("email")} as used')
                    break
                print(f'[{index}/{TOTAL_RESPONDENTS}] attempt '
                      f'{attempt}/{MAX_RETRIES} failed: {reason}')
                time.sleep(2)
'''

code = re.sub(
    r"    try:\s*with open\('participants.json', 'r', encoding='utf-8'\) as f:\s*all_participants = json.load\(f\)\s*except:\s*all_participants = \[\]\s*try:\s*for index, profile in enumerate\(plan, start=1\):\s*participant = all_participants\[\(index - 1\) % len\(all_participants\)\] if all_participants else None\s*stars = profile\s*for attempt in range\(1, MAX_RETRIES \+ 1\):\s*ok, reason, driver = submit_once\(FORM_LINK, stars, participant, driver\)\s*if driver is None:\s*print\('  browser died, restarting it'\)\s*driver = make_driver\(\)\s*continue\s*if ok:\s*submitted \+= 1\s*print\(f'\[\{index\}/\{TOTAL_RESPONDENTS\}\] OK  '\s*f'profile=\{profile\} \(\{stars\} stars\)'\)\s*break\s*print\(f'\[\{index\}/\{TOTAL_RESPONDENTS\}\] attempt '\s*f'\{attempt\}/\{MAX_RETRIES\} failed: \{reason\}'\)\s*time.sleep\(2\)",
    new_loop_logic.strip('\n'),
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied")
