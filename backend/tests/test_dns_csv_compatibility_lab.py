from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPAT_DIR = PROJECT_ROOT / "samples" / "dns" / "compatibility"


def test_dns_csv_template_endpoint_downloads_csv():
    response = client.get("/api/dns/csv-template")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "HostName,IPAddress,Zone" in response.text


def test_all_dns_compatibility_csv_fixtures_import_successfully():
    fixture_paths = sorted(COMPAT_DIR.glob("*.csv"))

    assert fixture_paths, "No DNS compatibility CSV fixtures found."

    for fixture_path in fixture_paths:
        response = client.post(
            "/api/dns/import-csv",
            json={
                "filename": fixture_path.name,
                "content": fixture_path.read_text(encoding="utf-8-sig"),
            },
        )

        assert response.status_code == 200, fixture_path.name

        data = response.json()

        assert data["parsed_record_count"] >= 1, fixture_path.name
        assert len(data["findings"]) >= 1, fixture_path.name

        finding_ids = {finding["finding_id"] for finding in data["findings"]}

        assert (
            "DNS_PTR_NOT_HEALTHY" in finding_ids
            or "DNS_POTENTIAL_STALE_RECORD" in finding_ids
            or "DNS_SHARED_IP_REVIEW_REQUIRED" in finding_ids
            or "DNS_FORWARD_NOT_OK" in finding_ids
        ), fixture_path.name