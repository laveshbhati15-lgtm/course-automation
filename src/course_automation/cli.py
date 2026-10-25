"""Command Line Interface for Course Automation."""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from course_automation import __version__
from course_automation.ai.gemini import GeminiProvider
from course_automation.browser.auth import AuthDetector, AuthState
from course_automation.browser.session import BrowserSession
from course_automation.config import settings
from course_automation.logger import logger
from course_automation.safety import SafetyGate
from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.storage.db import DatabaseManager
from course_automation.storage.models import ActivityStatus

app = typer.Typer(
    name="course-automation",
    help="Standalone, portable course automation and progress inspection tool.",
    add_completion=False,
)
console = Console()


def get_adapter(url: str):
    """Factory to retrieve matching website adapter."""
    codechef = CodeChefAdapter()
    if codechef.can_handle(url):
        return codechef
    raise typer.BadParameter(f"No adapter available for URL: {url}")


@app.command()
def version():
    """Display the application version."""
    console.print(f"[bold green]Course Automation[/bold green] version: {__version__}")


@app.command()
def config():
    """Display current configuration and resolved directory paths."""
    table = Table(title="Course Automation Configuration", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("AI Provider", settings.ai_provider)
    table.add_row("Gemini Model", settings.gemini_model)
    table.add_row("Gemini API Key", "[SET (REDACTED)]" if settings.gemini_api_key else "[NOT SET]")
    table.add_row("Browser Headless", str(settings.browser_headless))
    table.add_row("Browser Profile Dir", str(settings.browser_user_data_dir))
    table.add_row("Browser CDP URL", str(settings.browser_cdp_url or "None"))
    table.add_row("Database Path", str(settings.database_path))
    table.add_row("Log Level", settings.log_level)
    table.add_row("Dry Run Default", str(settings.dry_run))

    console.print(table)


@app.command()
def auth(
    site: str = typer.Option("codechef", help="Target site for authentication"),
    timeout: int = typer.Option(300, help="Maximum wait time in seconds for manual login"),
):
    """Launch headful browser to authenticate and save session to local profile."""
    console.print("[bold yellow]Opening browser for manual authentication...[/bold yellow]")
    console.print("Your credentials and cookies are stored solely in your local profile directory.")

    with BrowserSession(headless=False) as session:
        page = session.get_or_create_page()
        success = AuthDetector.wait_for_manual_login(
            page=page,
            site=site,
            timeout_seconds=timeout,
        )
        if success:
            console.print("[bold green]Authentication successful! Session saved to profile.[/bold green]")
        else:
            console.print("[bold red]Authentication was not completed within the time limit.[/bold red]")
            raise typer.Exit(code=1)


@app.command()
def inspect(
    url: str = typer.Argument(..., help="Course URL to inspect"),
    incomplete_only: bool = typer.Option(False, "--incomplete-only", help="Show only incomplete activities"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headful", help="Override browser headless setting"),
    as_json: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    save_db: bool = typer.Option(True, "--save-db/--no-save-db", help="Persist inspection results to SQLite"),
):
    """Inspect a course URL and display modules, activities, and progress."""
    adapter = get_adapter(url)
    db = DatabaseManager()

    console.print("[cyan]Connecting to browser and inspecting course...[/cyan]")
    with BrowserSession(headless=headless) as session:
        page = session.get_or_create_page()
        summary = adapter.inspect_course(page, url)

    if save_db:
        db.save_course_summary(summary)

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return

    table = Table(
        title=f"Course: {summary.title} ({summary.progress_percentage}% Complete)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Module", style="white", width=24)
    table.add_column("Activity", style="bold", width=36)
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Status", width=16)

    for mod in summary.modules:
        for act in mod.activities:
            if incomplete_only and act.status == ActivityStatus.COMPLETED:
                continue

            status_style = "green" if act.status == ActivityStatus.COMPLETED else (
                "yellow" if act.status == ActivityStatus.IN_PROGRESS else (
                    "red" if act.status == ActivityStatus.LOCKED else "white"
                )
            )
            table.add_row(
                mod.title,
                act.title,
                act.type.value,
                f"[{status_style}]{act.status.value}[/{status_style}]",
            )

    console.print(table)
    summary_msg = f"Summary: {summary.completed_activities} / {summary.total_activities} activities completed ({summary.progress_percentage}%)."
    console.print(f"[bold]{summary_msg}[/bold]")


@app.command()
def status(
    course_url_or_slug: str = typer.Argument(..., help="Course URL or slug to query from local database"),
):
    """View saved course status and progress history from local SQLite database."""
    slug = CodeChefAdapter().extract_course_slug(course_url_or_slug)
    db = DatabaseManager()
    summary = db.get_course_summary(slug)

    if not summary:
        console.print(f"[yellow]No saved data found for course slug: {slug}. Run 'inspect' first.[/yellow]")
        raise typer.Exit(code=1)

    table = Table(
        title=f"Local Status: {summary.title} ({summary.progress_percentage}% Complete)",
        show_header=True,
    )
    table.add_column("Module", style="white")
    table.add_column("Completed / Total", style="cyan")
    table.add_column("Progress", style="green")

    for mod in summary.modules:
        mod_completed = sum(1 for a in mod.activities if a.status == ActivityStatus.COMPLETED)
        table.add_row(
            mod.title,
            f"{mod_completed} / {len(mod.activities)}",
            f"{mod.completion_pct}%",
        )

    console.print(table)


@app.command()
def solve(
    url: str = typer.Argument(..., help="Course URL to solve"),
    activity_id: Optional[str] = typer.Option(None, "--activity", help="Specific activity ID to solve"),
    module_id: Optional[str] = typer.Option(None, "--module", help="Specific module ID to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without submitting"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Bypass interactive confirmation prompt"),
    use_ai: bool = typer.Option(True, "--ai/--no-ai", help="Use AI provider to generate solutions"),
):
    """Process or solve course activities with optional AI assistance."""
    adapter = get_adapter(url)
    db = DatabaseManager()
    safety = SafetyGate(dry_run=dry_run, auto_approve=auto_approve)

    ai_provider = None
    if use_ai and settings.ai_provider == "gemini":
        try:
            ai_provider = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )
        except Exception as e:
            console.print(f"[yellow]AI provider warning: {e}. Continuing without AI generation.[/yellow]")

    with BrowserSession(headless=False) as session:
        page = session.get_or_create_page()
        summary = adapter.inspect_course(page, url)
        db.save_course_summary(summary)

        targets = []
        for mod in summary.modules:
            if module_id and mod.id != module_id and mod.slug != module_id:
                continue
            for act in mod.activities:
                if activity_id and act.id != activity_id and act.slug != activity_id:
                    continue
                if not activity_id and act.status == ActivityStatus.COMPLETED:
                    continue
                targets.append(act)

        console.print(f"[cyan]Found {len(targets)} target activities to process.[/cyan]")

        for act in targets:
            console.print(f"Processing activity: {act.title} ({act.id})")
            if not safety.confirm_action(f"Solve and submit {act.title}"):
                console.print(f"[yellow]Skipped {act.title}.[/yellow]")
                continue

            record = adapter.solve_activity(
                page=page,
                activity=act,
                ai_provider=ai_provider,
                dry_run=dry_run,
            )
            db.record_submission(record, summary.slug)
            console.print(f"Result: [bold]{record.verdict}[/bold] - {record.details}")


def main():
    """Main CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
