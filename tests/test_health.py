"""Health report tests."""

import tempfile
from pathlib import Path
from newsletter_ai.health import build_health_report


def test_health_no_token_is_not_fatal():
    cfg = {"DATA_DIR": "/tmp", "OUTPUT_DIR": "/tmp/output", "BASE_DIR": "/tmp"}
    report = build_health_report(cfg)
    assert "Publisher: DryRunPublisher" in report or "no token" in report
    assert "Warnings" in report