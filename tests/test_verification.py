from fastapi.testclient import TestClient
from app.services.job_service import JobService


def test_certificate_verification_success(client: TestClient, sample_job_payload):
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]

    # Process job
    JobService.process_job_background(job_id)

    # Fetch generated certificate
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert = certs_res.json()["items"][0]
    cert_id = cert["certificate_id"]

    # Verify endpoint
    verify_res = client.get(f"/api/v1/verify/{cert_id}")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["valid"] is True
    assert data["certificate_id"] == cert_id
    assert data["recipient"] == cert["recipient_name"]
    assert data["event"] == sample_job_payload["event_name"]
    assert data["issued_by"] == sample_job_payload["issued_by"]
    assert data["issue_date"] == sample_job_payload["issue_date"]
    assert "authentic" in data["message"].lower()


def test_certificate_verification_nonexistent(client: TestClient):
    verify_res = client.get("/api/v1/verify/FORGED-OR-FAKE-ID")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["valid"] is False
    assert data["certificate_id"] == "FORGED-OR-FAKE-ID"
    assert "not found" in data["message"].lower()
