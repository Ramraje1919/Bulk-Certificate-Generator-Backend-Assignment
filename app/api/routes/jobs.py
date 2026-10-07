from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreate, JobCreateResponse, JobResponse
from app.schemas.certificate import CertificateResponse, CertificateListResponse
from app.services.job_service import JobService
from app.services.zip_service import ZipService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create bulk certificate generation job",
    description="Validates recipient payloads, creates records, and queues async background generation."
)
def create_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = JobService.create_job(db=db, job_in=job_in)
    # Queue background generation
    background_tasks.add_task(JobService.process_job_background, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        message="Bulk certificate generation job accepted and processing in background."
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details and progress",
    description="Poll job execution status, recipient counts, and progress percentage."
)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return job


@router.get(
    "/{job_id}/certificates",
    response_model=CertificateListResponse,
    summary="List certificates for a job",
    description="Retrieve all certificates for a job with optional status filtering and pagination."
)
def get_job_certificates(
    job_id: str,
    status: Optional[CertificateStatus] = Query(None, description="Filter certificates by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    query = db.query(Certificate).filter(Certificate.job_id == job_id)
    if status:
        query = query.filter(Certificate.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    certificates = query.order_by(Certificate.id.asc()).offset(offset).limit(page_size).all()

    items = []
    for cert in certificates:
        verification_url = f"{settings.BASE_URL}{settings.API_V1_STR}/verify/{cert.certificate_id}"
        download_url = f"{settings.BASE_URL}{settings.API_V1_STR}/certificates/{cert.certificate_id}/download" if cert.status == CertificateStatus.SUCCESS else None
        
        items.append(CertificateResponse(
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
        ))

    return CertificateListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get(
    "/{job_id}/download",
    summary="Download ZIP archive of all successful certificates",
    description="Compresses and returns a ZIP file containing all successfully generated PDFs for the job."
)
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    if job.status == JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is still pending and has not generated certificates yet."
        )

    # Get all successful certificates
    successful_certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id, Certificate.status == CertificateStatus.SUCCESS)
        .all()
    )

    if not successful_certs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No successful certificates available for download in this job."
        )

    pdf_paths = [c.pdf_path for c in successful_certs if c.pdf_path]
    zip_path = ZipService.create_job_zip(job_id, pdf_paths)

    if not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate ZIP archive."
        )

    safe_job_name = "".join(c for c in job.job_name if c.isalnum() or c in ("-", "_")).rstrip()
    download_filename = f"{safe_job_name}_{job_id[:8]}_certificates.zip"

    return FileResponse(
        path=str(zip_path),
        filename=download_filename,
        media_type="application/zip",
    )
