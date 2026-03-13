"""Analyze classified job listings for trends and insights."""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.models import Job


def analyze(jobs: list[Job]) -> dict[str, Any]:
    """Generate a full analysis of the job listings."""
    if not jobs:
        return {"total": 0}

    return {
        "total": len(jobs),
        "by_seniority": _count_field(jobs, "seniority"),
        "by_category": _count_field(jobs, "category"),
        "by_sector": _count_field(jobs, "sector"),
        "by_remote": _count_field(jobs, "remote"),
        "by_source": _count_field(jobs, "source"),
        "by_location": _top_locations(jobs),
        "top_skills": _top_skills(jobs),
        "top_companies": _top_companies(jobs),
    }


def _count_field(jobs: list[Job], field: str) -> list[tuple[str, int, float]]:
    """Count and rank a classification field. Returns (value, count, pct)."""
    values = [getattr(job, field, "unknown") or "unknown" for job in jobs]
    counts = Counter(values).most_common()
    total = len(jobs)
    return [(val, cnt, round(cnt / total * 100, 1)) for val, cnt in counts]


def _top_skills(jobs: list[Job], top_n: int = 15) -> list[tuple[str, int, float]]:
    """Most demanded skills across all listings."""
    skill_counts: Counter = Counter()
    for job in jobs:
        for skill in job.skills:
            skill_counts[skill] += 1
    total = len(jobs)
    return [
        (skill, cnt, round(cnt / total * 100, 1))
        for skill, cnt in skill_counts.most_common(top_n)
    ]


def _top_locations(jobs: list[Job], top_n: int = 10) -> list[tuple[str, int, float]]:
    """Most common job locations."""
    locations = []
    for job in jobs:
        loc = job.location.strip()
        if loc:
            # Normalise: take first part before comma or parenthesis
            loc = loc.split(",")[0].split("(")[0].strip()
            locations.append(loc)

    counts = Counter(locations).most_common(top_n)
    total = len(jobs)
    return [(loc, cnt, round(cnt / total * 100, 1)) for loc, cnt in counts]


def _top_companies(jobs: list[Job], top_n: int = 10) -> list[tuple[str, int, float]]:
    """Companies with the most AI/ML openings."""
    companies = [job.company for job in jobs if job.company and job.company != "Unknown"]
    counts = Counter(companies).most_common(top_n)
    total = len(jobs)
    return [(company, cnt, round(cnt / total * 100, 1)) for company, cnt in counts]
