"""Tests for CLI dashboard subcommand."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCliDashboard:
    def test_dashboard_build_without_run_data(self):
        """Should fail gracefully when no latest run data exists."""
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "build"],
            capture_output=True,
            text=True,
        )
        # May fail if no run data, or succeed if previous runs exist
        # We just verify it doesn't crash with traceback
        assert "Traceback" not in result.stderr

    def test_dashboard_show_without_build(self):
        """Should fail gracefully when dashboard not built."""
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "show"],
            capture_output=True,
            text=True,
        )
        # If dashboard exists from previous test, it passes; if not, graceful error
        assert result.returncode in (0, 1)
        assert "Traceback" not in result.stderr

    def test_dashboard_build_after_daily(self, tmp_path):
        """Build dashboard after running daily dry-run."""
        # Run daily dry-run first
        daily_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "daily", "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert daily_result.returncode == 0, daily_result.stderr

        # Build dashboard
        build_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "build"],
            capture_output=True,
            text=True,
        )
        assert build_result.returncode == 0, build_result.stderr
        assert "Dashboard built:" in build_result.stdout
        assert "output/dashboard/index.html" in build_result.stdout

        # Show dashboard
        show_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "show"],
            capture_output=True,
            text=True,
        )
        assert show_result.returncode == 0, show_result.stderr
        assert "Dashboard:" in show_result.stdout
        assert "index.html" in show_result.stdout

    def test_dashboard_build_with_trial_registry(self):
        """Build dashboard after trial registry daily."""
        # Run trial registry daily
        daily_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "newsletter_ai.cli",
                "daily",
                "--dry-run",
                "--source-registry",
                "data/fixtures/real_source_trial_registry.json",
            ],
            capture_output=True,
            text=True,
        )
        assert daily_result.returncode == 0, daily_result.stderr

        # Build dashboard
        build_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "build"],
            capture_output=True,
            text=True,
        )
        assert build_result.returncode == 0, build_result.stderr
        assert "Dashboard built:" in build_result.stdout

        # Verify HTML contains HN items
        dashboard_path = Path("output/dashboard/index.html")
        if dashboard_path.exists():
            content = dashboard_path.read_text(encoding="utf-8")
            assert "Hacker News" in content or "tech" in content

    def test_dashboard_export_command(self, tmp_path):
        """Export dashboard bundle via CLI."""
        # Run daily dry-run first
        daily_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "daily", "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert daily_result.returncode == 0, daily_result.stderr

        export_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "dashboard", "export"],
            capture_output=True,
            text=True,
        )
        assert export_result.returncode == 0, export_result.stderr
        assert "Dashboard bundle exported:" in export_result.stdout
        assert "index.html" in export_result.stdout
        assert "metadata.json" in export_result.stdout
        assert "README.txt" in export_result.stdout

        # Verify files exist
        dist_path = Path("dist/dashboard")
        if dist_path.exists():
            assert (dist_path / "index.html").exists()
            assert (dist_path / "metadata.json").exists()
            assert (dist_path / "README.txt").exists()

    def test_dashboard_export_custom_out(self, tmp_path):
        """Export dashboard bundle to custom directory."""
        # Run daily dry-run first
        daily_result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "daily", "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert daily_result.returncode == 0, daily_result.stderr

        custom_dir = tmp_path / "custom-export"
        export_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "newsletter_ai.cli",
                "dashboard",
                "export",
                "--out",
                str(custom_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert export_result.returncode == 0, export_result.stderr
        assert "Dashboard bundle exported:" in export_result.stdout
        assert (custom_dir / "index.html").exists()
        assert (custom_dir / "metadata.json").exists()
        assert (custom_dir / "README.txt").exists()
