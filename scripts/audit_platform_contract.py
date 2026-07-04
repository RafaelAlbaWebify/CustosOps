import argparse
import datetime as dt
import os
import re
import tempfile
import zipfile
from pathlib import Path


EXPECTED_WORKSPACES = [
    "overview",
    "endpoint",
    "dns",
    "app-log",
    "windows-events",
    "iis",
    "reports",
    "archive",
    "run-history",
    "redaction",
]


def read(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def extract_workspace_type(app_text):
    match = re.search(r"type\s+Workspace\s*=\s*([^;]+);", app_text, flags=re.S)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def extract_navigation_ids(app_text):
    return re.findall(r'id:\s*"([^"]+)"\s*,\s*label:\s*"([^"]+)"', app_text)


def extract_render_ids(app_text):
    return re.findall(r'activeWorkspace\s*===\s*"([^"]+)"', app_text)


def line_hits(text, patterns):
    lines = text.splitlines()
    result = []
    for index, line in enumerate(lines, start=1):
        for pattern in patterns:
            if pattern in line:
                result.append((index, pattern, line.strip()))
    return result


def zip_dir(source_dir, zip_path):
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"C:\Users\ralba\Documents\GitHub\custosops")
    args = parser.parse_args()

    root = Path(args.root)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(tempfile.gettempdir()) / f"CUSTOSOPS_PLATFORM_CONTRACT_AUDIT_{timestamp}"
    downloads = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
    zip_path = downloads / f"CUSTOSOPS_PLATFORM_CONTRACT_AUDIT_{timestamp}.zip"

    out_dir.mkdir(parents=True, exist_ok=True)

    app_path = root / "frontend" / "src" / "App.tsx"
    reports_path = root / "backend" / "app" / "api" / "reports.py"
    redaction_engine_path = root / "backend" / "app" / "services" / "redaction_engine.py"

    app_text = read(app_path)
    reports_text = read(reports_path)
    redaction_text = read(redaction_engine_path)

    workspace_type = extract_workspace_type(app_text)
    nav_items = extract_navigation_ids(app_text)
    nav_ids = [item[0] for item in nav_items]
    render_ids = extract_render_ids(app_text)

    report_lines = []

    report_lines.append("# CustosOps Platform Contract Audit")
    report_lines.append("")
    report_lines.append(f"Generated: {timestamp}")
    report_lines.append("")
    report_lines.append("## Workspace coverage")
    report_lines.append("")
    report_lines.append("| Workspace | Type | Navigation | Render block | Lifecycle reference |")
    report_lines.append("|---|---:|---:|---:|---:|")

    for workspace in EXPECTED_WORKSPACES:
        in_type = workspace in workspace_type
        in_nav = workspace in nav_ids
        in_render = workspace in render_ids
        in_lifecycle = f'workspace === "{workspace}"' in app_text or f'case "{workspace}"' in app_text
        report_lines.append(
            f"| {workspace} | {'OK' if in_type else 'MISSING'} | {'OK' if in_nav else 'MISSING'} | {'OK' if in_render else 'MISSING'} | {'OK' if in_lifecycle else 'MISSING'} |"
        )

    report_lines.append("")
    report_lines.append("## Navigation labels")
    report_lines.append("")

    for workspace_id, label in nav_items:
        report_lines.append(f"- {workspace_id}: {label}")

    report_lines.append("")
    report_lines.append("## Evidence module state patterns")
    report_lines.append("")

    state_patterns = [
        "endpointEvidence",
        "endpointFindings",
        "dnsEvidence",
        "dnsFindings",
        "appLogEvidence",
        "appLogFindings",
        "windowsEventEvidence",
        "windowsEventFindings",
        "recordEvidenceRun",
        "hasPersistableEvidence",
        "loadReportArchive",
        "loadRunHistory",
        "loadRedactionSettings",
    ]

    for line_no, pattern, line in line_hits(app_text, state_patterns):
        report_lines.append(f"- L{line_no}: {pattern}: `{line}`")

    report_lines.append("")
    report_lines.append("## Report and redaction hooks")
    report_lines.append("")

    hook_patterns = [
        "_apply_report_redaction",
        "_redact_report_value",
        "redact_text",
        "get_redaction_settings",
        "applied_rules",
    ]

    for line_no, pattern, line in line_hits(reports_text, hook_patterns):
        report_lines.append(f"- reports.py L{line_no}: {pattern}: `{line}`")

    for line_no, pattern, line in line_hits(redaction_text, ["WINDOWS_PROFILE_PATTERN", "sub(lambda", "redact_text", "redact_value"]):
        report_lines.append(f"- redaction_engine.py L{line_no}: {pattern}: `{line}`")

    report_lines.append("")
    report_lines.append("## API helper extraction")
    report_lines.append("")

    api_helper_path = root / "frontend" / "src" / "services" / "api.ts"
    api_helper_text = read(api_helper_path)

    if api_helper_path.exists():
        report_lines.append("- OK: frontend API helper exists at frontend/src/services/api.ts.")
    else:
        report_lines.append("- HIGH: frontend API helper is missing.")

    if "apiFetch(" in app_text:
        report_lines.append("- OK: App.tsx uses apiFetch helper.")
    else:
        report_lines.append("- CHECK: App.tsx does not appear to use apiFetch.")

    if "API_BASE" in app_text:
        report_lines.append("- MEDIUM: App.tsx still references API_BASE directly.")
    else:
        report_lines.append("- OK: App.tsx does not reference API_BASE directly.")

    if "fetch(`${API_BASE}" in app_text:
        report_lines.append("- HIGH: App.tsx still contains direct fetch API_BASE calls.")
    else:
        report_lines.append("- OK: App.tsx no longer contains direct fetch API_BASE calls.")

    report_lines.append("")
    report_lines.append("## Initial findings")
    report_lines.append("")

    if "async function ensureWorkspaceData" in app_text:
        report_lines.append("- OK: central workspace lifecycle dispatcher exists.")
    else:
        report_lines.append("- HIGH: central workspace lifecycle dispatcher missing.")

    if "hasPersistableEvidence" in app_text:
        report_lines.append("- OK: session persistence includes evidence-based guard.")
    else:
        report_lines.append("- MEDIUM: evidence-based persistence guard not detected.")

    if "disabled={!endpointEvidence}" in app_text:
        report_lines.append("- OK: endpoint report readiness is evidence-based.")
    else:
        report_lines.append("- CHECK: endpoint report readiness may need review.")

    if "_apply_report_redaction" in reports_text:
        report_lines.append("- OK: generated reports pass through redaction layer.")
    else:
        report_lines.append("- HIGH: generated reports do not pass through redaction layer.")

    app_line_count = len(app_text.splitlines())
    report_lines.append(f"- App.tsx line count: {app_line_count}")

    if app_line_count > 1800:
        report_lines.append("- MEDIUM: App.tsx is large enough to justify controlled component/API extraction.")
    else:
        report_lines.append("- INFO: App.tsx size is acceptable but should be watched.")

    report_lines.append("")
    report_lines.append("## Recommended next work")
    report_lines.append("")
    report_lines.append("1. Extract API helper functions before adding more fetch logic.")
    report_lines.append("2. Extract RedactionSettingsWorkspace and RunHistoryWorkspace first.")
    report_lines.append("3. Add module contract helpers before IIS/Application local collection.")
    report_lines.append("4. Keep zero-finding behavior and redaction report tests in the regression set.")

    write_text(out_dir / "PLATFORM_CONTRACT_AUDIT.md", "\n".join(report_lines))

    snapshot_dir = out_dir / "source_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for rel in [
        Path("frontend/src/App.tsx"),
        Path("backend/app/api/reports.py"),
        Path("backend/app/services/redaction_engine.py"),
        Path("docs/architecture/PLATFORM_MODULE_CONTRACT.md"),
        Path("docs/roadmap/MILESTONE_26_5_PLATFORM_CONTRACT.md"),
    ]:
        src = root / rel
        if src.exists():
            safe_name = str(rel).replace("\\", "_").replace("/", "_")
            (snapshot_dir / safe_name).write_text(read(src), encoding="utf-8", errors="replace")

    zip_dir(out_dir, zip_path)

    print("")
    print("Platform contract audit ZIP:")
    print(zip_path)
    print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
