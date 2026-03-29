"""
Centralized configuration loader.
All settings are pulled from environment variables (via .env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM (Groq)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Email
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    RECEIVER_EMAIL: str = os.getenv("RECEIVER_EMAIL", "")

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "output", "resumes")

    EXCEL_FILE: str = os.path.join(DATA_DIR, "option2_job_links.xlsx")
    JSON_FILE: str = os.path.join(DATA_DIR, "option2_jobs.json")
    RESUME_FILE: str = os.path.join(DATA_DIR, "candidate_resume.docx")

    # Sender name (appears in email body)
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Candidate")

    def validate(self) -> list[str]:
        """Return a list of missing/empty required settings."""
        errors: list[str] = []
        required = {
            "GROQ_API_KEY": self.GROQ_API_KEY,
            "EMAIL_USER": self.EMAIL_USER,
            "EMAIL_PASSWORD": self.EMAIL_PASSWORD,
            "RECEIVER_EMAIL": self.RECEIVER_EMAIL,
        }
        for key, val in required.items():
            if not val:
                errors.append(f"Missing environment variable: {key}")
        return errors


settings = Settings()
