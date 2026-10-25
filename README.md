# Course Automation

A standalone, modular, open-source Python application for automated inspection, progress tracking, and exercise assistance on learning platforms (beginning with CodeChef).

Built to be **100% portable and independent** — requires no IDE extensions, proprietary daemons, or paid cloud services.

---

## Key Features

- **Course Inspection & Syllabus Mapping:** Automatically discovers course structure, chapters, modules, and learning activities via platform APIs with robust DOM fallbacks.
- **Progress Tracking & Verification:** Distinguishes between completed, in-progress, locked, and untouched activities without relying on false assumptions.
- **Local Checkpoints & SQLite Persistence:** Saves course audits, activity statuses, and submission records locally for offline querying and interruption recovery.
- **Monaco & Ace Editor Automation:** Injects code safely into web IDEs using base64 decoding (preventing newline or quote escaping corruption), runs test cases, and polls real judge verdicts (`ACCEPTED`, `WRONG_ANSWER`, `COMPILATION_ERROR`).
- **Flexible Browser Automation:** Uses standard Playwright with an isolated persistent profile directory (`~/.course_automation/browser_profile`). Optionally connects to existing remote browser instances via Chrome DevTools Protocol (CDP).
- **Non-Intrusive Authentication:** Non-destructively classifies user login status (`AUTHENTICATED`, `LOGGED_OUT`, `SESSION_EXPIRED`, `LOGIN_PAGE`) and provides an interactive login helper.
- **Optional AI Integration:** Supports Google Gemini (`google-genai`) for generating solutions and answering MCQs. AI is **strictly optional** — core navigation and course inspection work completely offline/free without an API key.
- **Safety Gates & Secret Redaction:** Built-in interactive confirmation before any consequential action (such as submitting graded code). All logs and prompts are automatically scrubbed for credentials and API keys.

---

## Architecture Overview

```
course-automation/
├── src/course_automation/
│   ├── cli.py               # Typer & Rich CLI entrypoints
│   ├── config.py            # Pydantic Settings (.env configuration)
│   ├── logger.py            # Sanitized logging with regex redaction
│   ├── safety.py            # Action approval gate and dry-run controller
│   ├── browser/
│   │   ├── session.py       # Playwright persistent context & CDP connector
│   │   └── auth.py          # DOM-based auth state detector & login flow
│   ├── ai/
│   │   ├── base.py          # Abstract BaseAIProvider interface
│   │   ├── sanitizer.py     # Secret redaction utility
│   │   └── gemini.py        # Google Gemini provider implementation
│   ├── sites/
│   │   ├── base.py          # Abstract BaseSiteAdapter
│   │   └── codechef/        # CodeChef syllabus, editor, and verdicts
│   └── storage/
│       ├── models.py        # Pydantic data schemas
│       └── db.py            # SQLite database manager
├── tests/                   # Automated pytest suite
├── docs/                    # Architecture and development guides
└── pyproject.toml           # Packaging and dependencies
```

---

## Supported Websites

- **CodeChef (`https://www.codechef.com/learn/course/...`)**
  - Full syllabus inspection via `/api/learn/syllabus/<slug>`
  - Coding problem solving with Monaco editor interaction
  - Verdict parsing and status synchronization

*Additional platforms can be added by implementing `BaseSiteAdapter`. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).*

---

## Prerequisites

- **Python:** 3.10, 3.11, or 3.12
- **Operating System:** macOS (Apple Silicon / Intel), Linux, or Windows
- **Chromium / Playwright browser binaries**

---

## Installation

### 1. Clone the repository
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

| Environment Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `none` | Active AI provider (`gemini` or `none`). |
| `GEMINI_API_KEY` | None | API key from Google AI Studio (optional). |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name. |
| `BROWSER_HEADLESS` | `false` | Run browser in headless mode. |
| `BROWSER_USER_DATA_DIR` | `~/.course_automation/browser_profile` | Directory for persistent browser session. |
| `BROWSER_CDP_URL` | None | Optional CDP endpoint (e.g., `http://127.0.0.1:9222`). |
| `DATABASE_PATH` | `~/.course_automation/progress.db` | SQLite database file location. |
| `DRY_RUN` | `false` | When true, simulate actions without submitting. |

---

## CLI Usage

Verify installation:
```bash
course-automation --help
```

### 1. View configuration
```bash
course-automation config
```

### 2. Authenticate
Launch an interactive browser session to log in to your account. Your credentials and cookies are stored solely in your local profile directory:
```bash
course-automation auth
```

### 3. Inspect a course
Inspect any course URL to see modules, activities, and current progress:
```bash
course-automation inspect https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2
```
Options:
- `--incomplete-only`: Only display activities that are not yet completed.
- `--headless`: Run browser without GUI window.
- `--json`: Output raw structured JSON.

### 4. Query offline progress
Query previously inspected progress from local SQLite without opening the browser:
```bash
course-automation status cu-oops-sem3-2026-c2
```

### 5. Solve / Assist with course activities
Process activities with interactive confirmation gates:
```bash
# Dry-run: test problem discovery and solution generation without submitting
course-automation solve https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --dry-run

# Target a specific activity:
course-automation solve https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2 --activity RECT01
```

---

## Security & Privacy

1. **Zero Secret Leaks:** API keys and credentials are automatically scrubbed by regex filters from logs and outbound AI prompts.
2. **Local Session Storage:** Browser cookies and profiles are saved exclusively in your local user directory (`~/.course_automation/browser_profile`). They are **never** uploaded, tracked in git, or extracted.
3. **Safety Confirmation:** Submitting graded solutions or quiz answers requires explicit interactive approval unless `--auto-approve` is passed.
4. **No Hidden Telemetry:** The tool does not send metrics, telemetry, or analytics to any third party.

---

## Cost Considerations

- **Core Inspection & Automation:** 100% Free. Uses standard local browser automation.
- **AI Solving (Optional):** Using Google Gemini 2.5 Flash typically falls within Google AI Studio's free tier quotas. If you exceed free limits, standard per-token API pricing applies.

---

## Contributing

Pull requests are welcome! Please ensure:
1. All unit tests pass: `pytest`
2. No sensitive data or personal machine paths are introduced.
3. New site adapters adhere to `BaseSiteAdapter` (see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)).

---

## License

This project is licensed under the [MIT License](LICENSE).
