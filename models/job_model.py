from dataclasses import dataclass
import re


@dataclass
class Job:
    """Represents a single job posting with all relevant metadata."""
    id: int
    title: str
    company: str
    description: str
    url: str

    def safe_filename_part(self) -> str:
        """Returns a filesystem-safe string combining title and company."""
        raw = f"{self.title}_{self.company}"
        sanitized = re.sub(r"[^\w\s-]", "", raw)
        sanitized = re.sub(r"[\s]+", "_", sanitized.strip())
        return sanitized[:80]  # cap length for OS path limits

    def __repr__(self) -> str:
        return f"<Job id={self.id} title='{self.title}' company='{self.company}'>"
