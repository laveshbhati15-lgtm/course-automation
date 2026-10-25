# Course Automation

A standalone, modular, open-source Python application for automated course inspection, progress tracking, and exercise assistance on learning platforms (beginning with CodeChef).

Built to be **100% portable and independent** — runs without requiring Antigravity, proprietary daemons, or paid cloud services.

---

## Universal Course Compatibility

Course Automation is designed to work with **any compatible CodeChef Learn course across different subjects, semesters, and programming languages**:

- **Any Subject & Curriculum:** Automatically parses courses with arbitrary structures (Units, Modules, Chapters, or Lessons) — from *Object-Oriented Programming* to *Advanced Data Structures & Algorithms*, *Operating Systems*, and *Core Languages*.
- **Multi-Language Coding Labs:** Dynamically detects the required programming language (**C++, Java, C, Python, JavaScript, and more**) from problem metadata, the page selector dropdown, or editor models.
- **Active Browser Tab Auto-Detection:** Switch subjects or courses simply by navigating in your browser! Running `course-automation inspect` without arguments automatically discovers the currently active CodeChef course and activity.
- **Interactive Module Selection:** Select specific units or modules to inspect or solve using `--select-module` or `--module <id>`.
- **Honest Progress Verification:** Correctly identifies locked activities (`LOCKED`) and unsupported formats (`UNSUPPORTED_FORMAT`) instead of falsifying progress.

---

## Architecture Overview

```
course-automation/
├── src/course_automation/
│   ├── cli.py                     # Typer & Rich CLI with auto-detection & module selection
│   ├── config.py                  # Pydantic Settings (.env configuration)
│   ├── logger.py                  # Sanitized logging with regex secret masking
│   ├── safety.py                  # Consequential action safety gates
│   ├── browser/
│   │   ├── session.py             # Playwright persistent context & CDP connector
│   │   ├── auth.py                # DOM-based auth state detector & login flow
│   │   ├── active_session.py      # Active browser tab discovery & URL parsing
│   │   └── browser_use_bridge.py  # Bridge & docs for Browser Use agents
│   ├── ai/
│   │   ├── base.py                # Abstract BaseAIProvider interface
│   │   ├── sanitizer.py           # Regex credential scrubber
│   │   └── gemini.py              # Google Gemini provider (optional)
│   ├── sites/
│   │   ├── base.py                # Abstract BaseSiteAdapter
│   │   └── codechef/
│   │       ├── adapter.py         # CodeChefAdapter dispatching to handlers
│   │       ├── syllabus.py        # Generic syllabus API & DOM parser
│   │       ├── editor.py          # Monaco & Ace editor controller
│   │       ├── verdicts.py        # Verdict polling state machine
│   │       └── handlers/          # Modular activity handlers
│   │           ├── base.py        # BaseActivityHandler
│   │           ├── coding.py      # Coding problems & labs
│   │           ├── quiz.py        # Multiple-choice quizzes
│   │           ├── lesson.py      # Theory & reading lessons
│   │           └── locked.py      # Locked & unsupported activities
│   └── storage/
│       ├── models.py              # Pydantic schemas (courses, modules, activities)
│       └── db.py                  # SQLite database manager (~/.course_automation/)
├── tests/                         # Automated pytest suite (38 passing tests)
├── docs/                          # Architecture and development guides
└── pyproject.toml                 # Package definition and CLI entrypoint
```

---

## Installation

### 1. Clone repository
```bash
git clone https://github.com/your-username/course-automation.git
cd course-automation
```

### 2. Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
python -m pip install --upgrade pip
# Base install:
pip install -e .

# With optional AI and test dependencies:
pip install -e ".[dev]"

# Install Playwright browser dependencies (if not already installed):
playwright install chromium
```

---

## Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `none` | Active AI provider (`gemini` or `none`). Core navigation & inspection work without AI. |
| `GEMINI_API_KEY` | None | API key from Google AI Studio (optional). |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Default Gemini model. |
| `BROWSER_HEADLESS` | `false` | Run browser in headless mode. |
| `BROWSER_USER_DATA_DIR` | `~/.course_automation/browser_profile` | Directory for persistent session & cookies. |
| `BROWSER_CDP_URL` | None | Optional CDP endpoint (e.g., `http://127.0.0.1:9222`). |
| `DATABASE_PATH` | `~/.course_automation/progress.db` | Local SQLite progress tracking database. |
| `DRY_RUN` | `false` | When true, simulate actions without submitting. |

---

## CLI Usage

### 1. Authenticate (One-time setup)
Open a browser session to log in to your account. Your credentials and cookies remain strictly inside your local profile directory (`~/.course_automation/browser_profile`):
```bash
course-automation auth
```

### 2. Inspect a Course
**Automatic Tab Detection (No URL needed):**
Open any CodeChef course in your browser, then run:
```bash
course-automation inspect
```
The application detects the open course, queries the syllabus, and renders a structured progress table.

**Explicit Course URL:**
```bash
# Example 1: Java Object-Oriented Programming (Semester 3)
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2

# Example 2: C++ Advanced Data Structures & Algorithms
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2

# Example 3: C Data Structures
course-automation inspect https://www.codechef.com/learn/course/cu-adsa-sem3-2026-b1

# Example 4: Python for Beginners
course-automation inspect https://www.codechef.com/learn/course/python
```

**Options:**
- `--select-module`: Interactively choose which unit or module to display.
- `--incomplete-only`: Filter out already completed activities.
- `--json`: Output raw structured JSON.

### 3. Query Saved Courses Offline
Query all tracked courses or view details for a specific course from SQLite without opening the browser:
```bash
# List all saved courses and their completion percentages
course-automation status

# View detailed progress for a specific course
course-automation status cu-oops-sem3-2026-c2
```

### 4. Process / Assist with Activities
Process incomplete activities with safety approval prompts:
```bash
# Auto-detect active course and simulate (dry run):
course-automation solve --dry-run

# Select a specific module interactively:
course-automation solve --select-module

# Target a specific problem:
course-automation solve https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2 --activity INSSRTASCD
```

---

## Activity Handlers

- **`CodingActivityHandler`:** Handles Monaco and Ace web IDEs across any programming language (**C++, Java, C, Python**). Uses base64 buffer injection to prevent quotation or newline corruption, checks compilation, and polls judge verdicts.
- **`QuizActivityHandler`:** Extracts multiple-choice questions and options, generates suggestions with explanations, and enforces human review before proceeding.
- **`TheoryLessonActivityHandler`:** Inspects reading articles and video lessons without fabricating false completion.
- **`LockedOrUnsupportedActivityHandler`:** Identifies locked assessments or prerequisite gates honestly (`LOCKED_SKIPPED`).

---

## Security & Privacy

1. **Zero Secret Leaks:** Built-in regex filters redact API keys, tokens, and authorization headers from all logs, console output, and AI prompts.
2. **Local Session Storage:** Browser profiles and cookies are stored solely in your local user directory. They are never committed or transmitted.
3. **Safety Confirmation Gates:** Interactive terminal prompt required before any submission unless `--auto-approve` is passed.
4. **No IDE Lock-In:** Requires no proprietary IDE plugins, Antigravity daemons, or background services.

---

## Running Automated Tests

Run the full automated test suite (38 unit & regression tests):
```bash
pytest -v
```

---

## License

This project is licensed under the [MIT License](LICENSE).
