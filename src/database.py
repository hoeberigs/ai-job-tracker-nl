"""SQLite persistence layer for historical job tracking."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.models import Job


_SCHEMA = """
CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    run_timestamp TEXT NOT NULL,
    total_jobs INTEGER NOT NULL,
    source TEXT DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES scrape_runs(id),
    title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    source TEXT,
    description TEXT,
    salary TEXT,
    posted_date TEXT,
    scraped_at TEXT,
    seniority TEXT,
    category TEXT,
    sector TEXT,
    skills TEXT,
    remote TEXT,
    UNIQUE(url, run_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_run_id ON jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
"""


def init_db(db_path: str = "data/jobs.db") -> sqlite3.Connection:
    """Create tables if needed and return a connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_run(conn: sqlite3.Connection, jobs: list[Job], source: str = "manual") -> int:
    """Save a scrape run and all its jobs. Keeps only one run per day."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    # Delete any existing runs for today (keep one run per day)
    existing = conn.execute(
        "SELECT id FROM scrape_runs WHERE run_date = ?", (today,)
    ).fetchall()
    for row in existing:
        conn.execute("DELETE FROM jobs WHERE run_id = ?", (row["id"],))
        conn.execute("DELETE FROM scrape_runs WHERE id = ?", (row["id"],))

    cur = conn.execute(
        "INSERT INTO scrape_runs (run_date, run_timestamp, total_jobs, source) VALUES (?, ?, ?, ?)",
        (today, now.isoformat(), len(jobs), source),
    )
    run_id = cur.lastrowid

    for job in jobs:
        conn.execute(
            """INSERT OR IGNORE INTO jobs
               (run_id, title, company, location, url, source, description,
                salary, posted_date, scraped_at, seniority, category, sector, skills, remote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, job.title, job.company, job.location, job.url, job.source,
                job.description, job.salary, job.posted_date, job.scraped_at,
                job.seniority, job.category, job.sector,
                ", ".join(job.skills) if job.skills else "",
                job.remote,
            ),
        )

    conn.commit()
    return run_id


def get_all_runs(conn: sqlite3.Connection) -> list[dict]:
    """Return all scrape runs, newest first."""
    rows = conn.execute(
        "SELECT * FROM scrape_runs ORDER BY run_timestamp DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_jobs_for_run(conn: sqlite3.Connection, run_id: int) -> list[Job]:
    """Load jobs for a specific run back into Job objects."""
    rows = conn.execute("SELECT * FROM jobs WHERE run_id = ?", (run_id,)).fetchall()
    jobs = []
    for r in rows:
        job = Job(
            title=r["title"] or "",
            company=r["company"] or "",
            location=r["location"] or "",
            url=r["url"] or "",
            source=r["source"] or "",
            description=r["description"] or "",
            salary=r["salary"] or "",
            posted_date=r["posted_date"] or "",
            scraped_at=r["scraped_at"] or "",
            seniority=r["seniority"] or "",
            category=r["category"] or "",
            sector=r["sector"] or "",
            skills=[s.strip() for s in (r["skills"] or "").split(",") if s.strip()],
            remote=r["remote"] or "",
        )
        jobs.append(job)
    return jobs


def get_latest_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    """Get analysis data from the most recent run."""
    from src.analyzer import analyze

    run = conn.execute(
        "SELECT id FROM scrape_runs ORDER BY run_timestamp DESC LIMIT 1"
    ).fetchone()
    if not run:
        return {"total": 0}

    jobs = get_jobs_for_run(conn, run["id"])
    return analyze(jobs)


def get_trend_data(conn: sqlite3.Connection) -> dict[str, Any]:
    """Aggregate data across all runs for time-series charts."""
    runs = conn.execute(
        "SELECT id, run_date, total_jobs FROM scrape_runs ORDER BY run_timestamp ASC"
    ).fetchall()

    if not runs:
        return {"dates": [], "skills": {}, "categories": {}, "remote": {}, "totalPerRun": []}

    dates = []
    total_per_run = []
    skills_over_time: dict[str, list[int]] = {}
    categories_over_time: dict[str, list[int]] = {}
    remote_over_time: dict[str, list[int]] = {}

    all_skills: set[str] = set()
    all_categories: set[str] = set()
    all_remote: set[str] = set()

    # First pass: collect all unique values
    for run in runs:
        rows = conn.execute(
            "SELECT skills, category, remote FROM jobs WHERE run_id = ?", (run["id"],)
        ).fetchall()
        for row in rows:
            if row["skills"]:
                for s in row["skills"].split(", "):
                    if s.strip():
                        all_skills.add(s.strip())
            if row["category"]:
                all_categories.add(row["category"])
            if row["remote"]:
                all_remote.add(row["remote"])

    # Second pass: count per run
    for run in runs:
        dates.append(run["run_date"])
        total_per_run.append(run["total_jobs"])

        rows = conn.execute(
            "SELECT skills, category, remote FROM jobs WHERE run_id = ?", (run["id"],)
        ).fetchall()

        # Count skills
        skill_counts: dict[str, int] = {s: 0 for s in all_skills}
        cat_counts: dict[str, int] = {c: 0 for c in all_categories}
        remote_counts: dict[str, int] = {r: 0 for r in all_remote}

        for row in rows:
            if row["skills"]:
                for s in row["skills"].split(", "):
                    s = s.strip()
                    if s in skill_counts:
                        skill_counts[s] += 1
            if row["category"] and row["category"] in cat_counts:
                cat_counts[row["category"]] += 1
            if row["remote"] and row["remote"] in remote_counts:
                remote_counts[row["remote"]] += 1

        for s in all_skills:
            skills_over_time.setdefault(s, []).append(skill_counts[s])
        for c in all_categories:
            categories_over_time.setdefault(c, []).append(cat_counts[c])
        for r in all_remote:
            remote_over_time.setdefault(r, []).append(remote_counts[r])

    # Keep only top 8 skills by total count
    skill_totals = {s: sum(v) for s, v in skills_over_time.items()}
    top_skills = sorted(skill_totals, key=skill_totals.get, reverse=True)[:8]
    skills_over_time = {s: skills_over_time[s] for s in top_skills}

    return {
        "dates": dates,
        "skills": skills_over_time,
        "categories": categories_over_time,
        "remote": remote_over_time,
        "totalPerRun": total_per_run,
    }


def get_dashboard_data(db_path: str = "data/jobs.db") -> dict[str, Any]:
    """Get all data needed for the dashboard in a single call."""
    conn = init_db(db_path)

    runs = get_all_runs(conn)
    snapshot = get_latest_snapshot(conn)
    trends = get_trend_data(conn)

    # Aggregate top companies across all runs
    all_jobs_rows = conn.execute("SELECT company FROM jobs WHERE company != ''").fetchall()
    from collections import Counter
    company_counts = Counter(r["company"] for r in all_jobs_rows if r["company"])
    top_companies = [
        {"name": c, "count": n} for c, n in company_counts.most_common(10)
    ]

    total_jobs = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()["cnt"]

    conn.close()

    return {
        "lastUpdated": runs[0]["run_date"] if runs else "",
        "totalJobsTracked": total_jobs,
        "totalRuns": len(runs),
        "latestSnapshot": _serialise_snapshot(snapshot),
        "trends": trends,
        "topCompanies": top_companies,
    }


def _serialise_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Convert analyzer tuples to JSON-friendly dicts."""
    out: dict[str, Any] = {"total": snapshot.get("total", 0)}
    for key in ("by_category", "by_seniority", "by_remote", "by_sector",
                "by_source", "by_location", "top_skills", "top_companies"):
        value = snapshot.get(key, [])
        if isinstance(value, list) and value and isinstance(value[0], tuple):
            out[key] = [{"name": v[0], "count": v[1], "pct": v[2]} for v in value]
        else:
            out[key] = value
    return out
