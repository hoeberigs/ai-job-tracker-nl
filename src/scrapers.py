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
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
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


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn public job search (no auth required)."""

    name = "linkedin.com"
    BASE_URL = "https://www.linkedin.com/jobs/search"

    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        jobs = []
        seen_urls = set()

        params = {
            "keywords": query,
            "location": "Netherlands",
            "position": "1",
            "pageNum": "0",
        }
        try:
            time.sleep(random.uniform(1.5, 3.0))
            resp = requests.get(self.BASE_URL, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [linkedin] Request failed: {e}")
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.base-card")

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
            title_el = card.select_one("h3.base-search-card__title")
            title = title_el.get_text(strip=True) if title_el else ""

            link_el = card.select_one("a.base-card__full-link")
            href = link_el.get("href", "") if link_el else ""
            # Clean tracking params from URL
            if "?" in href:
                href = href.split("?")[0]

            company_el = card.select_one("h4.base-search-card__subtitle a")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.select_one("span.job-search-card__location")
            location = loc_el.get_text(strip=True) if loc_el else ""

            date_el = card.select_one("time")
            posted_date = date_el.get("datetime", "") if date_el else ""

            if not title:
                return None

            return Job(
                title=title,
                company=company,
                location=location,
                url=href,
                source=self.name,
                description="",
                posted_date=posted_date,
            )
        except Exception:
            return None


class JobbirdScraper(BaseScraper):
    """Scraper for Jobbird.com (Dutch job site, reliable HTML)."""

    name = "jobbird.com"
    BASE_URL = "https://www.jobbird.com/nl/vacature"

    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        jobs = []
        seen_urls = set()

        params = {"s": query, "l": "Nederland"}
        try:
            time.sleep(random.uniform(1.0, 2.5))
            resp = requests.get(self.BASE_URL, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [jobbird] Request failed: {e}")
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.job-search__result-list__result")

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
            title_el = card.select_one("a.job-search__result-list__result__title")
            title = title_el.get_text(strip=True) if title_el else ""
            href = title_el.get("href", "") if title_el else ""

            company_el = card.select_one(".cro-recruiter-name span")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.select_one(".cro-job-location span a, .cro-job-location span")
            location = loc_el.get_text(strip=True) if loc_el else ""

            salary_el = card.select_one(".cro-job-salary span:not(.icon-wrapper)")
            salary = ""
            if salary_el:
                salary_text = salary_el.get_text(strip=True)
                if salary_text and salary_text != salary_el.parent.get_text(strip=True):
                    salary = salary_text
                else:
                    # Get last span text
                    spans = card.select(".cro-job-salary span")
                    for s in spans:
                        t = s.get_text(strip=True)
                        if t and not s.select("i"):
                            salary = t
                            break

            if not title:
                return None

            return Job(
                title=title,
                company=company,
                location=location,
                url=href,
                source=self.name,
                description="",
                salary=salary,
            )
        except Exception:
            return None


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.nl — kept as fallback but may be blocked by bot detection."""

    name = "indeed.nl"
    BASE_URL = "https://nl.indeed.com/jobs"

    def scrape(self, query: str = "AI", max_results: int = 25) -> list[Job]:
        jobs = []
        seen_urls = set()

        session = requests.Session()
        session.headers.update(HEADERS)

        for start in range(0, max_results, 10):
            params = {
                "q": query,
                "l": "Nederland",
                "start": str(start),
            }
            try:
                time.sleep(random.uniform(2.0, 4.0))
                resp = session.get(self.BASE_URL, params=params, timeout=15)
                if resp.status_code == 403:
                    print(f"  [indeed] Blocked (403) — skipping")
                    return jobs
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [indeed] Request failed: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = (
                soup.select("div.job_seen_beacon")
                or soup.select("div.jobsearch-ResultsList > div")
                or soup.select("td.resultContent")
                or soup.select("div[data-jk]")
            )

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
            title_el = card.select_one("h2.jobTitle a, a[data-jk], h2 a, .jobTitle span")
            title = title_el.get_text(strip=True) if title_el else ""

            link_el = card.select_one("a[href*='/vacature'], a[href*='/rc/clk'], h2.jobTitle a, a[data-jk]")
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = f"https://nl.indeed.com{href}"

            company_el = card.select_one("[data-testid='company-name'], .companyName, .company")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.select_one("[data-testid='text-location'], .companyLocation, .location")
            location = loc_el.get_text(strip=True) if loc_el else ""

            snippet_el = card.select_one(".job-snippet, .underShelfFooter, td.snip")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

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


def scrape_all(queries: Optional[list[str]] = None, max_per_query: int = 15) -> list[Job]:
    """Scrape all sources for AI/ML jobs in the Netherlands."""
    if queries is None:
        queries = SEARCH_QUERIES

    scrapers: list[BaseScraper] = [
        LinkedInScraper(),
        JobbirdScraper(),
        IndeedScraper(),
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

    print(f"\n  Total: {len(all_jobs)} unique jobs from {len(scrapers)} sources")
    return all_jobs
