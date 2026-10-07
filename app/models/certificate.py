import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


def utcnow():
    return datetime.now(timezone.utc)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    certificate_id = Column(String(64), unique=True, nullable=False, index=True)
    verification_token = Column(String(64), unique=True, nullable=False, index=True)

    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False, index=True)

    status = Column(
        Enum(CertificateStatus),
        default=CertificateStatus.PENDING,
        nullable=False,
        index=True
    )

    pdf_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="certificates")

    def __repr__(self) -> str:
        return f"<Certificate {self.certificate_id} | recipient={self.recipient_email} | status={self.status.value}>"
