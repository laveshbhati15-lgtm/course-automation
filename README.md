# Course Automation

A lightweight, standalone, open-source tool for inspecting course progress, reading theory concepts, and assisting with exercises on CodeChef Learn.

Runs completely on your local machine using standard Python and Playwright. No browser extensions, cloud daemons, or paid subscriptions required.

---

## Prerequisites

- **Python 3.10+** (Python 3.10, 3.11, or 3.12)
- **Git**

---

## Quick Start (Copy-Paste Installation)

### macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies and the CLI tool
pip install --upgrade pip
pip install -e .

# 4. Install the Chromium browser binary
playwright install chromium

# 5. Verify installation
course-automation --help
```

### Windows (PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies and the CLI tool
python -m pip install --upgrade pip
pip install -e .

# 4. Install the Chromium browser binary
playwright install chromium

# 5. Verify installation
course-automation --help
```

---

## First-Run Walkthrough

Follow these 4 simple steps to get started:

### Step 1: One-Time Login (Authentication)
Launch a clean browser window to log in to your CodeChef account:
```bash
course-automation auth
```
Log in manually in the browser window. Your session cookies are stored locally and encrypted in `~/.course_automation/browser_profile` so you do not need to log in again.

### Step 2: Inspect Any Course
Inspect the full syllabus, module breakdown, and completion status for any course:
```bash
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2
```
*Tip: If you already have a course open in your browser, simply run `course-automation inspect` without a URL to auto-detect the active tab.*

### Step 3: Run a Safe Simulation (Dry-Run Mode)
Preview what the tool would do without submitting answers or changing progress:
```bash
course-automation solve https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --dry-run
```
In dry-run mode, the tool inspects the page, scrolls through reading content, extracts questions, and verifies controls, but **never clicks submit buttons or modifies course progress**.

### Step 4: Check Saved Progress Offline
View cached progress anytime from the local SQLite database without opening a browser:
```bash
course-automation status
```

---

## Configuration & Optional AI

The tool works **100% without an AI provider** for course inspection, syllabus discovery, and theory reading.

If you want AI assistance for reasoning through multiple-choice questions (MCQs) or starter code:

1. Copy the template configuration file:
   ```bash
   cp .env.example .env
   ```
2. Install optional AI dependencies:
   ```bash
   pip install -e ".[ai]"
   ```
3. Open `.env` and add your Google Gemini API key:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_google_api_key_here
   GEMINI_MODEL=gemini-flash-lite-latest
   ```
   *(You can obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey). The `gemini-flash-lite-latest` model operates under Google's generous free tier with zero subscription cost).*

### Configuration Options

| Setting in `.env` | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `none` | Set to `gemini` for AI reasoning, or `none` for purely manual/dry-run use. |
| `GEMINI_API_KEY` | None | Your Google AI Studio API key (supports `GEMINI_API_KEY` or `GOOGLE_API_KEY`). |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model identifier for reasoning. |
| `BROWSER_HEADLESS` | `false` | Set to `true` to run without a visible browser window. |
| `BROWSER_USER_DATA_DIR` | `~/.course_automation/browser_profile` | Directory where your authenticated session is saved. |
| `BROWSER_CDP_URL` | None | Optional CDP endpoint (e.g., `http://127.0.0.1:9222`) if attaching to an existing Chrome. |
| `DATABASE_PATH` | `~/.course_automation/progress.db` | Path to local SQLite progress database. |
| `DRY_RUN` | `false` | Default dry-run mode for CLI runs. |
| `LOG_LEVEL` | `INFO` | Console logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## Example Commands

```bash
# 1. Inspect any course (shows completed, in-progress, and incomplete activities)
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2

# 2. Inspect only incomplete activities
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --incomplete-only

# 3. Interactively select a specific module to inspect
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --select-module

# 4. Safe dry-run on theory reading and quizzes (limit to 5 activities)
course-automation solve https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --theory-only --max-activities 5 --dry-run

# 5. Target a specific problem or quiz activity
course-automation solve https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --activity INSSRTASCD --dry-run

# 6. Live assisted progression (prompts for terminal confirmation before each submission)
course-automation solve https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --theory-only --max-activities 5

# 7. View offline database summary of all tracked courses
course-automation status
```

---

## Features & Supported Activities

- **Theory & Concept Reading:** Smoothly scrolls through reading lessons to trigger dynamic MathJax rendering and code blocks, detects accessible enabled `Next` / `Continue` buttons, and confirms page advancement.
- **Multiple-Choice Questions (MCQs):** Extracts complete prompt statements and options, applies structured reasoning, pauses for human confirmation if confidence is below 85%, and verifies the visual checked state and platform feedback banner.
- **Multi-Language Coding Labs:** Handles Monaco and Ace code editors across **C++, Java, C, and Python** using base64 buffer injection to prevent quotation or newline corruption.
- **Safety by Default:**
  - Interactive terminal confirmation required before any submission unless `--auto-approve` is explicitly passed.
  - Built-in regex filters redact API keys, Bearer tokens, and secrets from all logs and prompts.
  - Browser profile and database remain strictly local inside `~/.course_automation/`.

---

## Troubleshooting Guide

### 1. Browser Error: `Executable doesn't exist at ...`
**Fix:** Install the Chromium browser binary:
```bash
playwright install chromium
```

### 2. Session Expired or `403 Not Authorised`
**Fix:** Your session cookies have expired. Re-authenticate:
```bash
course-automation auth
```

### 3. Model Error: `404 NOT_FOUND: models/... is no longer available`
**Fix:** Update `GEMINI_MODEL` in your `.env` file to the latest active model:
```env
GEMINI_MODEL=gemini-flash-lite-latest
```

### 4. CDP Connection: `Protocol error (Browser.setDownloadBehavior)`
**Fix:** Leave `BROWSER_CDP_URL=` empty in your `.env` file. The tool will automatically use its standalone persistent browser profile.

### 5. Permission Denied on Windows PowerShell Execution Policy
**Fix:** Allow local script execution for the current session:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

---

## Known Limitations

- **Locked Activities:** Activities locked by prerequisite gates or scheduling are recognized honestly as `LOCKED_SKIPPED` and are not bypassed.
- **Proctored Exams:** Secure exams with lockdown browsers or webcam proctoring are completely unsupported.
- **CAPTCHAs:** Rare CAPTCHA challenges require manual completion in the headful browser window.
- **Platforms:** Only CodeChef Learn is currently implemented.

---

## Running Automated Tests

All tests run completely offline using mocked DOM trees and synthetic fixtures without contacting live servers or touching user courses:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all 65 automated tests
pytest -v
```

---

## Disclaimer & Compliance

> [!IMPORTANT]
> **Educational and Personal Use Only:** Course Automation is an independent open-source tool designed solely for personal study tracking and coursework assistance.
>
> Users are solely responsible for ensuring compliance with CodeChef's Terms of Service, their academic institution's Honor Code, and all applicable academic integrity policies. The maintainers assume no liability for misuse, account penalties, or policy violations.

---

## License

This project is licensed under the [MIT License](LICENSE).
