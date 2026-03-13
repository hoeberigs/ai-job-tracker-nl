"""Export job data to CSV and JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from src.models import Job


def export_csv(jobs: list[Job], path: str = "data/jobs.csv") -> str:
    """Export jobs to CSV. Returns the file path."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "title", "company", "location", "category", "seniority",
        "sector", "remote", "skills", "salary", "source", "url",
        "scraped_at",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            row = job.to_dict()
            row["skills"] = ", ".join(row.get("skills", []))
            writer.writerow({k: row.get(k, "") for k in fields})

    return path


def export_json(jobs: list[Job], analysis: dict[str, Any], path: str = "data/results.json") -> str:
    """Export jobs and analysis to JSON. Returns the file path."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "analysis": _serialise_analysis(analysis),
        "jobs": [job.to_dict() for job in jobs],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return path


def _serialise_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    """Convert analysis tuples to serialisable dicts."""
    out = {}
    for key, value in analysis.items():
        if isinstance(value, list) and value and isinstance(value[0], tuple):
            out[key] = [
                {"name": v[0], "count": v[1], "pct": v[2]}
                for v in value
            ]
        else:
            out[key] = value
    return out
