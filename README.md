# Google Forms Bot

Ever get tiered or struggled to get a large number of responses in Google Forms
for a meaningless school, college or office project — where you know the
outcome is not really going to contribute to anything and you just wanted it
to be complete? Well then, here comes a Google Form Bot.

A Python + Selenium script that fills and submits a Google Form for you.

---

## Quick start (Windows, PowerShell)

```powershell
cd C:\Users\Gman\OneDrive\Documents\Gilbert\Googleforms-bot-main
python main_fixed.py --inspect
```

`--inspect` walks the form and prints what it would fill in, **without
submitting anything**. Once that output looks right, submit for real:

```powershell
python main_fixed.py --count 3     # try 3 first
python main_fixed.py               # uses TOTAL_RESPONDENTS from the config
```

A Brave window will open and close on its own while the bot works. Leave the
terminal alone until it prints the final summary.

### All terminal commands

| Command | What it does |
|---|---|
| `python main_fixed.py --inspect` | Walks every page, prints what it would answer. Submits nothing. |
| `python main_fixed.py --count 5` | Submits 5 responses (overrides `TOTAL_RESPONDENTS`). |
| `python main_fixed.py` | Submits `TOTAL_RESPONDENTS` responses. |
| `python main_fixed.py --help` | Shows usage. |
| `python _selftest.py` | Runs the offline logic tests. No browser, no submissions. |

---

## Setup

### 1. Requirements

```powershell
pip install selenium
```

You also need a browser and a matching driver. The config points at Brave and
ChromeDriver by default — change these two lines in `main_fixed.py` if yours
live somewhere else:

```python
BRAVE_PATH = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
CHROMEDRIVER_PATH = r'C:\...\chromedriver-win64\chromedriver.exe'
```

### 2. Google Form settings — do this first

Open your form → **Settings** tab:

- ☐ **Collect email addresses** → OFF
- ☐ **Limit to 1 response** → OFF
- ☑ **Accepting responses** → ON

> **Why this matters.** With email collection on, Google shows the bot a Google
> sign-in wall and caps you at one response per signed-in account, so bulk
> submissions are impossible. The bot runs in incognito and is not signed in.

---

## How it decides what to type

Questions are matched on their **title text**, so one script handles different
forms:

| Question title contains | Treated as |
|---|---|
| `name`, `participant` | A random person name |
| `suggest`, `feedback`, `comment` | A suggestion sentence |
| `feature`, `missing` | A feature-request sentence |
| Anything with radio buttons | A rating, from the profile below |
| A bare hyperlink, e.g. `Website Link` | Left alone, just clicks Next |
| A section header with no input | Skipped, just clicks Next |

## Rating profiles

Ratings are filled from a per-respondent profile, so the split is **exact**
rather than approximate:

```python
RATING_PROFILE_MIX = {'perfect': 50, 'fine': 50}   # 50% rate 5 stars, 50% rate 4
```

With `TOTAL_RESPONDENTS = 100` you get exactly 50 respondents rating 5 stars on
every rating question and 50 rating 4. The order is shuffled so they are not
grouped together. Add more profiles if you like, as long as the percentages sum
to 100.

## Multi-page forms

The bot walks page by page: answer what is on the page → click `Next` → repeat.
On the final page there is no `Next`, so it clicks `Submit` and then **waits for
Google's "Your response has been recorded." screen** before counting it.

---

## Reading the output

Trust this summary, **not** the response counter shown on the form page — that
counter can include responses from real people and does not prove the bot
worked.

```
==========================================================
VERIFIED submissions : 3
Failed respondents   : 0
==========================================================
```

### If it reports failures

| Message | Fix |
|---|---|
| `Google sign-in wall hit` | Turn OFF "Collect email addresses" |
| `form is closed` | Settings → re-enable "Accepting responses" |
| `Google blocked a repeat response` | Turn OFF "Limit to 1 response" |
| `This form requires answers` | A question type it cannot fill — check for a Scale or Date question |
| `no questions found` | You are looking at a different form than `FORM_LINK` points to |
| `browser crashed` | Usually a ChromeDriver / browser version mismatch |

---

## Files

| File | Purpose |
|---|---|
| `main_fixed.py` | **Use this one.** The working, verified bot. |
| `main.py` | The original script, kept for reference. It reports success even when submissions fail — do not use it for real runs. |
| `_selftest.py` | Offline logic tests, mock driver, no browser needed. |

---

## Timing

13 pages x 100 respondents is roughly **40–60 minutes** of continuous browser
automation. Start with `--count 3`, confirm it works, then scale up.

Note: the 50/50 split is based on `TOTAL_RESPONDENTS`. If you stop a run early,
the completed portion will not be exactly 50/50 — it is only exact across a full
run.

## Legal note

This is for forms you own, or where you have permission. Bulk-submitting to
forms you do not control may break Google's Terms of Service.

