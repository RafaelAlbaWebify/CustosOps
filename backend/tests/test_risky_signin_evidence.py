from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = PROJECT_ROOT / "samples" / "risky_signins" / "sample-risky-signins.json"


def test_risky_signin_sample_generates_soc_findings():
    response = client.get("/api/risky-signins/sample-findings")

    assert response.status_code == 200
    data = response.json()

    assert data["evidence"]["parsed_record_count"] == 8

    finding_ids = {finding["finding_id"] for finding in data["findings"]}

    assert "RISKY_SIGNIN_ACTIVE_HIGH_RISK" in finding_ids
    assert "RISKY_SIGNIN_SUCCESS_MFA_NOT_SATISFIED" in finding_ids
    assert "RISKY_SIGNIN_LEGACY_CLIENT_APP_USED" in finding_ids
    assert "RISKY_SIGNIN_REPEATED_FAILURES" in finding_ids
    assert "RISKY_SIGNIN_MULTI_COUNTRY_ACTIVITY" in finding_ids


def test_risky_signin_import_accepts_json_content():
    response = client.post(
        "/api/risky-signins/import",
        json={
            "filename": SAMPLE_PATH.name,
            "content": SAMPLE_PATH.read_text(encoding="utf-8-sig"),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["input_type"] == "risky_signin_import"
    assert data["parsed_record_count"] == 8
    assert len(data["findings"]) >= 4


def test_risky_signin_report_can_be_generated_without_archive():
    sample_response = client.get("/api/risky-signins/sample-findings")
    assert sample_response.status_code == 200
    sample = sample_response.json()

    report_response = client.post(
        "/api/reports/risky-signins",
        json={
            "evidence": sample["evidence"],
            "findings": sample["findings"],
            "format": "html",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    data = report_response.json()

    assert data["filename"].startswith("custosops_risky_signin_report_")
    assert "CustosOps Risky Sign-In Evidence Report" in data["content"]
    assert "RISKY_SIGNIN_ACTIVE_HIGH_RISK" in data["content"]


def test_risky_signin_json_report_has_stable_report_type():
    sample_response = client.get("/api/risky-signins/sample-findings")
    sample = sample_response.json()

    report_response = client.post(
        "/api/reports/risky-signins",
        json={
            "evidence": sample["evidence"],
            "findings": sample["findings"],
            "format": "json",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    assert '"report_type": "custosops.risky_signins.v0.1"' in report_response.json()["content"]
