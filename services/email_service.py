"""
email_service.py
----------------
Sends one email per job with:
  - A plain-text body containing job title, company, and URL.
  - The tailored DOCX resume as an attachment.

Uses Gmail SMTP with an App Password (TLS on port 587).
"""
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import settings
from models.job_model import Job
from utils.logger import get_logger
from utils.helpers import retry

logger = get_logger(__name__)


def _build_email_body(job: Job) -> str:
    return f"""\
Hi,

Please find attached my tailored resume for the {job.title} role at {job.company}.

Job URL: {job.url}

I am excited about the opportunity and believe my background is a strong match \
for what {job.company} is looking for. I look forward to discussing how I can \
contribute to your team.

Thanks & regards,
{settings.SENDER_NAME}
"""


@retry(max_attempts=3, delay=3.0, exceptions=(smtplib.SMTPException, OSError))
def send_application_email(job: Job, resume_path: str) -> None:
    """
    Send one application email for *job* with *resume_path* attached.
    Raises on persistent failure (after retries) so the caller can log and continue.
    """
    if not os.path.exists(resume_path):
        raise FileNotFoundError(
            f"Resume file not found for attachment: {resume_path}"
        )

    subject = f"Application for {job.title} at {job.company}"
    body = _build_email_body(job)

    # ── Build MIME message ────────────────────────────────────────────────────
    msg = MIMEMultipart()
    msg["From"] = settings.EMAIL_USER
    msg["To"] = settings.RECEIVER_EMAIL
    msg["Subject"] = subject
    msg["Reply-To"] = settings.EMAIL_USER

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # ── Attach resume file ────────────────────────────────────────────────────
    attachment_name = os.path.basename(resume_path)
    with open(resume_path, "rb") as fh:
        attachment = MIMEApplication(
            fh.read(),
            _subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    attachment.add_header(
        "Content-Disposition", "attachment", filename=attachment_name
    )
    msg.attach(attachment)

    # ── SMTP send ─────────────────────────────────────────────────────────────
    logger.info(
        f"Sending email for job id={job.id} '{job.title}' @ '{job.company}' "
        f"→ {settings.RECEIVER_EMAIL}"
    )

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        smtp.sendmail(settings.EMAIL_USER, settings.RECEIVER_EMAIL, msg.as_string())

    logger.info(
        f"Email sent successfully for job id={job.id} '{job.title}' "
        f"(attachment: {attachment_name})"
    )
