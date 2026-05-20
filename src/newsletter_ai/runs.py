"""Run artifact index for newsletter-ai v0.3.19.

Tracks snapshot, digest, telegram text, quality report, last-run-status,
ingestion report for each daily run. No secrets, no network.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

RUNS_DIR = "output/runs"
INDEX_FILE = "index.json"
MAX_INDEX_ENTRIES = 50


class RunIndexError(Exception):
    pass


def _runs_dir(output_dir: Path) -> Path:
    """Return output_dir/runs (not output_dir/output/runs)."""
    path = output_dir / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path, base: Path) -> str:
    """Return path relative to project base, or absolute if outside."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def make_run_record(
    run_id: str,
    created_at: str,
    status: str,
    input_mode: str,
    output_dir: Path,
    base_dir: Path,
    item_count: int = 0,
    section_count: int = 0,
    source_count: int = 0,
    source_registry_path: Optional[Path] = None,
    snapshot_path: Optional[Path] = None,
    digest_path: Optional[Path] = None,
    telegram_path: Optional[Path] = None,
    quality_report_path: Optional[Path] = None,
    last_run_status_path: Optional[Path] = None,
    ingestion_report_summary: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a run record dict. All paths stored relative to base_dir."""
    record: Dict[str, Any] = {
        "run_id": run_id,
        "created_at": created_at,
        "status": status,
        "input_mode": input_mode,
        "item_count": item_count,
        "section_count": section_count,
        "source_count": source_count,
    }
    if source_registry_path is not None:
        record["source_registry_path"] = _rel(source_registry_path, base_dir)
    if snapshot_path is not None:
        record["snapshot_path"] = _rel(snapshot_path, base_dir)
    if digest_path is not None:
        record["digest_path"] = _rel(digest_path, base_dir)
    if telegram_path is not None:
        record["telegram_path"] = _rel(telegram_path, base_dir)
    if quality_report_path is not None:
        record["quality_report_path"] = _rel(quality_report_path, base_dir)
    if last_run_status_path is not None:
        record["last_run_status_path"] = _rel(last_run_status_path, base_dir)
    if ingestion_report_summary is not None:
        record["ingestion_report_summary"] = ingestion_report_summary
    if warnings is not None:
        record["warnings"] = warnings
    if errors is not None:
        record["errors"] = errors
    return record


def append_run_record(
    record: Dict[str, Any],
    output_dir: Path,
    base_dir: Path,
) -> Path:
    """Write run record to output/runs/<run_id>.json and update index.json."""
    runs = _runs_dir(output_dir)
    run_id = record["run_id"]

    # Write individual run record
    record_path = runs / f"{run_id}.json"
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update index
    index_path = runs / INDEX_FILE
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            index = {"runs": []}
    else:
        index = {"runs": []}

    if not isinstance(index, dict):
        index = {"runs": []}
    if "runs" not in index or not isinstance(index["runs"], list):
        index["runs"] = []

    # Append new entry (lightweight)
    index_entry = {
        "run_id": run_id,
        "created_at": record.get("created_at", _now_iso()),
        "status": record.get("status", "unknown"),
        "input_mode": record.get("input_mode", "unknown"),
        "item_count": record.get("item_count", 0),
        "quality_report_path": record.get("quality_report_path"),
        "record_path": _rel(record_path, base_dir),
    }
    index["runs"].append(index_entry)

    # Trim old entries
    if len(index["runs"]) > MAX_INDEX_ENTRIES:
        index["runs"] = index["runs"][-MAX_INDEX_ENTRIES:]

    index["updated_at"] = _now_iso()
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    return record_path


def load_run_index(output_dir: Path) -> Dict[str, Any]:
    """Load index.json from output/runs/."""
    index_path = _runs_dir(output_dir) / INDEX_FILE
    if not index_path.exists():
        raise RunIndexError("No run index found.")
    return json.loads(index_path.read_text(encoding="utf-8"))


def load_run_record(run_id: str, output_dir: Path) -> Dict[str, Any]:
    """Load a specific run record by run_id."""
    record_path = _runs_dir(output_dir) / f"{run_id}.json"
    if not record_path.exists():
        raise RunIndexError(f"Run record not found: {run_id}")
    return json.loads(record_path.read_text(encoding="utf-8"))


def list_runs(output_dir: Path, limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent runs from index, newest first."""
    try:
        index = load_run_index(output_dir)
    except RunIndexError:
        return []
    runs = index.get("runs", [])
    # Already in chronological order; return newest first
    return list(reversed(runs[-limit:]))


def get_latest_run(output_dir: Path) -> Optional[Dict[str, Any]]:
    """Return the latest run record, or None."""
    runs = list_runs(output_dir, limit=1)
    return runs[0] if runs else None
