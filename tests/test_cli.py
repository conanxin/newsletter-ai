"""CLI integration tests for v0.2.1."""

import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "--help"],
        capture_output=True, text=True
    )
    assert "daily" in result.stdout


def test_cli_daily_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "daily", "--dry-run"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout or "success" in result.stdout


def test_cli_daily_no_publish():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "daily", "--no-publish"],
        capture_output=True, text=True
    )
    assert result.returncode == 0