# AI Job Market Tracker — Netherlands

Scrapes, classifies, and analyses AI/ML/Data Science job listings from Dutch job sites.

## What It Does

1. **Scrapes** job listings from Indeed.nl and Werkenbijdeoverheid.nl
2. **Classifies** each listing using keyword-based NLP:
   - **Category** — ML Engineer, Data Scientist, AI Engineer, NLP, Computer Vision, etc.
   - **Seniority** — Junior, Mid, Senior, Lead, Head
   - **Sector** — Tech, Finance, Healthcare, Consulting, Government, etc.
   - **Skills** — Python, PyTorch, LLM, RAG, Kubernetes, and 25+ more
   - **Remote status** — Remote, Hybrid, Onsite
3. **Analyses** trends with ranked breakdowns and bar charts
4. **Exports** to CSV and JSON for further analysis

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

### Live scraping

```bash
python -m src.main
```

### Custom queries

```bash
python -m src.main -q "generative AI" "LLM engineer" "data scientist" -n 20
```

## Sample Output

```
╭────────────────────────────────────────╮
│ AI/ML Job Market Tracker — Netherlands │
│ 25 jobs scraped and classified         │
╰────────────────────────────────────────╯

╭──────────╮ ╭────────────────╮ ╭────────╮ ╭────────╮
│ 25       │ │ data-scientist │ │ Python │ │ 20.0%  │
│ Total    │ │ Top Category   │ │ Top    │ │ Senior │
╰──────────╯ ╰────────────────╯ ╰────────╯ ╰────────╯

              Most In-Demand Skills
┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━┓
┃  # ┃ Name           ┃ Count ┃ Share ┃ Bar           ┃
┡━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━┩
│  1 │ Python         │    21 │ 84.0% │ ██████████████│
│  2 │ Deep Learning  │     7 │ 28.0% │ █████░░░░░░░░ │
│  3 │ LLM            │     5 │ 20.0% │ ███░░░░░░░░░░ │
│  4 │ NLP            │     5 │ 20.0% │ ███░░░░░░░░░░ │
│  5 │ Kubernetes     │     4 │ 16.0% │ ██░░░░░░░░░░░ │
└────┴────────────────┴───────┴───────┴───────────────┘
```

## CLI Options

| Flag | Description | Default |
|---|---|---|
| `-q` / `--queries` | Custom search queries | Built-in AI/ML terms |
| `-n` / `--max-per-query` | Max results per query per source | 15 |
| `--csv` | CSV export path | `data/jobs.csv` |
| `--json` | JSON export path | `data/results.json` |
| `--no-export` | Skip file export | — |
| `--demo` | Use sample data (no scraping) | — |

## Architecture

```
src/
├── main.py          # CLI entry point
├── scrapers.py      # Indeed.nl + Werkenbijdeoverheid scrapers
├── classifier.py    # NLP keyword classifier (seniority, category, sector, skills, remote)
├── analyzer.py      # Trend analysis and aggregation
├── display.py       # Rich terminal output with tables and charts
├── export.py        # CSV and JSON export
└── models.py        # Job data model
```

## Data Sources

- **Indeed.nl** — Largest job aggregator in the Netherlands
- **Werkenbijdeoverheid.nl** — Dutch government job portal (CC-0 license)

## Tech Stack

- Python 3.9+
- [Requests](https://docs.python-requests.org/) — HTTP client
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [Rich](https://github.com/Textualize/rich) — Terminal formatting

## License

MIT
