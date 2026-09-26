import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update RATING_PROFILE_MIX
code = re.sub(
    r"RATING_PROFILE_MIX = \{'perfect': 50, 'fine': 50\}\s*#.*",
    "RATING_PROFILE_MIX = {5: 60, 4: 30, 3: 10}  # 60% 5-stars, 30% 4-stars, 10% 3-stars (baseline)",
    code
)

# 2. Update stars assignment in main (remove the buggy RATING_PROFILE_MIX lookup, profile is already the key)
code = re.sub(
    r"stars = RATING_PROFILE_MIX\[profile\]",
    "stars = profile",
    code
)

# 3. Add dynamic wobble in answer_page
new_rating_logic = '''
        if kind == 'rating':
            # Dynamic rating: mostly the baseline, but occasionally varies by 1 star
            import random
            wobble = random.choice([0, 0, 0, 0, -1, 1])
            dynamic_stars = max(1, min(5, stars + wobble))
            count = set_rating(question, dynamic_stars, driver)
            answered += count
            log.append(f\'      [rating] "{clean(title)}" -> {dynamic_stars} '
                       f'({count} set)\')
'''

code = re.sub(
    r"if kind == 'rating':\s*count = set_rating\(question, stars, driver\)\s*answered \+= count\s*log\.append\(f'      \[rating\] \"\{clean\(title\)\}\" -> \{stars\} '\s*f'\(\{count\} set\)'\)",
    new_rating_logic.strip('\n'),
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied for dynamic ratings.")
