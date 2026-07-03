import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _zero_iis_payload() -> dict:
    return {
        "source_file": "zero-iis.json",
        "asset": "workstation-01",
        "iis_detected": False,
        "appcmd_available": False,
        "raw_item_count": 0,
        "parsed_item_count": 0,
        "services": [],
        "sites": [],
        "application_pools": [],
        "applications": [],
        "log_files": [],
        "collection_warnings": [
            "appcmd.exe was not found. IIS site and application pool inventory is unavailable.",
            "IIS W3C log directory was not found.",
        ],
    }


def _problem_iis_payload() -> dict:
    return {
        "source_file": "iis-problem.json",
        "asset": "web-01",
        "iis_detected": True,
        "appcmd_available": True,
        "raw_item_count": 4,
        "parsed_item_count": 4,
        "services": [
            {"name": "W3SVC", "display_name": "World Wide Web Publishing Service", "status": "Stopped", "start_type": "Automatic"},
            {"name": "WAS", "display_name": "Windows Process Activation Service", "status": "Running", "start_type": "Automatic"},
        ],
        "sites": [
            {"name": "FactoryPortal", "site_id": "1", "state": "Stopped", "bindings": ["http/*:80:factory.local"]}
        ],
        "application_pools": [
            {"name": "FactoryPortalPool", "state": "Stopped", "runtime_version": "v4.0", "pipeline_mode": "Integrated"}
        ],
        "applications": [
            {"path": "/", "site": "FactoryPortal", "application_pool": "FactoryPortalPool"}
        ],
        "log_files": [],
    }


def test_iis_import_zero_state_is_valid():
    response = client.post(
        "/api/iis/import",
        json={
            "filename": "zero-iis.json",
            "content": json.dumps(_zero_iis_payload()),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["parsed_item_count"] == 0
    assert data["findings"] == []
    assert data["evidence"]["iis_detected"] is False


def test_iis_import_detects_service_site_and_app_pool_findings():
    response = client.post(
        "/api/iis/import",
        json={
            "filename": "iis-problem.json",
            "content": json.dumps(_problem_iis_payload()),
        },
    )

    assert response.status_code == 200
    data = response.json()

    finding_ids = {finding["finding_id"] for finding in data["findings"]}

    assert "IIS_SERVICE_NOT_RUNNING" in finding_ids
    assert "IIS_SITE_STOPPED" in finding_ids
    assert "IIS_APP_POOL_STOPPED" in finding_ids
    assert "IIS_LOGS_NOT_OBSERVED" in finding_ids


def test_iis_report_can_be_generated_without_archive():
    import_response = client.post(
        "/api/iis/import",
        json={
            "filename": "iis-problem.json",
            "content": json.dumps(_problem_iis_payload()),
        },
    )

    assert import_response.status_code == 200
    imported = import_response.json()

    report_response = client.post(
        "/api/reports/iis",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "json",
            "archive": False,
        },
    )

    assert report_response.status_code == 200
    report = report_response.json()

    assert report["filename"].startswith("custosops_iis_application_report_")
    assert report["content_type"] == "application/json"
    assert report["archived"] is False
    assert '"report_type": "custosops.iis_application.v0.1"' in report["content"]


def test_iis_collect_local_returns_valid_payload_even_without_iis():
    response = client.post("/api/iis/collect-local")

    assert response.status_code == 200
    data = response.json()

    assert data["input_type"] == "local_iis_application_collection"
    assert "evidence" in data
    assert "findings" in data
    assert "warnings" in data
    assert isinstance(data["evidence"]["iis_detected"], bool)