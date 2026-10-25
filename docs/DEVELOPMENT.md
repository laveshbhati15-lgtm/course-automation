# Developer Guide: Adding a New Site Adapter

To support another learning platform (e.g., LeetCode, HackerRank, Coursera):

### Step 1: Create an Adapter Class
Create `src/course_automation/sites/<site_name>/adapter.py` inheriting from `BaseSiteAdapter`:

```python
from playwright.sync_api import Page
from course_automation.sites.base import BaseSiteAdapter
from course_automation.storage.models import CourseSummary, ActivitySummary, SubmissionRecord, ActivityStatus

class MySiteAdapter(BaseSiteAdapter):
    name = "mysite"

    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url.lower()

    def extract_course_slug(self, url: str) -> str:
        # Extract course identifier from URL
        return url.split("/")[-1]

    def inspect_course(self, page: Page, url: str) -> CourseSummary:
        # Parse syllabus from API or DOM
        ...

    def navigate_to_activity(self, page: Page, activity: ActivitySummary) -> bool:
        page.goto(activity.url)
        return True

    def solve_activity(self, page: Page, activity: ActivitySummary, ai_provider=None, dry_run=False) -> SubmissionRecord:
        # Solve coding or quiz exercise
        ...

    def verify_activity_status(self, page: Page, activity: ActivitySummary) -> ActivityStatus:
        # Verify status on page
        ...
```

### Step 2: Register Adapter
In `src/course_automation/cli.py`, add your adapter to `get_adapter(url: str)`:
```python
from course_automation.sites.mysite.adapter import MySiteAdapter

def get_adapter(url: str):
    if "mysite.com" in url:
        return MySiteAdapter()
    ...
```

### Step 3: Write Tests
Add unit tests in `tests/test_mysite.py` using mocked `Page` objects. Run:
```bash
pytest
```
