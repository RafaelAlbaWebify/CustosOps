from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dns_html_report_can_be_generated_from_sample():
    evidence = client.get("/api/dns/sample-evidence").json()
    findings = client.get("/api/dns/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/dns",
        json={"evidence": evidence, "findings": findings, "format": "html"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "html"
    assert data["filename"].endswith(".html")
    assert "CustosOps DNS Hygiene Report" in data["content"]


def test_dns_markdown_report_can_be_generated_from_sample():
    evidence = client.get("/api/dns/sample-evidence").json()
    findings = client.get("/api/dns/sample-findings").json()["findings"]

    response = client.post(
        "/api/reports/dns",
        json={"evidence": evidence, "findings": findings, "format": "markdown"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "markdown"
    assert data["filename"].endswith(".md")
    assert "# CustosOps DNS Hygiene Report" in data["content"]


def test_dns_json_report_can_be_generated_from_csv_import():
    csv_text = """HostName,IPAddress,Zone,ForwardStatus,PTRStatus,PingStatus,AgeDays,DupIP
app-old,10.10.10.25,lab.local,OK,NO_PTR,Failed,180,false
legacy-alias-01,10.10.10.40,lab.local,FORWARD_MISMATCH,PTR_MISMATCH,Failed,220,true
"""

    imported = client.post(
        "/api/dns/import-csv",
        json={"filename": "dns-audit.csv", "content": csv_text},
    ).json()

    response = client.post(
        "/api/reports/dns",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "json",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["filename"].endswith(".json")
    assert '"report_type": "custosops.dns.v0.1"' in data["content"]