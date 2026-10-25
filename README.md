# Course Automation

A standalone, portable open-source CLI tool for inspecting course progress, reading theory concepts, and assisting with coursework on CodeChef Learn.

Runs completely on your local machine using standard Python and Playwright. No browser extensions, cloud daemons, or paid subscriptions required.

---

## Table of Contents
- [What the Project Does](#what-the-project-does)
- [Current Features & Limitations](#current-features--limitations)
- [Supported Operating Systems & Python Versions](#supported-operating-systems--python-versions)
- [macOS Installation Guide](#macos-installation-guide)
- [Windows 10/11 (PowerShell) Installation Guide](#windows-1011-powershell-installation-guide)
- [Package Installation Commands (Verification)](#package-installation-commands-verification)
- [Authentication & Browser Session Handling](#authentication--browser-session-handling)
- [Configuration & Optional AI Setup](#configuration--optional-ai-setup)
- [Basic Usage & Examples](#basic-usage--examples)
- [Safe Dry-Run Testing](#safe-dry-run-testing)
- [Troubleshooting](#troubleshooting)
- [Testing & Contributor Instructions](#testing--contributor-instructions)
- [Safety, Compliance & Responsible Use](#safety-compliance--responsible-use)
- [License](#license)

---

## What the Project Does

Course Automation provides an accessible command-line interface to:
1. **Inspect Course Structure:** Dynamically discovers modules, theory lessons, quizzes, and coding exercises from any valid CodeChef Learn course URL or active browser tab.
2. **Read Theory Concepts:** Traverses reading lessons, smoothly scrolling to trigger dynamic rendering (MathJax and code snippets) and advancing using accessible navigation controls.
3. **Assist with Quizzes (MCQs):** Extracts questions and answer choices, evaluates answers using local heuristic matching or optional AI reasoning, and requires human terminal confirmation before any action.
4. **Assist with Coding Labs:** Injects code into Monaco and Ace editors across C++, Java, C, and Python using base64 buffer injection to prevent quotation or newline corruption.
5. **Track Offline Progress:** Maintains a local SQLite database of course syllabi and activity statuses without requiring an active browser session.

---

## Current Features & Limitations

### Core Features
- **Dynamic Course Discovery:** Supports any valid CodeChef Learn course URL; nothing is hardcoded to a specific course.
- **Active Tab Auto-Detection:** Automatically detects what course is currently open in your browser session if no URL is provided.
- **Zero-Mutation Dry-Run:** Full simulation mode (`--dry-run`) to inspect pages, read content, and reason about questions without clicking submit or altering course progress.
- **Interactive Safety Gates:** Prompts for terminal approval before any live submission unless `--auto-approve` is explicitly specified.
- **Local SQLite Tracking:** Stores syllabus hierarchies and completed activity records locally for offline inspection.
- **Credential Redaction:** Automatically scrubs API keys, session tokens, and passwords from console output and log files.

### Known Limitations
- **Locked Activities (`LOCKED_SKIPPED`):** Activities locked by prerequisite gates or scheduling deadlines are recognized honestly and skipped; they are never bypassed.
- **Proctored Exams:** Proctored tests, webcam-monitored exams, or lockdown browser assessments are completely unsupported.
- **CAPTCHAs / Bot Challenges:** Rare Cloudflare or CAPTCHA challenges require manual interaction in the headful browser window.
- **Supported Site:** Only CodeChef Learn is currently implemented.

---

## Supported Operating Systems & Python Versions

### Supported Python Versions
- **Python 3.10**
- **Python 3.11**
- **Python 3.12** *(Recommended)*
- *(Python 3.14 has also been verified in clean local test environments; Python 3.9 and below are not supported).*

### Supported Operating Systems
| Operating System | Support Status | Verification Notes |
|---|---|---|
| **macOS (Apple Silicon & Intel)** | **Verified** | Fully tested and verified on macOS Darwin. |
| **Linux (Ubuntu, Debian, Fedora)** | **Supported** | Standard POSIX Python and Playwright environments. |
| **Windows 10 / Windows 11** | **Unverified on Host** | Architecturally supported; instructions below use standard PowerShell workflows. Must be validated on a physical Windows machine. |

---

## macOS Installation Guide

Follow these steps to set up Course Automation on macOS (Sonoma, Ventura, Monterey, or later):

### Step 1: Install Prerequisites
Ensure you have **Python 3.10+** and **Git** installed. You can install them using [Homebrew](https://brew.sh/):
```bash
brew install python git
```
*(Alternatively, install the Xcode Command Line Tools via `xcode-select --install`).*

### Step 2: Clone the Repository
Clone your private repository and navigate into the project directory:
```bash
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation
```

### Step 3: Create and Activate a Virtual Environment
Create an isolated Python virtual environment and activate it:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(Your terminal prompt should now show `(.venv)`).*

### Step 4: Upgrade Pip and Install the Project
Upgrade `pip` to the latest version and install the project in editable mode:
```bash
python3 -m pip install --upgrade pip
pip install -e .
```
> **Tip for Contributors / Testers:** If you plan to run automated tests, install development dependencies:
> ```bash
> pip install -e ".[dev]"
> ```

### Step 5: Install the Required Playwright Browser
Download the standalone Chromium browser binary used by Playwright:
```bash
playwright install chromium
```

### Step 6: Verify the Installation
Check that the CLI entry point and configuration load correctly:
```bash
course-automation --help
course-automation config
```

### Step 7: Run Automated Tests
Verify that all unit and integration tests pass offline:
```bash
pytest -v
```

---

## Windows 10/11 (PowerShell) Installation Guide

> [!NOTE]
> **Windows Verification Notice:** These instructions are based on standard Windows 10/11 PowerShell conventions and standard Playwright/Python procedures. Because our primary development machine is macOS, Windows execution has not been verified on this host and should be confirmed on your Windows machine.

### Step 1: Install Prerequisites
1. **Python 3.10 - 3.12:**
   - Download the official installer from [python.org](https://www.python.org/downloads/).
   - **CRITICAL:** On the first installer screen, check the box: **"Add python.exe to PATH"** before clicking Install Now.
2. **Git for Windows:**
   - Download and install from [git-scm.com](https://git-scm.com/download/win).

### Step 2: Open PowerShell & Clone the Repository
Open **PowerShell** (search for "PowerShell" in the Start menu) and clone the repository:
```powershell
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation
```

### Step 3: Create a Virtual Environment
```powershell
python -m venv .venv
```
*(If `python` is not recognized, try `py -3 -m venv .venv`).*

### Step 4: Activate the Virtual Environment Safely
By default, Windows PowerShell restricts script execution (`PSSecurityException`).
**Do NOT disable system security globally.** Instead, allow script execution safely for the current PowerShell process only:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```
*(Your PowerShell prompt will now show `(.venv)`).*

### Step 5: Upgrade Pip & Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -e .
```
*(Or install dev dependencies for running tests: `pip install -e ".[dev]"`).*

### Step 6: Install the Playwright Chromium Browser
```powershell
playwright install chromium
```

### Step 7: Verify Installation & Tests
```powershell
course-automation --help
course-automation config
pytest -v
```

---

## Package Installation Commands (Verification)

The project relies strictly on standard Python packaging specified in `pyproject.toml`. Here is the reference for verified installation commands:

| Command | Purpose | When to Use |
|---|---|---|
| `pip install -e .` | Installs base project & runtime dependencies (Playwright, Typer, Rich, Pydantic, Requests, Dotenv). | Standard user installation. |
| `pip install -e ".[dev]"` | Installs base project + testing dependencies (`pytest`, `pytest-mock`, `google-genai`). | Development and running tests. |
| `pip install -e ".[ai]"` | Installs optional Google Gemini AI provider dependencies (`google-genai`). | Optional AI reasoning. |
| `playwright install chromium` | Downloads the headless/headful Chromium browser binary. | Required before first browser run. |
| `course-automation --help` | Validates CLI entry point and displays commands. | Smoke test installation. |
| `course-automation config` | Displays resolved configuration paths and environment settings. | Diagnostics and path verification. |

---

## Authentication & Browser Session Handling

Course Automation uses a persistent local browser profile to maintain your logged-in state without storing your plaintext username or password.

### Step 1: Perform One-Time Login
Launch a headful browser to log in to your CodeChef account:
```bash
course-automation auth
```
1. A Chromium browser window will open to the CodeChef login page.
2. Complete your login manually (using email/password, Google OAuth, or GitHub).
3. Once logged in, the tool detects your active session, saves cookies, and exits cleanly.

### Secure Handling & Transparency
> [!IMPORTANT]
> **No Application-Level Encryption:**
> Browser cookies and session data are stored locally in standard Chromium format inside `~/.course_automation/browser_profile` (or `%USERPROFILE%\.course_automation\browser_profile` on Windows).
>
> They are **NOT encrypted at rest by the application**. Security is maintained strictly through your operating system's local user account permissions.
> - **Never** commit, publish, or share your `~/.course_automation` directory.
> - The `.gitignore` file in this repository strictly excludes all `.course_automation` and session directories.

---

## Configuration & Optional AI Setup

The tool is **100% functional without any AI provider** for course inspection, syllabus discovery, and theory reading.

If you would like optional AI assistance for reasoning through multiple-choice questions (MCQs):

### 1. Copy the Configuration Template
```bash
cp .env.example .env
```

### 2. Install AI Dependencies
```bash
pip install -e ".[ai]"
```

### 3. Configure `.env`
Open `.env` in any text editor and configure your Google Gemini key:
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```

> [!NOTE]
> **About Google AI Studio API Keys:**
> You can generate a personal developer API key from [Google AI Studio](https://aistudio.google.com/app/apikey). The `gemini-flash-lite-latest` model is eligible for Google's free tier for developers.
> **Disclaimer:** API availability, free tier access, quotas, and rate limits are managed solely by Google and are subject to change. This project does not guarantee unlimited or perpetual free access.

### Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `none` | AI provider to use (`gemini` or `none`). |
| `GEMINI_API_KEY` | None | Google AI Studio API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`). |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model identifier for reasoning. |
| `BROWSER_HEADLESS` | `false` | Run browser in headless mode (`true`/`false`). |
| `BROWSER_USER_DATA_DIR` | `~/.course_automation/browser_profile` | Local storage location for browser session. |
| `BROWSER_CDP_URL` | None | Optional CDP endpoint (e.g., `http://127.0.0.1:9222`) if attaching to an external browser. |
| `DATABASE_PATH` | `~/.course_automation/progress.db` | Local SQLite database for syllabus and progress caching. |
| `DRY_RUN` | `false` | Global default dry-run flag. |
| `LOG_LEVEL` | `INFO` | Console log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## Basic Usage & Examples

### 1. Inspect a Course Syllabus
Inspect modules, lessons, and completion percentage for any CodeChef Learn course:
```bash
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2
```
*Tip: If you already have the course open in your browser, omit the URL to auto-detect the active tab:*
```bash
course-automation inspect
```

### 2. Filter Incomplete Activities
```bash
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --incomplete-only
```

### 3. Interactively Select a Module
```bash
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --select-module
```

### 4. Safe Dry-Run Simulation (Recommended First Step)
Preview course progression without clicking buttons or submitting answers:
```bash
course-automation solve https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --dry-run
```

### 5. Assisted Theory Reading & Quizzes
Process reading lessons and quizzes with interactive terminal confirmation before every submission:
```bash
course-automation solve https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --theory-only --max-activities 5
```

### 6. View Saved Progress Offline
Query cached syllabi and completion statistics from the local SQLite database without opening a browser:
```bash
course-automation status
```

---

## Safe Dry-Run Testing

The `--dry-run` flag is a first-class feature designed to protect your account and course progress.

When running with `--dry-run`:
- The browser opens the course and navigates to activities.
- For **theory lessons**, the page scrolls to ensure dynamic content loads, verifies the presence of the `Next` button, but **does not click it**.
- For **quizzes (MCQs)**, the tool extracts the question and choices, computes an answer, but **does not select the option or submit**.
- For **coding exercises**, the tool detects language and problem statement without submitting code.
- **Zero mutations occur on CodeChef servers.**

---

## Troubleshooting

### 1. Browser Binary Missing
**Symptom:** `playwright._impl._errors.Error: Executable doesn't exist at ...`
**Solution:**
```bash
playwright install chromium
```

### 2. Session Expired or `403 Not Authorised`
**Symptom:** CodeChef redirects to login or returns an authorization error.
**Solution:** Re-authenticate your session:
```bash
course-automation auth
```

### 3. Windows PowerShell: Script Execution Disabled
**Symptom:** `File ... .venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
**Solution:** Set the execution policy for the current process:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

### 4. Windows: `python` or `pip` is Not Recognized
**Symptom:** `'python' is not recognized as an internal or external command...`
**Solution:**
- Ensure Python was installed with **"Add python.exe to PATH"** checked.
- Alternatively, use the Windows Python launcher: `py -3 -m venv .venv`.

### 5. CDP Protocol Error / Port 9222 Conflict
**Symptom:** `Protocol error (Browser.setDownloadBehavior)` or unable to connect to CDP.
**Solution:** Leave `BROWSER_CDP_URL=` empty in your `.env` file. The tool will use its isolated persistent browser profile automatically.

### 6. Gemini Model Not Found
**Symptom:** `404 NOT_FOUND: models/... is no longer available`
**Solution:** In `.env`, ensure you are using an active model:
```env
GEMINI_MODEL=gemini-flash-lite-latest
```

---

## Testing & Contributor Instructions

### Running Tests
All 67 tests in the test suite run **100% offline** using synthetic mocks and isolated local databases:
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run the test suite
pytest -v
```

### Testing Policy & Safety Rules
> [!CAUTION]
> **NEVER test against live personal courses or user accounts.**
>
> In particular, **never use completed or active courses (such as DBMS `cu-dbms-sem3-2026-c2`) as a test target**.
> All contributions and pull requests must be validated using mocked DOM pages, synthetic fixtures, and local database instances.

---

## Safety, Compliance & Responsible Use

> [!IMPORTANT]
> **Educational & Study Tracking Purpose:**
> Course Automation is an independent open-source tool created solely for personal study tracking and coursework assistance.
>
> Users are solely responsible for ensuring compliance with CodeChef's Terms of Service, their academic institution's Honor Code, and all applicable academic integrity policies. The maintainers assume no liability for misuse, account penalties, or policy violations.

---

## License

This project is licensed under the [MIT License](LICENSE).
