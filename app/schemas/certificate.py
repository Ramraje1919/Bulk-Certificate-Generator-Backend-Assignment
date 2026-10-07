from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.certificate import CertificateStatus


class CertificateResponse(BaseModel):
    id: str
    job_id: str
    certificate_id: str
    verification_token: str
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None
    verification_url: Optional[str] = None
    download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CertificateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CertificateResponse]
