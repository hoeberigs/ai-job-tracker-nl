"""NLP-based job classifier using keyword matching.

Classifies jobs by seniority, category, sector, skills, and remote status.
Zero ML dependencies — pure keyword heuristics.
"""

from __future__ import annotations

import re
from src.models import Job


# ── Seniority Classification ──────────────────────────────────────────

SENIORITY_PATTERNS = {
    "head": [
        r"\bhead of\b", r"\bvp\b", r"\bdirector\b", r"\bchief\b",
        r"\bc[a-z]o\b", r"\bvice president\b",
    ],
    "lead": [
        r"\blead\b", r"\bprincipal\b", r"\bstaff\b", r"\barchitect\b",
        r"\bteam lead\b",
    ],
    "senior": [
        r"\bsenior\b", r"\bsr\.?\b", r"\bexperienced\b", r"\biii\b",
    ],
    "mid": [
        r"\bmid[\s-]?level\b", r"\bmedior\b", r"\bii\b", r"\b2\b",
    ],
    "junior": [
        r"\bjunior\b", r"\bjr\.?\b", r"\bentry[\s-]?level\b",
        r"\bintern\b", r"\bstage\b", r"\bstarter\b", r"\bgraduate\b",
        r"\btraineeship\b",
    ],
}


def classify_seniority(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    for level, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return level
    return "unknown"


# ── Job Category Classification ───────────────────────────────────────

CATEGORY_PATTERNS = {
    "ml-engineer": [
        r"\bmachine learning engineer\b", r"\bml engineer\b", r"\bmlops\b",
        r"\bml platform\b", r"\bml infrastructure\b",
    ],
    "data-scientist": [
        r"\bdata scientist\b", r"\bdata science\b", r"\bresearch scientist\b",
        r"\bapplied scientist\b",
    ],
    "ai-engineer": [
        r"\bai engineer\b", r"\bartificial intelligence engineer\b",
        r"\bgenai\b", r"\bgenerative ai\b", r"\bllm engineer\b",
        r"\bprompt engineer\b", r"\bai developer\b",
    ],
    "nlp-engineer": [
        r"\bnlp\b", r"\bnatural language\b", r"\bcomputational linguist\b",
        r"\btext mining\b", r"\bconversational ai\b",
    ],
    "cv-engineer": [
        r"\bcomputer vision\b", r"\bimage\b.*\bengineer\b",
        r"\bvision engineer\b", r"\b3d\b.*\bvision\b",
    ],
    "data-engineer": [
        r"\bdata engineer\b", r"\bdata platform\b", r"\betl\b",
        r"\bdata pipeline\b", r"\bdata infrastructure\b",
    ],
    "data-analyst": [
        r"\bdata analyst\b", r"\bdata analytics\b", r"\bbi analyst\b",
        r"\bbusiness intelligence\b",
    ],
    "ai-researcher": [
        r"\bai research\b", r"\bresearch\b.*\bai\b", r"\bphd\b",
        r"\bdeep learning research\b",
    ],
    "ai-product": [
        r"\bai product\b", r"\bproduct.*ai\b", r"\bai.*product\b",
        r"\bai strategy\b",
    ],
    "ai-manager": [
        r"\bai manager\b", r"\bmanager.*ai\b", r"\bmanager.*data\b",
        r"\bhead.*data\b", r"\bhead.*ai\b",
    ],
}


def classify_category(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    # Fallback
    if re.search(r"\bai\b|\bartificial intelligence\b", text):
        return "ai-general"
    if re.search(r"\bdata\b", text):
        return "data-general"
    return "other"


# ── Sector Classification ─────────────────────────────────────────────

SECTOR_KEYWORDS = {
    "tech": [
        "software", "saas", "cloud", "platform", "startup", "tech",
        "digital", "it", "ict", "cyber", "devops",
    ],
    "finance": [
        "bank", "finance", "fintech", "trading", "insurance",
        "pension", "investment", "financial", "abn", "ing", "rabobank",
    ],
    "healthcare": [
        "health", "medical", "pharma", "biotech", "hospital",
        "clinical", "genomic", "patient", "zorg",
    ],
    "consulting": [
        "consult", "advisory", "deloitte", "mckinsey", "bcg",
        "accenture", "capgemini", "kpmg", "pwc", "ey ",
    ],
    "government": [
        "overheid", "government", "gemeente", "ministerie", "rijks",
        "defensie", "politie", "belastingdienst", "uwv",
    ],
    "retail": [
        "retail", "e-commerce", "ecommerce", "webshop", "bol.com",
        "coolblue", "ahold", "albert heijn", "jumbo",
    ],
    "telecom": [
        "telecom", "kpn", "vodafone", "t-mobile", "ziggo",
    ],
    "energy": [
        "energy", "oil", "gas", "shell", "renewable", "solar",
        "wind", "sustainability", "energie",
    ],
    "logistics": [
        "logistics", "supply chain", "transport", "shipping",
        "warehouse", "post nl", "dhl",
    ],
    "academia": [
        "university", "universiteit", "research", "academic",
        "professor", "postdoc", "phd",
    ],
}


def classify_sector(company: str, title: str = "", description: str = "") -> str:
    text = f"{company} {title} {description}".lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return sector
    return "other"


# ── Skills Extraction ─────────────────────────────────────────────────

SKILL_PATTERNS = {
    "Python": r"\bpython\b",
    "R": r"\br\b(?:\s+programming|\s+studio|\s+language)",
    "SQL": r"\bsql\b",
    "Spark": r"\bspark\b|\bpyspark\b",
    "TensorFlow": r"\btensorflow\b|\btf\b",
    "PyTorch": r"\bpytorch\b|\btorch\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Docker": r"\bdocker\b",
    "AWS": r"\baws\b|\bamazon web\b",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|\bgoogle cloud\b",
    "Databricks": r"\bdatabricks\b",
    "MLflow": r"\bmlflow\b",
    "Hugging Face": r"\bhugging\s?face\b|\btransformers\b",
    "LangChain": r"\blangchain\b",
    "RAG": r"\brag\b|\bretrieval.augmented\b",
    "LLM": r"\bllm\b|\blarge language\b",
    "NLP": r"\bnlp\b|\bnatural language\b",
    "Computer Vision": r"\bcomputer vision\b|\bcv\b|\bopencv\b",
    "Deep Learning": r"\bdeep learning\b",
    "Airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "Tableau": r"\btableau\b",
    "Power BI": r"\bpower\s?bi\b",
    "Git": r"\bgit\b",
    "CI/CD": r"\bci/?cd\b",
    "Agile": r"\bagile\b|\bscrum\b",
}


def extract_skills(title: str, description: str = "") -> list[str]:
    text = f"{title} {description}".lower()
    found = []
    for skill, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text):
            found.append(skill)
    return sorted(found)


# ── Remote Classification ─────────────────────────────────────────────

def classify_remote(title: str, location: str = "", description: str = "") -> str:
    text = f"{title} {location} {description}".lower()
    if re.search(r"\bremote\b|\bfully remote\b|\b100% remote\b|\bthuiswerk\b", text):
        return "remote"
    if re.search(r"\bhybrid\b|\bhybride\b|\bdeels thuis\b", text):
        return "hybrid"
    if re.search(r"\bon[\s-]?site\b|\bop locatie\b|\bop kantoor\b", text):
        return "onsite"
    return "unknown"


# ── Main Classifier ───────────────────────────────────────────────────

def classify_job(job: Job) -> Job:
    """Classify a job in-place and return it."""
    text = f"{job.title} {job.description}"
    job.seniority = classify_seniority(job.title, job.description)
    job.category = classify_category(job.title, job.description)
    job.sector = classify_sector(job.company, job.title, job.description)
    job.skills = extract_skills(job.title, job.description)
    job.remote = classify_remote(job.title, job.location, job.description)
    return job


def classify_all(jobs: list[Job]) -> list[Job]:
    """Classify all jobs."""
    return [classify_job(job) for job in jobs]
