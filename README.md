# Course Automation

A standalone, modular, open-source Python application for automated course inspection, progress tracking, theory concept reading, and exercise assistance on web learning platforms (featuring full support for CodeChef Learn).

Built to be **100% portable, secure, and vendor-independent** — runs entirely on your local machine without requiring proprietary IDE plugins, cloud daemons, or paid subscriptions.

---

## Key Highlights

- **Universal Course Compatibility:** Works with **any** CodeChef Learn course URL (DBMS, OOPS, Data Structures & Algorithms, Python, C, Java, etc.) — zero hard-coded course IDs or fixed structures.
- **Dynamic Content & Theory Concept Reading:** Smoothly scrolls through theory lessons to trigger lazily loaded dynamic content, code blocks, and MathJax widgets, locating and clicking enabled **Next** or **Continue** buttons.
- **Multiple-Choice Question (MCQ) Automation:**
  - Extracts full question statements (combining problem prompts and MCQ instructions) and candidate radio options with DOM locators.
  - Generates structured reasoning and candidate selection via AI provider.
  - **Human Review Safeguard:** Halts and prompts for user terminal approval whenever confidence is below 85% instead of guessing.
  - Verifies visual checked state (`is_checked=True`), clicks submit, and parses platform feedback banners (`ACCEPTED` vs `WRONG_ANSWER`).
  - Seamlessly falls back to theory reading mode for concept pages that do not contain radio inputs.
- **Multi-Language Coding Labs:** Automates Monaco and Ace code editors across **C++, Java, C, and Python** using base64 buffer injection to prevent quotation or newline corruption.
- **Multi-Activity Traversal & Checkpointing:** Iterates sequentially through course activities using SQLite checkpointing so already-completed lessons are never redundantly reprocessed.
- **Safety by Default:** Full dry-run mode (`--dry-run`) inspects pages and reasons about solutions without submitting anything or advancing lessons. Consequential actions require explicit user approval.
- **Zero Credential Leaking:** Automatic regex sanitization scrubs API keys, authorization tokens, and personal secrets from all terminal logs and AI prompts.

---

## Architecture Overview

```
course-automation/
├── src/course_automation/
│   ├── cli.py                     # Typer CLI commands (inspect, solve, status, auth, config)
│   ├── config.py                  # Pydantic Settings configuration from environment and .env
│   ├── logger.py                  # Sanitized logging with regex credential redaction
│   ├── safety.py                  # Confirmation gates for live or consequential actions
│   ├── browser/
│   │   ├── session.py             # Playwright persistent context & CDP connector
│   │   ├── auth.py                # DOM-based login state detection
│   │   ├── active_session.py      # Active browser tab detection
│   │   └── browser_use_bridge.py  # Bridge for Browser Use agent automation
│   ├── ai/
│   │   ├── base.py                # BaseAIProvider interface and MCQReasoningResult
│   │   ├── sanitizer.py           # Credential scrubber
│   │   └── gemini.py              # Optional Google Gemini integration
│   ├── sites/
│   │   ├── base.py                # Abstract BaseSiteAdapter
│   │   └── codechef/
│   │       ├── adapter.py         # CodeChef site adapter
│   │       ├── syllabus.py        # Generic syllabus API & DOM fallback parser
│   │       ├── editor.py          # Monaco and Ace code editor controller
│   │       ├── verdicts.py        # Submission verdict polling state machine
│   │       ├── navigator.py       # Sequential multi-lesson traversal controller
│   │       └── handlers/          # Modular activity handlers
│   │           ├── base.py        # BaseActivityHandler
│   │           ├── coding.py      # Coding problems & labs
│   │           ├── quiz.py        # Multiple-choice quizzes
│   │           ├── lesson.py      # Theory reading concepts
│   │           └── locked.py      # Locked & unsupported assessments
│   └── storage/
│       ├── models.py              # Pydantic schemas (courses, modules, activities)
│       └── db.py                  # SQLite database manager (~/.course_automation/)
├── tests/                         # Automated pytest suite (60 passing tests)
├── docs/                          # Architecture and development guides
└── pyproject.toml                 # Package definition and CLI entrypoint
```

---

## System Requirements

- **Operating System:** macOS (Apple Silicon or Intel), Linux (Ubuntu, Debian, Fedora, Arch), or Windows 10/11 (WSL2 recommended).
- **Python:** 3.10, 3.11, or 3.12.
- **Browser:** Chromium (automatically installed via Playwright).
- **RAM:** Minimum 2 GB (4 GB recommended for browser automation).

---

## Installation Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/course-automation.git
cd course-automation
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip

# Install package in editable mode with development & AI extras:
pip install -e ".[dev,ai]"

# Install Chromium browser binary:
playwright install chromium
```

---

## Configuration

Copy the template configuration to create your local `.env` file:
```bash
cp .env.example .env
```

### Configuration Options

| Environment Variable | Default Value | Description |
|---|---|---|
| `AI_PROVIDER` | `none` | Active AI provider (`gemini` or `none`). Inspection and theory reading work 100% without AI. |
| `GEMINI_API_KEY` | None | API key from Google AI Studio (supports `GEMINI_API_KEY` or `GOOGLE_API_KEY`). |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Gemini model identifier (e.g. `gemini-flash-lite-latest`, `gemini-flash-latest`). |
| `BROWSER_HEADLESS` | `false` | Run browser in headless mode (`true`/`false`). Recommended: `false` for transparency. |
| `BROWSER_USER_DATA_DIR` | `~/.course_automation/browser_profile` | Directory for persistent browser session and cookies. |
| `BROWSER_CDP_URL` | None | Optional CDP URL to attach to an existing Chrome browser (e.g., `http://127.0.0.1:9222`). |
| `DATABASE_PATH` | `~/.course_automation/progress.db` | Local SQLite database for syllabus caching and checkpointing. |
| `DRY_RUN` | `false` | When true, simulate actions without submitting or advancing. |
| `LOG_LEVEL` | `INFO` | Console log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## AI Provider Setup & Costs

- **AI is completely optional:** You can inspect syllabi, check progress, offline query databases, and read theory lessons with `AI_PROVIDER=none`.
- **Google Gemini:** If enabled, you need an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
  - The default model is `gemini-flash-lite-latest`, which qualifies for Google's generous free tier (no credit card required for standard rate limits).
  - All prompts are strictly scrubbed of API keys, authentication tokens, and personal secrets before transmission.

---

## Usage Guide & Realistic Examples

### 1. One-Time Authentication
Launch a persistent headful browser window to log in to your account. Your authenticated session is stored securely in `~/.course_automation/browser_profile` and persists across CLI runs:
```bash
course-automation auth
```

### 2. Inspecting Course Progress

**Auto-Detect Active Tab in Browser:**
If you already have a CodeChef course open in your browser, inspect it without specifying a URL:
```bash
course-automation inspect
```

**Inspect by Explicit Course URL:**
```bash
# Database Management Systems (DBMS)
course-automation inspect https://www.codechef.com/learn/course/cu-dbms-sem3-2026-c2

# Object-Oriented Programming (OOPS)
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2

# Advanced Data Structures & Algorithms (ADSA)
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2
```

**Inspection Flags:**
- `--incomplete-only`: Filter out completed lessons to focus on remaining tasks.
- `--select-module`: Interactively choose which unit or module to inspect.
- `--json`: Output raw structured JSON for integration with other tools.

### 3. Querying Progress Offline (SQLite)
Query course syllabi and completion status from the local database without opening a browser:
```bash
# List all tracked courses and overall progress percentages
course-automation status

# View detailed unit-by-unit breakdown for a specific course
course-automation status cu-dbms-sem3-2026-c2
```

### 4. Processing Activities (Theory, Quizzes & Coding)

**Safe Simulation Mode (Dry-Run):**
Inspect pages, scroll through reading content, extract MCQ options, and reason about answers without clicking or submitting:
```bash
# Safe simulation on theory and MCQs (limit to 5 activities)
course-automation solve https://www.codechef.com/learn/course/cu-dbms-sem3-2026-c2 --theory-only --max-activities 5 --dry-run

# Dry-run on a single specific quiz or lesson
course-automation solve https://www.codechef.com/learn/course/cu-dbms-sem3-2026-c2 --activity CLGDBMSP08 --dry-run
```

**Live Traversal with Interactive Confirmation:**
Prompts you for approval before submitting any quiz answer or code solution:
```bash
course-automation solve https://www.codechef.com/learn/course/cu-dbms-sem3-2026-c2 --theory-only --max-activities 5
```

**Automated Progression (Bypassing Prompts):**
Bypasses high-level activity confirmation prompts while still enforcing the low-confidence safeguard:
```bash
course-automation solve https://www.codechef.com/learn/course/cu-dbms-sem3-2026-c2 --theory-only --max-activities 10 --auto-approve
```

---

## Security & Privacy Safeguards

1. **Zero Secret Exposure:** Built-in regex filters redact Google API keys, Bearer tokens, and authorization headers from all logs, console outputs, and AI prompts.
2. **Local Session Isolation:** Cookies, storage, and database files remain strictly inside your local user directory (`~/.course_automation/`). They are never committed, uploaded, or transmitted.
3. **Safety Confirmation Gates:** Consequential actions require explicit terminal confirmation unless `--auto-approve` is passed.
4. **Non-Mutating Dry-Run:** In dry-run mode (`--dry-run`), button clicking and form submissions are completely disabled in the DOM.

---

## Known Limitations & Unsupported Scenarios

- **Locked Assessments:** Activities locked by platform prerequisites or scheduling are recognized honestly as `LOCKED_SKIPPED` and will not be bypassed.
- **Proctored / External Exams:** Secure university tests or exams with webcam monitoring or lockdown browsers are unsupported.
- **CAPTCHAs:** In the rare event of a CAPTCHA challenge, human manual completion in the browser window is required.
- **Non-CodeChef Platforms:** While the codebase is architected with an abstract `BaseSiteAdapter`, only CodeChef Learn is currently implemented.

---

## Troubleshooting Guide

### 1. Browser Error: `Executable doesn't exist`
**Cause:** Playwright browser binaries are not installed.
**Fix:**
```bash
playwright install chromium
```

### 2. Session Expired or `403 Not Authorised`
**Cause:** CodeChef session cookie has expired or was logged out.
**Fix:** Run the authentication helper to refresh your session:
```bash
course-automation auth
```

### 3. Model Error: `404 NOT_FOUND: models/gemini-2.5-flash is no longer available`
**Cause:** Google AI Studio deprecated older model identifiers.
**Fix:** Update `GEMINI_MODEL` in your `.env` file:
```env
GEMINI_MODEL=gemini-flash-lite-latest
```

### 4. CDP Connection: `Protocol error (Browser.setDownloadBehavior)`
**Cause:** Chrome was started on port 9222 without an open tab or in an incompatible context state.
**Fix:** Leave `BROWSER_CDP_URL=` empty in `.env`. The application will launch an isolated persistent browser profile automatically.

---

## Running Automated Tests

The test suite runs entirely offline using synthetic HTML fixtures and mocked network responses without contacting external servers or consuming account quotas:

```bash
# Run all 60 tests
pytest -v

# Run with test failure details
pytest -v --tb=short
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup instructions, architecture guides, and coding guidelines. All participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Disclaimer & Compliance Notice

> [!IMPORTANT]
> **Educational & Personal Use Only:** Course Automation is an open-source development tool intended solely for personal study management, progress inspection, and assisting with coursework navigation.
>
> Users are strictly responsible for complying with CodeChef's Terms of Service, their academic institution's Honor Code, and all applicable academic integrity policies. The maintainers and contributors do not endorse academic dishonesty and assume no liability for misuse, account penalties, or honor code violations.

---

## License

This project is licensed under the [MIT License](LICENSE).
