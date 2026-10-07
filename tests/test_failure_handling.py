from fastapi.testclient import TestClient
from app.services.job_service import JobService
from app.models.job import JobStatus
from app.models.certificate import CertificateStatus


def test_failure_isolation_and_partial_completion(client: TestClient, db_session):
    """
    Verify that individual failures do NOT abort the job.
    Recipient 1 -> SUCCESS
    Recipient 2 -> FAILED (using test hook __FORCE_FAIL__)
    Recipient 3 -> SUCCESS
    Result: success=2, failed=1, status=PARTIALLY_COMPLETED.
    """
    payload = {
        "job_name": "Resilience and Fault-Tolerance Workshop",
        "event_name": "Distributed Systems Reliability",
        "issued_by": "Architecture Institute",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "recipient_name": "Valid Recipient One",
                "recipient_email": "one@example.com"
            },
            {
                "recipient_name": "__FORCE_FAIL__ Recipient Two",
                "recipient_email": "two@example.com"
            },
            {
                "recipient_name": "Valid Recipient Three",
                "recipient_email": "three@example.com"
            }
        ]
    }

    # Create job via API
    res = client.post("/api/v1/jobs", json=payload)
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # Explicitly run worker synchronously to simulate background execution in test environment
    JobService.process_job_background(job_id)

    # Inspect Job Record
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()

    assert job_data["status"] == JobStatus.PARTIALLY_COMPLETED.value
    assert job_data["total_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 1
    assert job_data["progress_percentage"] == 100.0

    # Inspect Individual Certificates
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    items = certs_res.json()["items"]

    r1 = next(item for item in items if item["recipient_email"] == "one@example.com")
    assert r1["status"] == CertificateStatus.SUCCESS.value
    assert r1["pdf_path"] is not None
    assert r1["error_message"] is None

    r2 = next(item for item in items if item["recipient_email"] == "two@example.com")
    assert r2["status"] == CertificateStatus.FAILED.value
    assert r2["pdf_path"] is None
    assert "Simulated generation failure" in r2["error_message"]

    r3 = next(item for item in items if item["recipient_email"] == "three@example.com")
    assert r3["status"] == CertificateStatus.SUCCESS.value
    assert r3["pdf_path"] is not None
    assert r3["error_message"] is None
