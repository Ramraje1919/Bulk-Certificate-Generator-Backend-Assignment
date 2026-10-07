import logging
import sys
from typing import Any, Dict
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """
    Format logs with structured context and ISO timestamps.
    Provides human-readable output in console while retaining key metadata.
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname
        name = record.name
        message = record.getMessage()

        # Extract extra structured attributes if present
        extra_attrs: Dict[str, Any] = {}
        for key in ("job_id", "certificate_id", "recipient_email", "status", "error"):
            if hasattr(record, key):
                extra_attrs[key] = getattr(record, key)

        if extra_attrs:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in extra_attrs.items())
        else:
            extra_str = ""

        return f"[{timestamp}] [{level:<7}] [{name}] {message}{extra_str}"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure root logging and return application logger.
    """
    logger = logging.getLogger("bulk_certificate_generator")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on re-initialization
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    # Configure uvicorn loggers as well
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
