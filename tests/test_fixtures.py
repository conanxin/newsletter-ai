"""Tests for the fixture loader (v0.3.7+)."""

import pytest
from pathlib import Path

from newsletter_ai.fixtures import (
    load_dry_run_items,
    load_fixture_items_from_path,
    normalize_fixture_item,
    load_rss_fixture_items,
)


def test_load_dry_run_items():
    items = load_dry_run_items()
    assert isinstance(items, list)
    assert len(items) > 0
    for item in items:
        assert "source" in item
        assert "title" in item
        assert "topic_tags" in item
        assert "item_id" in item


def test_normalize_fixture_item():
    raw = {"id": "1", "source": "test", "title": "Test", "base_score": 0.9}
    norm = normalize_fixture_item(raw)
    assert "item_id" in norm
    assert norm["source"] == "test"
    assert norm["title"] == "Test"
    assert norm["topic_tags"] == []
    assert norm["style_tags"] == []


def test_load_fixture_items_from_path_invalid():
    with pytest.raises(FileNotFoundError):
        load_fixture_items_from_path(Path("/nonexistent/path.json"))


def test_load_rss_fixture_items():
    items = load_rss_fixture_items("e2e")
    assert isinstance(items, list)
    assert len(items) >= 5
    for item in items:
        assert "item_id" in item
        assert "source" in item
        assert "title" in item