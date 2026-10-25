"""Command Line Interface for Course Automation."""

from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from course_automation import __version__
from course_automation.ai.gemini import GeminiProvider
from course_automation.browser.active_session import ActiveSessionDetector
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
    url: Optional[str] = typer.Argument(
        None,
        help="Course URL to inspect. If omitted, automatically detects the active course in your browser.",
    ),
    incomplete_only: bool = typer.Option(False, "--incomplete-only", help="Show only incomplete activities"),
    select_module: bool = typer.Option(False, "--select-module", help="Interactively select a specific module to view"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headful", help="Override browser headless setting"),
    as_json: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    save_db: bool = typer.Option(True, "--save-db/--no-save-db", help="Persist inspection results to SQLite"),
):
    """Inspect any CodeChef course and display modules, activities, and progress."""
    db = DatabaseManager()

    console.print("[cyan]Connecting to browser session...[/cyan]")
    with BrowserSession(headless=headless) as session:
        # Auto-detect course from active browser tab if URL not supplied
        if not url:
            active = ActiveSessionDetector.detect_active_course(session.context)
            if active and active.course_slug:
                url = f"https://www.codechef.com/learn/course/{active.course_slug}"
                console.print(f"[bold green]Auto-detected active course in browser:[/bold green] {active.course_slug} ({url})")
            else:
                console.print("[bold red]No course URL provided and no active CodeChef tab was detected in the browser.[/bold red]")
                console.print("Please provide a course URL or open a CodeChef course in your browser.")
                raise typer.Exit(code=1)

        adapter = get_adapter(url)
        page = session.get_or_create_page()
        summary = adapter.inspect_course(page, url)

    if save_db:
        db.save_course_summary(summary)

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return

    # Interactive module selection if requested
    modules_to_show = summary.modules
    if select_module and len(summary.modules) > 1:
        console.print("\n[bold cyan]Available Modules / Units:[/bold cyan]")
        for idx, mod in enumerate(summary.modules, 1):
            console.print(f"  [{idx}] {mod.title} ({mod.completion_pct}% complete, {len(mod.activities)} activities)")
        choice = Prompt.ask(
            "Select module number to inspect",
            choices=[str(i) for i in range(1, len(summary.modules) + 1)],
            default="1",
        )
        selected_mod = summary.modules[int(choice) - 1]
        modules_to_show = [selected_mod]

    # Render formatted table
    table = Table(
        title=f"Course: {summary.title} ({summary.progress_percentage}% Complete)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Module", style="white", width=24)
    table.add_column("Activity", style="bold", width=36)
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Status", width=16)

    for mod in modules_to_show:
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
    course_url_or_slug: Optional[str] = typer.Argument(
        None,
        help="Course URL or slug to query. If omitted, lists all saved courses in the database.",
    ),
):
    """View saved course status and progress history from local SQLite database."""
    db = DatabaseManager()

    if not course_url_or_slug:
        # List all tracked courses in local SQLite
        with db._get_connection() as conn:
            rows = conn.execute("SELECT slug, title, total_activities, completed_activities, last_inspected_at FROM courses").fetchall()
        if not rows:
            console.print("[yellow]No courses currently recorded in the local database. Run 'inspect' on a course first.[/yellow]")
            return

        table = Table(title="Tracked Courses in Local Database", show_header=True)
        table.add_column("Course Slug", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Progress", style="green")
        table.add_column("Last Inspected", style="magenta")

        for r in rows:
            pct = round((r["completed_activities"] / r["total_activities"]) * 100, 1) if r["total_activities"] else 0.0
            table.add_row(
                r["slug"],
                r["title"],
                f"{r['completed_activities']}/{r['total_activities']} ({pct}%)",
                r["last_inspected_at"][:19] if r["last_inspected_at"] else "N/A",
            )
        console.print(table)
        return

    slug = CodeChefAdapter().extract_course_slug(course_url_or_slug)
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
    url: Optional[str] = typer.Argument(
        None,
        help="Course URL to solve. If omitted, automatically detects active course in your browser.",
    ),
    activity_id: Optional[str] = typer.Option(None, "--activity", help="Specific activity ID to solve"),
    module_id: Optional[str] = typer.Option(None, "--module", help="Specific module ID or slug to process"),
    select_module: bool = typer.Option(False, "--select-module", help="Interactively select a module to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without submitting"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Bypass interactive confirmation prompt"),
    use_ai: bool = typer.Option(True, "--ai/--no-ai", help="Use AI provider to generate solutions"),
):
    """Process or solve course activities with optional AI assistance and safety gates."""
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
        if not url:
            active = ActiveSessionDetector.detect_active_course(session.context)
            if active and active.course_slug:
                url = f"https://www.codechef.com/learn/course/{active.course_slug}"
                console.print(f"[bold green]Auto-detected active course in browser:[/bold green] {active.course_slug} ({url})")
            else:
                console.print("[bold red]No course URL provided and no active CodeChef tab was detected in the browser.[/bold red]")
                raise typer.Exit(code=1)

        adapter = get_adapter(url)
        page = session.get_or_create_page()
        summary = adapter.inspect_course(page, url)
        db.save_course_summary(summary)

        # Module selection
        target_mod_id = module_id
        if select_module and not target_mod_id:
            console.print("\n[bold cyan]Select Module / Unit to Process:[/bold cyan]")
            for idx, mod in enumerate(summary.modules, 1):
                console.print(f"  [{idx}] {mod.title} ({mod.completion_pct}% complete)")
            choice = Prompt.ask(
                "Select module number",
                choices=[str(i) for i in range(1, len(summary.modules) + 1)],
                default="1",
            )
            target_mod_id = summary.modules[int(choice) - 1].id

        targets = []
        for mod in summary.modules:
            if target_mod_id and mod.id != target_mod_id and mod.slug != target_mod_id:
                continue
            for act in mod.activities:
                if activity_id and act.id != activity_id and act.slug != activity_id:
                    continue
                if not activity_id and act.status == ActivityStatus.COMPLETED:
                    continue
                targets.append(act)

        console.print(f"[cyan]Found {len(targets)} target activities to process.[/cyan]")

        for act in targets:
            console.print(f"\nProcessing activity: [bold]{act.title}[/bold] ({act.id}) [{act.type.value}]")
            if not safety.confirm_action(f"Process {act.title}"):
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
