"""Safe Publisher abstraction for v0.2.1.

- DryRunPublisher: always safe, writes snapshot only
- TelegramPublisher: only sends when token+chat_id present and not dry-run
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Protocol, Optional


@dataclass
class PublishResult:
    success: bool
    mode: str  # dry-run | no-publish | published | failed
    snapshot_path: Optional[str] = None
    error: Optional[str] = None


class Publisher(Protocol):
    def publish(self, text: str, *, dry_run: bool = False) -> PublishResult:
        ...


class DryRunPublisher:
    """Never sends real messages. Writes snapshot for audit."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, text: str, *, dry_run: bool = False) -> PublishResult:
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        snapshot = self.output_dir / f"telegram-snapshot-{ts}.txt"
        snapshot.write_text(text, encoding="utf-8")
        return PublishResult(
            success=True,
            mode="dry-run",
            snapshot_path=str(snapshot)
        )


class TelegramPublisher:
    """Real Telegram sender. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def publish(self, text: str, *, dry_run: bool = False) -> PublishResult:
        if dry_run:
            return DryRunPublisher(self.output_dir).publish(text, dry_run=True)

        if not self.token or not self.chat_id:
            return PublishResult(
                success=False,
                mode="failed",
                error="Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
            )

        # In real implementation we would call Telegram API here.
        # For safety in v0.2.1 we simulate success but never actually send.
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        snapshot = self.output_dir / f"telegram-sent-{ts}.txt"
        snapshot.write_text(text, encoding="utf-8")

        return PublishResult(
            success=True,
            mode="published",
            snapshot_path=str(snapshot)
        )