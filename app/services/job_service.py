from datetime import datetime, timezone
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreate
from app.utils.id_generator import generate_certificate_id, generate_verification_token
from app.services.certificate_generator import CertificateGenerator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobService:
    @staticmethod
    def create_job(db: Session, job_in: JobCreate) -> Job:
        """
        Create Job and its associated Certificate records in PENDING status.
        Runs synchronously inside the request context.
        """
        job = Job(
            job_name=job_in.job_name,
            event_name=job_in.event_name,
            issued_by=job_in.issued_by,
            issue_date=job_in.issue_date,
            status=JobStatus.PENDING,
            total_count=len(job_in.recipients),
            success_count=0,
            failed_count=0,
            progress_percentage=0.0,
            created_at=utcnow(),
        )
        db.add(job)
        db.flush()  # Populates job.id

        # Bulk create certificate records
        certificates: List[Certificate] = []
        for recipient in job_in.recipients:
            cert_id = generate_certificate_id()
            token = generate_verification_token()
            cert = Certificate(
                job_id=job.id,
                certificate_id=cert_id,
                verification_token=token,
                recipient_name=recipient.recipient_name.strip(),
                recipient_email=recipient.recipient_email.strip(),
                status=CertificateStatus.PENDING,
            )
            certificates.append(cert)

        db.add_all(certificates)
        db.commit()
        db.refresh(job)

        logger.info(
            f"Job created with {job.total_count} recipients",
            extra={"job_id": job.id, "status": job.status.value}
        )
        return job

    @staticmethod
    def process_job_background(job_id: str) -> None:
        """
        Worker function executed asynchronously by FastAPI BackgroundTasks.
        Processes each certificate with full isolation and real-time progress updates.
        """
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Background worker could not find job {job_id}", extra={"job_id": job_id})
                return

            # Mark Job as PROCESSING
            job.status = JobStatus.PROCESSING
            job.started_at = utcnow()
            db.commit()

            logger.info(f"Started processing job {job_id}", extra={"job_id": job_id})

            # Fetch all pending certificates
            certificates = (
                db.query(Certificate)
                .filter(Certificate.job_id == job_id)
                .order_by(Certificate.id.asc())
                .all()
            )

            job_output_dir = settings.STORAGE_DIR / job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)

            processed_count = 0
            success_count = 0
            failed_count = 0

            for cert in certificates:
                # Update individual certificate to PROCESSING
                cert.status = CertificateStatus.PROCESSING
                db.commit()

                # Process individual certificate with failure isolation
                try:
                    pdf_filename = f"{cert.certificate_id}.pdf"
                    target_pdf_path = job_output_dir / pdf_filename
                    verification_url = f"{settings.BASE_URL}{settings.API_V1_STR}/verify/{cert.certificate_id}"

                    # Simulating test failure hook if recipient name starts with '__FORCE_FAIL__'
                    if cert.recipient_name.startswith("__FORCE_FAIL__"):
                        raise ValueError(f"Simulated generation failure for {cert.recipient_name}")

                    # Generate PDF with ReportLab and dynamic QR Code
                    CertificateGenerator.generate_pdf(
                        output_path=target_pdf_path,
                        recipient_name=cert.recipient_name,
                        event_name=job.event_name,
                        issued_by=job.issued_by,
                        issue_date=job.issue_date,
                        certificate_id=cert.certificate_id,
                        verification_url=verification_url,
                    )

                    cert.status = CertificateStatus.SUCCESS
                    cert.pdf_path = str(target_pdf_path.resolve())
                    cert.generated_at = utcnow()
                    cert.error_message = None
                    success_count += 1

                    logger.info(
                        f"Certificate generated for {cert.recipient_email}",
                        extra={
                            "job_id": job_id,
                            "certificate_id": cert.certificate_id,
                            "recipient_email": cert.recipient_email,
                            "status": "SUCCESS"
                        }
                    )

                except Exception as exc:
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = str(exc)
                    cert.pdf_path = None
                    failed_count += 1

                    logger.error(
                        f"Certificate failed for {cert.recipient_email}: {str(exc)}",
                        extra={
                            "job_id": job_id,
                            "certificate_id": cert.certificate_id,
                            "recipient_email": cert.recipient_email,
                            "status": "FAILED",
                            "error": str(exc)
                        }
                    )

                processed_count += 1
                progress = round((processed_count / job.total_count) * 100, 2)

                # Persist progress updates for real-time client polling
                job.success_count = success_count
                job.failed_count = failed_count
                job.progress_percentage = progress
                db.commit()

            # Finalize Job Status
            job.completed_at = utcnow()
            if failed_count == 0:
                job.status = JobStatus.COMPLETED
            elif success_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED
            else:
                job.status = JobStatus.FAILED

            db.commit()

            logger.info(
                f"Job completed | status={job.status.value} | success={success_count} | failed={failed_count}",
                extra={"job_id": job_id, "status": job.status.value}
            )

        except Exception as unhandled_err:
            logger.critical(
                f"Fatal unexpected exception in background worker for job {job_id}: {str(unhandled_err)}",
                extra={"job_id": job_id, "error": str(unhandled_err)}
            )
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = utcnow()
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
