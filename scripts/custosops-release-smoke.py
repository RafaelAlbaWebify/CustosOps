import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "release_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = TestClient(app)

    def get(path: str) -> dict[str, Any]:
        response = client.get(path)
        if response.status_code != 200:
            raise RuntimeError(f"GET {path} failed: {response.status_code} {response.text}")
        return response.json()

    def post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = client.post(path, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"POST {path} failed: {response.status_code} {response.text}")
        return response.json()

    endpoint_evidence = get("/api/endpoint/sample-evidence")
    endpoint_findings = get("/api/endpoint/sample-findings")["findings"]

    dns_evidence = get("/api/dns/sample-evidence")
    dns_findings = get("/api/dns/sample-findings")["findings"]

    app_log_sample = get("/api/app-log/sample-findings")
    app_log_evidence = app_log_sample["evidence"]
    app_log_findings = app_log_sample["findings"]

    windows_sample = get("/api/windows-events/sample-findings")
    windows_evidence = windows_sample["evidence"]
    windows_findings = windows_sample["findings"]

    modules = [
        {
            "module_id": "endpoint",
            "module_name": "Endpoint Security",
            "source": "Sample endpoint evidence",
            "evidence": endpoint_evidence,
            "findings": endpoint_findings,
        },
        {
            "module_id": "dns",
            "module_name": "DNS Hygiene",
            "source": "Sample DNS evidence",
            "evidence": dns_evidence,
            "findings": dns_findings,
        },
        {
            "module_id": "app-log",
            "module_name": "Application Logs",
            "source": app_log_evidence.get("source_file") or "sample application log",
            "evidence": app_log_evidence,
            "findings": app_log_findings,
        },
        {
            "module_id": "windows-events",
            "module_name": "Windows Event Evidence",
            "source": windows_evidence.get("source_file") or "sample Windows Event evidence",
            "evidence": windows_evidence,
            "findings": windows_findings,
        },
    ]

    reports = []

    report_requests = [
        (
            "endpoint",
            "/api/reports/endpoint",
            {
                "format": "html",
                "archive": True,
                "evidence": endpoint_evidence,
                "findings": endpoint_findings,
            },
            "CustosOps Endpoint Security Report",
        ),
        (
            "dns",
            "/api/reports/dns",
            {
                "format": "html",
                "archive": True,
                "evidence": dns_evidence,
                "findings": dns_findings,
            },
            "CustosOps DNS Hygiene Report",
        ),
        (
            "app_log",
            "/api/reports/app-log",
            {
                "format": "html",
                "archive": True,
                "evidence": app_log_evidence,
                "findings": app_log_findings,
            },
            "Application Log Evidence Report",
        ),
        (
            "windows_events",
            "/api/reports/windows-events",
            {
                "format": "html",
                "archive": True,
                "evidence": windows_evidence,
                "findings": windows_findings,
            },
            "Windows Event Evidence Report",
        ),
        (
            "executive_summary",
            "/api/reports/executive-summary",
            {
                "format": "html",
                "archive": True,
                "modules": modules,
            },
            "Operational Evidence Summary",
        ),
    ]

    for report_type, path, payload, expected_text in report_requests:
        data = post(path, payload)

        content = data.get("content", "")
        filename = data.get("filename", f"{report_type}.html")

        if expected_text not in content:
            raise RuntimeError(f"{report_type} report did not contain expected text: {expected_text}")

        if data.get("archived") is not True:
            raise RuntimeError(f"{report_type} report was not archived")

        output_path = out_dir / filename
        output_path.write_text(content, encoding="utf-8")

        reports.append(
            {
                "report_type": report_type,
                "filename": filename,
                "archived": data.get("archived"),
                "archive_entry_id": data.get("archive_entry_id"),
                "content_type": data.get("content_type"),
                "size_bytes": len(content.encode("utf-8")),
            }
        )

    archive = get("/api/reports/archive")

    result = {
        "status": "ok",
        "sample_counts": {
            "endpoint_findings": len(endpoint_findings),
            "dns_findings": len(dns_findings),
            "app_log_findings": len(app_log_findings),
            "windows_event_findings": len(windows_findings),
            "executive_modules": len(modules),
        },
        "reports": reports,
        "archive_count_after_smoke": len(archive.get("reports", [])),
    }

    result_path = out_dir / "release_smoke_results.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
