from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = PROJECT_ROOT / "samples" / "app_logs" / "fastapi-api-errors.log"


def test_app_log_import_returns_api_operational_summary():
    response = client.post(
        "/api/app-log/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["api_summary"]

    assert summary["http_request_count"] >= 1
    assert summary["server_error_count"] == 1
    assert summary["auth_failure_count"] == 2
    assert summary["status_code_breakdown"]["500"] == 1
    assert any(item["endpoint"] == "/api/orders" for item in summary["top_failing_endpoints"])
    assert summary["first_seen"].startswith("2026-06-30")
    assert summary["last_seen"].startswith("2026-06-30")


def test_app_log_report_redacts_token_and_contains_api_summary():
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
            "format": "html",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    content = report_response.json()["content"]

    assert "API Operational Summary" in content
    assert "synthetic-token-value-1234567890" not in content
    assert "[REDACTED_AUTH_HEADER]" in content or "[REDACTED_BEARER_TOKEN]" in content
    assert "Top failing endpoints" in content
