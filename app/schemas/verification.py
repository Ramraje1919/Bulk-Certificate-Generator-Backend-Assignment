from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_id: str
    recipient: Optional[str] = None
    event: Optional[str] = None
    issue_date: Optional[date] = None
    issued_by: Optional[str] = None
    status: Optional[str] = None
    generated_at: Optional[datetime] = None
    verification_token: Optional[str] = None
    message: str
