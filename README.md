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
- [Configuration & Gemini API Setup](#configuration--gemini-api-setup)
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

> [!IMPORTANT]
> **Strict Python Requirement:**
> Course Automation strictly requires **Python 3.10 or newer** (`requires-python = ">=3.10"` in `pyproject.toml`).
> We strongly recommend **Python 3.12** for all new users. Older Python versions (such as macOS default Python 3.9.6) are **not supported** and will fail during installation.

### Supported Python Versions
- **Python 3.12** *(Recommended for all users)*
- **Python 3.11**
- **Python 3.10**
- *(Python 3.14 has also been verified in clean local test environments; Python 3.9 and older will fail).*

### Supported Operating Systems
| Operating System | Support Status | Verification Notes |
|---|---|---|
| **macOS (Apple Silicon & Intel)** | **Verified** | Fully tested and verified on macOS Darwin. |
| **Linux (Ubuntu, Debian, Fedora)** | **Supported** | Standard POSIX Python and Playwright environments. |
| **Windows 10 / Windows 11** | **Unverified on Host** | Architecturally supported; instructions below use standard PowerShell workflows. Must be validated on a physical Windows machine. |

---

## macOS Installation Guide

Follow these steps to set up Course Automation on macOS (Sonoma, Sequoia, Ventura, Monterey, or later):

### Step 1: Check Python Version & Install Prerequisites
> [!IMPORTANT]
> **Check your Python version before creating a virtual environment.**
> Fresh Macs frequently default to Apple's Xcode Command Line Tools Python version **3.9.6**, which does not meet the project's `>=3.10` requirement and will fail when running `pip install -e .`.

Check your current installed Python version:
```bash
python3 --version
```
- If your version is **3.9.x or older**, or if `python3` is not found, install **Python 3.12** and **Git** via [Homebrew](https://brew.sh/):
  ```bash
  brew install python@3.12 git
  ```
- Verify that Python 3.12 is available:
  ```bash
  python3.12 --version
  ```
  *(Expected output: `Python 3.12.x`)*

### Step 2: Clone the Repository
Clone your private repository and navigate into the project directory:
```bash
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation
```

### Step 3: Create and Activate a Virtual Environment
Explicitly use `python3.12` to create the virtual environment so it is never bound to older system Python versions:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```
*(Your terminal prompt will now show `(.venv)`).*

Verify that the active virtual environment is running Python 3.12:
```bash
python --version
```
*(Must display `Python 3.12.x` or at least `Python 3.10+`).*

### Step 4: Upgrade Pip and Install the Project
Upgrade `pip` to the latest version and install the project in editable mode using `python3.12`:
```bash
python3.12 -m pip install --upgrade pip
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
1. **Python 3.10 - 3.12 (Recommend 3.12):**
   - Download the official installer from [python.org](https://www.python.org/downloads/).
   - **CRITICAL:** On the first installer screen, check the box: **"Add python.exe to PATH"** before clicking Install Now.
2. **Git for Windows:**
   - Download and install from [git-scm.com](https://git-scm.com/download/win).
3. **Verify Version:**
   ```powershell
   python --version
   ```
   *(Ensure it reports `Python 3.10.x`, `3.11.x`, or `3.12.x`).*

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
*(If you have multiple Python versions installed, specify Python 3.12 explicitly: `py -3.12 -m venv .venv`).*

> [!NOTE]
> **Recreating an Outdated Environment on Windows:**
> If an existing `.venv` was created with Python 3.9 or older, remove and recreate it safely:
> ```powershell
> deactivate
> Remove-Item -Recurse -Force .venv
> py -3.12 -m venv .venv
> ```
> *Safe removal note: Only the `.venv` directory is removed; all project files remain intact.*

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

## Configuration & Gemini API Setup

The core application runs without an API key for login, course inspection, theory reading, and local progress tracking. A personal Gemini API key and the AI dependencies (`google-genai`) are required for AI-powered reasoning on quiz questions and generating coding solutions. Students who want automated question-answering functionality must complete the Gemini setup below before using that feature.

---

### Feature Breakdown: What Requires an API Key?

| Feature | Requires API Key? | Behavior Without API Key |
|---|---|---|
| **One-time Login & Auth** (`course-automation auth`) | **No** | Saves session cookies locally in `~/.course_automation/browser_profile`. |
| **Syllabus Inspection** (`course-automation inspect`) | **No** | Dynamically parses full course units, module percentages, and activity counts. |
| **Active Tab Detection** (`course-automation inspect`) | **No** | Automatically queries open CodeChef tab in the browser session. |
| **Module Selection** (`--incomplete-only`, `--select-module`) | **No** | Interactively filters course navigation based on local syllabus discovery. |
| **Theory Reading Lessons** (`course-automation solve --theory-only`) | **No** | Smoothly scrolls lessons to trigger dynamic MathJax rendering, finds enabled `Next` buttons, and advances. |
| **Offline Progress Tracking** (`course-automation status`) | **No** | Queries local SQLite database (`~/.course_automation/progress.db`) completely offline. |
| **Safe Dry-Run Simulations** (`--dry-run`) | **No** | Inspects DOM and navigates without clicking submit buttons or changing progress. |
| **Automated Test Suite** (`pytest -v`) | **No** | All 67 unit and integration tests run 100% offline using synthetic fixtures and mocks. |
| **Multiple-Choice Questions (MCQs)** | **Requires Key** | With API key: reasons about question options and evaluates answer confidence. Without API key: extracts question/options from DOM and reports verdict `INSPECTED_NO_AI` without guessing. |
| **Coding Exercises & Labs** | **Requires Key** | With API key: generates language-specific code solutions. Without API key: inspects editor buffer and reports verdict `INSPECTED_NO_AI`. |

> [!NOTE]
> **Implementation Note on Answer Reasoning:**
> Course Automation uses the Google Gemini API (`gemini-flash-lite-latest` via the official `google-genai` SDK) for structured prompt reasoning. There is **no separate web search provider or `search.answer` endpoint** in this project; question evaluation and code solutions are powered directly by Gemini when configured.

---

### Step-by-Step API Key Setup (For Students)

If you want automated reasoning for quizzes or coding exercises, follow these steps to configure your own personal key.

#### 1. Obtain a Personal Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your personal Google account.
3. Click **Create API Key** and copy your newly generated key.

> [!IMPORTANT]
> **Student Responsibility & Quota Notice:**
> - **Each student must configure their own personal API key.** Never share your key with classmates or commit it to GitHub.
> - The default model `gemini-flash-lite-latest` is eligible for Google's developer free tier.
> - **API Quotas & Costs:** Free-tier usage is subject to Google's rate limits (requests per minute/day). If you exceed free-tier quotas or configure a paid billing account in Google Cloud, charges may apply according to Google's pricing terms. The maintainers do not supply, sponsor, or guarantee free or unlimited API access.

#### 2. Create Your Local `.env` File
In the project root directory, copy the configuration template:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

#### 3. Edit `.env` with Your Key
Open `.env` in any text editor (VS Code, Nano, Notepad, etc.) and configure your settings using placeholder syntax:
```env
# Enable the Gemini AI provider (default is 'none')
AI_PROVIDER=gemini

# Your personal Google AI Studio API key (supports GEMINI_API_KEY or GOOGLE_API_KEY)
GEMINI_API_KEY=your_gemini_api_key_here

# Model identifier
GEMINI_MODEL=gemini-flash-lite-latest
```

#### 4. Install the Optional AI Package
Ensure the `google-genai` SDK is installed in your virtual environment:
```bash
pip install -e ".[ai]"
```

#### 5. Verify That Configuration is Loaded
Run the CLI configuration diagnostic command:
```bash
course-automation config
```
You should see:
- `AI Provider: gemini`
- `Gemini Model: gemini-flash-lite-latest`
- `Gemini API Key: [SET (REDACTED)]`

*(If the key is displayed as `[NOT SET]`, ensure your `.env` file is in the project root directory and the variable name is spelled `GEMINI_API_KEY`).*

---

### Git Safety & Secret Hygiene
- The `.env` and `.env.local` files are strictly excluded by [`.gitignore`](.gitignore).
- Verify that your key is ignored by Git:
  ```bash
  git status
  ```
  Your `.env` file should **never** appear in the output. Never commit or push API keys to Git repositories.

---

### Configuration Reference

| Setting in `.env` | Alias / Alternative | Default | Description |
|---|---|---|---|
| `AI_PROVIDER` | — | `none` | Active provider: `gemini` (enables AI solving) or `none` (manual / theory only). |
| `GEMINI_API_KEY` | `GOOGLE_API_KEY` | None | Google AI Studio API key. |
| `GEMINI_MODEL` | — | `gemini-flash-lite-latest` | Model identifier used for reasoning. |
| `BROWSER_HEADLESS` | — | `false` | Set to `true` to run browser invisibly. |
| `BROWSER_USER_DATA_DIR` | — | `~/.course_automation/browser_profile` | Directory for authenticated cookies and browser state. |
| `BROWSER_CDP_URL` | — | None | Optional CDP endpoint (e.g., `http://127.0.0.1:9222`) if attaching to an external Chrome. |
| `DATABASE_PATH` | — | `~/.course_automation/progress.db` | Local SQLite database for syllabus and progress caching. |
| `DRY_RUN` | — | `false` | Default dry-run mode for CLI operations. |
| `LOG_LEVEL` | — | `INFO` | Console log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

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

### 7. macOS: Python 3.9 Error during `pip install -e .`
**Symptom:**
```
ERROR: Package 'course-automation' requires a different Python: 3.9.6 not in '>=3.10'
```
**Cause:** Default macOS Command Line Tools provides Python 3.9.6. Additionally, an existing `.venv` created with Python 3.9 retains that version even if Python 3.12 is subsequently installed on the system.
**Solution:**
1. Install Python 3.12 via Homebrew:
   ```bash
   brew install python@3.12
   ```
2. Delete the outdated `.venv` folder (only the isolated virtual environment is removed; project files are untouched):
   ```bash
   rm -rf .venv
   ```
3. Recreate the environment using Python 3.12 explicitly:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python3.12 -m pip install --upgrade pip
   pip install -e .
   ```
4. Verify the active version:
   ```bash
   python --version
   # Expected output: Python 3.12.x
   ```

### 8. CLI Reports `INSPECTED_NO_AI` on Quizzes or Coding Labs
**Symptom:** During `course-automation solve`, quiz and coding activities log:
```
Discovered options; no AI provider configured. (Verdict: INSPECTED_NO_AI)
```
**Cause:** `AI_PROVIDER=none` or `GEMINI_API_KEY` is not configured in `.env`.
**Solution:**
- To process reading lessons without AI, add the `--theory-only` flag:
  ```bash
  course-automation solve <COURSE_URL> --theory-only
  ```
- To enable AI reasoning, configure `AI_PROVIDER=gemini` and your `GEMINI_API_KEY` in `.env`, install dependencies with `pip install -e ".[ai]"`, and verify with `course-automation config`.

### 9. Invalid API Key / `400 API_KEY_INVALID` or `403 PERMISSION_DENIED`
**Symptom:** `google.genai.errors.ClientError: 400 API_KEY_INVALID` or `403 PERMISSION_DENIED`.
**Cause:** The configured `GEMINI_API_KEY` has a typo, was revoked, or lacks permission for the Gemini API.
**Solution:**
1. Generate a fresh API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Update `GEMINI_API_KEY=your_new_key` in `.env`.
3. Test with `course-automation config`.

### 10. Rate Limit / Quota Exceeded (`429 RESOURCE_EXHAUSTED`)
**Symptom:** `google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED` (Quota exceeded for metric).
**Cause:** Exceeded Google AI Studio's free tier requests-per-minute or daily quota.
**Solution:**
- Wait 60 seconds before retrying.
- Or pass `--no-ai` / `--theory-only` to continue reading theory lessons without consuming API calls.

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
