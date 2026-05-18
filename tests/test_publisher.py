"""Test safe publisher layer."""

from pathlib import Path
import tempfile
from newsletter_ai.publisher import DryRunPublisher, TelegramPublisher, PublishResult


def test_dry_run_publisher_writes_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        p = DryRunPublisher(Path(tmp))
        result = p.publish("test digest", dry_run=True)
        assert result.success is True
        assert result.mode == "dry-run"
        assert result.snapshot_path is not None
        assert Path(result.snapshot_path).exists()


def test_telegram_publisher_missing_token_does_not_crash_on_dry_run():
    with tempfile.TemporaryDirectory() as tmp:
        pub = TelegramPublisher(Path(tmp))
        result = pub.publish("test", dry_run=True)
        assert result.success is True
        assert result.mode == "dry-run"


def test_telegram_publisher_real_publish_fails_without_token():
    with tempfile.TemporaryDirectory() as tmp:
        pub = TelegramPublisher(Path(tmp))
        result = pub.publish("test", dry_run=False)
        assert result.success is False
        assert "Missing TELEGRAM" in result.error