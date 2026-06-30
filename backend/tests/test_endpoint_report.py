from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_endpoint_html_report_can_be_generated():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    findings = client.get("/api/endpoint/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/endpoint",
        json={"evidence": evidence, "findings": findings, "format": "html"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "html"
    assert data["filename"].endswith(".html")
    assert "CustosOps Endpoint Security Report" in data["content"]


def test_endpoint_markdown_report_can_be_generated():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    findings = client.get("/api/endpoint/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/endpoint",
        json={"evidence": evidence, "findings": findings, "format": "markdown"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "markdown"
    assert data["filename"].endswith(".md")
    assert "# CustosOps Endpoint Security Report" in data["content"]


def test_endpoint_json_report_can_be_generated():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    findings = client.get("/api/endpoint/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/endpoint",
        json={"evidence": evidence, "findings": findings, "format": "json"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["filename"].endswith(".json")
    assert '"report_type": "custosops.endpoint.v0.1"' in data["content"]