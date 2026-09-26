import random
import threading
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =========================================
# Config
# =========================================

# Example: 50% Perfect and 50% Fair for each question
# If your form has 2 answer choices, use: [(50, 50)]
# If it has 3 answer choices, use: [(50, 50, 0)]
# If all questions should be the same: [(50, 50)] * 10
TARGET_DISTRIBUTION = [(50, 50)]

TOTAL_RESPONDENTS = 1000
FORM_LINK = 'https://docs.google.com/forms/d/e/1FAIpQLScKDzVp96x2yHRtvjYIrRS9-lWLEii0ryuvHay62YOEweEXXg/viewform'  # paste your form link here
BRAVE_PATH = r'C:\Users\Gman\OneDrive\Documents\Gilbert\Googleforms-bot-main\Files\brave.exe'
CHROMEDRIVER_PATH = r'C:\Users\Gman\OneDrive\Documents\Gilbert\Googleforms-bot-main\Files\chromedriver.exe'  # update this if needed

# =========================================
# Browser setup
# =========================================
chrome_options = ChromeOptions()
chrome_options.binary_location = BRAVE_PATH
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--incognito')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# =========================================
# Random name generator
# =========================================
NAMES = [
    'John Smith', 'Maria Santos', 'Alex Ramos', 'Ana Reyes', 'Luis Cruz', 'Sarah Johnson',
    'Daniel Lee', 'Emma Garcia', 'Michael Tan', 'Sophia Lopez', 'David Nguyen', 'Grace Miller',
    'James Wilson', 'Isabella Brown', 'Ethan Davis', 'Mia Walker', 'Noah Hall', 'Amelia Scott',
    'Benjamin Adams', 'Charlotte Young', 'Lucas Baker', 'Harper Clark', 'Henry Evans', 'Ella Green',
    'Alexander Perez', 'Lily Hill', 'Jack Flores', 'Zoe Torres', 'Oliver Brooks', 'Chloe Ward',
    'Samuel Reed', 'Ava Richardson', 'Nathan Cooper', 'Layla Price', 'Leo Bennett', 'Nora Coleman',
    'Mateo Foster', 'Hannah Ross', 'Gabriel Murphy', 'Sofia Russell', 'Julian Jenkins', 'Aria Perry',
    'Wyatt Powell', 'Mila Long', 'Elijah Foster', 'Naomi Hughes', 'Christopher Kim', 'Luna Sanders',
    'Leo Patel', 'Ruby Stone', 'Aaron Diaz', 'Hazel Butler', 'Ryan Simmons', 'Violet Bailey',
    'Isaac Ross', 'Penelope Flores', 'Sebastian Cox', 'Aubrey Gray', 'David King', 'Scarlett Price',
    'Anthony Rivera', 'Stella Ward', 'Cole Stewart', 'Aurora Hughes', 'Jonathan West', 'Paisley Bennett'
]


def random_name():
    return random.choice(NAMES)


# =========================================
# Response distribution setup
# =========================================

persons = {}


def build_persons(total_people, target_distribution):
    persons_map = {}
    for idx in range(1, total_people + 1):
        response_plan = []
        for option_percentages in target_distribution:
            option_index = random.choices(
                population=list(range(len(option_percentages))),
                weights=list(option_percentages),
                k=1,
            )[0]
            response_plan.append(option_index)
        persons_map[str(idx)] = response_plan
    return persons_map


persons = build_persons(TOTAL_RESPONDENTS, TARGET_DISTRIBUTION)


# =========================================
# Form filling logic
# =========================================

def fill_random_name_if_present(driver):
    try:
        possible_selectors = [
            'input[type="text"]',
            'input[name*="name" i]',
            'input[aria-label*="name" i]',
            'textarea[name*="name" i]',
            'textarea[aria-label*="name" i]',
        ]

        for selector in possible_selectors:
            try:
                field = driver.find_element(By.CSS_SELECTOR, selector)
                if field.is_displayed() and field.get_attribute('type') != 'hidden':
                    field.clear()
                    field.send_keys(random_name())
                    return True
            except Exception:
                pass

        return False
    except Exception:
        return False


def click_answer(question_element, selected_index):
    try:
        choice_container = question_element.find_element(By.CSS_SELECTOR, '[jscontroller="eFy6Rc"]')
        choices = choice_container.find_elements(By.CSS_SELECTOR, '[jscontroller="EcW08c"]')
        if 0 <= selected_index < len(choices):
            choices[selected_index].click()
            return True
    except Exception:
        pass

    try:
        matrix_container = question_element.find_element(By.CSS_SELECTOR, '[jscontroller="tjSPQb"]')
        lines = WebDriverWait(matrix_container, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                '[class="appsMaterialWizToggleRadiogroupGroupContainer exportGroupContainer freebirdFormviewerComponentsQuestionGridRowGroup"]'))
        )
        for line in lines:
            choices = line.find_elements(By.CSS_SELECTOR, '[jscontroller="EcW08c"]')
            if 0 <= selected_index < len(choices):
                choices[selected_index].click()
                return True
    except Exception:
        pass

    return False


def fill_form(link_):
    global tf
    try:
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)

        for respondent_id in range(1, TOTAL_RESPONDENTS + 1):
            driver.get(link_)
            time.sleep(2)

            fill_random_name_if_present(driver)

            questions = driver.find_elements(By.CSS_SELECTOR, '[class="freebirdFormviewerViewNumberedItemContainer"]')
            response_plan = persons[str(respondent_id)]

            for index, question_element in enumerate(questions):
                if index >= len(response_plan):
                    break
                selected_index = response_plan[index]
                click_answer(question_element, selected_index)

            submit_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Submit')]")
            submit_button.click()
            time.sleep(2)

        tf = True
        driver.quit()
    except Exception as e:
        print(f'Error in filling your form: {e}')
        tf = True


# =========================================
# Runner
# =========================================

tf = False


def start_form_fill():
    fill_form(FORM_LINK)
    if tf:
        print(f'{TOTAL_RESPONDENTS} responses submitted.')


start_form_fill()
