"""
main.py
-------
Entry point for the AI Resume Tailoring Agent.

Flow:
  1. Load and validate environment variables.
  2. Parse & merge job data (Excel + JSON).
  3. Read the candidate's base resume.
  4. For each job (independently):
       a. Call Gemini to produce a tailored resume.
       b. Save the tailored resume as a DOCX file.
       c. Send an application email with the resume attached.
  5. Print a final summary of successes and failures.
"""
import sys
from dataclasses import dataclass, field

from config.settings import settings
from models.job_model import Job
from services.parser_service import parse_jobs
from services.document_service import read_resume, save_resume
from services.llm_service import tailor_resume
from services.email_service import send_application_email
from utils.logger import get_logger

logger = get_logger("main")


@dataclass
class JobResult:
    job: Job
    success: bool = False
    resume_path: str = ""
    error: str = ""


def process_job(job: Job, resume_text: str) -> JobResult:
    """
    Process a single job end-to-end.
    All exceptions are caught here so a failure never aborts the pipeline.
    """
    result = JobResult(job=job)

    # ── Step 1: Tailor resume via LLM ────────────────────────────────────────
    try:
        logger.info(f"[Job {job.id}] Tailoring resume …")
        tailored_text = tailor_resume(resume_text, job)
    except Exception as exc:
        result.error = f"LLM error: {exc}"
        logger.error(f"[Job {job.id}] {result.error}", exc_info=True)
        return result

    # ── Step 2: Save tailored DOCX ────────────────────────────────────────────
    try:
        logger.info(f"[Job {job.id}] Saving DOCX …")
        result.resume_path = save_resume(tailored_text, job)
    except Exception as exc:
        result.error = f"Document save error: {exc}"
        logger.error(f"[Job {job.id}] {result.error}", exc_info=True)
        return result

    # ── Step 3: Send email ────────────────────────────────────────────────────
    try:
        logger.info(f"[Job {job.id}] Sending email …")
        send_application_email(job, result.resume_path)
    except Exception as exc:
        # Email failure is logged but does NOT invalidate the saved resume
        result.error = f"Email error (resume saved OK): {exc}"
        logger.error(f"[Job {job.id}] {result.error}", exc_info=True)
        # Mark partial success so we still report the saved file
        result.success = True
        return result

    result.success = True
    return result


def print_summary(results: list[JobResult]) -> None:
    """Print a human-readable run summary to stdout and the log."""
    border = "═" * 60
    logger.info(border)
    logger.info("FINAL SUMMARY")
    logger.info(border)

    successes = [r for r in results if r.success]
    failures  = [r for r in results if not r.success]

    logger.info(f"Total jobs   : {len(results)}")
    logger.info(f"Succeeded    : {len(successes)}")
    logger.info(f"Failed       : {len(failures)}")
    logger.info("")

    for r in successes:
        status = "✓ OK" if not r.error else "✓ PARTIAL (email failed)"
        logger.info(f"  {status}  | Job {r.job.id:>3} | {r.job.title} @ {r.job.company}")
        if r.resume_path:
            logger.info(f"            → {r.resume_path}")
        if r.error:
            logger.info(f"            ⚠  {r.error}")

    for r in failures:
        logger.info(f"  ✗ FAIL    | Job {r.job.id:>3} | {r.job.title} @ {r.job.company}")
        logger.info(f"            → {r.error}")

    logger.info(border)


def main() -> int:
    """
    Main pipeline. Returns 0 on full success, 1 if any job failed.
    """
    logger.info("═" * 60)
    logger.info("AI Resume Tailoring Agent – starting")
    logger.info("═" * 60)

    # ── Validate environment ──────────────────────────────────────────────────
    errors = settings.validate()
    if errors:
        for e in errors:
            logger.critical(e)
        logger.critical("Aborting: fix the issues above and re-run.")
        return 1

    # ── Parse job data ────────────────────────────────────────────────────────
    try:
        jobs = parse_jobs()
    except Exception as exc:
        logger.critical(f"Failed to parse job data: {exc}", exc_info=True)
        return 1

    # ── Read base resume ──────────────────────────────────────────────────────
    try:
        resume_text = read_resume()
    except Exception as exc:
        logger.critical(f"Failed to read resume: {exc}", exc_info=True)
        return 1

    logger.info(f"Processing {len(jobs)} job(s) …\n")

    # ── Process each job independently ────────────────────────────────────────
    results: list[JobResult] = []
    for job in jobs:
        logger.info(f"{'─' * 50}")
        logger.info(f"Processing job {job.id}: {job.title} @ {job.company}")
        result = process_job(job, resume_text)
        results.append(result)

    # ── Summary ───────────────────────────────────────────────────────────────
    print_summary(results)

    any_failure = any(not r.success for r in results)
    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
