from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import evidence_run_history


client = TestClient(app)


def test_evidence_run_history_create_list_and_clear(tmp_path, monkeypatch):
    history_path = tmp_path / "runs.json"

    monkeypatch.setattr(evidence_run_history, "RUN_HISTORY_DIR", tmp_path)
    monkeypatch.setattr(evidence_run_history, "RUN_HISTORY_PATH", history_path)

    clear_response = client.delete("/api/runs")
    assert clear_response.status_code == 200
    assert clear_response.json()["cleared"] is True

    create_response = client.post(
        "/api/runs",
        json={
            "module_id": "windows-events",
            "module_name": "Windows Event Evidence",
            "source": "local-windows-events",
            "source_type": "windows_event_log_local_collection",
            "asset": "TRON",
            "status": "success",
            "raw_count": 43,
            "parsed_count": 43,
            "finding_count": 4,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "warning_count": 0,
            "notes": "Local collection test run.",
            "metadata": {
                "output_path": "reports/windows-event-evidence.local.json"
            },
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()

    assert created["run_id"].startswith("run-windows-events-")
    assert created["created_at"].endswith("Z")
    assert created["module_id"] == "windows-events"
    assert created["asset"] == "TRON"
    assert created["finding_count"] == 4

    list_response = client.get("/api/runs")
    assert list_response.status_code == 200

    listed = list_response.json()
    assert listed["count"] == 1
    assert listed["runs"][0]["run_id"] == created["run_id"]

    clear_response = client.delete("/api/runs")
    assert clear_response.status_code == 200
    assert clear_response.json()["previous_count"] == 1

    empty_response = client.get("/api/runs")
    assert empty_response.status_code == 200
    assert empty_response.json()["count"] == 0


def test_evidence_run_history_limit(tmp_path, monkeypatch):
    history_path = tmp_path / "runs.json"

    monkeypatch.setattr(evidence_run_history, "RUN_HISTORY_DIR", tmp_path)
    monkeypatch.setattr(evidence_run_history, "RUN_HISTORY_PATH", history_path)

    client.delete("/api/runs")

    for index in range(3):
        response = client.post(
            "/api/runs",
            json={
                "module_id": "endpoint",
                "module_name": "Endpoint Security",
                "source": f"source-{index}",
                "source_type": "sample",
                "asset": "LAB-WIN11-01",
                "status": "success",
                "raw_count": index,
                "parsed_count": index,
                "finding_count": index,
            },
        )
        assert response.status_code == 200

    limited = client.get("/api/runs?limit=2")
    assert limited.status_code == 200
    assert limited.json()["count"] == 2
