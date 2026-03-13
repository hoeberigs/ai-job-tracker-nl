"""Job scrapers for Dutch job listing sites."""

from __future__ import annotations

import re
import time
import random
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from src.models import Job


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SEARCH_QUERIES = [
    "AI engineer",
    "machine learning",
    "data scientist",
    "NLP engineer",
    "MLOps",
    "deep learning",
    "computer vision",
    "LLM",
    "generative AI",
    "AI researcher",
]


class BaseScraper(ABC):
    """Base class for job scrapers."""

    name: str = "base"

    @abstractmethod
    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        ...


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.nl AI/ML job listings."""

    name = "indeed.nl"
    BASE_URL = "https://nl.indeed.com/jobs"

    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        jobs = []
        seen_urls = set()

        for start in range(0, max_results, 10):
            params = {
                "q": query,
                "l": "Nederland",
                "start": str(start),
            }
            try:
                time.sleep(random.uniform(1.5, 3.0))
                resp = requests.get(self.BASE_URL, params=params, headers=HEADERS, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [indeed] Request failed: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.job_seen_beacon") or soup.select("div.jobsearch-ResultsList > div")

            if not cards:
                # Try alternative selectors
                cards = soup.select("td.resultContent") or soup.select("div[data-jk]")

            for card in cards:
                job = self._parse_card(card)
                if job and job.url not in seen_urls:
                    seen_urls.add(job.url)
                    jobs.append(job)

            if len(jobs) >= max_results:
                break

        return jobs[:max_results]

    def _parse_card(self, card) -> Optional[Job]:
        try:
            # Title
            title_el = card.select_one("h2.jobTitle a, a[data-jk], h2 a, .jobTitle span")
            title = title_el.get_text(strip=True) if title_el else ""

            # URL
            link_el = card.select_one("a[href*='/vacature'], a[href*='/rc/clk'], h2.jobTitle a, a[data-jk]")
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = f"https://nl.indeed.com{href}"

            # Company
            company_el = card.select_one("[data-testid='company-name'], .companyName, .company")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location
            loc_el = card.select_one("[data-testid='text-location'], .companyLocation, .location")
            location = loc_el.get_text(strip=True) if loc_el else ""

            # Snippet / description
            snippet_el = card.select_one(".job-snippet, .underShelfFooter, td.snip")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            # Salary
            salary_el = card.select_one("[data-testid='attribute_snippet_testid'], .salary-snippet, .salaryText")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            if not title:
                return None

            return Job(
                title=title,
                company=company,
                location=location,
                url=href,
                source=self.name,
                description=snippet,
                salary=salary,
            )
        except Exception:
            return None


class OverheidScraper(BaseScraper):
    """Scraper for Werkenbijdeoverheid.nl (Dutch government jobs)."""

    name = "werkenbijdeoverheid.nl"
    BASE_URL = "https://www.werkenbijdeoverheid.nl/vacatures"

    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        jobs = []
        seen_urls = set()

        params = {"query": query}
        try:
            time.sleep(random.uniform(1.0, 2.0))
            resp = requests.get(self.BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [overheid] Request failed: {e}")
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("li.search-result, div.vacancy-card, article, .result-item")

        for card in cards[:max_results]:
            job = self._parse_card(card)
            if job and job.url not in seen_urls:
                seen_urls.add(job.url)
                jobs.append(job)

        return jobs[:max_results]

    def _parse_card(self, card) -> Optional[Job]:
        try:
            title_el = card.select_one("h3 a, h2 a, .vacancy-title a, a.result-title")
            title = title_el.get_text(strip=True) if title_el else ""

            href = title_el.get("href", "") if title_el else ""
            if href and not href.startswith("http"):
                href = f"https://www.werkenbijdeoverheid.nl{href}"

            company_el = card.select_one(".organisation, .company, .employer")
            company = company_el.get_text(strip=True) if company_el else "Overheid"

            loc_el = card.select_one(".location, .city, .plaats")
            location = loc_el.get_text(strip=True) if loc_el else ""

            snippet_el = card.select_one(".description, .summary, p")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            if not title:
                return None

            return Job(
                title=title,
                company=company,
                location=location,
                url=href,
                source=self.name,
                description=snippet,
            )
        except Exception:
            return None


def scrape_all(queries: Optional[list[str]] = None, max_per_query: int = 15) -> list[Job]:
    """Scrape all sources for AI/ML jobs in the Netherlands."""
    if queries is None:
        queries = SEARCH_QUERIES

    scrapers: list[BaseScraper] = [
        IndeedScraper(),
        OverheidScraper(),
    ]

    all_jobs: list[Job] = []
    seen_urls: set[str] = set()

    for scraper in scrapers:
        for query in queries:
            print(f"  Scraping {scraper.name} for '{query}'...")
            try:
                jobs = scraper.scrape(query=query, max_results=max_per_query)
                for job in jobs:
                    if job.url and job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
            except Exception as e:
                print(f"  Error scraping {scraper.name} for '{query}': {e}")

    return all_jobs
