# Architecture Guide

## System Design
Course Automation uses a clean, layered architecture separating CLI entrypoints, browser context, site-specific adapters, AI providers, and persistence.

```
+-----------------------------------------------------------+
|                        CLI (Typer)                        |
|        inspect  |  auth  |  solve  |  status  | config    |
+-----------------------------------------------------------+
        |                  |                    |
        v                  v                    v
+----------------+  +-----------------+  +------------------+
| BrowserSession |  | BaseSiteAdapter |  |  BaseAIProvider  |
|  (Playwright)  |  |   (CodeChef)    |  |     (Gemini)     |
+----------------+  +-----------------+  +------------------+
        |                  |                    |
        +------------------+--------------------+
                           |
                           v
              +--------------------------+
              | DatabaseManager (SQLite) |
              |  ~/.course_automation/   |
              +--------------------------+
```

### Key Components

1. **`BrowserSession` (`src/course_automation/browser/session.py`)**
   Wraps Playwright's `sync_playwright()` with persistent context. It launches Chromium with user-specified user data directory or connects over CDP (`connect_over_cdp`).

2. **`AuthDetector` (`src/course_automation/browser/auth.py`)**
   Inspects page DOM non-intrusively to verify session validity. It never injects test credentials or alters account settings.

3. **`BaseSiteAdapter` (`src/course_automation/sites/base.py`)**
   Contract for website-specific behavior. Handles URL routing, syllabus parsing, editor injection, and status checks.

4. **`MonacoEditorController` (`src/course_automation/sites/codechef/editor.py`)**
   Interacts with Monaco and Ace code editors via base64 buffer injection (`atob(...)`), preventing syntax errors from shell or quote escaping.

5. **`DatabaseManager` (`src/course_automation/storage/db.py`)**
   Provides ACID-compliant SQLite storage for courses, modules, activities, submissions, and key-value checkpoints.

6. **`TheoryCourseNavigator` (`src/course_automation/sites/codechef/navigator.py`)**
   Orchestrates sequential multi-lesson traversals across a course curriculum. Coordinates candidate activity filtering (`--theory-only`, `--coding-only`), safety confirmation gates, and SQLite progress persistence.

7. **`TheoryLessonActivityHandler` (`src/course_automation/sites/codechef/handlers/lesson.py`)**
   Automates reading concept lessons: smooth scrolling to trigger MathJax and dynamic assets, accessible navigation button discovery, and live advancement verification.

8. **`QuizActivityHandler` (`src/course_automation/sites/codechef/handlers/quiz.py`)**
   Automates multiple-choice questions: extracts full prompt statements and radio options, performs structured AI reasoning, halts for human review if confidence is below 85%, and verifies visual checked state and platform feedback banners.
