import secrets
from datetime import datetime


def generate_certificate_id(prefix: str = "CERT") -> str:
    """
    Generate a professional, readable, collision-resistant Certificate ID.
    Example: CERT-20261007-8F2B9D1A
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(4).upper()
    return f"{prefix}-{date_str}-{random_suffix}"


def generate_verification_token() -> str:
    """
    Generate a cryptographic verification token.
    """
    return secrets.token_urlsafe(32)
