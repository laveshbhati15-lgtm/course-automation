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
- [Configuration & Gemini API Setup (Required for Search Engine)](#configuration--gemini-api-setup-required-for-search-engine)
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
3. **Assist with Quizzes (MCQs):** Extracts questions and answer choices, evaluates answers using local heuristic matching or the Gemini AI search & reasoning engine, and requires human terminal confirmation before any action.
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
| **macOS (Apple Silicon & Intel)** | **Verified** | Fully tested and verified on macOS Darwin with Python 3.12 and 3.14. |
| **Fedora Linux (39, 40, 41, 42)** | **Documented** | Native Python 3.12/3.13, DNF packaging, and Playwright Chromium. |
| **Other Linux (Ubuntu, Debian, Arch)** | **Supported** | Standard POSIX Python 3.10+ and Playwright environments. |
| **Windows 10 / Windows 11** | **Unverified on Host** | Architecturally supported; instructions use standard PowerShell workflows. Must be validated on a physical Windows machine. |

---

---

## Download & Installation Overview

Getting started takes only a few minutes. Follow the sequential 6-stage installation sequence below:
1. **Download project:** Clone the repository or download the ZIP source archive.
2. **Install dependencies:** Create a Python virtual environment (`.venv`), upgrade `pip`, and install package dependencies with AI search engine extras (`pip install -e ".[ai]"`).
3. **Configure Gemini API:** Copy `.env.example` to `.env` and configure your personal Google Gemini API key and `AI_PROVIDER=gemini` (required for automated question reasoning and coding search).
4. **Install browser dependencies:** Install Playwright's Chromium browser binary and operating system shared libraries.
5. **Authenticate with CodeChef:** Run `course-automation auth --timeout 300` to establish and save your persistent session.
6. **Verify the search engine:** Run `course-automation config --check-ai` to verify that your API key and Gemini model connection are live and functional.

### Downloading the Source Code (Git Clone vs. ZIP)
Public GitHub repository: **[github.com/laveshbhati15-lgtm/course-automation](https://github.com/laveshbhati15-lgtm/course-automation)**

| Method | Command or Link | Notes |
|---|---|---|
| **Option A: Git Clone<br>*(Strongly Recommended)*** | `git clone https://github.com/laveshbhati15-lgtm/course-automation.git` | Preserves full Git history. Easily update to new releases and bug fixes with `git pull`. |
| **Option B: ZIP Download** | [Download Source Code (.ZIP)](https://github.com/laveshbhati15-lgtm/course-automation/archive/refs/heads/main.zip) | Useful if Git is not installed. *Limitation:* Does not include Git metadata; **cannot be updated via `git pull`**. Future updates require re-downloading and extracting manually. |

### Platform Installation Guides
Choose your platform below for dedicated, step-by-step instructions:
- [Fedora Linux Installation Guide](#fedora-linux-installation-guide) *(Beginner-friendly)*
- [macOS Installation Guide](#macos-installation-guide)
- [Windows 10/11 (PowerShell) Installation Guide](#windows-1011-powershell-installation-guide)
- Or read the interactive documentation website: **[https://laveshbhati15-lgtm.github.io/course-automation/](https://laveshbhati15-lgtm.github.io/course-automation/)**

---

## Fedora Linux Installation Guide

This guide is designed for beginners on Fedora Linux (Fedora 39, 40, 41, and 42 Workstation/Silverblue/KDE).

### Step 1: Check Prerequisites in Terminal
Open your **Terminal** application (press <kbd>Super</kbd> / Windows key, type `Terminal`, and press <kbd>Enter</kbd>).

1. Check your Fedora version:
   ```bash
   cat /etc/os-release
   ```
2. Verify Python 3 (Fedora 39/40 provide Python 3.12; Fedora 41 provides Python 3.13; `>=3.10` is required):
   ```bash
   python3 --version
   ```
3. Check Git:
   ```bash
   git --version
   ```

### Step 2: Install Required System Packages via DNF
Install Git, Python 3, pip, and development headers using Fedora's `dnf` package manager:
```bash
sudo dnf install -y git python3 python3-pip python3-devel
```

### Step 3: Clone and Enter the Repository
Clone the repository to your local computer and enter the directory:
```bash
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation
```
Confirm you are in the project directory:
```bash
pwd
ls
```
*(You will see `pyproject.toml`, `README.md`, `src/`, and `docs/`).*

### Step 4: Create and Activate a Virtual Environment
Virtual environments prevent conflicts with system packages and protect Fedora's system Python (avoiding PEP 668 errors):
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(Your terminal prompt will now start with `(.venv)`).*

### Step 5: Upgrade Pip & Install Dependencies (including AI Search Engine)
1. Upgrade `pip` and install the package with AI extras enabled:
   ```bash
   python3 -m pip install --upgrade pip
   pip install -e ".[ai]"
   ```
   *(To install development and testing dependencies as well: `pip install -e ".[dev]"`).*

### Step 6: Configure the Gemini API (Required for Search Engine)
> [!IMPORTANT]
> **Mandatory Step for Search & Deduction Features:**
> Configuring your Gemini API key is required to use the project's AI-powered search and deduction engine (answering quizzes, MCQs, and coding challenges). While non-API commands like `auth`, `inspect`, and `status` work without an API key, the search engine requires a valid personal Gemini key.

1. Obtain a personal API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Copy the configuration template to create `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` in a terminal editor (e.g., `nano .env` or `gedit .env`) and configure:
   ```env
   # AI Search Engine Configuration (Required for MCQs and Code Reasoning)
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-flash-lite-latest
   ```
4. **Configuration Details:**
   - `AI_PROVIDER=gemini`: The project defaults to `none`. Setting `AI_PROVIDER=gemini` is **required** to activate the search engine.
   - `GEMINI_API_KEY`: Your personal secret key from Google AI Studio. Never share or commit this key.
   - `GEMINI_MODEL`: Defaults to `gemini-flash-lite-latest`.
   - **Security:** The application automatically loads `.env` on startup via Pydantic Settings. The `.env` file is strictly excluded from Git tracking via `.gitignore` (line 70).

### Step 7: Install Browser Dependencies (Playwright Chromium & System Libraries)
1. Install Playwright's Chromium browser binary:
   ```bash
   playwright install chromium
   ```
2. Install Chromium system shared libraries (NSS, Cairo, Pango, ATK, ALSA):
   ```bash
   playwright install-deps chromium
   ```
   *(Playwright will prompt for your `sudo` password to install any missing DNF packages automatically. If you prefer to install them manually: `sudo dnf install -y alsa-lib at-spi2-atk cairo cups-libs dbus-libs expat glib2 gtk3 libX11 libXcomposite libXdamage libXext libXfixes libXrandr libdrm libgbm libxcb libxshmfence mesa-libgbm nss nspr pango`).*

### Step 8: Authenticate with CodeChef
Launch the headful browser to log in to your CodeChef account:
```bash
course-automation auth --timeout 300
```
1. A visible Chromium window will open to `https://www.codechef.com/login`.
2. **You must manually log in** inside the opened browser window using your CodeChef credentials, Google OAuth, or GitHub.
3. The CLI monitors open browser tabs for authenticated course indicators and session cookies.
4. Once detected, the CLI prints `[SUCCESS] Authentication detected! Session saved to profile.` and disconnects cleanly.
5. *Troubleshooting:* If signing in via Google/GitHub opens a new tab, ensure you navigate to your course URL (`https://www.codechef.com/learn/course/<slug>`) so the detector can identify course elements. Do not close the browser manually. To diagnose issues without exposing secrets, run: `LOG_LEVEL=DEBUG course-automation auth --timeout 300`.

### Step 9: Verify Your Search Engine Setup
Do not assume the search engine is working merely because the CLI opens. Perform a safe, non-destructive connection test:
```bash
course-automation config --check-ai
```
**Expected Output:**
```text
[AI Check] Testing Gemini API connection...
[AI Check] Gemini search & reasoning engine connected successfully!
  Model: gemini-flash-lite-latest
  Ping response: pong
```

You can also view the resolved local configuration paths:
```bash
course-automation config
```

### Step 10: Common Fedora Troubleshooting
- **Python version error (`requires-python >= 3.10`):** Install Python 3.12 explicitly: `sudo dnf install -y python3.12 python3.12-devel`, then recreate `.venv` with `python3.12 -m venv .venv`.
- **`externally-managed-environment` pip error:** Ensure your virtual environment is activated before installing: `source .venv/bin/activate`.
- **Playwright missing library error:** Run `playwright install-deps chromium`. On Wayland desktops, ensure XWayland is available: `sudo dnf install -y xorg-x11-server-Xwayland`.
- **Permission errors on `~/.course_automation`:** Restore ownership: `sudo chown -R $USER:$USER ~/.course_automation`.
- **Missing test dependencies:** Run `pip install -e ".[dev]"` before running `pytest -v`.

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
Clone the repository and navigate into the project directory:
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

### Step 4: Upgrade Pip and Install Dependencies (including AI Search Engine)
Upgrade `pip` to the latest version and install the project with AI search dependencies in editable mode using `python3.12`:
```bash
python3.12 -m pip install --upgrade pip
pip install -e ".[ai]"
```
> **Tip for Contributors / Testers:** If you plan to run automated tests, install development dependencies:
> ```bash
> pip install -e ".[dev]"
> ```

### Step 5: Configure the Gemini API (Required for Search Engine)
> [!IMPORTANT]
> **Mandatory Step for Search & Deduction Features:**
> Configuring your Gemini API key is required to use the project's AI-powered search and deduction engine (answering quizzes, MCQs, and coding challenges). While non-API commands like `auth`, `inspect`, and `status` work without an API key, the search engine requires a valid personal Gemini key.

1. Obtain a personal API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Copy the template to create your local `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` in your editor (e.g., `nano .env` or VS Code) and configure:
   ```env
   # AI Search Engine Configuration (Required for MCQs and Code Reasoning)
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-flash-lite-latest
   ```
4. **Configuration Details:**
   - `AI_PROVIDER=gemini`: The project defaults to `none`. You **must** set `AI_PROVIDER=gemini` to activate the AI search engine.
   - `GEMINI_API_KEY`: Your personal secret API key from Google AI Studio. Never share or commit this key.
   - `GEMINI_MODEL`: Defaults to `gemini-flash-lite-latest`.
   - **Security:** The application automatically loads `.env` on startup via Pydantic Settings. The `.env` file is strictly excluded from Git tracking via `.gitignore` (line 70).

### Step 6: Install the Required Playwright Browser
Download the standalone Chromium browser binary used by Playwright:
```bash
playwright install chromium
```

### Step 7: Authenticate with CodeChef
Authenticate once using the headful browser to create and persist your session:
```bash
course-automation auth --timeout 300
```
- A visible Chromium browser window will open to `https://www.codechef.com/login`.
- **Manually log in** using your CodeChef username/password, Google OAuth, or GitHub.
- Once detected, the CLI saves your session to `~/.course_automation/browser_profile` and closes the browser cleanly.

### Step 8: Verify Search Engine Setup
Run the active connection test to verify your Gemini API key and model connectivity:
```bash
course-automation config --check-ai
```
**Expected Output:**
```text
[AI Check] Testing Gemini API connection...
[AI Check] Gemini search & reasoning engine connected successfully!
  Model: gemini-flash-lite-latest
  Ping response: pong
```

You can also check resolved configuration paths and status:
```bash
course-automation config
```

### Step 9: Run Automated Tests
Verify that all unit and integration tests pass offline:
```bash
pytest -v
```
*(All 76 offline tests should pass).*

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

### Step 5: Upgrade Pip & Install Dependencies (including AI Search Engine)
```powershell
python -m pip install --upgrade pip
pip install -e ".[ai]"
```
*(Or install dev dependencies for running tests: `pip install -e ".[dev]"`).*

### Step 6: Configure the Gemini API (Required for Search Engine)
> [!IMPORTANT]
> **Mandatory Step for Search & Deduction Features:**
> Configuring your Gemini API key is required to use the project's AI-powered search and deduction engine (answering quizzes, MCQs, and coding challenges). While non-API commands like `auth`, `inspect`, and `status` work without an API key, the search engine requires a valid personal Gemini key.

1. Obtain a personal API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Copy the template to create `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `.env` in Notepad and configure:
   ```env
   # AI Search Engine Configuration (Required for MCQs and Code Reasoning)
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-flash-lite-latest
   ```
4. **Configuration Details:**
   - `AI_PROVIDER=gemini`: The project defaults to `none`. You **must** set `AI_PROVIDER=gemini` to activate the AI search engine.
   - `GEMINI_API_KEY`: Your personal secret API key from Google AI Studio. Never share or commit this key.
   - `GEMINI_MODEL`: Defaults to `gemini-flash-lite-latest`.
   - **Security:** The application automatically loads `.env` on startup via Pydantic Settings. The `.env` file is strictly excluded from Git tracking via `.gitignore` (line 70).

### Step 7: Install the Playwright Chromium Browser
```powershell
playwright install chromium
```

### Step 8: Authenticate with CodeChef
Launch the headful browser to log in to your CodeChef account:
```powershell
course-automation auth --timeout 300
```
- A visible Chromium browser window will open to `https://www.codechef.com/login`.
- **Manually log in** using your CodeChef credentials, Google OAuth, or GitHub.
- Once detected, the CLI saves your session to `%USERPROFILE%\.course_automation\browser_profile` and closes the browser cleanly.

### Step 9: Verify Search Engine Setup & Run Tests
Run the active connection test to verify your Gemini API key and model connectivity:
```powershell
course-automation config --check-ai
```
**Expected Output:**
```text
[AI Check] Testing Gemini API connection...
[AI Check] Gemini search & reasoning engine connected successfully!
  Model: gemini-flash-lite-latest
  Ping response: pong
```

You can also inspect resolved paths and run the offline test suite:
```powershell
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
| `pip install -e ".[ai]"` | Installs Google Gemini AI provider dependencies (`google-genai`). | Required for AI search & deduction engine. |
| `playwright install chromium` | Downloads the headless/headful Chromium browser binary. | Required before first browser run. |
| `course-automation --help` | Validates CLI entry point and displays commands. | Smoke test installation. |
| `course-automation config` | Displays resolved configuration paths and environment settings. | Diagnostics and path verification. |

---

## Authentication & Browser Session Handling

Course Automation uses a persistent local browser profile to maintain your logged-in state without storing your plaintext username or password.

### Step 1: Perform One-Time Login
Course Automation uses an isolated persistent browser profile to maintain your logged-in state across CLI runs without storing your plaintext username or password.

To authenticate, launch a visible (headful) browser window from your terminal:
```bash
course-automation auth
```

By default, the CLI waits up to **300 seconds** for you to sign in. If you need more time (for two-factor authentication or slower connections), specify `--timeout`:
```bash
course-automation auth --timeout 600
```

#### Supported Options for `auth`
- `--timeout <int>`: Maximum wait time in seconds for manual login (default: `300`).
- `--site <str>`: Target platform (default: `codechef`).
- `--help`: Display command usage details.

*(Note: Unsupported flags like `--manual` do not exist. Authentication is always interactive and headful.)*

#### How Authentication Works
1. A headful Chromium browser window automatically opens to the CodeChef login page.
2. **You must manually log in** inside the opened browser window using your preferred login method (CodeChef credentials, Google OAuth, or GitHub). The CLI does not read, intercept, or enter your passwords.
3. The CLI monitors open browser tabs for authenticated course indicators (such as user avatar elements, course syllabus cards, and session cookies).
4. Once authentication is detected, the CLI prints:
   ```text
   [SUCCESS] Authentication detected! Session saved to profile.
   ```
   and closes the browser cleanly, persisting your session in `~/.course_automation/browser_profile` (or `%USERPROFILE%\.course_automation\browser_profile` on Windows).

### Secure Handling & Transparency
> [!IMPORTANT]
> **No Application-Level Encryption:**
> Browser cookies and session data are stored locally in standard Chromium format inside `~/.course_automation/browser_profile` (or `%USERPROFILE%\.course_automation\browser_profile` on Windows).
>
> They are **NOT encrypted at rest by the application**. Security is maintained strictly through your operating system's local user account permissions.
> - **Never** commit, publish, or share your `~/.course_automation` directory.
> - The `.gitignore` file in this repository strictly excludes all `.course_automation` and session directories.

---

## Configuration & Gemini API Setup (Required for Search Engine)

Configuring the Google Gemini API is a **mandatory installation step** to use the project's AI-powered search and reasoning engine. Without a valid API key, question reasoning and coding search cannot function.

> [!IMPORTANT]
> **API Key Requirement & Feature Separation:**
> - **Required for Search & Deduction:** Accessing automated question-answering on quizzes (MCQs) and generating code solutions requires a valid personal Gemini API key.
> - **Basic Features Run Without API:** Authentication (`course-automation auth`), syllabus inspection (`course-automation inspect`), offline progress tracking (`course-automation status`), and theory-only lesson advancement (`course-automation solve --theory-only`) do not require an API key.

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
| **Automated Test Suite** (`pytest -v`) | **No** | All 76 unit and integration tests run 100% offline using synthetic fixtures and mocks. |
| **Multiple-Choice Questions (MCQs)** (`course-automation solve`) | **Requires Key** | **With API key:** Evaluates options against lesson context and selects high-confidence answers.<br>**Without API key:** Discovers options and logs `INSPECTED_NO_AI` without guessing. |
| **Coding Exercises & Labs** (`course-automation solve`) | **Requires Key** | **With API key:** Generates syntactic solutions matching the requested problem statement.<br>**Without API key:** Inspects starter code and logs `INSPECTED_NO_AI`. |

> [!NOTE]
> **Architecture of the Search Engine:**
> Course Automation uses the Google Gemini API (`gemini-flash-lite-latest` via the official `google-genai` SDK) as its underlying reasoning and search engine over lesson contexts and problem prompts. There is **no external web crawler or `search.answer` endpoint**; all conceptual search and answer deduction are performed by Gemini.

---

### Step-by-Step Gemini API Setup

Follow these steps to configure your personal Gemini API key securely.

#### 1. Obtain a Personal Google Gemini API Key
1. Navigate to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your personal Google account.
3. Click **Create API Key** and copy your generated key string.

> [!IMPORTANT]
> **User Responsibility & Quota Rules:**
> - **Each user must configure their own personal API key.** Never share your key or commit it to Git repositories.
> - Google AI Studio accounts provide developer access with per-minute and per-day rate limits.
> - The default model `gemini-flash-lite-latest` is eligible for Google's free tier. The project maintainers do not supply or guarantee free, unlimited API access.

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

#### 3. Edit `.env` with Required Variables
Open `.env` in any text editor and configure the required settings:
```env
# AI Search Engine Configuration (Required for MCQs and Code Reasoning)
AI_PROVIDER=gemini

# Your personal Google AI Studio API key (supports GEMINI_API_KEY or GOOGLE_API_KEY)
GEMINI_API_KEY=your_gemini_api_key_here

# Model identifier
GEMINI_MODEL=gemini-flash-lite-latest
```

**Variable Breakdown:**
- `AI_PROVIDER=gemini`: The application defaults to `none`. You **must** set `AI_PROVIDER=gemini` to activate the AI search engine.
- `GEMINI_API_KEY`: Your secret key from Google AI Studio. Never use dummy or real keys in public files.
- `GEMINI_MODEL`: Defaults to `gemini-flash-lite-latest`.

#### 4. Install the AI Search Engine Package
Install the official `google-genai` SDK and AI dependencies:
```bash
pip install -e ".[ai]"
```

#### 5. Verify Your Search Engine Setup
Do not assume your API key is functioning simply because the CLI launches. Run the dedicated, non-destructive health-check test:
```bash
course-automation config --check-ai
```
**Expected Output:**
```text
[AI Check] Testing Gemini API connection...
[AI Check] Gemini search & reasoning engine connected successfully!
  Model: gemini-flash-lite-latest
  Ping response: pong
```

You can also view your loaded settings and masked key status:
```bash
course-automation config
```
You should see:
- `AI Provider: gemini`
- `Gemini Model: gemini-flash-lite-latest`
- `Gemini API Key: [SET (REDACTED)]`

To test the full question-solving pipeline safely without modifying your real course progress, run a dry-run:
```bash
course-automation solve "https://www.codechef.com/learn/course/<slug>" --dry-run
```

---

### Understanding API Limits & Errors

| Error / Symptom | Root Cause | Solution |
|---|---|---|
| `GEMINI_API_KEY is not set` / `INSPECTED_NO_AI` | Missing key in `.env` or `AI_PROVIDER=none`. | Ensure `.env` contains `AI_PROVIDER=gemini` and a valid `GEMINI_API_KEY`. |
| `400 API_KEY_INVALID` / `403 PERMISSION_DENIED` | Key string has a typo, extra whitespace, or was revoked. | Generate a fresh key at Google AI Studio and update `.env`. |
| `429 RESOURCE_EXHAUSTED` | Exceeded Google AI Studio free tier rate limits (requests/minute or quota/day). | Wait 60 seconds for the rate limit window to reset, or run with `--theory-only` to bypass AI calls. |
| `404 NOT_FOUND: models/...` | The configured model name is deprecated or misspelled. | Ensure `GEMINI_MODEL=gemini-flash-lite-latest` in `.env`. |

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

### 3. Login Succeeds in Browser but CLI Keeps Waiting and Times Out
**Symptom:** You manually log in to CodeChef in the opened browser window and the course or dashboard is visibly displayed, but the terminal continues waiting and eventually reports: `Authentication was not completed within the time limit.`

**Potential Causes:**
- **Multi-Tab / OAuth Redirection:** Signing in via Google or GitHub OAuth may open a popup or redirect in a new tab, leaving the initial tab on an intermediate URL while the course loads in another tab.
- **Course Page Not Loaded:** The browser remained on an account settings, payment, or home page rather than an active course or learning dashboard.
- **Browser Window Closed Early:** Closing the browser window manually before the CLI confirms authentication interrupts session verification.

**Solution:**
1. **Keep the browser open:** Do not close the Chromium browser manually. The tool will automatically close it and save the session once authentication is verified.
2. **Navigate to your course:** If redirected to the home page or a blank tab, navigate directly to your course (e.g. `https://www.codechef.com/learn/course/...`) so the detector can identify course elements.
3. **Extend the timeout:** If your login flow or 2FA requires more time, increase the timeout:
   ```bash
   course-automation auth --timeout 600
   ```

**Collecting Safe Diagnostic Logs:**
To inspect what the detector sees during authentication without leaking any secrets, run the command with debug logging enabled:
- **macOS / Linux:**
  ```bash
  LOG_LEVEL=DEBUG course-automation auth --timeout 300
  ```
- **Windows PowerShell:**
  ```powershell
  $env:LOG_LEVEL="DEBUG"; course-automation auth --timeout 300
  ```

> [!CAUTION]
> **Privacy Notice for Reporting Issues:**
> When reporting an authentication issue on GitHub:
> - The built-in diagnostic logs automatically sanitize query parameters and redact sensitive tokens using `SanitizingFilter`. Diagnostic logs will only display sanitized URL paths and state transitions (e.g. `LOGIN_PAGE -> AUTHENTICATED`).
> - **NEVER** attach or copy files from your `~/.course_automation/browser_profile` directory. This directory contains raw Chromium cookie databases and local storage.
> - **NEVER** share your password, session cookies, or `.env` file.
> - *Note: Offline synthetic unit tests verify detection logic across mock pages, but real-world site structure updates or third-party OAuth flows should always be validated live.*

### 4. Windows PowerShell: Script Execution Disabled
**Symptom:** `File ... .venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
**Solution:** Set the execution policy for the current process:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

### 5. Windows: `python` or `pip` is Not Recognized
**Symptom:** `'python' is not recognized as an internal or external command...`
**Solution:**
- Ensure Python was installed with **"Add python.exe to PATH"** checked.
- Alternatively, use the Windows Python launcher: `py -3 -m venv .venv`.

### 6. CDP Protocol Error / Port 9222 Conflict
**Symptom:** `Protocol error (Browser.setDownloadBehavior)` or unable to connect to CDP.
**Solution:** Leave `BROWSER_CDP_URL=` empty in your `.env` file. The tool will use its isolated persistent browser profile automatically.

### 7. Gemini Model Not Found
**Symptom:** `404 NOT_FOUND: models/... is no longer available`
**Solution:** In `.env`, ensure you are using an active model:
```env
GEMINI_MODEL=gemini-flash-lite-latest
```

### 8. macOS: Python 3.9 Error during `pip install -e .`
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

### 9. CLI Reports `INSPECTED_NO_AI` on Quizzes or Coding Labs
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

### 10. Invalid API Key / `400 API_KEY_INVALID` or `403 PERMISSION_DENIED`
**Symptom:** `google.genai.errors.ClientError: 400 API_KEY_INVALID` or `403 PERMISSION_DENIED`.
**Cause:** The configured `GEMINI_API_KEY` has a typo, was revoked, or lacks permission for the Gemini API.
**Solution:**
1. Generate a fresh API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Update `GEMINI_API_KEY=your_new_key` in `.env`.
3. Test with `course-automation config`.

### 11. Rate Limit / Quota Exceeded (`429 RESOURCE_EXHAUSTED`)
**Symptom:** `google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED` (Quota exceeded for metric).
**Cause:** Exceeded Google AI Studio's free tier requests-per-minute or daily quota.
**Solution:**
- Wait 60 seconds before retrying.
- Or pass `--no-ai` / `--theory-only` to continue reading theory lessons without consuming API calls.

---

## Testing & Contributor Instructions

### Running Tests
All 76 tests in the test suite run **100% offline** using synthetic mocks and isolated local databases:
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
