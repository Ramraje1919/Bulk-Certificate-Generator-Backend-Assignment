from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "version" in data


def test_root_endpoint(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "docs" in data
