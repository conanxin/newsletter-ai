"""Tests for CLI sources report commands (v0.3.11)."""

import pytest
from pathlib import Path

from newsletter_ai.cli import main


def test_cli_sources_ingest_fixtures_with_report(capsys, monkeypatch):
    """Test sources ingest-fixtures shows per-source status."""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "ingest-fixtures"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "Ingested" in captured.out
    assert "Per-source status:" in captured.out
    assert "sample-ai-feed" in captured.out


def test_cli_sources_report(capsys, monkeypatch):
    """Test sources report shows latest ingestion report."""
    # First run ingest-fixtures to generate report
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "ingest-fixtures"])
    try:
        main()
    except SystemExit:
        pass

    # Then run report
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "report"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "Source Ingestion Report" in captured.out
    assert "sample-ai-feed" in captured.out


def test_cli_sources_validate_no_regression(capsys, monkeypatch):
    """Test sources validate still works."""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "validate"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()
