#!/usr/bin/env python3
"""AI/ML Job Market Tracker — Netherlands.

Scrapes, classifies, and analyses AI/ML job listings from Dutch job sites.
Supports historical tracking via SQLite and dashboard generation.
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from src.scrapers import scrape_all, SEARCH_QUERIES
from src.classifier import classify_all
from src.analyzer import analyze
from src.display import display_results
from src.export import export_csv, export_json

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="AI/ML Job Market Tracker — Netherlands",
    )
    parser.add_argument(
        "-q", "--queries",
        nargs="+",
        default=None,
        help="Custom search queries (default: built-in AI/ML terms)",
    )
    parser.add_argument(
        "-n", "--max-per-query",
        type=int,
        default=15,
        help="Max results per query per source (default: 15)",
    )
    parser.add_argument(
        "--csv",
        default="data/jobs.csv",
        help="CSV export path (default: data/jobs.csv)",
    )
    parser.add_argument(
        "--json",
        default="data/results.json",
        help="JSON export path (default: data/results.json)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip file export",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with sample data (no scraping)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Full pipeline: scrape → classify → save to DB → regenerate dashboard",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Regenerate dashboard from existing database (no scraping)",
    )
    parser.add_argument(
        "--db",
        default="data/jobs.db",
        help="SQLite database path (default: data/jobs.db)",
    )
    args = parser.parse_args()

    # Dashboard-only mode: regenerate from existing DB
    if args.dashboard and not args.update:
        console.print()
        console.print("[bold bright_blue]AI/ML Job Market Tracker — Netherlands[/]")
        console.print("[dim]Regenerating dashboard from database...[/]")
        console.print()
        _regenerate_dashboard(args.db)
        return

    console.print()
    console.print("[bold bright_blue]AI/ML Job Market Tracker — Netherlands[/]")
    console.print("[dim]Scraping, classifying, and analysing...[/]")
    console.print()

    # Scrape
    if args.demo:
        console.print("[yellow]Running in demo mode with sample data[/]")
        jobs = _demo_jobs()
    else:
        with console.status("[bold green]Scraping job listings..."):
            jobs = scrape_all(
                queries=args.queries,
                max_per_query=args.max_per_query,
            )

    console.print(f"  Found [bold]{len(jobs)}[/] unique listings")

    # Classify
    with console.status("[bold green]Classifying jobs..."):
        jobs = classify_all(jobs)

    console.print(f"  Classified [bold]{len(jobs)}[/] jobs")

    # Analyse
    analysis = analyze(jobs)

    # Display
    display_results(jobs, analysis)

    # Export
    if not args.no_export and jobs:
        csv_path = export_csv(jobs, args.csv)
        json_path = export_json(jobs, analysis, args.json)
        console.print(f"[green]Exported to {csv_path} and {json_path}[/]")

    # Save to database and regenerate dashboard
    if args.update and jobs:
        _save_and_update(args.db, jobs, source="demo" if args.demo else "manual")


def _save_and_update(db_path: str, jobs: list, source: str = "manual"):
    """Save jobs to database and regenerate dashboard."""
    from src.database import init_db, save_run

    with console.status("[bold green]Saving to database..."):
        conn = init_db(db_path)
        run_id = save_run(conn, jobs, source=source)
        conn.close()

    console.print(f"  Saved run #{run_id} to [bold]{db_path}[/]")
    _regenerate_dashboard(db_path)


def _regenerate_dashboard(db_path: str):
    """Regenerate the dashboard HTML and JSON from the database."""
    from src.dashboard import generate_dashboard

    with console.status("[bold green]Generating dashboard..."):
        html_path, json_path = generate_dashboard(db_path=db_path)

    console.print(f"  Dashboard generated: [bold]{html_path}[/]")
    console.print(f"  Data JSON: [bold]{json_path}[/]")


def _demo_jobs():
    """Generate sample jobs for demo mode."""
    from src.models import Job

    samples = [
        Job("Senior Machine Learning Engineer", "Booking.com", "Amsterdam", "https://booking.com/careers/1", "indeed.nl",
            "Build and deploy ML models at scale. Python, PyTorch, Kubernetes, AWS. Hybrid work."),
        Job("AI Engineer — Generative AI", "ING Bank", "Amsterdam", "https://ing.com/careers/2", "indeed.nl",
            "Develop LLM-based applications for banking. Python, LangChain, RAG, Azure. Senior level."),
        Job("Data Scientist", "Philips", "Eindhoven", "https://philips.com/careers/3", "indeed.nl",
            "Apply deep learning to medical imaging. Python, TensorFlow, computer vision. Healthcare innovation."),
        Job("Junior Data Analyst", "Coolblue", "Rotterdam", "https://coolblue.nl/careers/4", "indeed.nl",
            "Analyse e-commerce data. SQL, Python, Tableau, Power BI. Agile team."),
        Job("MLOps Engineer", "Adyen", "Amsterdam", "https://adyen.com/careers/5", "indeed.nl",
            "Build ML infrastructure and CI/CD pipelines. Docker, Kubernetes, MLflow, Python, AWS."),
        Job("NLP Engineer", "Ahold Delhaize", "Zaandam", "https://ahold.com/careers/6", "indeed.nl",
            "Develop NLP solutions for retail. Hugging Face, Python, transformers, deep learning."),
        Job("Head of Data Science", "bol.com", "Utrecht", "https://bol.com/careers/7", "indeed.nl",
            "Lead a team of 15+ data scientists. Strategy, stakeholder management, Python, Databricks."),
        Job("Computer Vision Researcher", "TomTom", "Amsterdam", "https://tomtom.com/careers/8", "indeed.nl",
            "Research autonomous driving perception. PyTorch, deep learning, computer vision. PhD preferred."),
        Job("Lead AI Engineer", "Rabobank", "Utrecht", "https://rabobank.com/careers/9", "indeed.nl",
            "Lead GenAI initiatives for banking. LLM, RAG, Python, Azure, responsible AI."),
        Job("Data Engineer — AI Platform", "KLM", "Schiphol", "https://klm.com/careers/10", "indeed.nl",
            "Build data pipelines for ML models. Spark, Airflow, dbt, Python, GCP."),
        Job("AI Researcher — Reinforcement Learning", "Universiteit van Amsterdam", "Amsterdam",
            "https://uva.nl/careers/11", "indeed.nl",
            "Postdoc position in RL research. Deep learning, Python, PyTorch. Academic track."),
        Job("Medior Data Scientist", "ABN AMRO", "Amsterdam", "https://abnamro.com/careers/12", "indeed.nl",
            "Fraud detection and risk modelling. Python, SQL, Spark, machine learning."),
        Job("AI Product Manager", "Elsevier", "Amsterdam", "https://elsevier.com/careers/13", "indeed.nl",
            "Define AI product roadmap for scientific publishing. NLP, LLM, stakeholder management."),
        Job("Machine Learning Engineer", "ASML", "Veldhoven", "https://asml.com/careers/14", "indeed.nl",
            "Apply ML to semiconductor manufacturing. Python, deep learning, computer vision. Senior."),
        Job("Data Scientist — Sustainability", "Shell", "Den Haag", "https://shell.com/careers/15", "indeed.nl",
            "ML for energy optimisation. Python, TensorFlow, time series, remote option."),
        Job("Junior AI Developer", "Deloitte", "Amsterdam", "https://deloitte.com/careers/16", "indeed.nl",
            "GenAI consulting projects. Python, LLM, prompt engineering. Graduate programme."),
        Job("Senior Data Analyst", "Heineken", "Amsterdam", "https://heineken.com/careers/17", "indeed.nl",
            "Supply chain analytics. SQL, Python, Power BI, Tableau. Hybrid."),
        Job("AI Beleidsadviseur", "Ministerie van BZK", "Den Haag",
            "https://werkenbijdeoverheid.nl/vacatures/18", "werkenbijdeoverheid.nl",
            "AI policy and governance for the Dutch government."),
        Job("Data Scientist", "Rijkswaterstaat", "Utrecht",
            "https://werkenbijdeoverheid.nl/vacatures/19", "werkenbijdeoverheid.nl",
            "Machine learning for water management. Python, GCP, deep learning."),
        Job("AI Engineer", "Belastingdienst", "Apeldoorn",
            "https://werkenbijdeoverheid.nl/vacatures/20", "werkenbijdeoverheid.nl",
            "Develop AI solutions for tax services. Python, NLP, responsible AI, Azure."),
        Job("Lead Machine Learning Engineer", "Spotify", "Amsterdam", "https://spotify.com/careers/21", "indeed.nl",
            "Recommendation systems at scale. Python, TensorFlow, Kubernetes, A/B testing."),
        Job("Senior Data Scientist — GenAI", "Accenture", "Amsterdam", "https://accenture.com/careers/22", "indeed.nl",
            "Client-facing GenAI projects. LLM, RAG, Python, Azure, consulting."),
        Job("AI Ethics Researcher", "TNO", "Den Haag", "https://tno.nl/careers/23", "indeed.nl",
            "Research responsible AI frameworks. Policy, NLP, fairness, explainability."),
        Job("Data Platform Engineer", "Takeaway.com", "Amsterdam", "https://takeaway.com/careers/24", "indeed.nl",
            "Build real-time ML platforms. Kafka, Spark, Python, Kubernetes, AWS."),
        Job("Machine Learning Intern", "Uber", "Amsterdam", "https://uber.com/careers/25", "indeed.nl",
            "Summer internship in ML team. Python, deep learning, NLP. Graduate level."),
    ]
    return samples


if __name__ == "__main__":
    main()
