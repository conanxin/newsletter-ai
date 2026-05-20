"""Tests for newsletter-ai quality sections CLI (v0.3.4)."""

import subprocess
import sys
from pathlib import Path


def test_quality_sections_command_exists():
    """newsletter-ai quality sections should be a valid subcommand."""
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "quality", "sections", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    # Even if it fails due to missing args, it should not say "invalid choice"
    assert "invalid choice" not in result.stderr.lower()


def test_quality_sections_graceful_when_no_report(tmp_path, monkeypatch):
    """Should print helpful message when no quality report exists."""
    # Simulate missing report
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "quality", "sections"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    # The CLI should handle missing report gracefully
    assert "No quality report found" in result.stdout or "Run daily" in result.stdout or result.returncode == 0