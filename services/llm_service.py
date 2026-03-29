"""
Groq-backed LLM service for resume tailoring.
"""

import hashlib
import re

import requests

from config.settings import settings
from models.job_model import Job
from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _build_focus_angle(job: Job) -> str:
    words = re.findall(r"\b[a-zA-Z]{5,}\b", job.description.lower())
    stopwords = {
        "about", "above", "after", "again", "against", "their", "there",
        "these", "those", "through", "under", "until", "while", "would",
        "should", "could", "which", "within", "across", "using", "based",
        "working", "looking", "including", "experience", "required",
        "responsibilities", "qualifications", "candidate", "position",
        "company", "skills", "years", "ability", "knowledge",
    }
    freq: dict[str, int] = {}
    for word in words:
        if word not in stopwords:
            freq[word] = freq.get(word, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:5]
    return ", ".join(top) if top else job.title


def _build_prompt(resume_text: str, job: Job) -> str:
    focus = _build_focus_angle(job)
    seed = int(hashlib.md5(f"{job.id}{job.title}".encode()).hexdigest()[:6], 16)

    return f"""
You are an expert resume writer.

ORIGINAL RESUME:
{resume_text}

JOB:
Title: {job.title}
Company: {job.company}
Description: {job.description}

Instructions:
- Tailor resume specifically for this job.
- Make it ATS optimized.
- Use keywords: {focus}.
- Make output unique (variant #{seed % 1000}).
- Do NOT add fake experience.

Output format:

[Name]
[Contact]

SUMMARY

SKILLS

EXPERIENCE

PROJECTS

EDUCATION
"""


@retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
def _call_groq(prompt: str) -> str:
    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a precise resume tailoring assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
        },
        timeout=120,
    )

    if response.status_code != 200:
        raise Exception(f"Groq error [{response.status_code}]: {response.text}")

    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise Exception(f"Unexpected Groq response format: {payload}") from exc


def tailor_resume(resume_text: str, job: Job) -> str:
    logger.info(f"Calling Groq for job {job.id}: {job.title}")

    prompt = _build_prompt(resume_text, job)
    tailored = _call_groq(prompt)

    if len(tailored) < 200:
        raise ValueError("Groq returned weak output")

    logger.info(f"Generated resume for job {job.id}")
    return tailored
