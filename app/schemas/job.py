from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.models.job import JobStatus


class RecipientCreate(BaseModel):
    recipient_name: str = Field(..., min_length=1, max_length=150, description="Full name of certificate recipient")
    recipient_email: EmailStr = Field(..., description="Valid email address of recipient")


class JobCreate(BaseModel):
    job_name: str = Field(..., min_length=2, max_length=200, description="Identifying name for the batch job")
    event_name: str = Field(..., min_length=2, max_length=200, description="Title of course, workshop, or event")
    issued_by: str = Field(..., min_length=2, max_length=200, description="Issuing organization or authority")
    issue_date: date = Field(default_factory=date.today, description="Official date of issuance (YYYY-MM-DD)")
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="List of recipients to generate certificates for"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_name": "Python Backend Mastery Cohort 2026",
                "event_name": "Advanced Python & Distributed Systems Bootcamp",
                "issued_by": "Global Tech Academy",
                "issue_date": "2026-10-07",
                "recipients": [
                    {
                        "recipient_name": "Alice Johnson",
                        "recipient_email": "alice@example.com"
                    },
                    {
                        "recipient_name": "Bob Smith",
                        "recipient_email": "bob@example.com"
                    }
                ]
            }
        }
    )


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    total_count: int
    message: str = "Job accepted and queued for generation."


class JobResponse(BaseModel):
    id: str
    job_name: str
    event_name: str
    issued_by: str
    issue_date: date
    status: JobStatus
    total_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
