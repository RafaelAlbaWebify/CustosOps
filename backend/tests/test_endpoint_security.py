from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_endpoint_sample_evidence_loads():
    response = client.get("/api/endpoint/sample-evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "custosops.endpoint.v0.1"
    assert data["computer"]["computer_name"] == "LAB-WIN11-01"


def test_endpoint_sample_findings_load():
    response = client.get("/api/endpoint/sample-findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    finding_ids = {finding["finding_id"] for finding in data["findings"]}
    assert "ENDPOINT_BITLOCKER_NOT_CONFIRMED_ON" in finding_ids
    assert "ENDPOINT_DEFENDER_NOT_HEALTHY" in finding_ids
    assert "ENDPOINT_RDP_ENABLED" in finding_ids


def test_endpoint_analyze_accepts_payload():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    response = client.post("/api/endpoint/analyze", json=evidence)
    assert response.status_code == 200
    data = response.json()
    assert len(data["findings"]) >= 1