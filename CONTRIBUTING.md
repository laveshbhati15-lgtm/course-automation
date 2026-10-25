# Contributing to Course Automation

Thank you for your interest in contributing to Course Automation! We welcome contributions from developers of all skill levels.

This guide outlines our development workflow, coding standards, and testing policies to help you get started quickly and safely.

---

## Code of Conduct

All contributors and participants are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect, patience, and empathy.

---

## Development Setup

### Prerequisites
- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **Git**
- **Chromium browser** (installed via Playwright)

### 1. Fork & Clone
```bash
git clone https://github.com/laveshbhati15-lgtm/course-automation.git
cd course-automation
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install in Editable Mode with Dev Dependencies
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Install Playwright Browsers
```bash
playwright install chromium
```

### 5. Configure Local Environment
```bash
cp .env.example .env
```
Customize `.env` with your desired settings. Setting `AI_PROVIDER=none` allows you to run all tests and non-AI features without external API keys.

---

## Running the Test Suite

We use `pytest` with `pytest-mock` for unit and integration testing.

```bash
# Run all automated tests
pytest -v

# Run a specific test module
pytest tests/test_theory_mcq.py -v

# Run with coverage (optional)
pytest --cov=src/course_automation -v
```

### Critical Testing Rule
> [!IMPORTANT]
> **Never run automated tests against live personal courses or user accounts.**
>
> All test cases in this repository must use **synthetic fixtures, mocked DOM pages, or isolated local databases**. Never submit answers, advance live syllabus progress, or consume live platform credentials during test execution.

---

## Project Structure & Architecture

```
src/course_automation/
├── cli.py                     # Typer CLI commands (inspect, solve, status, auth, config)
├── config.py                  # Pydantic Settings configuration from environment and .env
├── logger.py                  # Sanitized logging with regex credential redaction
├── safety.py                  # Confirmation gates for live or consequential actions
├── browser/
│   ├── session.py             # Playwright browser context & CDP connector
│   ├── auth.py                # DOM-based login state detection
│   ├── active_session.py      # Active browser tab detection
│   └── browser_use_bridge.py  # Bridge for Browser Use agent automation
├── ai/
│   ├── base.py                # BaseAIProvider interface and MCQReasoningResult
│   ├── sanitizer.py           # Credential scrubber
│   └── gemini.py              # Optional Google Gemini integration
├── sites/
│   ├── base.py                # Abstract BaseSiteAdapter
│   └── codechef/
│       ├── adapter.py         # CodeChef site adapter
│       ├── syllabus.py        # Generic syllabus API & DOM fallback parser
│       ├── editor.py          # Monaco and Ace code editor controller
│       ├── verdicts.py        # Submission verdict polling state machine
│       ├── navigator.py       # Sequential multi-lesson traversal controller
│       └── handlers/          # Modular activity handlers
│           ├── base.py        # BaseActivityHandler
│           ├── coding.py      # Coding problems & labs
│           ├── quiz.py        # Multiple-choice quizzes
│           ├── lesson.py      # Theory reading concepts
│           └── locked.py      # Locked & unsupported assessments
└── storage/
    ├── db.py                  # SQLite database manager
    └── models.py              # Dataclasses & Pydantic models
```

---

## Contributing Guidelines

### 1. Modularity & Platform Independence
- Keep site-specific logic inside `src/course_automation/sites/<site_name>/`.
- Do not introduce dependencies on proprietary IDE extensions, specific operating systems, or closed-source cloud services.

### 2. Privacy & Secret Hygiene
- **Never commit credentials, cookies, tokens, or browser profile directories.**
- Ensure any user input or logging passes through the credential sanitizer in `src/course_automation/ai/sanitizer.py`.
- Check `.gitignore` before staging new files.

### 3. Non-Destructive Defaults & Dry-Run Safety
- All actions that modify platform state (submitting code, clicking quiz answers, advancing lessons) must be protected by `SafetyGate`.
- Dry-run mode (`--dry-run`) must be completely non-mutating: inspecting DOM and reasoning without clicking buttons or submitting.

---

## Submitting Pull Requests

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write clean code with type annotations and docstrings.
3. Add corresponding test cases in `tests/`.
4. Ensure all 60+ tests pass:
   ```bash
   pytest -v
   ```
5. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add support for multiple question quizzes"
   ```
6. Open a Pull Request with a clear description of the problem solved and the tests performed.
