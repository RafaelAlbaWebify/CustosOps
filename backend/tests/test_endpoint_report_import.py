from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_endpoint_analyze_accepts_generated_report_json():
    evidence = client.get("/api/endpoint/sample-evidence").json()
    findings = client.get("/api/endpoint/sample-findings").json()["findings"]

    report_response = client.post(
        "/api/reports/endpoint",
        json={"evidence": evidence, "findings": findings, "format": "json"},
    )

    assert report_response.status_code == 200
    report_payload = report_response.json()

    import json

    generated_report_json = json.loads(report_payload["content"])

    analyze_response = client.post("/api/endpoint/analyze", json=generated_report_json)

    assert analyze_response.status_code == 200
    data = analyze_response.json()
    assert data["input_type"] == "endpoint_report_json"
    assert len(data["findings"]) >= 1