"""Pipeline status checker."""

import json
from pathlib import Path
from typing import Dict


def check_pipeline_status(cfg: Dict) -> str:
    status_file = cfg["OUTPUT_DIR"] / "state" / "last-run-status.json"
    if status_file.exists():
        data = json.loads(status_file.read_text())
        return json.dumps(data, indent=2, ensure_ascii=False)
    return "No previous run status found."