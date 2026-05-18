"""Feedback engine v0.2.2 - real preference updates with audit trail."""

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
    "version": "0.2.2",
}


def load_preferences(data_dir: Path) -> Dict:
    pref_file = data_dir / "state" / "preferences.json"
    if pref_file.exists():
        return _load_json(pref_file, DEFAULT_PREFERENCES)
    example = data_dir / "state" / "preferences.example.json"
    if example.exists():
        return _load_json(example, DEFAULT_PREFERENCES)
    return DEFAULT_PREFERENCES.copy()


def save_preferences(data_dir: Path, prefs: Dict) -> None:
    pref_file = data_dir / "state" / "preferences.json"
    _write_json(pref_file, prefs)


def record_feedback_event(
    data_dir: Path,
    action: str,
    item_id: Optional[str] = None,
    item_index: Optional[int] = None,
    source: Optional[str] = None,
    title: Optional[str] = None,
    url: Optional[str] = None,
    topic_tags: Optional[List[str]] = None,
    style_tags: Optional[List[str]] = None,
    delta: float = 0.0,
    note: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict:
    event = {
        "event_id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "action": action,
        "item_id": item_id,
        "item_index": item_index,
        "source": source,
        "title": title,
        "url": url,
        "topic_tags": topic_tags or [],
        "style_tags": style_tags or [],
        "delta": delta,
        "note": note,
        "run_id": run_id,
    }
    event_file = data_dir / "state" / "feedback_events.jsonl"
    _append_jsonl(event_file, event)
    return event


def update_preferences(
    data_dir: Path, action: str, source: Optional[str] = None,
    topic_tags: Optional[List[str]] = None, style_tags: Optional[List[str]] = None,
    delta: Optional[float] = None
) -> Dict:
    prefs = load_preferences(data_dir)
    before = json.loads(json.dumps(prefs))

    # Determine delta
    if delta is None:
        if action in ("like", "save"):
            delta = 0.15 if action == "like" else 0.25
        elif action == "dislike":
            delta = -0.15
        elif action == "skip":
            delta = -0.05
        elif action.endswith("_up"):
            delta = 0.2
        elif action.endswith("_down"):
            delta = -0.2
        else:
            delta = 0.0

    changed = []

    def _update_weight(container: Dict, key: str, d: float):
        if not key:
            return
        old = container.get(key, 1.0)
        new = max(0.1, min(3.0, old + d))
        if abs(new - old) > 0.001:
            container[key] = round(new, 3)
            changed.append((key, round(old, 3), round(new, 3)))

    if action in ("like", "dislike", "save", "skip"):
        for tag in (topic_tags or []):
            _update_weight(prefs["topic_weights"], tag, delta)
        for tag in (style_tags or []):
            _update_weight(prefs["style_weights"], tag, delta)
        if source:
            _update_weight(prefs["source_weights"], source, delta * 0.8)

    elif action == "source_up":
        _update_weight(prefs["source_weights"], source, 0.25)
    elif action == "source_down":
        _update_weight(prefs["source_weights"], source, -0.25)
    elif action == "topic_up":
        for tag in (topic_tags or []):
            _update_weight(prefs["topic_weights"], tag, 0.25)
    elif action == "topic_down":
        for tag in (topic_tags or []):
            _update_weight(prefs["topic_weights"], tag, -0.25)
    elif action == "style_up":
        for tag in (style_tags or []):
            _update_weight(prefs["style_weights"], tag, 0.25)
    elif action == "style_down":
        for tag in (style_tags or []):
            _update_weight(prefs["style_weights"], tag, -0.25)

    save_preferences(data_dir, prefs)

    # Record history
    history_file = data_dir / "state" / "preferences_history.jsonl"
    _append_jsonl(history_file, {
        "created_at": _now_iso(),
        "action": action,
        "before": before,
        "after": prefs,
        "changed": changed,
        "reason": f"feedback:{action}"
    })

    return {
        "changed": changed,
        "before": before,
        "after": prefs,
        "reason": f"feedback:{action}"
    }


def apply_feedback(command: str, cfg: Dict, dry_run: bool = False) -> str:
    """Main entry for CLI feedback commands."""
    data_dir = Path(cfg.get("DATA_DIR", "data"))
    parts = command.strip().split()
    if not parts:
        return "ERROR: empty command"

    action = parts[0]
    item_index = None
    note = None
    target = None

    # Parse simple commands like "like 1" or "source_up Stratechery"
    if len(parts) > 1:
        if parts[1].isdigit():
            item_index = int(parts[1])
        else:
            target = " ".join(parts[1:])

    if dry_run:
        return f"[DRY-RUN] would apply {action} on item {item_index or target}"

    event = record_feedback_event(
        data_dir,
        action=action,
        item_index=item_index,
        source=target,
        note=note,
    )

    result = update_preferences(
        data_dir,
        action=action,
        source=target,
        topic_tags=event.get("topic_tags"),
        style_tags=event.get("style_tags"),
    )

    return f"feedback applied: {action} → changed {len(result['changed'])} weights"