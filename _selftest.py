"""Mock-driver unit tests for main_fixed.py (no real browser needed)."""
import sys
sys.path.insert(0, r'c:\Users\Gman\OneDrive\Documents\Gilbert\Googleforms-bot-main')

import main_fixed as m

failures = []


def check(name, got, expected):
    if got == expected:
        print(f'  PASS  {name}')
    else:
        print(f'  FAIL  {name}: got {got!r}, expected {expected!r}')
        failures.append(name)


class El:
    def __init__(self, text='', displayed=True, attrs=None, children=None):
        self.text = text
        self._displayed = displayed
        self._attrs = attrs or {}
        self._children = children or {}
        self.clicked = False
        self.keys = []
        self.cleared = False

    def click(self):
        self.clicked = True

    def is_displayed(self):
        return self._displayed

    def get_attribute(self, name):
        return self._attrs.get(name)

    def send_keys(self, value):
        self.keys.append(value)

    def clear(self):
        self.cleared = True

    def find_elements(self, by, sel):
        return self._children.get(sel, [])


class Question(El):
    """A question container with a title, like Google Forms renders them."""

    def __init__(self, title, children=None):
        heading = El(text=title)
        super().__init__(children=dict(children or {}))
        self._children['.freebirdFormviewerViewQuestionTitle'] = [heading]
        self._children['div[role="heading"]'] = [heading]


class Driver:
    def __init__(self, source='', alerts=(), elements=(), url=None, body='', by_selector=None):
        self.page_source = source
        self._alerts = list(alerts)
        self._elements = list(elements)
        self._by_selector = dict(by_selector or {})
        self.current_url = url or 'https://docs.google.com/forms/d/e/X/viewform'
        self.body = body
        self.js_clicks = 0

    def find_elements(self, by, sel):
        if sel in self._by_selector:
            return self._by_selector[sel]
        if sel == '[role="alert"]':
            return self._alerts
        # Only the generic button selector returns the default elements, so a
        # test for a specific jsname does not accidentally match everything.
        if sel == 'div[role="button"]':
            return self._elements
        return []

    def find_element(self, by, value):
        if by == m.By.TAG_NAME and value == 'body':
            return El(text=self.body)
        return El()

    def execute_script(self, script, element):
        self.js_clicks += 1
        element.clicked = True
        return True


# ---------------------------------------------------------------- real form
print('\n--- classify: the actual questions in your form ---')
cases = [
    ('Name of the participant (Optional)', 'input[type="text"]', 'name'),
    ('Website Link', 'a[href]', 'link'),
    ('I. System Performance', 'nothing', 'skip'),
    ('Timeliness of the System', 'nothing', 'skip'),
    ('any suggestions for our website. ?', 'input[type="text"]', 'suggestion'),
    ('Any Features You Think That Are Missing In Our Website?',
     'input[type="text"]', 'feature'),
]
for title, kind_sel, expected in cases:
    children = {} if kind_sel == 'nothing' else {kind_sel: [El()]}
    q = Question(title, children)
    check(f'"{title[:40]}" -> {expected}', m.classify(q)[0], expected)

stars = [El(text=str(n)) for n in range(1, 6)]
q = Question('The system is easy to learn and use.', {
    '[role="radiogroup"], [role="group"]': [El(children={'[role="radio"]': stars})],
    '[role="radio"]': stars,
})
check('"The system is easy to learn..." -> rating', m.classify(q)[0], 'rating')

print('\n--- set_rating (your 1-5 star scale) ---')
for target in (1, 3, 4, 5):
    opts = [El(text=str(n)) for n in range(1, 6)]
    group = El(children={'[role="radio"]': opts})
    q = Question('rate me', {
        '[role="radiogroup"], [role="group"]': [group],
        '[role="radio"]': opts,
    })
    count = m.set_rating(q, target, Driver())
    idx = [i for i, o in enumerate(opts) if o.clicked]
    check(f'{target} stars clicks option {target}', (count, idx), (1, [target - 1]))

grid = [El(children={'[role="radio"]': [El(), El(), El()]}) for _ in range(3)]
q = Question('grid', {'[role="radiogroup"], [role="group"]': grid, '[role="radio"]': []})
check('grid answers one cell per row', m.set_rating(q, 3, Driver()), 3)

print('\n--- build_profile_plan: exact 50/50 split ---')
mix = {'perfect': 50, 'fine': 50}
for total in (2, 3, 4, 7, 10, 100, 250):
    plan = m.build_profile_plan(total, mix)
    check(f'total={total} keeps every respondent assigned',
          len(plan), total)

plan = m.build_profile_plan(100, mix)
check('100 respondents gives exactly 50 perfect', plan.count('perfect'), 50)
check('100 respondents gives exactly 50 fine', plan.count('fine'), 50)
check('order is shuffled (not blocked)',
      plan != ['perfect'] * 50 + ['fine'] * 50, True)


print('\n--- page_position ("Page 3 of 13") ---')
check('parses page and total',
      m.page_position(Driver(body='Stuff\nPage 3 of 13\nClear form')), (3, 13))
check('parses FILIPINO "Page 1 ng 13"',
      m.page_position(Driver(body='Stuff\nPage 1 ng 13\nI-clear ang form')), (1, 13))
check('missing indicator returns (None, None)',
      m.page_position(Driver(body='no indicator here')), (None, None))

print('\n--- form_url: pins the UI language ---')
check('appends hl=en', m.form_url().endswith('?hl=en'), True)
check('does not double up the query string',
      m.form_url().count('?'), 1)
saved = m.FORM_LINK
m.FORM_LINK = saved + '?hl=en'
check('idempotent if link already has hl=en',
      m.form_url(), saved + '?hl=en')
m.FORM_LINK = saved
check('strips other query params',
      m.form_url(), saved + '?hl=en')

print('\n--- find_next_button / find_submit_button (language proof) ---')
filipino_next = El(text='Susunod')
clear_btn = El(text='I-clear ang form')
check('finds "Susunod" by text when jsname is absent',
      m.find_next_button(Driver(elements=[clear_btn, filipino_next])) is filipino_next,
      True)
check('finds "Next" by text',
      m.find_next_button(Driver(elements=[El(text='Next')])) is not None, True)
by_js = El(text='Susunod')
check('prefers jsname over text (any language)',
      m.find_next_button(Driver(
          elements=[El(text='Something else'), by_js],
          by_selector={'div[role="button"][jsname="OCpkoe"]': [by_js]})) is by_js,
      True)
check('returns None when there is no Next',
      m.find_next_button(Driver(elements=[El(text='Clear form')])), None)
sub = El(text='Isumite')
check('finds "Isumite" (Filipino Submit)',
      m.find_submit_button(Driver(elements=[sub])) is sub, True)
check('submit_button() uses the same finder',
      m.submit_button(Driver(elements=[sub])) is sub, True)

print('\n--- detect_blocker: why your run was failing ---')
check('google sign-in URL caught',
      'sign-in' in m.detect_blocker(Driver(url='https://accounts.google.com/signin')),
      True)
check('"sign in to continue" text caught',
      'sign-in' in m.detect_blocker(Driver(body='You need to sign in to continue')),
      True)
check('closed form caught',
      'closed' in m.detect_blocker(Driver(body='This form is no longer accepting responses.')),
      True)
check('repeat response caught',
      'repeat' in m.detect_blocker(Driver(body='You can only submit one response.')),
      True)
check('normal form page is not blocked',
      m.detect_blocker(Driver(body='Hotel Booking System\nPage 1 of 13')), None)

print('\n--- detect_state: submission verification ---')
check('confirmation screen recognised',
      m.detect_state(Driver(source='<p>Your response has been recorded.</p>')),
      'confirmed')
check('validation error captured',
      m.detect_state(Driver(source='<form>x</form>',
                             alerts=[El(text='This form requires answers to all questions.')])),
      'failed:This form requires answers to all questions.')
check('page still on the form is unknown',
      m.detect_state(Driver(source='<form>Question one?</form>')), 'unknown')
check('confirmation detected structurally, any language',
      m.detect_state(Driver(source='<p>anything at all</p>',
                            by_selector={
                                'div.freebirdFormviewerViewConfirmationScreen': [El()]
                            })),
      'confirmed')

print('\n--- find_button_by_text: exact match only ---')
next_btn = El(text='Next')
d = Driver(elements=[El(text='Clear form'), next_btn, El(text='Back')])
check('finds Next among Back/Clear form', m.find_button_by_text(d, 'next') is next_btn, True)
check('returns None when absent',
      m.find_button_by_text(Driver(elements=[El(text='Back')]), 'next'), None)
check('finds Submit',
      m.find_button_by_text(Driver(elements=[El(text='Submit')]), 'submit') is not None, True)

print('\n--- type_into ---')
field = El(attrs={'type': 'text'})
q = Question('any suggestions for our website. ?', {
    'textarea': [], 'input[type="text"]': [field],
})
check('text typed', m.type_into(q, 'Add a dark mode', Driver()), True)
check('value sent', field.keys, ['Add a dark mode'])

print('\n--- safe_click fallback ---')


class Broken(El):
    def click(self):
        raise m.ElementClickInterceptedException('blocked')


check('blocked click falls back to JS', m.safe_click(Broken(), Driver()), True)
check('no driver -> reports failure honestly', m.safe_click(Broken()), False)

print('\n' + '=' * 58)
if failures:
    print(f'{len(failures)} TEST(S) FAILED: {failures}')
    sys.exit(1)
print('ALL TESTS PASSED')
