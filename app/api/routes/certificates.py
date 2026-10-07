from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.certificate import CertificateResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
    summary="Get certificate metadata",
    description="Retrieve details and status for a specific certificate by its public certificate ID."
)
def get_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found."
        )

    verification_url = f"{settings.BASE_URL}{settings.API_V1_STR}/verify/{cert.certificate_id}"
    download_url = f"{settings.BASE_URL}{settings.API_V1_STR}/certificates/{cert.certificate_id}/download" if cert.status == CertificateStatus.SUCCESS else None

    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        certificate_id=cert.certificate_id,
        verification_token=cert.verification_token,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        pdf_path=cert.pdf_path,
        error_message=cert.error_message,
        generated_at=cert.generated_at,
        verification_url=verification_url,
        download_url=download_url,
    )


@router.get(
    "/{certificate_id}/download",
    summary="Download certificate PDF",
    description="Download the generated PDF for an individual certificate."
)
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found."
        )

    if cert.status != CertificateStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not ready for download. Current status: {cert.status.value}. Error: {cert.error_message or 'N/A'}"
        )

    if not cert.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF record exists but path is not registered."
        )

    pdf_file = Path(cert.pdf_path)
    if not pdf_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file is missing on server storage."
        )

    safe_recipient = "".join(c for c in cert.recipient_name if c.isalnum() or c in ("-", "_", " ")).strip()
    download_filename = f"Certificate_{safe_recipient}_{cert.certificate_id}.pdf".replace(" ", "_")

    return FileResponse(
        path=str(pdf_file),
        filename=download_filename,
        media_type="application/pdf",
    )
