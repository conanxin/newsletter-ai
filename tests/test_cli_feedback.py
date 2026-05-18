"""CLI feedback and prefs tests."""

import subprocess
import sys


def test_cli_feedback_like_dry_run():
    # Current implementation treats dry-run inside apply_feedback
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "feedback", "like 1"],
        capture_output=True, text=True, env={"NEWSLETTER_BASE_DIR": "/tmp"}
    )
    # Even without flag it should not crash
    assert result.returncode == 0 or "feedback applied" in result.stdout


def test_cli_prefs_show():
    result = subprocess.run(
        [sys.executable, "-m", "newsletter_ai.cli", "prefs", "show"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "source_weights" in result.stdout or "version" in result.stdout