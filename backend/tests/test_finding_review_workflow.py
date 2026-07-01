from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_endpoint_report_includes_operator_review_metadata():
    response = client.post(
        "/api/reports/endpoint",
        json={
            "evidence": {
                "source_type": "endpoint_session_evidence",
                "generated_from": "loaded findings",
                "source_file": "custosops-session",
                "endpoint_name": "LAB-WIN11-01",
            },
            "findings": [
                {
                    "finding_id": "ENDPOINT_REVIEW_TEST",
                    "title": "Reviewed endpoint finding",
                    "severity": "medium",
                    "confidence": "medium",
                    "category": "Review workflow",
                    "affected_asset": "LAB-WIN11-01",
                    "evidence": [{"source": "endpoint", "key": "review_test", "value": "present"}],
                    "why_it_matters": "Review metadata should be preserved in reports.",
                    "safe_next_steps": ["Validate the finding review state."],
                    "limitations": ["This is a test finding."],
                    "non_actions": ["Do not remediate from this test."],
                    "status": "reviewed",
                    "review_notes": "Validated by operator.",
                    "reviewed_at": "2026-07-01T10:00:00Z",
                    "reviewed_by": "local-operator",
                }
            ],
            "format": "html",
            "archive": False,
        },
    )

    assert response.status_code == 200
    content = response.json()["content"]

    assert "reviewed" in content
    assert "Validated by operator." in content
    assert "local-operator" in content
