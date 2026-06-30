from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["product"] == "CustosOps"


def test_modules_endpoint_returns_modules():
    response = client.get("/api/modules")
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) >= 1


def test_sample_findings_endpoint_returns_findings():
    response = client.get("/api/sample-findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert data["findings"][0]["finding_id"] == "CUSTOSOPS_FOUNDATION_SAMPLE"