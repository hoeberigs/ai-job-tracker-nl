"""Data models for job listings."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """A single job listing."""

    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    salary: str = ""
    posted_date: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat()[:10])

    # Classification fields (populated by classifier)
    seniority: str = ""       # junior, mid, senior, lead, head, unknown
    category: str = ""        # ml-engineer, data-scientist, ai-engineer, etc.
    sector: str = ""          # tech, finance, healthcare, etc.
    skills: list[str] = field(default_factory=list)
    remote: str = ""          # remote, hybrid, onsite, unknown

    def to_dict(self) -> dict:
        return asdict(self)
