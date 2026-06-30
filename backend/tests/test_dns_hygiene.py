from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dns_sample_evidence_loads():
    response = client.get("/api/dns/sample-evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "custosops.dns.v0.1"
    assert len(data["records"]) >= 1


def test_dns_sample_findings_load():
    response = client.get("/api/dns/sample-findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    finding_ids = {finding["finding_id"] for finding in data["findings"]}
    assert "DNS_PTR_NOT_HEALTHY" in finding_ids
    assert "DNS_POTENTIAL_STALE_RECORD" in finding_ids
    assert "DNS_SHARED_IP_REVIEW_REQUIRED" in finding_ids


def test_dns_analyze_accepts_payload():
    evidence = client.get("/api/dns/sample-evidence").json()
    response = client.post("/api/dns/analyze", json=evidence)
    assert response.status_code == 200
    data = response.json()
    assert len(data["findings"]) >= 1