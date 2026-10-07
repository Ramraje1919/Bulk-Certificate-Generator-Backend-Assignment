import io
import zipfile
from fastapi.testclient import TestClient
from app.services.job_service import JobService


def test_job_zip_download(client: TestClient, sample_job_payload):
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]

    # Process job
    JobService.process_job_background(job_id)

    # Download ZIP
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify ZIP structure
    zip_buffer = io.BytesIO(zip_res.content)
    with zipfile.ZipFile(zip_buffer, "r") as archive:
        namelist = archive.namelist()
        assert len(namelist) == 3
        for filename in namelist:
            assert filename.endswith(".pdf")
            file_content = archive.read(filename)
            assert file_content.startswith(b"%PDF-")


def test_job_zip_download_not_ready_or_empty(client: TestClient):
    # Job not found
    res = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000/download")
    assert res.status_code == 404
