"""Tests for sources CLI commands (v0.3.9)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.cli import main


def test_cli_sources_list(capsys, monkeypatch):
    """Test newsletter-ai sources list"""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "list"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "sample-ai-feed" in captured.out or "Source ID" in captured.out


def test_cli_sources_validate(capsys, monkeypatch):
    """Test newsletter-ai sources validate"""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "validate"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "valid" in captured.out.lower() or "OK" in captured.out


def test_cli_sources_ingest_fixtures(capsys, monkeypatch):
    """Test newsletter-ai sources ingest-fixtures"""
    monkeypatch.setattr("sys.argv", ["newsletter-ai", "sources", "ingest-fixtures"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "Ingested" in captured.out
