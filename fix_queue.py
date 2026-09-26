import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_queue_logic = '''
            if not unused_participants:
                print("No more unused participants available! Stopping early to avoid duplicates.")
                break
                
            participant = unused_participants.pop(0)
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
                    # Save back to file
                    with open('participants.json', 'w', encoding='utf-8') as f:
                        json.dump(all_participants, f, indent=2)
'''

code = re.sub(
    r"            if not unused_participants:\s*print\(\"No more unused participants available! Stopping early to avoid duplicates.\"\)\s*break\s*participant = unused_participants\[\(index - 1\) % len\(unused_participants\)\]\s*stars = profile\s*for attempt in range\(1, MAX_RETRIES \+ 1\):\s*ok, reason, driver = submit_once\(FORM_LINK, stars, participant, driver\)\s*if driver is None:\s*print\('  browser died, restarting it'\)\s*driver = make_driver\(\)\s*continue\s*if ok:\s*submitted \+= 1\s*participant\['used'\] = True\s*# Remove from unused list for subsequent iterations\s*unused_participants.remove\(participant\)\s*# Save back to file\s*with open\('participants.json', 'w', encoding='utf-8'\) as f:\s*json.dump\(all_participants, f, indent=2\)",
    new_queue_logic.strip('\n'),
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)
