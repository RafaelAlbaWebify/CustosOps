from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = PROJECT_ROOT / "samples" / "app_logs" / "fastapi-api-errors.log"


def test_app_log_import_detects_operational_findings():
    response = client.post(
        "/api/app-log/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert response.status_code == 200

    data = response.json()
    finding_ids = {finding["finding_id"] for finding in data["findings"]}

    assert data["parsed_entry_count"] >= 1
    assert "APP_LOG_HTTP_5XX_ERRORS" in finding_ids
    assert "APP_LOG_AUTH_FAILURES" in finding_ids
    assert "APP_LOG_TIMEOUT_ERRORS" in finding_ids
    assert "APP_LOG_DNS_RESOLUTION_ERRORS" in finding_ids
    assert "APP_LOG_TLS_CERTIFICATE_ERRORS" in finding_ids
    assert "APP_LOG_DATABASE_DEPENDENCY_ERRORS" in finding_ids
    assert "APP_LOG_UNHANDLED_EXCEPTIONS" in finding_ids
    assert "APP_LOG_SENSITIVE_DATA_INDICATORS" in finding_ids


def test_app_log_report_can_be_archived():
    import_response = client.post(
        "/api/app-log/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert import_response.status_code == 200
    imported = import_response.json()

    report_response = client.post(
        "/api/reports/app-log",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "markdown",
            "archive": True,
        },
    )

    assert report_response.status_code == 200

    report = report_response.json()

    assert report["archived"] is True
    assert report["archive_entry_id"]
    assert "CustosOps Application Log Evidence Report" in report["content"]