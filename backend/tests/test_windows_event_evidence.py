from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = PROJECT_ROOT / "samples" / "windows_events" / "sample-windows-events.json"


def test_windows_event_import_generates_operational_findings():
    response = client.post(
        "/api/windows-events/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["parsed_event_count"] == 6

    finding_ids = {finding["finding_id"] for finding in data["findings"]}

    assert "WIN_EVT_SERVICE_FAILURES" in finding_ids
    assert "WIN_EVT_FAILED_LOGONS" in finding_ids
    assert "WIN_EVT_APPLICATION_ERRORS" in finding_ids
    assert "WIN_EVT_DNS_CLIENT_ERRORS" in finding_ids
    assert "WIN_EVT_REBOOT_UPDATE_SIGNALS" in finding_ids


def test_windows_event_report_can_be_generated_and_archived_off():
    import_response = client.post(
        "/api/windows-events/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert import_response.status_code == 200
    imported = import_response.json()

    report_response = client.post(
        "/api/reports/windows-events",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "html",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    data = report_response.json()

    assert data["filename"].startswith("custosops_windows_event_report_")
    assert "Windows Event Evidence Report" in data["content"]
    assert "WIN_EVT_FAILED_LOGONS" in data["content"]


def test_windows_event_json_report_has_stable_report_type():
    import_response = client.post(
        "/api/windows-events/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    imported = import_response.json()

    report_response = client.post(
        "/api/reports/windows-events",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "json",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    assert '"report_type": "custosops.windows_events.v0.1"' in report_response.json()["content"]
