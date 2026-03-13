"""Generate a standalone HTML dashboard with Chart.js visualisations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.database import get_dashboard_data


def generate_dashboard(
    db_path: str = "data/jobs.db",
    output_dir: str = "docs",
) -> tuple[str, str]:
    """Generate dashboard.html and data.json. Returns (html_path, json_path)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    data = get_dashboard_data(db_path)

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


def _build_html(data: dict[str, Any]) -> str:
    """Build the complete dashboard HTML string."""
    snapshot = data.get("latestSnapshot", {})
    trends = data.get("trends", {})
    top_companies = data.get("topCompanies", [])

    # Extract summary stats
    total_tracked = data.get("totalJobsTracked", 0)
    total_runs = data.get("totalRuns", 0)
    last_updated = data.get("lastUpdated", "—")

    top_skill = "—"
    skills_list = snapshot.get("top_skills", [])
    if skills_list:
        top_skill = skills_list[0]["name"] if isinstance(skills_list[0], dict) else skills_list[0][0]

    top_category = "—"
    cat_list = snapshot.get("by_category", [])
    if cat_list:
        top_category = cat_list[0]["name"] if isinstance(cat_list[0], dict) else cat_list[0][0]

    latest_total = snapshot.get("total", 0)

    # Chart data
    chart_data = json.dumps(data, default=str)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Job Market Dashboard — Netherlands</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --accent: #6b5ce7;
            --accent-light: #8b7cf0;
            --teal: #2dd4bf;
            --warm: #f59e0b;
            --rose: #f43f5e;
            --sky: #38bdf8;
            --emerald: #34d399;
            --violet: #a78bfa;
            --orange: #fb923c;
            --charcoal: #1e1b2e;
            --dark: #2a2742;
            --card-bg: #ffffff;
            --bg: #f8f7fc;
            --text: #1e1b2e;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --radius: 16px;
            --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
        }}

        header h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
        }}

        header h1 span {{
            background: linear-gradient(135deg, var(--accent), var(--teal));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        header p {{
            color: var(--text-muted);
            font-size: 0.95rem;
        }}

        /* Stat Cards */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.25rem;
            box-shadow: var(--shadow);
            text-align: center;
            border: 1px solid var(--border);
        }}

        .stat-card .value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--accent);
            line-height: 1.2;
        }}

        .stat-card .label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        }}

        /* Chart Grid */
        .charts {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }}

        .chart-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }}

        .chart-card.wide {{
            grid-column: 1 / -1;
        }}

        .chart-card h3 {{
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--charcoal);
        }}

        .chart-container {{
            position: relative;
            width: 100%;
            height: 300px;
        }}

        .chart-container.short {{
            height: 250px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 2.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        footer a {{
            color: var(--accent);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .charts {{
                grid-template-columns: 1fr;
            }}
            header h1 {{
                font-size: 1.5rem;
            }}
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }}

        .empty-state h2 {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
            color: var(--charcoal);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><span>AI/ML Job Market</span> — Netherlands</h1>
            <p>Live tracker &middot; Updated {last_updated} &middot; {total_runs} scrape runs</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{total_tracked}</div>
                <div class="label">Jobs Tracked</div>
            </div>
            <div class="stat-card">
                <div class="value">{latest_total}</div>
                <div class="label">Latest Run</div>
            </div>
            <div class="stat-card">
                <div class="value" style="font-size:1.1rem;">{top_skill}</div>
                <div class="label">Top Skill</div>
            </div>
            <div class="stat-card">
                <div class="value" style="font-size:1.1rem;">{top_category}</div>
                <div class="label">Top Category</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-card wide">
                <h3>Most In-Demand Skills Over Time</h3>
                <div class="chart-container">
                    <canvas id="skillsTrend"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>Job Categories</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>Seniority Distribution</h3>
                <div class="chart-container">
                    <canvas id="seniorityChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>Work Arrangement</h3>
                <div class="chart-container short">
                    <canvas id="remoteChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>Top Companies Hiring</h3>
                <div class="chart-container short">
                    <canvas id="companiesChart"></canvas>
                </div>
            </div>

            <div class="chart-card wide">
                <h3>Jobs Per Scrape Run</h3>
                <div class="chart-container short">
                    <canvas id="runsChart"></canvas>
                </div>
            </div>
        </div>

        <footer>
            <p>
                Built by <a href="https://lindahoeberigs.com">Linda Hoeberigs</a> &middot;
                <a href="https://github.com/hoeberigs/ai-job-tracker-nl">View on GitHub</a>
            </p>
        </footer>
    </div>

    <script>
    const DATA = {chart_data};

    const COLORS = [
        '#6b5ce7', '#2dd4bf', '#f59e0b', '#f43f5e',
        '#38bdf8', '#34d399', '#a78bfa', '#fb923c',
        '#ec4899', '#14b8a6'
    ];

    const chartDefaults = {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{
                labels: {{
                    font: {{ family: "'Inter', sans-serif", size: 11 }},
                    usePointStyle: true,
                    pointStyle: 'circle',
                    padding: 16
                }}
            }}
        }}
    }};

    // --- Skills Trend (Line) ---
    const skillsTrend = DATA.trends || {{}};
    const skillNames = Object.keys(skillsTrend.skills || {{}});

    if (skillNames.length > 0 && (skillsTrend.dates || []).length > 0) {{
        new Chart(document.getElementById('skillsTrend'), {{
            type: 'line',
            data: {{
                labels: skillsTrend.dates,
                datasets: skillNames.map((name, i) => ({{
                    label: name,
                    data: skillsTrend.skills[name],
                    borderColor: COLORS[i % COLORS.length],
                    backgroundColor: COLORS[i % COLORS.length] + '20',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    borderWidth: 2.5
                }}))
            }},
            options: {{
                ...chartDefaults,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{ font: {{ size: 11 }}, stepSize: 1 }}
                    }},
                    x: {{
                        ticks: {{ font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});
    }}

    // --- Doughnut percentage plugin ---
    const pctPlugin = {{
        id: 'doughnutPct',
        afterDraw(chart) {{
            const {{ ctx, data }} = chart;
            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
            if (!total) return;
            chart.getDatasetMeta(0).data.forEach((arc, i) => {{
                const val = data.datasets[0].data[i];
                const pct = Math.round(val / total * 100);
                if (pct < 5) return; // skip tiny slices
                const {{ x, y }} = arc.tooltipPosition();
                ctx.save();
                ctx.fillStyle = '#1e1b2e';
                ctx.font = "600 11px 'Inter', sans-serif";
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(pct + '%', x, y);
                ctx.restore();
            }});
        }}
    }};

    // --- Category (Doughnut) ---
    const cats = (DATA.latestSnapshot || {{}}).by_category || [];
    if (cats.length > 0) {{
        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: cats.map(c => c.name),
                datasets: [{{
                    data: cats.map(c => c.count),
                    backgroundColor: COLORS.slice(0, cats.length),
                    borderWidth: 0,
                    hoverOffset: 8
                }}]
            }},
            plugins: [pctPlugin],
            options: {{
                ...chartDefaults,
                cutout: '55%',
                plugins: {{
                    ...chartDefaults.plugins,
                    legend: {{
                        ...chartDefaults.plugins.legend,
                        position: 'right'
                    }}
                }}
            }}
        }});
    }}

    // --- Seniority (Horizontal Bar) ---
    const seniorityRaw = (DATA.latestSnapshot || {{}}).by_seniority || [];
    const seniority = seniorityRaw.filter(s => s.name !== 'unknown');
    if (seniority.length > 0) {{
        new Chart(document.getElementById('seniorityChart'), {{
            type: 'bar',
            data: {{
                labels: seniority.map(s => s.name),
                datasets: [{{
                    data: seniority.map(s => s.count),
                    backgroundColor: COLORS.slice(0, seniority.length),
                    borderRadius: 6,
                    borderSkipped: false
                }}]
            }},
            options: {{
                ...chartDefaults,
                indexAxis: 'y',
                plugins: {{ ...chartDefaults.plugins, legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, ticks: {{ stepSize: 1, font: {{ size: 11 }} }} }},
                    y: {{ ticks: {{ font: {{ size: 12 }} }} }}
                }}
            }}
        }});
    }}

    // --- Remote (Doughnut) ---
    const remote = (DATA.latestSnapshot || {{}}).by_remote || [];
    if (remote.length > 0) {{
        const remoteColors = {{
            'remote': '#34d399',
            'hybrid': '#38bdf8',
            'onsite': '#f59e0b',
            'unknown': '#d1d5db'
        }};
        new Chart(document.getElementById('remoteChart'), {{
            type: 'doughnut',
            data: {{
                labels: remote.map(r => r.name),
                datasets: [{{
                    data: remote.map(r => r.count),
                    backgroundColor: remote.map(r => remoteColors[r.name] || '#d1d5db'),
                    borderWidth: 0,
                    hoverOffset: 8
                }}]
            }},
            plugins: [pctPlugin],
            options: {{
                ...chartDefaults,
                cutout: '55%',
                plugins: {{
                    ...chartDefaults.plugins,
                    legend: {{
                        ...chartDefaults.plugins.legend,
                        position: 'right'
                    }}
                }}
            }}
        }});
    }}

    // --- Top Companies (Horizontal Bar) ---
    const companies = DATA.topCompanies || [];
    if (companies.length > 0) {{
        new Chart(document.getElementById('companiesChart'), {{
            type: 'bar',
            data: {{
                labels: companies.map(c => c.name),
                datasets: [{{
                    data: companies.map(c => c.count),
                    backgroundColor: '#6b5ce7',
                    borderRadius: 6,
                    borderSkipped: false
                }}]
            }},
            options: {{
                ...chartDefaults,
                indexAxis: 'y',
                plugins: {{ ...chartDefaults.plugins, legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, ticks: {{ stepSize: 1, font: {{ size: 11 }} }} }},
                    y: {{ ticks: {{ font: {{ size: 11 }} }} }}
                }}
            }}
        }});
    }}

    // --- Jobs Per Run (Bar) ---
    const runDates = (skillsTrend.dates || []);
    const runTotals = (skillsTrend.totalPerRun || []);
    if (runDates.length > 0) {{
        new Chart(document.getElementById('runsChart'), {{
            type: 'bar',
            data: {{
                labels: runDates,
                datasets: [{{
                    label: 'Jobs found',
                    data: runTotals,
                    backgroundColor: '#6b5ce7',
                    borderRadius: 8,
                    borderSkipped: false
                }}]
            }},
            options: {{
                ...chartDefaults,
                plugins: {{ ...chartDefaults.plugins, legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ stepSize: 5, font: {{ size: 11 }} }} }},
                    x: {{ ticks: {{ font: {{ size: 11 }} }} }}
                }}
            }}
        }});
    }}
    </script>
</body>
</html>"""
