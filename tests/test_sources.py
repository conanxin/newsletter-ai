"""Tests for source registry and offline ingestion (v0.3.9)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.sources import (
    load_source_registry,
    validate_source,
    validate_source_registry,
    enabled_sources,
    ingest_offline_sources,
)


def test_load_source_registry(tmp_path):
    registry = [
        {"source_id": "test", "name": "Test", "type": "rss_fixture", "enabled": True, "fixture_path": "tests/fixtures/e2e_rss_sample.xml"}
    ]
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    loaded = load_source_registry(path)
    assert len(loaded) == 1
    assert loaded[0]["source_id"] == "test"


def test_validate_source():
    good = {"source_id": "a", "name": "A", "type": "rss_fixture", "enabled": True, "fixture_path": "x.xml"}
    assert validate_source(good) == []

    bad = {"name": "A"}
    errs = validate_source(bad)
    assert any("missing_field" in e for e in errs)


def test_validate_source_registry():
    sources = [
        {"source_id": "a", "name": "A", "type": "rss_fixture", "enabled": True, "fixture_path": "x.xml"},
        {"name": "B"},
    ]
    result = validate_source_registry(sources)
    assert not result["valid"]
    assert len(result["errors"]) > 0


def test_enabled_sources():
    sources = [
        {"source_id": "a", "enabled": True},
        {"source_id": "b", "enabled": False},
        {"source_id": "c"},
    ]
    enabled = enabled_sources(sources)
    assert len(enabled) == 2
    assert enabled[0]["source_id"] == "a"


def test_ingest_offline_sources():
    base_dir = Path(__file__).parent.parent
    sources = [
        {
            "source_id": "sample-ai-feed",
            "name": "Sample AI Feed",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
            "topic_hints": ["ai"],
            "style_hints": ["analysis"],
        }
    ]
    items = ingest_offline_sources(sources, base_dir=base_dir)
    assert len(items) > 0
    for item in items:
        assert "item_id" in item
        assert "source" in item
        assert "topic_tags" in item


def test_ingest_disabled_source_skipped():
    sources = [
        {"source_id": "a", "type": "rss_fixture", "enabled": False, "fixture_path": "tests/fixtures/e2e_rss_sample.xml"}
    ]
    base_dir = Path(__file__).parent.parent
    items = ingest_offline_sources(sources, base_dir=base_dir)
    assert len(items) == 0


def test_ingest_invalid_fixture_path():
    sources = [
        {"source_id": "a", "type": "rss_fixture", "enabled": True, "fixture_path": "nonexistent.xml"}
    ]
    base_dir = Path(__file__).parent.parent
    items = ingest_offline_sources(sources, base_dir=base_dir)
    assert len(items) == 0
