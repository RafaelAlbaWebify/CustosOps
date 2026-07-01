from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dns_csv_import_accepts_common_headers():
    csv_text = """HostName,IPAddress,Zone,ForwardStatus,PTRStatus,PingStatus,AgeDays,DupIP
app-old,10.10.10.25,lab.local,OK,NO_PTR,Failed,180,false
legacy-alias-01,10.10.10.40,lab.local,FORWARD_MISMATCH,PTR_MISMATCH,Failed,220,true
legacy-alias-02,10.10.10.40,lab.local,OK,PTR_MISMATCH,Failed,220,true
"""

    response = client.post(
        "/api/dns/import-csv",
        json={"filename": "dns-audit.csv", "content": csv_text},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_record_count"] == 3
    assert data["ignored_row_count"] == 0

    finding_ids = {finding["finding_id"] for finding in data["findings"]}
    assert "DNS_PTR_NOT_HEALTHY" in finding_ids
    assert "DNS_POTENTIAL_STALE_RECORD" in finding_ids
    assert "DNS_SHARED_IP_REVIEW_REQUIRED" in finding_ids
    assert "DNS_FORWARD_NOT_OK" in finding_ids


def test_dns_csv_import_accepts_semicolon_delimiter():
    csv_text = """FQDN;IP;ZoneName;ForwardStatus;PTRStatus;AgeDays
app-old.lab.local;10.10.10.25;lab.local;OK;NO_PTR;180
"""

    response = client.post(
        "/api/dns/import-csv",
        json={"filename": "dns-audit-semicolon.csv", "content": csv_text},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_record_count"] == 1
    assert len(data["findings"]) >= 1


def test_dns_csv_import_empty_content_returns_warning():
    response = client.post(
        "/api/dns/import-csv",
        json={"filename": "empty.csv", "content": ""},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_record_count"] == 0
    assert data["warnings"]