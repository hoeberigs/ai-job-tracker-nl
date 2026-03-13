"""Rich terminal display for job analysis results."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from src.models import Job

console = Console()


def display_results(jobs: list[Job], analysis: dict[str, Any]) -> None:
    """Display full analysis with rich formatting."""
    total = analysis.get("total", 0)

    # Header
    console.print()
    console.print(
        Panel.fit(
            f"[bold white]AI/ML Job Market Tracker — Netherlands[/]\n"
            f"[dim]{total} jobs scraped and classified[/]",
            border_style="bright_blue",
        )
    )
    console.print()

    if total == 0:
        console.print("[yellow]No jobs found. Try again later.[/]")
        return

    # Summary cards
    _display_summary_cards(analysis)

    # Category breakdown
    _display_ranked_table(
        "Job Categories",
        analysis.get("by_category", []),
        emoji="briefcase",
    )

    # Seniority breakdown
    _display_ranked_table(
        "Seniority Levels",
        analysis.get("by_seniority", []),
        emoji="chart_increasing",
    )

    # Top skills
    _display_ranked_table(
        "Most In-Demand Skills",
        analysis.get("top_skills", []),
        emoji="wrench",
    )

    # Top locations
    _display_ranked_table(
        "Top Locations",
        analysis.get("by_location", []),
        emoji="round_pushpin",
    )

    # Top companies
    _display_ranked_table(
        "Top Hiring Companies",
        analysis.get("top_companies", []),
        emoji="office_building",
    )

    # Remote status
    _display_ranked_table(
        "Remote Work Status",
        analysis.get("by_remote", []),
        emoji="house",
    )

    # Sector breakdown
    _display_ranked_table(
        "Industry Sectors",
        analysis.get("by_sector", []),
        emoji="factory",
    )

    # Source breakdown
    _display_ranked_table(
        "Data Sources",
        analysis.get("by_source", []),
        emoji="globe_with_meridians",
    )

    # Sample listings
    _display_sample_listings(jobs)


def _display_summary_cards(analysis: dict[str, Any]) -> None:
    total = analysis["total"]
    categories = analysis.get("by_category", [])
    skills = analysis.get("top_skills", [])
    seniority = analysis.get("by_seniority", [])

    top_category = categories[0][0] if categories else "—"
    top_skill = skills[0][0] if skills else "—"
    senior_pct = next(
        (f"{pct}%" for val, _, pct in seniority if val == "senior"), "—"
    )

    cards = [
        Panel(f"[bold cyan]{total}[/]\nTotal Jobs", expand=True, border_style="cyan"),
        Panel(f"[bold green]{top_category}[/]\nTop Category", expand=True, border_style="green"),
        Panel(f"[bold yellow]{top_skill}[/]\nTop Skill", expand=True, border_style="yellow"),
        Panel(f"[bold magenta]{senior_pct}[/]\nSenior Roles", expand=True, border_style="magenta"),
    ]
    console.print(Columns(cards, equal=True, expand=True))
    console.print()


def _display_ranked_table(
    title: str,
    data: list[tuple[str, int, float]],
    emoji: str = "",
    max_rows: int = 12,
) -> None:
    if not data:
        return

    table = Table(
        title=f"  {title}",
        title_style="bold bright_blue",
        show_header=True,
        header_style="bold",
        border_style="dim",
        expand=False,
        min_width=50,
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Name", min_width=20)
    table.add_column("Count", justify="right", width=7)
    table.add_column("Share", justify="right", width=8)
    table.add_column("Bar", min_width=15)

    max_count = max(cnt for _, cnt, _ in data) if data else 1

    for i, (name, count, pct) in enumerate(data[:max_rows], 1):
        bar_len = int((count / max_count) * 15)
        bar = "[bright_blue]" + "█" * bar_len + "[/]" + "░" * (15 - bar_len)

        table.add_row(
            str(i),
            name,
            str(count),
            f"{pct}%",
            bar,
        )

    console.print(table)
    console.print()


def _display_sample_listings(jobs: list[Job], max_show: int = 10) -> None:
    table = Table(
        title="  Sample Listings",
        title_style="bold bright_blue",
        show_header=True,
        header_style="bold",
        border_style="dim",
        expand=True,
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Title", min_width=25, max_width=35)
    table.add_column("Company", min_width=12, max_width=20)
    table.add_column("Location", min_width=10, max_width=15)
    table.add_column("Category", min_width=12)
    table.add_column("Seniority", width=10)
    table.add_column("Source", width=12)

    for i, job in enumerate(jobs[:max_show], 1):
        table.add_row(
            str(i),
            job.title[:35],
            job.company[:20],
            job.location[:15],
            job.category,
            job.seniority,
            job.source,
        )

    console.print(table)
    console.print()
