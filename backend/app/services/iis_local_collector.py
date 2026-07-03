import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.iis import IisEvidence


def collect_local_iis_evidence() -> IisEvidence:
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    computer_name = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or platform.node() or "local-host"

    inetsrv_dir = Path(system_root) / "System32" / "inetsrv"
    appcmd_path = inetsrv_dir / "appcmd.exe"
    inetpub_dir = Path(r"C:\inetpub")
    log_root = inetpub_dir / "logs" / "LogFiles"
    httperr_root = Path(system_root) / "System32" / "LogFiles" / "HTTPERR"

    path_checks = [
        {"path": str(inetsrv_dir), "exists": inetsrv_dir.exists()},
        {"path": str(appcmd_path), "exists": appcmd_path.exists()},
        {"path": str(inetpub_dir), "exists": inetpub_dir.exists()},
        {"path": str(log_root), "exists": log_root.exists()},
        {"path": str(httperr_root), "exists": httperr_root.exists()},
    ]

    warnings: list[str] = []
    services = _collect_services()
    sites: list[dict[str, Any]] = []
    app_pools: list[dict[str, Any]] = []
    applications: list[dict[str, Any]] = []

    if appcmd_path.exists():
        sites = _collect_appcmd_records(str(appcmd_path), "site")
        app_pools = _collect_appcmd_records(str(appcmd_path), "apppool")
        applications = _collect_appcmd_records(str(appcmd_path), "app")
    else:
        warnings.append("appcmd.exe was not found. IIS site and application pool inventory is unavailable.")

    log_directories = _collect_log_directories(log_root)
    log_files = _collect_log_files(log_root)

    if not log_root.exists():
        warnings.append("IIS W3C log directory was not found.")

    event_channels = _collect_event_channels()

    appcmd_available = appcmd_path.exists()
    iis_detected = bool(appcmd_available or services or sites or app_pools or applications or log_files)

    raw_item_count = len(services) + len(sites) + len(app_pools) + len(applications) + len(log_files) + len(event_channels)

    return IisEvidence.model_validate(
        {
            "source_file": "local-iis-application-collection",
            "source_type": "iis_application_local",
            "asset": computer_name,
            "iis_detected": iis_detected,
            "appcmd_available": appcmd_available,
            "raw_item_count": raw_item_count,
            "parsed_item_count": raw_item_count,
            "services": services,
            "sites": sites,
            "application_pools": app_pools,
            "applications": applications,
            "path_checks": path_checks,
            "log_directories": log_directories,
            "log_files": log_files,
            "event_channels": event_channels,
            "collection_warnings": warnings,
            "metadata": {
                "collector": "iis_local_collector",
                "collector_version": "0.1",
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "read_only": True,
            },
        }
    )


def _collect_services() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []

    powershell = shutil.which("powershell") or shutil.which("powershell.exe")
    if not powershell:
        return []

    command = [
        powershell,
        "-NoProfile",
        "-Command",
        "Get-Service -Name W3SVC,WAS,IISADMIN,WebManagementService -ErrorAction SilentlyContinue | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json -Compress",
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=12, check=False)
    except Exception:
        return []

    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        import json

        parsed = json.loads(result.stdout)
    except Exception:
        return []

    if isinstance(parsed, dict):
        parsed_items = [parsed]
    elif isinstance(parsed, list):
        parsed_items = parsed
    else:
        return []

    services: list[dict[str, Any]] = []
    for item in parsed_items:
        if not isinstance(item, dict):
            continue

        services.append(
            {
                "name": str(item.get("Name") or ""),
                "display_name": item.get("DisplayName"),
                "status": str(item.get("Status")) if item.get("Status") is not None else None,
                "start_type": str(item.get("StartType")) if item.get("StartType") is not None else None,
            }
        )

    return [service for service in services if service["name"]]


def _collect_appcmd_records(appcmd_path: str, entity: str) -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            [appcmd_path, "list", entity, "/text:*"],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except Exception:
        return []

    if result.returncode != 0 or not result.stdout.strip():
        return []

    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()

        if not line:
            if current:
                records.append(_normalize_appcmd_record(entity, current))
                current = {}
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip().strip('"')
        else:
            current.setdefault("raw_lines", []).append(line)

    if current:
        records.append(_normalize_appcmd_record(entity, current))

    return records


def _normalize_appcmd_record(entity: str, raw: dict[str, Any]) -> dict[str, Any]:
    lowered = {str(key).lower(): value for key, value in raw.items()}

    if entity == "site":
        return {
            "name": lowered.get("site.name") or lowered.get("name"),
            "site_id": lowered.get("site.id") or lowered.get("id"),
            "state": lowered.get("state"),
            "bindings": _split_bindings(lowered.get("bindings")),
            "physical_path": lowered.get("physicalpath") or lowered.get("physical_path"),
            "raw": raw,
        }

    if entity == "apppool":
        return {
            "name": lowered.get("apppool.name") or lowered.get("name"),
            "state": lowered.get("state"),
            "runtime_version": lowered.get("managedruntimeversion"),
            "pipeline_mode": lowered.get("managedpipelinemode"),
            "identity_type": lowered.get("processmodel.identitytype"),
            "raw": raw,
        }

    return {
        "path": lowered.get("app.path") or lowered.get("path"),
        "site": lowered.get("app.site.name") or lowered.get("site.name"),
        "application_pool": lowered.get("applicationpool"),
        "physical_path": lowered.get("physicalpath"),
        "raw": raw,
    }


def _split_bindings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _collect_log_directories(log_root: Path) -> list[str]:
    if not log_root.exists():
        return []

    try:
        return [str(path) for path in sorted(log_root.rglob("*")) if path.is_dir()][:50]
    except Exception:
        return []


def _collect_log_files(log_root: Path) -> list[dict[str, Any]]:
    if not log_root.exists():
        return []

    try:
        files = [path for path in log_root.rglob("*") if path.is_file()]
    except Exception:
        return []

    files = sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[:30]

    results: list[dict[str, Any]] = []
    for path in files:
        try:
            stat = path.stat()
        except Exception:
            continue

        results.append(
            {
                "path": str(path),
                "length": int(stat.st_size),
                "last_write_time": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )

    return results


def _collect_event_channels() -> list[str]:
    if os.name != "nt":
        return []

    wevtutil = shutil.which("wevtutil") or shutil.which("wevtutil.exe")
    if not wevtutil:
        return []

    try:
        result = subprocess.run([wevtutil, "el"], capture_output=True, text=True, timeout=10, check=False)
    except Exception:
        return []

    if result.returncode != 0:
        return []

    needles = ("iis", "w3svc", "was", "httpservice")
    return [line.strip() for line in result.stdout.splitlines() if any(needle in line.lower() for needle in needles)]