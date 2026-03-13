# AI Job Market Tracker — Netherlands

Scrapes, classifies, and tracks AI/ML/Data Science job listings from Dutch job sites over time. Stores data in SQLite, generates a Chart.js dashboard, and updates automatically every week via GitHub Actions.

**[Live Dashboard](https://hoeberigs.github.io/ai-job-tracker-nl/dashboard.html)**

## What It Does

1. **Scrapes** job listings from Indeed.nl and Werkenbijdeoverheid.nl
2. **Classifies** each listing using keyword-based NLP:
   - **Category** — ML Engineer, Data Scientist, AI Engineer, NLP, Computer Vision, etc.
   - **Seniority** — Junior, Mid, Senior, Lead, Head
   - **Sector** — Tech, Finance, Healthcare, Consulting, Government, etc.
   - **Skills** — Python, PyTorch, LLM, RAG, Kubernetes, and 25+ more
   - **Remote status** — Remote, Hybrid, Onsite
3. **Stores** every scrape run in a SQLite database for historical tracking
4. **Visualises** trends with a Chart.js dashboard (6 interactive charts)
5. **Updates automatically** every Monday via GitHub Actions
6. **Exports** to CSV and JSON for further analysis

## Quick Start

```bash
git clone https://github.com/hoeberigs/ai-job-tracker-nl.git
cd ai-job-tracker-nl
python3 -m venv .venv && source .venv/bin/activate
pip install requests beautifulsoup4 rich
```

### Demo mode (sample data, no scraping)

```bash
python -m src.main --demo
```

### Full pipeline — scrape, classify, save to DB, generate dashboard

```bash
python -m src.main --update
```

### Regenerate dashboard from existing data

```bash
python -m src.main --dashboard
```

### Custom queries

```bash
python -m src.main --update -q "generative AI" "LLM engineer" "data scientist" -n 20
```

## Dashboard

The dashboard is a standalone HTML page at `docs/dashboard.html` with 6 charts:

1. **Skills Trends Over Time** — line chart tracking the top 8 skills across scrape runs
2. **Job Categories** — doughnut chart of the latest category distribution
3. **Seniority Distribution** — horizontal bar chart
4. **Work Arrangement** — remote vs hybrid vs onsite breakdown
5. **Top Companies Hiring** — aggregated across all runs
6. **Jobs Per Run** — bar chart showing volume over time

## CLI Options

| Flag | Description | Default |
|---|---|---|
| `-q` / `--queries` | Custom search queries | Built-in AI/ML terms |
| `-n` / `--max-per-query` | Max results per query per source | 15 |
| `--update` | Full pipeline: scrape + DB + dashboard | — |
| `--dashboard` | Regenerate dashboard from DB (no scraping) | — |
| `--db` | SQLite database path | `data/jobs.db` |
| `--csv` | CSV export path | `data/jobs.csv` |
| `--json` | JSON export path | `data/results.json` |
| `--no-export` | Skip file export | — |
| `--demo` | Use sample data (no scraping) | — |

## Architecture

```
src/
├── main.py          # CLI entry point
├── scrapers.py      # Indeed.nl + Werkenbijdeoverheid scrapers
├── classifier.py    # NLP keyword classifier
├── analyzer.py      # Trend analysis and aggregation
├── database.py      # SQLite persistence layer
├── dashboard.py     # Chart.js HTML dashboard generator
├── display.py       # Rich terminal output
├── export.py        # CSV and JSON export
└── models.py        # Job data model

docs/
├── dashboard.html   # Generated standalone dashboard
└── data.json        # Dashboard data (consumed by website embed)

.github/workflows/
└── update.yml       # Weekly cron — scrape, save, regenerate, push
```

## Automation

The GitHub Actions workflow runs every Monday at 08:00 UTC:

1. Scrapes live job listings from Dutch job sites
2. Classifies each listing
3. Saves to the SQLite database
4. Regenerates the dashboard
5. Commits and pushes the updated files

You can also trigger it manually from the GitHub Actions tab.

## Data Sources

- **Indeed.nl** — Largest job aggregator in the Netherlands
- **Werkenbijdeoverheid.nl** — Dutch government job portal (CC-0 license)

## Tech Stack

- Python 3.9+
- SQLite (standard library — zero config)
- [Chart.js](https://www.chartjs.org/) — Interactive charts (CDN, no build step)
- [Requests](https://docs.python-requests.org/) — HTTP client
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [Rich](https://github.com/Textualize/rich) — Terminal formatting
- GitHub Actions — Automated weekly updates

## License

MIT
