from fastapi.testclient import TestClient


def test_create_job_success(client: TestClient, sample_job_payload):
    response = client.post("/api/v1/jobs", json=sample_job_payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_count"] == 3
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]


def test_create_job_validation_empty_recipients(client: TestClient, sample_job_payload):
    sample_job_payload["recipients"] = []
    response = client.post("/api/v1/jobs", json=sample_job_payload)
    assert response.status_code == 422


def test_create_job_validation_invalid_email(client: TestClient, sample_job_payload):
    sample_job_payload["recipients"][0]["recipient_email"] = "not-an-email"
    response = client.post("/api/v1/jobs", json=sample_job_payload)
    assert response.status_code == 422


def test_get_job_details(client: TestClient, sample_job_payload):
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]

    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    job_data = get_res.json()
    assert job_data["id"] == job_id
    assert job_data["job_name"] == sample_job_payload["job_name"]
    assert job_data["total_count"] == 3


def test_get_job_not_found(client: TestClient):
    response = client.get("/api/v1/jobs/non-existent-uuid")
    assert response.status_code == 404


def test_get_job_certificates_listing(client: TestClient, sample_job_payload):
    create_res = client.post("/api/v1/jobs", json=sample_job_payload)
    job_id = create_res.json()["job_id"]

    res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    emails = {item["recipient_email"] for item in data["items"]}
    assert "ada@example.com" in emails
    assert "alan@example.com" in emails
    assert "grace@example.com" in emails
