import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix all the broken indentation blocks
code = re.sub(
    r"                if kind == 'rating':\s*# Dynamic rating: mostly the baseline, but occasionally varies by 1 star\s*import random\s*wobble = random.choice\(\[0, 0, 0, 0, -1, 1\]\)\s*dynamic_stars = max\(1, min\(5, stars \+ wobble\)\)\s*count = set_rating\(question, dynamic_stars, driver\)\s*answered \+= count\s*log.append\(f'      \[rating\] \"\{clean\(title\)\}\" -> \{dynamic_stars\} '\s*f'\(\{count\} set\)'\)\s*elif kind == 'name':",
    '''        if kind == 'rating':
            # Dynamic rating: mostly the baseline, but occasionally varies by 1 star
            import random
            wobble = random.choice([0, 0, 0, 0, -1, 1])
            dynamic_stars = max(1, min(5, stars + wobble))
            count = set_rating(question, dynamic_stars, driver)
            answered += count
            log.append(f\'      [rating] "{clean(title)}" -> {dynamic_stars} '
                       f'({count} set)\')
        elif kind == 'name':''',
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Formatting fixed again")
