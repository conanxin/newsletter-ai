"""Tests for CLI daily with --source-registry (v0.3.10)."""

import pytest
from pathlib import Path

from newsletter_ai.cli import main


def test_cli_daily_source_registry_dry_run(capsys, monkeypatch):
    """Test newsletter-ai daily --dry-run --source-registry"""
    registry = Path(__file__).parent.parent / "data" / "fixtures" / "source_registry.json"
    monkeypatch.setattr("sys.argv", [
        "newsletter-ai", "daily", "--dry-run",
        "--source-registry", str(registry)
    ])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "source_registry" in captured.out or "success" in captured.out.lower()


def test_cli_daily_source_registry_requires_dry_run(capsys, monkeypatch):
    """Test --source-registry without --dry-run fails"""
    registry = Path(__file__).parent.parent / "data" / "fixtures" / "source_registry.json"
    monkeypatch.setattr("sys.argv", [
        "newsletter-ai", "daily",
        "--source-registry", str(registry)
    ])
    try:
        main()
    except SystemExit as e:
        assert e.code == 1

    captured = capsys.readouterr()
    assert "requires --dry-run" in captured.out or "Error" in captured.out


def test_cli_daily_source_registry_invalid_path(capsys, monkeypatch):
    """Test invalid registry path gives clear error"""
    monkeypatch.setattr("sys.argv", [
        "newsletter-ai", "daily", "--dry-run",
        "--source-registry", "/nonexistent/registry.json"
    ])
    try:
        main()
    except SystemExit as e:
        assert e.code == 1

    captured = capsys.readouterr()
    assert "not found" in captured.out.lower() or "Error" in captured.out


def test_cli_daily_default_no_regression(capsys, monkeypatch):
    """Test default daily --dry-run still works"""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "daily", "--dry-run"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "success" in captured.out.lower()
