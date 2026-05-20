"""Tests for quality sources and duplicates CLI commands (v0.3.2.1)."""

import subprocess
import sys
from pathlib import Path


def test_quality_sources_runs():
    """quality sources should be accepted by the CLI parser."""
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "quality", "sources"],
        capture_output=True,
        text=True,
    )
    # Should not fail with "invalid choice"
    assert "invalid choice" not in result.stderr
    assert result.returncode in (0, 1)  # 0 if report exists, 1 if missing (graceful)


def test_quality_duplicates_runs():
    """quality duplicates should be accepted by the CLI parser."""
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "quality", "duplicates"],
        capture_output=True,
        text=True,
    )
    assert "invalid choice" not in result.stderr
    assert result.returncode in (0, 1)


def test_quality_sources_missing_report_graceful():
    """When no report exists, should print clear message instead of traceback."""
    # Temporarily move the report if it exists
    quality_dir = Path("output/quality")
    latest = quality_dir / "latest_quality.json"
    backup = None
    if latest.exists():
        backup = latest.read_text()
        latest.unlink()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "quality", "sources"],
            capture_output=True,
            text=True,
        )
        assert "No quality report found" in result.stdout or "No quality report found" in result.stderr
        assert "Traceback" not in result.stderr
    finally:
        if backup:
            quality_dir.mkdir(parents=True, exist_ok=True)
            latest.write_text(backup)


def test_quality_duplicates_missing_report_graceful():
    """When no report exists, should print clear message instead of traceback."""
    quality_dir = Path("output/quality")
    latest = quality_dir / "latest_quality.json"
    backup = None
    if latest.exists():
        backup = latest.read_text()
        latest.unlink()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "quality", "duplicates"],
            capture_output=True,
            text=True,
        )
        assert "No quality report found" in result.stdout or "No quality report found" in result.stderr
        assert "Traceback" not in result.stderr
    finally:
        if backup:
            quality_dir.mkdir(parents=True, exist_ok=True)
            latest.write_text(backup)
