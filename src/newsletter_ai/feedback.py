"""Feedback engine v0.2.4R - fixed for test closure."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_jsonl(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


DEFAULT_PREFERENCES = {
    "source_weights": {},
    "topic_weights": {},
    "style_weights": {},
    "version": "0.2.4R",
}


def load_preferences(data_dir: Path) -> Dict:
    pref_file = data_dir / "state" / "preferences.json"
    if pref_file.exists():
        return _load_json(pref_file, DEFAULT_PREFERENCES)
    return DEFAULT_PREFERENCES.copy()


def save_preferences(data_dir: Path, prefs: Dict) -> None:
    pref_file = data_dir / "state" / "preferences.json"
    _write_json(pref_file, prefs)


def record_feedback_event(data_dir: Path, **kwargs) -> Dict:
    event = {
        "event_id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        **kwargs,
    }
    event_file = data_dir / "state" / "feedback_events.jsonl"
    _append_jsonl(event_file, event)
    return event


def update_preferences(data_dir: Path, action: str, **kwargs) -> Dict:
    prefs = load_preferences(data_dir)
    before = json.loads(json.dumps(prefs))
    changed = []

    source = kwargs.get("source")
    delta = 0.15 if action in ("like", "save") else -0.15 if action == "dislike" else 0.0

    if source:
        old = prefs.setdefault("source_weights", {}).get(source, 1.0)
        new = max(0.1, min(3.0, old + delta))
        if abs(new - old) > 0.001:
            prefs["source_weights"][source] = round(new, 3)
            changed.append((source, round(old, 3), round(new, 3)))

    save_preferences(data_dir, prefs)

    history_file = data_dir / "state" / "preferences_history.jsonl"
    _append_jsonl(history_file, {
        "created_at": _now_iso(),
        "action": action,
        "before": before,
        "after": prefs,
        "changed": changed,
        "reason": f"feedback:{action}"
    })

    return {"changed": changed, "before": before, "after": prefs, "reason": f"feedback:{action}"}


def resolve_item_from_snapshot(data_dir: Path, output_dir: Path, item_index: int) -> Optional[Dict]:
    latest = output_dir / "snapshots" / "latest_items.json"
    if not latest.exists():
        ptr = data_dir / "state" / "latest_snapshot.json"
        if ptr.exists():
            p = _load_json(ptr, {})
            latest = Path(p.get("latest_items", ""))

    if not latest or not latest.exists():
        return None

    items = _load_json(latest, [])
    if not items or item_index < 1 or item_index > len(items):
        return None
    return items[item_index - 1]


def apply_feedback(command: str, cfg: Dict, dry_run: bool = False) -> str:
    data_dir = Path(cfg.get("DATA_DIR", "data"))
    output_dir = Path(cfg.get("OUTPUT_DIR", "output"))

    parts = command.strip().split()
    if not parts:
        return "ERROR: empty command"

    action = parts[0]
    item_index = None
    target = None

    if len(parts) > 1 and parts[1].isdigit():
        item_index = int(parts[1])
    elif len(parts) > 1:
        target = " ".join(parts[1:])

    resolved = None
    if item_index is not None:
        resolved = resolve_item_from_snapshot(data_dir, output_dir, item_index)
        if resolved is None:
            return ("ERROR: No latest snapshot found or index out of range. "
                    "Run newsletter-ai daily --dry-run first.")

    if dry_run:
        meta = resolved or {"source": target}
        return f"[DRY-RUN] would apply {action} on {meta.get('title') or target}"

    event = record_feedback_event(
        data_dir,
        action=action,
        item_index=item_index,
        source=resolved.get("source") if resolved else target,
        title=resolved.get("title") if resolved else None,
        url=resolved.get("url") if resolved else None,
        topic_tags=resolved.get("topic_tags") if resolved else [],
        style_tags=resolved.get("style_tags") if resolved else [],
    )

    result = update_preferences(data_dir, action=action, source=event.get("source"))
    return f"feedback applied: {action} on item {item_index} → changed {len(result.get('changed', []))} weights"