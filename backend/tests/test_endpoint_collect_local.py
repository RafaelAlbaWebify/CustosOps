from fastapi.testclient import TestClient

from app.api import endpoint as endpoint_api
from app.main import app


client = TestClient(app)


def test_collect_local_endpoint_route_accepts_mocked_collector(monkeypatch):
    sample_evidence = client.get("/api/endpoint/sample-evidence").json()

    def fake_collector():
        return {
            "output_path": "reports/endpoint-evidence.local.json",
            "relative_output_path": "reports/endpoint-evidence.local.json",
            "stdout": "",
            "stderr": "",
            "evidence": sample_evidence,
        }

    monkeypatch.setattr(endpoint_api, "collect_local_endpoint_evidence", fake_collector)

    response = client.post("/api/endpoint/collect-local")

    assert response.status_code == 200
    data = response.json()
    assert data["input_type"] == "local_endpoint_collection"
    assert data["output_path"] == "reports/endpoint-evidence.local.json"
    assert len(data["findings"]) >= 1