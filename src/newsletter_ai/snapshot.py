"""Digest snapshot engine for v0.2.3.

Writes stable latest_items.json + historical snapshots for feedback resolution.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_item_snapshot(
    items: List[Dict[str, Any]],
    output_dir: Path,
    data_dir: Path,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create latest + historical snapshot from ranked items."""
    ts = _now_ts()
    run_id = run_id or ts

    snapshot_items = []
    for idx, item in enumerate(items, start=1):
        snap = {
            "item_id": item.get("id") or f"item-{idx}",
            "item_index": idx,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": item.get("source"),
            "title": item.get("title"),
            "url": item.get("url"),
            "summary": item.get("summary") or item.get("description", "")[:200],
            "topic_tags": item.get("topic_tags", []),
            "style_tags": item.get("style_tags", []),
            "score": item.get("score", 0.0),
            "score_breakdown": item.get("score_breakdown", {}),
        }
        snapshot_items.append(snap)

    # latest
    latest_path = output_dir / "snapshots" / "latest_items.json"
    _write_json(latest_path, snapshot_items)

    # historical
    hist_path = output_dir / "snapshots" / f"items-{ts}.json"
    _write_json(hist_path, snapshot_items)

    # pointer in state
    pointer = data_dir / "state" / "latest_snapshot.json"
    _write_json(pointer, {
        "latest_items": str(latest_path),
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(snapshot_items),
    })

    return {
        "latest": str(latest_path),
        "historical": str(hist_path),
        "pointer": str(pointer),
        "count": len(snapshot_items),
        "run_id": run_id,
    }