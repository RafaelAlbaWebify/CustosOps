import json
import subprocess
from pathlib import Path
from typing import Any

from app.schemas.windows_event import WindowsEventEvidence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
COLLECTOR_PATH = PROJECT_ROOT / "collectors" / "powershell" / "windows_events" / "Get-WindowsEventEvidence.ps1"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "windows-event-evidence.local.json"


class WindowsEventCollectionError(RuntimeError):
    pass


def collect_local_windows_event_evidence(
    output_path: Path | None = None,
    since_hours: int = 72,
    max_events_per_log: int = 300,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    target_output = output_path or DEFAULT_OUTPUT_PATH
    target_output.parent.mkdir(parents=True, exist_ok=True)

    if not COLLECTOR_PATH.exists():
        raise FileNotFoundError(f"Windows Event collector was not found: {COLLECTOR_PATH}")

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(COLLECTOR_PATH),
        "-OutputPath",
        str(target_output),
        "-SinceHours",
        str(since_hours),
        "-MaxEventsPerLog",
        str(max_events_per_log),
    ]

    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )

    if result.returncode != 0:
        raise WindowsEventCollectionError(
            "Windows Event collector failed.\n"
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    if not target_output.exists():
        raise WindowsEventCollectionError(f"Windows Event collector did not create output: {target_output}")

    raw = target_output.read_text(encoding="utf-8-sig")
    parsed = json.loads(raw)
    evidence = WindowsEventEvidence.model_validate(parsed)

    return {
        "output_path": str(target_output),
        "relative_output_path": str(target_output.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "evidence": evidence.model_dump(),
    }
