from fastapi.testclient import TestClient

from app.api import windows_events as windows_events_api
from app.main import app


client = TestClient(app)


def test_collect_local_windows_event_route_accepts_mocked_collector(monkeypatch):
    sample_response = client.get("/api/windows-events/sample-findings")
    assert sample_response.status_code == 200

    sample_evidence = sample_response.json()["evidence"]

    def fake_collector():
        return {
            "output_path": "reports/windows-event-evidence.local.json",
            "relative_output_path": "reports/windows-event-evidence.local.json",
            "stdout": "",
            "stderr": "",
            "evidence": sample_evidence,
        }

    monkeypatch.setattr(windows_events_api, "collect_local_windows_event_evidence", fake_collector)

    response = client.post("/api/windows-events/collect-local")

    assert response.status_code == 200
    data = response.json()

    assert data["input_type"] == "local_windows_event_collection"
    assert data["output_path"] == "reports/windows-event-evidence.local.json"
    assert data["parsed_event_count"] == sample_evidence["parsed_event_count"]
    assert len(data["findings"]) >= 1


def test_windows_event_collector_script_exists_and_is_read_only():
    script_path = windows_events_api.PROJECT_ROOT / "collectors" / "powershell" / "windows_events" / "Get-WindowsEventEvidence.ps1"

    assert script_path.exists()

    script = script_path.read_text(encoding="utf-8-sig").lower()

    assert "get-winevent" in script
    assert "clear-eventlog" not in script
    assert "remove-eventlog" not in script
    assert "restart-service" not in script
    assert "stop-service" not in script
    assert "set-service" not in script
