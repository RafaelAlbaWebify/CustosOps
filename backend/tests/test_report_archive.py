from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_endpoint_report_can_be_archived():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    findings = client.get("/api/endpoint/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/endpoint",
        json={
            "evidence": evidence,
            "findings": findings,
            "format": "markdown",
            "archive": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["archived"] is True
    assert data["archived_path"]
    assert data["archive_entry_id"]


def test_dns_report_can_be_archived():
    evidence = client.get("/api/dns/sample-evidence").json()
    findings = client.get("/api/dns/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/dns",
        json={
            "evidence": evidence,
            "findings": findings,
            "format": "markdown",
            "archive": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["archived"] is True
    assert data["archived_path"]
    assert data["archive_entry_id"]


def test_report_archive_list_returns_reports():
    response = client.get("/api/reports/archive")

    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert isinstance(data["reports"], list)