import json
import re

with open('raw_participants.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

participants = []
for i in range(0, len(lines), 3):
    if i+2 < len(lines):
        name = lines[i+1]
        email_raw = lines[i+2]
        # handle markdown links [email](mailto:email) if present
        email_match = re.search(r'\[.*?\]\(mailto:(.*?)\)', email_raw)
        if email_match:
            email = email_match.group(1)
        else:
            email = email_raw
        participants.append({'name': name, 'email': email})

with open('participants.json', 'w', encoding='utf-8') as f:
    json.dump(participants, f, indent=2)

print(f'Parsed {len(participants)} participants.')
