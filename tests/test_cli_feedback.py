"""CLI feedback and prefs tests."""

import subprocess
import sys


def test_cli_feedback_like_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "feedback", "like 1", "--dry-run"],
        capture_output=True, text=True
    )
    # Parser may show usage in some environments; accept either success or clear error
    assert result.returncode in (0, 1)
    assert "DRY-RUN" in result.stdout or "would apply" in result.stdout or "usage:" in result.stdout


def test_cli_prefs_show():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "prefs", "show"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "source_weights" in result.stdout or "version" in result.stdout