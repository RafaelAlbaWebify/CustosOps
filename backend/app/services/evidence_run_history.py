import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.evidence_run import EvidenceRunCreateRequest, EvidenceRunRecord


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUN_HISTORY_DIR = PROJECT_ROOT / "reports" / "custosops_run_history"
RUN_HISTORY_PATH = RUN_HISTORY_DIR / "runs.json"
MAX_RUNS = 500


def list_evidence_runs(limit: int | None = None) -> list[EvidenceRunRecord]:
    runs = _load_raw_runs()

    records = [EvidenceRunRecord.model_validate(run) for run in runs]
    records.sort(key=lambda run: run.created_at, reverse=True)

    if limit is not None:
        records = records[: max(0, limit)]

    return records


def record_evidence_run(request: EvidenceRunCreateRequest) -> EvidenceRunRecord:
    RUN_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    current = _load_raw_runs()

    record = EvidenceRunRecord(
        **request.model_dump(),
        run_id=_new_run_id(request.module_id),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    current.append(record.model_dump())
    current = current[-MAX_RUNS:]

    _write_raw_runs(current)

    return record


def clear_evidence_runs() -> int:
    previous = len(_load_raw_runs())

    RUN_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    _write_raw_runs([])

    return previous


def _load_raw_runs() -> list[dict[str, Any]]:
    if not RUN_HISTORY_PATH.exists():
        return []

    try:
        raw = RUN_HISTORY_PATH.read_text(encoding="utf-8-sig")
        parsed = json.loads(raw)

        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]

        if isinstance(parsed, dict) and isinstance(parsed.get("runs"), list):
            return [item for item in parsed["runs"] if isinstance(item, dict)]
    except Exception:
        return []

    return []


def _write_raw_runs(runs: list[dict[str, Any]]) -> None:
    RUN_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    RUN_HISTORY_PATH.write_text(json.dumps(runs, indent=2), encoding="utf-8")


def _new_run_id(module_id: str) -> str:
    safe_module = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in module_id.lower()).strip("-")
    return f"run-{safe_module}-{uuid4().hex[:12]}"
