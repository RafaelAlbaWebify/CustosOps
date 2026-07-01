import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_ROOT = PROJECT_ROOT / "reports" / "custosops_archive"
MANIFEST_PATH = ARCHIVE_ROOT / "manifest.json"


def save_archived_report(
    report_type: str,
    report_format: str,
    filename: str,
    content_type: str,
    content: str,
) -> dict:
    generated_at = datetime.now(timezone.utc)
    date_folder = generated_at.strftime("%Y%m%d")
    entry_id = uuid4().hex[:12]

    safe_report_type = _safe_part(report_type)
    safe_filename = _safe_filename(filename)

    target_dir = ARCHIVE_ROOT / safe_report_type / date_folder
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / safe_filename
    target_path.write_text(content, encoding="utf-8")

    relative_path = target_path.relative_to(PROJECT_ROOT)

    entry = {
        "id": entry_id,
        "report_type": safe_report_type,
        "format": report_format,
        "filename": safe_filename,
        "relative_path": str(relative_path).replace("\\", "/"),
        "content_type": content_type,
        "generated_at_utc": generated_at.isoformat(),
        "size_bytes": target_path.stat().st_size,
    }

    entries = _load_manifest()
    entries.insert(0, entry)
    entries = entries[:300]
    _write_manifest(entries)

    return entry


def list_archived_reports(limit: int = 100) -> list[dict]:
    entries = _load_manifest()
    existing_entries: list[dict] = []

    for entry in entries:
        path = resolve_archive_entry_path(entry)
        if path and path.exists():
            existing_entries.append(entry)

    if len(existing_entries) != len(entries):
        _write_manifest(existing_entries)

    return existing_entries[:limit]


def get_archived_report(entry_id: str) -> tuple[dict, bytes]:
    entries = _load_manifest()

    for entry in entries:
        if entry.get("id") != entry_id:
            continue

        path = resolve_archive_entry_path(entry)

        if not path or not path.exists():
            raise FileNotFoundError("Archived report file was not found.")

        return entry, path.read_bytes()

    raise KeyError("Archived report entry was not found.")


def delete_archived_report(entry_id: str) -> dict:
    entries = _load_manifest()
    kept_entries: list[dict] = []
    deleted_entry: dict | None = None

    for entry in entries:
        if entry.get("id") == entry_id:
            deleted_entry = entry
            continue

        kept_entries.append(entry)

    if deleted_entry is None:
        raise KeyError("Archived report entry was not found.")

    path = resolve_archive_entry_path(deleted_entry)

    if path and path.exists():
        path.unlink()

    _write_manifest(kept_entries)

    return deleted_entry


def resolve_archive_entry_path(entry: dict) -> Path | None:
    raw_relative = entry.get("relative_path")

    if not isinstance(raw_relative, str) or raw_relative.strip() == "":
        return None

    candidate = (PROJECT_ROOT / raw_relative).resolve()

    try:
        candidate.relative_to(ARCHIVE_ROOT.resolve())
    except ValueError:
        return None

    return candidate


def _load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []

    try:
        raw = MANIFEST_PATH.read_text(encoding="utf-8-sig")
        parsed = json.loads(raw)
    except Exception:
        return []

    if not isinstance(parsed, list):
        return []

    return [entry for entry in parsed if isinstance(entry, dict)]


def _write_manifest(entries: list[dict]) -> None:
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _safe_part(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return cleaned.strip("_")[:50] or "report"


def _safe_filename(value: str) -> str:
    filename = Path(value).name
    cleaned = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in filename)
    return cleaned.strip("_")[:160] or "custosops_report.txt"