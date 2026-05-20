"""Tests for pipeline source registry mode (v0.3.10)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.pipeline import run_daily_pipeline
from newsletter_ai.sources import load_source_registry, enabled_sources, ingest_offline_sources


def test_pipeline_default_fixture_mode(tmp_path):
    """Default dry-run should still use fixture JSON."""
    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True)
    assert result["status"] == "success"
    assert result["input_mode"] == "fixture_json"
    assert result["item_count"] == 5  # dry_run_items.json has 5 items


def test_pipeline_source_registry_mode(tmp_path):
    """Pipeline with source_registry should ingest from enabled rss_fixture sources."""
    base_dir = Path(__file__).parent.parent
    registry_path = base_dir / "data" / "fixtures" / "source_registry.json"

    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True, source_registry=registry_path)
    assert result["status"] == "success"
    assert result["input_mode"] == "source_registry"
    assert result["source_count"] == 2  # 2 enabled sources in registry
    assert result["item_count"] == 14  # 7 items x 2 sources from same fixture


def test_pipeline_source_registry_disabled_skipped(tmp_path):
    """Disabled sources should not contribute items."""
    base_dir = Path(__file__).parent.parent
    registry_path = base_dir / "data" / "fixtures" / "source_registry.json"

    registry = load_source_registry(registry_path)
    enabled = enabled_sources(registry)
    assert len(enabled) == 2  # 3 total, 1 disabled

    items = ingest_offline_sources(enabled, base_dir=base_dir)
    assert len(items) == 14


def test_pipeline_registry_snapshot_has_source_metadata(tmp_path):
    """Snapshot items should include source_id from registry."""
    base_dir = Path(__file__).parent.parent
    registry_path = base_dir / "data" / "fixtures" / "source_registry.json"

    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    run_daily_pipeline(cfg=cfg, dry_run=True, source_registry=registry_path)

    latest = tmp_path / "snapshots" / "latest_items.json"
    assert latest.exists()
    items = json.loads(latest.read_text(encoding="utf-8"))
    assert len(items) > 0
    # Items should have source metadata from registry
    for item in items:
        assert "item_id" in item
        assert "source" in item


def test_pipeline_invalid_registry_path(tmp_path):
    """Invalid registry path should produce error gracefully."""
    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True, source_registry=tmp_path / "nonexistent.json")
    assert result["status"] == "success"  # Falls back to fixture mode
    assert result["input_mode"] == "fixture_json"
