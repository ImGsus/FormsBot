import re

with open('main_fixed.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix classify indentation
code = re.sub(
    r"    textareas = question.find_elements\(By.CSS_SELECTOR, 'textarea'\)\s*inputs = question.find_elements\(By.CSS_SELECTOR, 'input\[type=\"text\"\]'\)\s*if textareas or inputs:\s*if 'gmail' in low or 'email' in low:\s*return 'email', title\s*if 'name' in low or 'participant' in low:\s*return 'name', title",
    '''    textareas = question.find_elements(By.CSS_SELECTOR, 'textarea')
    inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
    if textareas or inputs:
        if 'gmail' in low or 'email' in low:
            return 'email', title
        if 'name' in low or 'participant' in low:
            return 'name', title''',
    code
)

# Fix answer_page indentation
code = re.sub(
    r"                         f'\(\{count\} set\)'\)\s*elif kind == 'name':\s*value = participant\['name'\] if participant else random_name\(\)",
    '''                         f'({count} set)')
        elif kind == 'name':
            value = participant['name'] if participant else random_name()''',
    code
)

with open('main_fixed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Formatting fixed")
