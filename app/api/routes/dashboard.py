from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get system aggregate statistics",
    description="Returns high-level analytics on jobs, certificates, success rate, and failure numbers."
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_certificates = db.query(func.count(Certificate.id)).scalar() or 0

    successful_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.SUCCESS)
        .scalar()
        or 0
    )

    failed_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.FAILED)
        .scalar()
        or 0
    )

    pending_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.PENDING)
        .scalar()
        or 0
    )

    processing_certificates = (
        db.query(func.count(Certificate.id))
        .filter(Certificate.status == CertificateStatus.PROCESSING)
        .scalar()
        or 0
    )

    success_rate = (
        round((successful_certificates / total_certificates) * 100, 2)
        if total_certificates > 0
        else 0.0
    )

    # Job status distribution
    job_statuses = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )
    jobs_by_status = {status.value: count for status, count in job_statuses}
    # Ensure all enum values exist in response dictionary
    for s in JobStatus:
        if s.value not in jobs_by_status:
            jobs_by_status[s.value] = 0

    return DashboardStatsResponse(
        total_jobs=total_jobs,
        total_certificates=total_certificates,
        success_rate=success_rate,
        successful_certificates=successful_certificates,
        failed_certificates=failed_certificates,
        pending_certificates=pending_certificates,
        processing_certificates=processing_certificates,
        jobs_by_status=jobs_by_status,
    )
