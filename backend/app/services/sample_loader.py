import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[3]


def load_sample_json(relative_path: str) -> dict[str, Any]:
    path = ROOT_DIR / relative_path

    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Sample JSON must contain an object: {relative_path}")

    return data