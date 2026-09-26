"""
Google Forms bot - multi-page / sectioned form aware.

Built for the "Hotel Booking Management System Evaluation Survey"
(13 pages, section page breaks, star rating questions).

HOW IT WORKS
  * Walks the form page by page: answer what is on the page, then click Next.
  * The last page has Submit instead of Next -> clicks it and then VERIFIES
    that Google shows the "Your response has been recorded." screen.
  * Every rating question is answered from a per-respondent profile, so you
    get an exact 50/50 split (e.g. 50 respondents rate 5 stars, 50 rate 4).
  * Questions are classified by their TITLE, so:
      - "Name of the participant"        -> a random person name
      - "Website Link" (a bare link)     -> left alone, just clicks Next
      - "any suggestions for our website"-> a suggestion sentence
      - "Any Features ... Missing"       -> a feature request sentence

RUN
  python main_fixed.py            submit TOTAL_RESPONDENTS responses
  python main_fixed.py --inspect  just walk the form and print what it finds
                                 (never submits - use this to debug first)

!! BEFORE THE FIRST REAL RUN, IN GOOGLE FORMS SETTINGS:
     1. Turn OFF "Collect email addresses"
     2. Turn OFF "Limit to 1 response" / "One response per person"
     3. Make sure the form is set to ACCEPTING responses
   With email collection on, Google shows a Google sign-in wall to the bot
   and caps you at one response per signed-in account, so 100 submissions
   are impossible.
"""

import random
import re
import json
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# =========================================
# Config
# =========================================

TOTAL_RESPONDENTS = 100
MAX_RETRIES = 2
MAX_PAGES = 40                 # safety stop; your form has 13

FORM_LINK = (
    'https://docs.google.com/forms/d/e/'
    '1FAIpQLScKDzVp96x2yHRtvjYIrRS9-lWLEii0ryuvHay62YOEweEXXg/viewform'
)

# Google Forms picks its own UI language, which can differ from the language
# your questions are written in. This form was being served in FILIPINO, so
# the buttons read "Susunod" (Next) / "Isumite" (Submit) and the page counter
# read "Page 1 ng 13" - which is why plain text matching failed.
# Pinning hl=en makes the form chrome English without touching the questions.
FORM_UI_LANGUAGE = 'en'

# Google renders its navigation buttons with a fixed jsname that is identical
# in every language, so matching on it works regardless of the form language.
NEXT_JSNAME = 'OCpkoe'
SUBMIT_JSNAME = 'M7QdBf'

# Text fallbacks, in case Google ever changes those jsnames.
NEXT_TEXTS = (
    'next', 'susunod', 'siguiente', 'suivant', 'weiter', 'avanti',
    'próximo', 'proximo', 'volgende', 'naprej', 'далее', 'continue',
)
SUBMIT_TEXTS = (
    'submit', 'isumite', 'sendsa', 'senden', 'enviar', 'envoyer',
    'invia', 'vidare', '送信', '提交',
)
BRAVE_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
CHROMEDRIVER_PATH = (
    r'D:\User\Downloads\Code VS\Survery-Auto-Answer-Program\FormsBot\Files\chromedriver.exe'
)

# Star rating given to EVERY rating question, per profile.
# Must sum to 100 -> an exact split across TOTAL_RESPONDENTS.
RATING_PROFILE_MIX = {5: 60, 4: 30, 3: 10}  # 60% 5-stars, 30% 4-stars, 10% 3-stars (baseline)

PAGE_LOAD_PAUSE = 1.2
VERIFY_TIMEOUT = 15

# =========================================
# Browser setup
# =========================================

chrome_options = ChromeOptions()
chrome_options.binary_location = BRAVE_PATH
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--incognito')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument('--window-size=1280,1600')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)



# =========================================
# Content pools
# =========================================

NAME_POOL = [
    'John Smith', 'Maria Santos', 'Alex Ramos', 'Ana Reyes', 'Luis Cruz',
    'Sarah Johnson', 'Daniel Lee', 'Emma Garcia', 'Michael Tan', 'Sophia Lopez',
    'David Nguyen', 'Grace Miller', 'James Wilson', 'Isabella Brown',
    'Ethan Davis', 'Mia Walker', 'Noah Hall', 'Amelia Scott', 'Benjamin Adams',
    'Charlotte Young', 'Lucas Baker', 'Harper Clark', 'Henry Evans', 'Ella Green',
    'Alexander Perez', 'Lily Hill', 'Jack Flores', 'Zoe Torres', 'Oliver Brooks',
    'Chloe Ward', 'Samuel Reed', 'Ava Richardson', 'Nathan Cooper', 'Layla Price',
    'Leo Bennett', 'Nora Coleman', 'Mateo Foster', 'Hannah Ross', 'Gabriel Murphy',
    'Sofia Russell', 'Julian Jenkins', 'Aria Perry', 'Wyatt Powell', 'Mila Long',
    'Isaac Ross', 'Penelope Flores', 'Sebastian Cox', 'Aubrey Gray', 'David King',
    'Scarlett Price', 'Anthony Rivera', 'Stella Ward', 'Cole Stewart',
    'Aurora Hughes', 'Jonathan West', 'Paisley Bennett',
]

# "any suggestions for our website?"
SUGGESTION_POOL = [
    'The booking flow is smooth. Adding a live chat support widget would help '
    'when I need to change a reservation at night.',
    'It would be helpful to see a map of the hotel location on the room page '
    'before I confirm the booking.',
    'Please add a promo or discount code field at the final checkout step.',
    'A clearer breakdown of the total price, taxes and resort fees would avoid '
    'any surprises at the end.',
    'Please add the option to save a favourite hotel for quicker rebooking.',
    'The guest review section is great. Adding photos to the reviews would make '
    'it even more useful.',
    'Could you add a date picker that shows which days are fully booked before '
    'I start searching?',
    'An option to pay at the property instead of only online would suit me better.',
    'Please add a filter for hotels with a pool, gym or airport shuttle.',
    'It would help to have a printable or shareable booking confirmation email.',
]

# "Any Features You Think That Are Missing In Our Website?"
FEATURE_POOL = [
    'A loyalty points system that rewards guests for repeat bookings.',
    'A live availability calendar showing real time room counts per room type.',
    'A compare feature that lets me view two or three hotels side by side.',
    'An offline mode so I can review my itinerary without internet access.',
    'A referral link that lets me invite a friend and both get a discount.',
    'A room upgrade or early check-in request form during booking.',
    'Dark mode for the whole site, which is easier on the eyes at night.',
    'A multi-language selector so the site can be used in more languages.',
    'Notifications by SMS or email when a booking is cancelled or confirmed.',
    'An option to add special requests, such as a quiet room or late arrival, '
    'when making a reservation.',
    'A wishlist feature to save hotels and compare prices before booking.',
    'A small map showing how far the hotel is from the airport or city centre.',
]


def random_name():
    return random.choice(NAME_POOL)


def random_suggestion():
    return random.choice(SUGGESTION_POOL)


def random_feature():
    return random.choice(FEATURE_POOL)


# =========================================
# Rating profile plan (exact split)
# =========================================

def build_profile_plan(total, mix):
    """
    Assign each respondent a rating profile so the split is EXACT,
    e.g. 100 respondents -> 50 'perfect' + 50 'fine', shuffled.
    """
    names = list(mix.keys())
    weights = [mix[name] for name in names]
    total_weight = sum(weights)

    counts = [total * w // total_weight for w in weights]
    # Give any rounding remainder to the last bucket so it stays exact.
    counts[-1] += total - sum(counts)

    plan = []
    for name, count in zip(names, counts):
        plan.extend([name] * count)
    random.shuffle(plan)
    return plan[:total]


# =========================================
# Browser + DOM helpers
# =========================================

def make_driver():
    return webdriver.Chrome(
        service=Service(CHROMEDRIVER_PATH),
        options=chrome_options,
    )


def get_questions(driver):
    """Question containers, supporting both old and current Forms markup."""
    for selector in (
        'div[role="listitem"]',
        'div.freebirdFormviewerViewNumberedItemContainer',
    ):
        found = driver.find_elements(By.CSS_SELECTOR, selector)
        if found:
            return found
    return []


def safe_click(element, driver=None):
    """Click, falling back to a direct DOM click if the hit test is blocked."""
    try:
        element.click()
        return True
    except StaleElementReferenceException:
        return False
    except Exception:
        pass
    if driver is not None:
        try:
            driver.execute_script('arguments[0].click();', element)
            return True
        except Exception:
            pass
    return False


def find_button_by_text(driver, label):
    """Find a div[role=button] whose visible text matches `label`."""
    for button in driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]'):
        try:
            text = (button.text or '').strip().lower()
        except StaleElementReferenceException:
            continue
        if text == label:
            return button
    return None


def form_url():
    """
    The form URL with the UI language pinned to English.

    Without this the page can load in Filipino ("Susunod" / "Page 1 ng 13"),
    which is exactly what broke button matching.
    """
    base = FORM_LINK.split('?')[0].split('#')[0]
    return f'{base}?hl={FORM_UI_LANGUAGE}'


def page_position(driver):
    """
    Parse the 'Page 3 of 13' indicator. Returns (current, total).
    'ng' is the Filipino equivalent of 'of', so accept both.
    """
    try:
        body = driver.find_element(By.TAG_NAME, 'body').text
    except WebDriverException:
        return None, None
    match = re.search(
        r'Page\s+(\d+)\s+(?:of|ng|de|von|di)\s+(\d+)', body, re.IGNORECASE
    )
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def find_button(driver, jsname, texts):
    """
    Find a navigation button, preferring its language-independent jsname and
    falling back to matching the visible text in any of several languages.
    """
    for element in driver.find_elements(
        By.CSS_SELECTOR, f'div[role="button"][jsname="{jsname}"]'
    ):
        return element

    for button in driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]'):
        try:
            text = (button.text or '').strip().lower()
        except StaleElementReferenceException:
            continue
        if text in texts:
            return button
    return None


def find_next_button(driver):
    return find_button(driver, NEXT_JSNAME, NEXT_TEXTS)


def find_submit_button(driver):
    return find_button(driver, SUBMIT_JSNAME, SUBMIT_TEXTS)


def question_title(question):
    """The question's heading text, used to decide what answer it wants."""
    for selector in (
        '.freebirdFormviewerViewQuestionTitle',
        'div[role="heading"]',
    ):
        for element in question.find_elements(By.CSS_SELECTOR, selector):
            try:
                text = (element.text or '').strip()
            except StaleElementReferenceException:
                continue
            if text:
                return text
    return ''


# =========================================
# Question classification
# =========================================

def classify(question):
    """
    Decide what a question wants, based on its structure and its title.

    Returns one of:
      'rating'    - radio/scale, answer from the respondent's profile
      'name'      - participant name text box
      'suggestion' - "any suggestions for our website"
      'feature'   - "Any Features ... Missing"
      'checkbox'  - checkbox group
      'text'      - any other text box
      'link'      - just a hyperlink, nothing to type (e.g. "Website Link")
      'skip'      - section header / description, nothing to answer
    """
    title = question_title(question)
    low = title.lower()

    groups = question.find_elements(
        By.CSS_SELECTOR, '[role="radiogroup"], [role="group"]'
    )
    radios = question.find_elements(By.CSS_SELECTOR, '[role="radio"]')
    if groups or radios:
        return 'rating', title

    if question.find_elements(By.CSS_SELECTOR, '[role="checkbox"]'):
        return 'checkbox', title

    textareas = question.find_elements(By.CSS_SELECTOR, 'textarea')
    inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
    if textareas or inputs:
        if 'gmail' in low or 'email' in low:
            return 'email', title
        if 'name' in low or 'participant' in low:
            return 'name', title
        if 'feature' in low or 'missing' in low:
            return 'feature', title
        if any(word in low for word in ('suggest', 'feedback', 'comment',
                                        'improve', 'opinion')):
            return 'suggestion', title
        return 'text', title

    if question.find_elements(By.CSS_SELECTOR, 'a[href]'):
        return 'link', title

    return 'skip', title



# =========================================
# Answering
# =========================================

def type_into(question, text, driver):
    """Replace the contents of a question's first visible text field."""
    for selector in ('textarea', 'input[type="text"]'):
        for field in question.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not field.is_displayed():
                    continue
                safe_click(field, driver)
                field.clear()
                field.send_keys(text)
                return True
            except StaleElementReferenceException:
                continue
    return False


def set_rating(question, stars, driver):
    """
    Click the Nth option of a linear-scale / radio question.

    stars=5 -> the 5th option (index 4) on a 1-5 scale.
    Handles grid questions by answering one choice per row.
    """
    targets = question.find_elements(
        By.CSS_SELECTOR, '[role="radiogroup"], [role="group"]'
    )
    if not targets:
        targets = [question]

    clicked = 0
    for group in targets:
        options = group.find_elements(By.CSS_SELECTOR, '[role="radio"]')
        if not options:
            continue
        index = max(0, min(len(options) - 1, stars - 1))
        if safe_click(options[index], driver):
            clicked += 1
    return clicked


def clean(text, limit=60):
    """Collapse the newlines Google puts inside question titles."""
    flat = ' '.join((text or '').split())
    return flat if len(flat) <= limit else flat[:limit - 1] + '…'


def answer_page(driver, stars, participant, dry_run=False):
    """
    Answer every question visible on the current page.
    Returns (answers, log) where log describes what happened per question.

    dry_run does NOT stop the answers being filled in - it only makes this
    quieter. Required questions must genuinely be answered or Google will
    refuse to advance to the next page, which is exactly what an inspect run
    needs to test.
    """
    log = []
    answered = 0

    for question in get_questions(driver):
        kind, title = classify(question)

        if kind == 'rating':
            # Dynamic rating: mostly the baseline, but occasionally varies by 1 star
            import random
            wobble = random.choice([0, 0, 0, 0, -1, 1])
            dynamic_stars = max(1, min(5, stars + wobble))
            count = set_rating(question, dynamic_stars, driver)
            answered += count
            log.append(f'      [rating] "{clean(title)}" -> {dynamic_stars} '
                       f'({count} set)')
        elif kind == 'name':
            value = participant['name'] if participant else random_name()
            if type_into(question, value, driver):
                answered += 1
            log.append(f'      [name]   "{clean(title)}" -> "{value}"')
        elif kind == 'email':
            value = participant['email'] if participant else "default@gmail.com"
            if type_into(question, value, driver):
                answered += 1
            log.append(f'      [email]  "{clean(title)}" -> "{value}"')
        elif kind == 'suggestion':
            value = random_suggestion()
            if type_into(question, value, driver):
                answered += 1
            log.append(f'      [suggest] "{clean(title)}" -> {value[:40]}...')
        elif kind == 'feature':
            value = random_feature()
            if type_into(question, value, driver):
                answered += 1
            log.append(f'      [feature] "{clean(title)}" -> {value[:40]}...')
        elif kind == 'checkbox':
            boxes = question.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
            if boxes:
                safe_click(boxes[0], driver)
                answered += 1
            log.append(f'      [checkbox] "{clean(title)}" -> first option')
        elif kind == 'text':
            value = random_suggestion()
            if type_into(question, value, driver):
                answered += 1
            log.append(f'      [text]   "{clean(title)}" -> {value[:40]}...')
        elif kind == 'link':
            log.append(f'      [link]   "{clean(title)}" -> left alone, '
                       f'just clicks Next')
        else:
            log.append(f'      [skip]   {clean(title) or "(no title)"}')

        if not dry_run:
            time.sleep(0.12)

    return answered, log



# =========================================
# State detection
# =========================================

CONFIRMED_MARKERS = (
    'your response has been recorded',
    'your response has been saved',
    'you submitted this form',
    'naitala na ang iyong tugon',        # Filipino
    'na-save na ang iyong tugon',
)

FAILURE_MARKERS = (
    'this form requires answers',
    'this question is required',
    'please fill out this field',
    'no longer accepting responses',
)


def detect_blocker(driver):
    """
    Things that stop a submission outright. Checked BEFORE trying to submit
    so the failure message is specific instead of a generic timeout.
    """
    try:
        url = (driver.current_url or '').lower()
    except WebDriverException:
        url = ''

    if 'accounts.google.com' in url or 'servicelogin' in url:
        return ('Google sign-in wall hit - turn OFF "Collect email addresses" '
                'in the form Settings')

    try:
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
    except WebDriverException:
        return None

    if 'sign in to continue' in body or 'you need to sign in' in body:
        return 'form requires sign-in - turn OFF "Collect email addresses"'
    if 'no longer accepting responses' in body or 'not accepting responses' in body:
        return 'form is closed - turn it back on in Settings'
    if 'only submit one response' in body or 'already submitted' in body:
        return 'Google blocked a repeat response from the same account'
    return None


def detect_state(driver):
    """'confirmed' | 'failed:<reason>' | 'unknown' after clicking Submit."""
    # Structural check first: this class only exists on the thank-you screen,
    # so confirmation is detected no matter what language the form uses.
    for selector in (
        'div.freebirdFormviewerViewConfirmationScreen',
        '.freebirdFormviewerViewConfirmationMessage',
    ):
        if driver.find_elements(By.CSS_SELECTOR, selector):
            return 'confirmed'

    try:
        source = driver.page_source.lower()
    except WebDriverException:
        return 'unknown'

    for marker in CONFIRMED_MARKERS:
        if marker in source:
            return 'confirmed'

    for alert in driver.find_elements(By.CSS_SELECTOR, '[role="alert"]'):
        try:
            text = (alert.text or '').strip()
        except StaleElementReferenceException:
            continue
        if text:
            return f'failed:{text}'

    for marker in FAILURE_MARKERS:
        if marker in source:
            return f'failed:{marker}'

    return 'unknown'


def submit_button(driver):
    """Scoped submit lookup, so a question titled 'Submit...' can't be hit."""
    by_jsname = find_submit_button(driver)
    if by_jsname is not None:
        return by_jsname

    for element in driver.find_elements(
        By.CSS_SELECTOR, 'div.freebirdFormviewerViewSubmitButton'
    ):
        return element

    xpath = (
        '//div[@role="button"][.//text()[contains(translate(., '
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "submit")]]'
    )
    for element in driver.find_elements(By.XPATH, xpath):
        return element
    return None


def submit_and_verify(driver):
    """Click Submit and confirm Google actually recorded the response."""
    button = submit_button(driver)
    if button is None:
        return False, 'submit button not found'

    safe_click(button, driver)

    deadline = time.time() + VERIFY_TIMEOUT
    state = 'unknown'
    while time.time() < deadline:
        state = detect_state(driver)
        if state != 'unknown':
            break
        time.sleep(0.5)

    if state == 'confirmed':
        return True, ''
    if state.startswith('failed:'):
        return False, state[len('failed:'):]
    return False, 'no confirmation screen appeared'



# =========================================
# The page walker
# =========================================

def walk_form(driver, stars, participant, dry_run=False):
    """
    Walk page by page: answer what is on the page, then click Next.
    On the last page there is no Next, so it clicks Submit and verifies.

    In dry_run mode the per-question log is printed and Next IS still clicked
    (otherwise the pages after the first could never be inspected). Only the
    final Submit is withheld.
    """
    stuck = 0

    for page_index in range(MAX_PAGES):
        current, total = page_position(driver)
        label = f'Page {current or page_index + 1} of {total or "?"}'

        answered, log = answer_page(driver, stars, participant, dry_run=dry_run)
        if dry_run:
            print(f'\n  -- {label}   [{answered} answers]')
            for line in log:
                print(line)

        blocker = detect_blocker(driver)
        if blocker:
            return False, blocker, page_index

        nxt = find_next_button(driver)
        if nxt is not None:
            # Next must be clicked in BOTH modes, or we can never reach the
            # pages after this one.
            if not safe_click(nxt, driver):
                return False, f'could not click Next on {label}', page_index
            if dry_run:
                print('      -> clicked Next')
            time.sleep(PAGE_LOAD_PAUSE)

            # Guard against a Next button that silently does nothing.
            new_current, _ = page_position(driver)
            if current is not None and new_current == current:
                stuck += 1
                if stuck >= 2:
                    return (False,
                            f'Next did not advance past {label} after 2 tries',
                            page_index)
            else:
                stuck = 0
            continue

        if submit_button(driver) is not None:
            if dry_run:
                print('      -> LAST PAGE. Would click Submit here '
                      '(not clicking in inspect mode).')
                return True, 'inspect complete', page_index + 1
            ok, reason = submit_and_verify(driver)
            return ok, reason, page_index + 1

        return False, f'no Next or Submit button on {label}', page_index

    return False, f'stopped after MAX_PAGES ({MAX_PAGES})', MAX_PAGES


def submit_once(link, stars, participant, driver, dry_run=False):
    """One complete respondent, using the caller's browser session."""
    try:
        try:
            driver.delete_all_cookies()
        except Exception:
            pass
        driver.get(form_url())
        time.sleep(PAGE_LOAD_PAUSE)

        blocker = detect_blocker(driver)
        if blocker:
            return False, blocker, driver

        ok, reason, _pages = walk_form(driver, stars, participant, dry_run)
        return ok, reason, driver

    except TimeoutException as exc:
        return False, f'timeout: {exc.msg}', driver
    except WebDriverException as exc:
        return False, f'browser crashed: {str(exc).splitlines()[0]}', None
    except Exception as exc:
        return False, f'unexpected: {type(exc).__name__}: {exc}', driver


# =========================================
# Modes
# =========================================

def inspect():
    """Walk the form and print what would be answered. Submits nothing."""
    print('INSPECT MODE - walking the form without submitting.\n')
    driver = make_driver()
    try:
        driver.get(form_url())
        time.sleep(PAGE_LOAD_PAUSE)

        blocker = detect_blocker(driver)
        if blocker:
            print(f'BLOCKED: {blocker}')
            return 1

        ok, reason, pages = walk_form(driver, 5, None, dry_run=True)
        print('\n' + '-' * 60)
        print(f'Walked {pages} page(s). Final status: {reason}')
        if ok:
            print('\nEvery page parsed correctly.')
            print('Now run without --inspect to actually submit.')
        else:
            print('\nSomething above needs fixing before real submissions.')
        return 0 if ok else 1
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    plan = build_profile_plan(TOTAL_RESPONDENTS, RATING_PROFILE_MIX)
    print(f'Submitting {TOTAL_RESPONDENTS} responses.')
    print(f'Rating split: {RATING_PROFILE_MIX}  (exact, shuffled)\n')

    driver = make_driver()
    submitted = 0
    failures = {}

    try:
        with open('participants.json', 'r', encoding='utf-8') as f:
            all_participants = json.load(f)
    except:
        all_participants = []

    unused_participants = [p for p in all_participants if not p.get('used')]
    import random
    random.shuffle(unused_participants)

    try:
        for index, profile in enumerate(plan, start=1):
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
                        
                    print(f'[{index}/{TOTAL_RESPONDENTS}] OK  '
                          f'profile={profile} ({stars} stars) -> Marked {participant.get("email")} as used')
                    break
                print(f'[{index}/{TOTAL_RESPONDENTS}] attempt '
                      f'{attempt}/{MAX_RETRIES} failed: {reason}')
                time.sleep(2)
            else:
                failures[reason] = failures.get(reason, 0) + 1
            time.sleep(0.4)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print('\n' + '=' * 58)
    print(f'VERIFIED submissions : {submitted}')
    print(f'Failed respondents   : {sum(failures.values())}')
    for reason, count in failures.items():
        print(f'   - {count}x  {reason}')
    print('=' * 58)
    print('Trust this number, not the counter on the form page.')
    return 0 if submitted == TOTAL_RESPONDENTS else 1


USAGE = """Hotel Booking Management System Evaluation Survey - form bot

USAGE
  python main_fixed.py                 submit TOTAL_RESPONDENTS responses
  python main_fixed.py --inspect       walk the form and print what it would
                                       answer, without submitting anything
  python main_fixed.py --count 5       submit 5 responses (overrides the config)
  python main_fixed.py --help          show this message

BEFORE A REAL RUN, in Google Forms > Settings:
  - turn OFF "Collect email addresses"
  - turn OFF "Limit to 1 response"
  - confirm the form is accepting responses
"""


def parse_args(argv):
    global TOTAL_RESPONDENTS
    if '--help' in argv or '-h' in argv:
        print(USAGE)
        return None
    if '--count' in argv:
        index = argv.index('--count')
        if index + 1 < len(argv) and argv[index + 1].isdigit():
            TOTAL_RESPONDENTS = int(argv[index + 1])
    return argv


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    if args is None:
        sys.exit(0)
    if '--inspect' in args:
        sys.exit(inspect())
    sys.exit(main())

