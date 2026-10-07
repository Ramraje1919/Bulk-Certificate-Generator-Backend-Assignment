from typing import Dict
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_jobs: int
    total_certificates: int
    success_rate: float
    successful_certificates: int
    failed_certificates: int
    pending_certificates: int
    processing_certificates: int
    jobs_by_status: Dict[str, int]
