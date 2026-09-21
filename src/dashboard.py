"""Generate a standalone HTML dashboard (hand-drawn SVG, no chart library)."""

from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path
from typing import Any

from src.database import get_dashboard_data

_TEMPLATE_PATH = Path(__file__).with_name("dashboard_template.html")

# A skill's share is compared between the first and the last MOVER_WINDOW runs
# that carry a share. Daily shares rest on roughly 100 ads, so single days are
# noisy; a four-week mean on each side is steady enough to read a direction.
# MOVER_THRESHOLD is a display cut-off in percentage points, not a test of
# statistical significance, and the dashboard says so.
MOVER_WINDOW = 28
MOVER_THRESHOLD = 3.0


def generate_dashboard(
    db_path: str = "data/jobs.db",
    output_dir: str = "docs",
) -> tuple[str, str]:
    """Generate dashboard.html and data.json. Returns (html_path, json_path)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    data = get_dashboard_data(db_path)
    data["skillMovers"] = _skill_movers(data.get("trends", {}))

    # Write data.json
    json_path = f"{output_dir}/data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    # Write dashboard.html
    html_path = f"{output_dir}/dashboard.html"
    html = _build_html(data)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html_path, json_path


def _fmt_label(slug: str) -> str:
    mapping = {
        "ml-engineer": "ML Engineer",
        "ai-engineer": "AI Engineer",
        "ai-general": "AI General",
        "data-scientist": "Data Scientist",
        "ai-researcher": "AI Researcher",
        "data-general": "Data General",
        "ai-product": "AI Product",
        "cv-engineer": "CV Engineer",
        "data-analyst": "Data Analyst",
        "nlp-engineer": "NLP Engineer",
        "ai-manager": "AI Manager",
        "data-engineer": "Data Engineer",
        "remote": "Remote",
        "hybrid": "Hybrid",
        "onsite": "Onsite",
        "senior": "Senior",
        "junior": "Junior",
        "lead": "Lead",
        "mid": "Mid",
        "head": "Head",
    }
    return mapping.get(slug, slug.replace("-", " ").title())


def _skill_movers(trends: dict[str, Any]) -> dict[str, Any]:
    """Compare each tracked skill's share at the start and end of the panel."""
    dates = trends.get("dates", [])
    out: dict[str, Any] = {
        "window": MOVER_WINDOW,
        "threshold": MOVER_THRESHOLD,
        "baselineDate": None,
        "skills": [],
    }

    for name, series in (trends.get("skillsPct") or {}).items():
        valid = [(i, v) for i, v in enumerate(series) if v is not None]
        # Both windows must be full and must not overlap.
        if len(valid) < 2 * MOVER_WINDOW:
            continue
        head, tail = valid[:MOVER_WINDOW], valid[-MOVER_WINDOW:]
        start = sum(v for _, v in head) / MOVER_WINDOW
        now = sum(v for _, v in tail) / MOVER_WINDOW
        delta = now - start
        status = "flat"
        if delta >= MOVER_THRESHOLD:
            status = "rising"
        elif delta <= -MOVER_THRESHOLD:
            status = "falling"
        out["skills"].append({
            "name": name,
            "start": round(start, 1),
            "now": round(now, 1),
            "delta": round(delta, 1),
            "status": status,
        })
        if out["baselineDate"] is None and head[MOVER_WINDOW // 2][0] < len(dates):
            out["baselineDate"] = dates[head[MOVER_WINDOW // 2][0]]

    out["skills"].sort(key=lambda s: s["delta"], reverse=True)
    return out


def _month_name(iso_date: str | None, latest: str | None = None) -> str:
    """Month of the baseline; the year is added once the panel spans two years."""
    try:
        d = date.fromisoformat(str(iso_date))
    except (TypeError, ValueError):
        return ""
    try:
        same_year = date.fromisoformat(str(latest)).year == d.year
    except (TypeError, ValueError):
        same_year = True
    return d.strftime("%B") if same_year else d.strftime("%B %Y")


def _headline(movers: dict[str, Any], latest: str | None = None) -> tuple[str, str]:
    """Return (headline, follow-up sentence) stating the largest moves.

    Runs on every daily update, so every branch must read correctly whatever
    the day's data looks like: no riser, no faller, or a panel too short to
    compare all fall back to a plain descriptive headline.
    """
    skills = movers.get("skills", [])
    month = _month_name(movers.get("baselineDate"), latest)
    risers = [s for s in skills if s["status"] == "rising"]
    fallers = [s for s in skills if s["status"] == "falling"]

    if not month or not (risers or fallers):
        return "What Dutch AI and ML job ads ask for, tracked daily.", ""

    if not risers:
        low = fallers[-1]
        return (
            f"{low['now']:.0f}% of Dutch AI job ads now ask for {low['name']}, "
            f"down from {low['start']:.0f}% in {month}."
        ), ""

    top = risers[0]
    headline = (
        f"{top['now']:.0f}% of Dutch AI job ads now ask for {top['name']}. "
        f"In {month} it was {top['start']:.0f}%."
    )
    follow = ""
    if fallers:
        low = fallers[-1]
        follow = (
            f"{low['name']} moved the other way, from {low['start']:.0f}% "
            f"to {low['now']:.0f}% over the same period."
        )
    return headline, follow


def _join_names(names: list[str]) -> str:
    if len(names) < 2:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def _long_date(iso_date: str | None) -> str:
    try:
        d = date.fromisoformat(str(iso_date))
    except (TypeError, ValueError):
        return "n/a"
    return f"{d.day} {d.strftime('%B %Y')}"


def _json_for_script(data: dict[str, Any]) -> str:
    # Company names and titles are scraped from third-party pages. Inside a
    # <script> block the HTML parser ends the script at the first "</script",
    # so escape every "<" and keep scraped text from breaking out of the JSON.
    # U+2028 and U+2029 are legal in JSON but end a line in older JS engines.
    text = json.dumps(data, default=str, ensure_ascii=False).replace("<", "\\u003c")
    for codepoint in (0x2028, 0x2029):
        text = text.replace(chr(codepoint), f"\\u{codepoint:04x}")
    return text


def _build_html(data: dict[str, Any]) -> str:
    """Fill the dashboard template with the headline, ledger and chart data."""
    snapshot = data.get("latestSnapshot", {})
    dates = data.get("trends", {}).get("dates", [])
    sources = [s["name"] for s in snapshot.get("by_source", []) if isinstance(s, dict)]

    headline, follow = _headline(data.get("skillMovers", {}), data.get("lastUpdated"))

    tokens = {
        "__HEADLINE__": escape(headline),
        "__FOLLOW__": escape(follow),
        "__SOURCES__": escape(_join_names(sources) if sources else "Dutch job sites"),
        "__UPDATED__": escape(_long_date(data.get("lastUpdated"))),
        "__SINCE__": escape(_long_date(dates[0] if dates else None)),
        "__OPEN_TODAY__": f"{snapshot.get('total', 0):,}",
        "__TOTAL_POSTINGS__": f"{data.get('totalJobsTracked', 0):,}",
        "__TOTAL_RUNS__": f"{data.get('totalRuns', 0):,}",
        "__TOTAL_OBSERVATIONS__": f"{data.get('totalObservations', 0):,}",
        "__DATA__": _json_for_script(data),
    }

    html = _TEMPLATE_PATH.read_text(encoding="utf-8")
    for token, value in tokens.items():
        html = html.replace(token, value)
    return html
