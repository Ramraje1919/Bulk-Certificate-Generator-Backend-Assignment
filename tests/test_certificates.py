from fastapi.testclient import TestClient
from app.services.job_service import JobService
from app.models.certificate import CertificateStatus


def test_certificate_metadata_and_download(client: TestClient, sample_job_payload):
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]

    # Process job
    JobService.process_job_background(job_id)

    # Fetch certificates list to retrieve a certificate_id
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates?status=SUCCESS")
    assert certs_res.status_code == 200
    items = certs_res.json()["items"]
    assert len(items) == 3

    sample_cert = items[0]
    cert_id = sample_cert["certificate_id"]

    # Test metadata endpoint
    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["certificate_id"] == cert_id
    assert meta_data["status"] == CertificateStatus.SUCCESS.value
    assert meta_data["recipient_name"] == sample_cert["recipient_name"]
    assert meta_data["download_url"] is not None

    # Test PDF download endpoint
    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert dl_res.content.startswith(b"%PDF-")


def test_certificate_download_not_found(client: TestClient):
    res = client.get("/api/v1/certificates/NON_EXISTENT_ID/download")
    assert res.status_code == 404


def test_certificate_metadata_not_found(client: TestClient):
    res = client.get("/api/v1/certificates/NON_EXISTENT_ID")
    assert res.status_code == 404
