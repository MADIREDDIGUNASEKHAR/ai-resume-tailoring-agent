"""
General-purpose utility functions.
"""
import os
import re
import time
import functools
from typing import Callable, TypeVar, Any

from utils.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_attempts: int = 3, delay: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator that retries a function up to *max_attempts* times on failure.
    Waits *delay* seconds (doubled each retry) between attempts.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            wait = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        f"[retry] {func.__name__} attempt {attempt}/{max_attempts} "
                        f"failed: {exc}. Retrying in {wait:.1f}s …"
                    )
                    if attempt < max_attempts:
                        time.sleep(wait)
                        wait *= 2
            raise last_exc  # re-raise after all retries exhausted
        return wrapper  # type: ignore[return-value]
    return decorator


def ensure_dir(path: str) -> str:
    """Create directory (and parents) if it does not exist. Returns *path*."""
    os.makedirs(path, exist_ok=True)
    return path


def sanitize_filename(name: str, max_len: int = 100) -> str:
    """Strip illegal filesystem characters and cap length."""
    name = re.sub(r"[^\w\s\-.]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]
