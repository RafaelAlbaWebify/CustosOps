from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _create_archived_endpoint_report() -> str:
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
    assert data["archive_entry_id"]

    return data["archive_entry_id"]


def test_archived_report_can_be_opened():
    entry_id = _create_archived_endpoint_report()

    response = client.get(f"/api/reports/archive/{entry_id}/open")

    assert response.status_code == 200
    assert "CustosOps Endpoint Security Report" in response.text


def test_archived_report_can_be_downloaded():
    entry_id = _create_archived_endpoint_report()

    response = client.get(f"/api/reports/archive/{entry_id}/download")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert "CustosOps Endpoint Security Report" in response.text


def test_archived_report_can_be_deleted():
    entry_id = _create_archived_endpoint_report()

    delete_response = client.delete(f"/api/reports/archive/{entry_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    open_response = client.get(f"/api/reports/archive/{entry_id}/open")

    assert open_response.status_code == 404