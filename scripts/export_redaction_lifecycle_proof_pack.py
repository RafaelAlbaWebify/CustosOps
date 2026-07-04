import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run_command(args, cwd, output_file):
    with output_file.open("w", encoding="utf-8", errors="replace") as handle:
        handle.write("$ " + " ".join(str(item) for item in args) + "\n\n")
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
        )
        handle.write(f"\n\nexit_code={completed.returncode}\n")
        return completed.returncode


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def copy_snapshot(root, out_dir, relative_path):
    src = root / relative_path
    if not src.exists():
        return
    safe_name = str(relative_path).replace("\\", "_").replace("/", "_")
    shutil.copy2(src, out_dir / safe_name)


def static_hook_report(root, out_file):
    checks = {
        "frontend/src/App.tsx": [
            "ensureWorkspaceData",
            "activeWorkspace",
            "loadRedactionSettings",
            "loadRunHistory",
            "loadReportArchive",
            "hasPersistableEvidence",
            "runRedactionPreview",
        ],
        "backend/app/api/reports.py": [
            "_apply_report_redaction",
            "_redact_report_value",
            "redact_text",
            "get_redaction_settings",
            "applied_rules",
        ],
        "backend/app/services/redaction_engine.py": [
            "redact_text",
            "WINDOWS_PROFILE_PATTERN",
            "sub(lambda",
        ],
        "backend/app/api/redaction_settings.py": [
            "/preview",
            "/settings",
            "RedactionPreviewResponse",
        ],
    }

    lines = ["# Static hook report", ""]

    for rel, patterns in checks.items():
        path = root / rel
        lines.append(f"## {rel}")
        if not path.exists():
            lines.append("MISSING")
            lines.append("")
            continue

        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for pattern in patterns:
            lines.append(f"- {pattern}: {'OK' if pattern in text else 'MISSING'}")
        lines.append("")

    write_text(out_file, "\n".join(lines))


def api_proof(root, out_file):
    sys.path.insert(0, str(root / "backend"))

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    client.post("/api/redaction/settings/reset")

    lines = []
    ok = True

    def check(label, response):
        nonlocal ok
        lines.append(f"{label}: {response.status_code}")
        try:
            payload = response.json()
            lines.append(json.dumps(payload, indent=2)[:2500])
        except Exception:
            payload = {}
            lines.append(response.text[:2500])

        if response.status_code >= 400:
            ok = False

        return payload

    check("GET /api/health", client.get("/api/health"))
    check("GET /api/redaction/settings", client.get("/api/redaction/settings"))
    check("GET /api/runs", client.get("/api/runs"))
    check("GET /api/reports/archive", client.get("/api/reports/archive"))

    preview = check(
        "POST /api/redaction/preview",
        client.post(
            "/api/redaction/preview",
            json={"text": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop"},
        ),
    )

    preview_text = preview.get("redacted", "")
    if "analyst@example.com" in preview_text or "C:\\Users\\analyst" in preview_text:
        lines.append("ERROR: preview redaction failed")
        ok = False

    report = check(
        "POST /api/reports/app-log",
        client.post(
            "/api/reports/app-log",
            json={
                "evidence": {
                    "source_file": "C:\\Users\\analyst\\logs\\app.log",
                    "raw_line_count": 1,
                    "parsed_entry_count": 1,
                },
                "findings": [
                    {
                        "finding_id": "PROOF_REDACTION_APP_LOG",
                        "title": "Proof redaction app log",
                        "severity": "medium",
                        "confidence": "medium",
                        "category": "Application logs",
                        "affected_asset": "app01",
                        "evidence": [
                            {
                                "source": "app-log",
                                "key": "message",
                                "value": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                            }
                        ],
                        "why_it_matters": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                        "safe_next_steps": ["Review C:\\Users\\analyst\\Desktop safely."],
                        "limitations": ["Synthetic proof."],
                        "non_actions": ["Do not remediate."],
                    }
                ],
                "format": "json",
                "archive": False,
            },
        ),
    )

    report_content = report.get("content", "")
    if "analyst@example.com" in report_content or "C:\\Users\\analyst" in report_content:
        lines.append("ERROR: app-log report redaction failed")
        ok = False

    executive = check(
        "POST /api/reports/executive-summary",
        client.post(
            "/api/reports/executive-summary",
            json={
                "modules": [
                    {
                        "module_id": "app-logs",
                        "module_name": "Application Logs",
                        "source": "Contact analyst@example.com from C:\\Users\\analyst\\logs\\app.log",
                        "evidence": {
                            "source_file": "Contact analyst@example.com from C:\\Users\\analyst\\logs\\app.log",
                        },
                        "findings": [],
                    }
                ],
                "format": "html",
                "archive": False,
            },
        ),
    )

    executive_content = executive.get("content", "")
    if "analyst@example.com" in executive_content or "C:\\Users\\analyst" in executive_content:
        lines.append("ERROR: executive report redaction failed")
        ok = False

    write_text(out_file, "\n\n".join(lines))
    return ok


def zip_dir(source_dir, zip_path):
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    root = Path(args.root)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(tempfile.gettempdir()) / f"CUSTOSOPS_REDACTION_LIFECYCLE_PROOF_{timestamp}"
    downloads = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
    zip_path = downloads / f"CUSTOSOPS_REDACTION_LIFECYCLE_PROOF_{timestamp}.zip"

    out_dir.mkdir(parents=True, exist_ok=True)

    ok = True

    print("")
    print("=== CustosOps Redaction and Lifecycle Proof Pack ===")
    print(f"Output folder: {out_dir}")
    print(f"ZIP: {zip_path}")

    if run_command(["git", "status", "--short"], root, out_dir / "01_git_status.txt") != 0:
        ok = False
    if run_command(["git", "--no-pager", "log", "--oneline", "-20"], root, out_dir / "02_git_log.txt") != 0:
        ok = False
    if run_command(["git", "--no-pager", "tag", "--list", "custosops-*"], root, out_dir / "03_git_tags.txt") != 0:
        ok = False

    static_hook_report(root, out_dir / "04_static_hooks.md")

    print("")
    print("Running backend tests...")
    if run_command([str(root / "backend" / ".venv" / "Scripts" / "python.exe"), "-m", "pytest", "-q"], root / "backend", out_dir / "05_backend_tests.txt") != 0:
        print("Backend tests failed.")
        ok = False
    else:
        print("Backend tests passed.")

    print("")
    print("Running frontend build...")
    if run_command(["npm.cmd", "run", "build"], root / "frontend", out_dir / "06_frontend_build.txt") != 0:
        print("Frontend build failed.")
        ok = False
    else:
        print("Frontend build passed.")

    print("")
    print("Running API proof checks...")
    try:
        if api_proof(root, out_dir / "07_api_proof.txt"):
            print("API proof checks passed.")
        else:
            print("API proof checks failed.")
            ok = False
    except Exception as exc:
        write_text(out_dir / "07_api_proof.txt", f"API proof exception:\n{exc!r}\n")
        print("API proof checks failed with exception.")
        ok = False

    snapshot_dir = out_dir / "source_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for rel in [
        Path("frontend/src/App.tsx"),
        Path("backend/app/api/reports.py"),
        Path("backend/app/api/redaction_settings.py"),
        Path("backend/app/services/redaction_engine.py"),
        Path("backend/tests/test_report_redaction.py"),
        Path("docs/roadmap/MILESTONE_26_REDACTION_CONTROLS_UI.md"),
        Path("docs/roadmap/ROADMAP.md"),
    ]:
        copy_snapshot(root, snapshot_dir, rel)

    summary = f"""# CustosOps Redaction and Lifecycle Proof Pack

Generated: {timestamp}

Overall success: {ok}

Validated:

- Workspace lifecycle hooks
- Redaction settings API
- Redaction preview API
- Generated report redaction
- Executive summary report redaction
- Run History API availability
- Report Archive API availability
- Backend tests
- Frontend build
- Git commit/tag state

Expected baseline:

- custosops-v0.26.5-report-redaction or later
"""
    write_text(out_dir / "00_PROOF_SUMMARY.md", summary)

    zip_dir(out_dir, zip_path)

    print("")
    if ok:
        print("PROOF PACK COMPLETE.")
    else:
        print("PROOF PACK CREATED WITH FAILURES.")

    print("")
    print("ZIP:")
    print(zip_path)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
