from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_LOG_SAMPLE = PROJECT_ROOT / "samples" / "app_logs" / "fastapi-api-errors.log"


def test_app_log_html_report_is_not_markdown_wrapped_in_paragraphs():
    import_response = client.post(
        "/api/app-log/import",
        json={
            "filename": APP_LOG_SAMPLE.name,
            "content": APP_LOG_SAMPLE.read_text(encoding="utf-8-sig"),
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

    assert "<h1>Application Log Evidence Report</h1>" in content
    assert "<p># CustosOps Application Log Evidence Report</p>" not in content
    assert "Sensitive Evidence Warning" in content