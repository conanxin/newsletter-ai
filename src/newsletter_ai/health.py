"""Health report v0.2.2 - real status of feedback, preferences and safety."""

import os
from pathlib import Path
from typing import Dict


def build_health_report(cfg: Dict) -> str:
    data_dir = Path(cfg.get("DATA_DIR", "data"))
    output_dir = Path(cfg.get("OUTPUT_DIR", "output"))

    lines = ["=== Newsletter AI Health Report v0.2.2 ==="]

    # Config
    lines.append(f"BASE_DIR: {cfg.get('BASE_DIR')}")
    lines.append(f"DATA_DIR: {data_dir}")
    lines.append(f"OUTPUT_DIR: {output_dir}")

    # Preferences
    pref_file = data_dir / "state" / "preferences.json"
    lines.append(f"preferences.json: {'EXISTS' if pref_file.exists() else 'MISSING'}")

    # Feedback events
    events_file = data_dir / "state" / "feedback_events.jsonl"
    event_count = 0
    if events_file.exists():
        event_count = sum(1 for _ in events_file.open())
    lines.append(f"feedback_events.jsonl count: {event_count}")

    # Last run status
    status_file = output_dir / "state" / "last-run-status.json"
    lines.append(f"last-run-status.json: {'EXISTS' if status_file.exists() else 'MISSING'}")

    # Publisher safety
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        lines.append("Publisher: TelegramPublisher (token present)")
    else:
        lines.append("Publisher: DryRunPublisher (no token) - safe")

    # Legacy
    lines.append("Legacy scripts: migrated to legacy/v0.1/scripts/ (deprecated)")

    # Warnings
    warnings = []
    if not pref_file.exists():
        warnings.append("No preferences.json - using defaults")
    if not (token and chat_id):
        warnings.append("No Telegram credentials - publish will be dry-run only")
    lines.append(f"Warnings: {', '.join(warnings) if warnings else 'None'}")

    return "\n".join(lines)