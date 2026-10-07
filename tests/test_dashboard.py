from fastapi.testclient import TestClient
from app.services.job_service import JobService


def test_dashboard_stats(client: TestClient, sample_job_payload):
    # Empty stats initially
    init_res = client.get("/api/v1/dashboard/stats")
    assert init_res.status_code == 200
    assert init_res.json()["total_jobs"] == 0
    assert init_res.json()["total_certificates"] == 0

    # Create job and process
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]
    JobService.process_job_background(job_id)

    # Check populated stats
    stats_res = client.get("/api/v1/dashboard/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()

    assert data["total_jobs"] == 1
    assert data["total_certificates"] == 3
    assert data["successful_certificates"] == 3
    assert data["failed_certificates"] == 0
    assert data["success_rate"] == 100.0
    assert "COMPLETED" in data["jobs_by_status"]
    assert data["jobs_by_status"]["COMPLETED"] == 1
