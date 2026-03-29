"""
parser_service.py
-----------------
Responsible for:
  - Reading the Excel file (job id → URL)
  - Reading the JSON file  (job details)
  - Merging both datasets into a list of Job objects
"""
import json
from typing import Any

import openpyxl

from config.settings import settings
from models.job_model import Job
from utils.logger import get_logger

logger = get_logger(__name__)


def _read_excel(path: str) -> dict[int, str]:
    """
    Parse the Excel file and return a mapping of {job_id: url}.

    Expected columns (row 1 = header):
        Column A  →  # (job id, integer)
        Column B  →  URL
    """
    logger.info(f"Reading Excel file: {path}")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    id_to_url: dict[int, str] = {}
    rows = list(ws.iter_rows(values_only=True))

    if not rows:
        raise ValueError(f"Excel file '{path}' is empty.")

    # Detect header row – skip it
    header = rows[0]
    logger.debug(f"Excel header: {header}")
    normalized_header = [
        str(cell).strip().lower() if cell is not None else ""
        for cell in header
    ]
    id_col = next(
        (idx for idx, name in enumerate(normalized_header) if name in {"#", "id", "job id"}),
        0,
    )
    url_col = next(
        (idx for idx, name in enumerate(normalized_header) if name == "url"),
        1,
    )

    for row_idx, row in enumerate(rows[1:], start=2):
        try:
            job_id = int(row[id_col])
            url = str(row[url_col]).strip() if row[url_col] else ""
            id_to_url[job_id] = url
        except (TypeError, ValueError, IndexError) as exc:
            logger.warning(f"Skipping Excel row {row_idx} due to parse error: {exc} | row={row}")

    logger.info(f"Loaded {len(id_to_url)} job URL(s) from Excel.")
    wb.close()
    return id_to_url


def _read_json(path: str) -> list[dict[str, Any]]:
    """
    Parse the JSON file.

    Supports two shapes:
      - A JSON array: [{id, title, company, description}, …]
      - A JSON object with a top-level list key (e.g. {"jobs": […]})
    """
    logger.info(f"Reading JSON file: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, list):
        jobs_raw = data
    elif isinstance(data, dict):
        # Find the first list value
        jobs_raw = next(
            (v for v in data.values() if isinstance(v, list)), []
        )
    else:
        raise ValueError(f"Unexpected JSON structure in '{path}'.")

    logger.info(f"Loaded {len(jobs_raw)} job record(s) from JSON.")
    return jobs_raw


def parse_jobs() -> list[Job]:
    """
    Main entry point.
    Reads Excel + JSON, merges on id, and returns a validated list of Job objects.
    Logs a warning for any jobs that cannot be merged.
    """
    id_to_url = _read_excel(settings.EXCEL_FILE)
    jobs_raw = _read_json(settings.JSON_FILE)

    jobs: list[Job] = []

    for record in jobs_raw:
        try:
            job_id = int(record["id"])
            title = str(record.get("title", "")).strip()
            company = str(record.get("company", "")).strip()
            description = str(record.get("description", "")).strip()

            url = id_to_url.get(job_id, "")
            if not url:
                logger.warning(
                    f"Job id={job_id} ('{title}' @ '{company}') has no URL in Excel. "
                    "Skipping URL field but still processing."
                )

            if not title or not company:
                logger.warning(
                    f"Job id={job_id} is missing title or company – skipping."
                )
                continue

            job = Job(
                id=job_id,
                title=title,
                company=company,
                description=description,
                url=url,
            )
            jobs.append(job)
            logger.debug(f"Merged {job}")

        except (KeyError, TypeError, ValueError) as exc:
            logger.error(f"Failed to parse job record {record}: {exc}")

    if not jobs:
        raise RuntimeError("No valid jobs were parsed. Check your input files.")

    logger.info(f"Successfully merged {len(jobs)} job(s).")
    return jobs
