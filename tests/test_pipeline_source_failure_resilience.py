"""Tests for pipeline source failure resilience (v0.3.11)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.pipeline import run_daily_pipeline


def test_pipeline_mixed_registry_continues(tmp_path):
    """Daily pipeline with mixed success/failure registry should continue."""
    base_dir = Path(__file__).parent.parent
    registry_path = base_dir / "data" / "fixtures" / "source_registry.json"

    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True, source_registry=registry_path)
    assert result["status"] == "success"
    assert result["input_mode"] == "source_registry"
    assert result["item_count"] > 0

    # Check ingestion report in last-run-status
    status_file = tmp_path / "state" / "last-run-status.json"
    assert status_file.exists()
    status = json.loads(status_file.read_text())
    assert "ingestion_report" in status
    assert status["ingestion_report"]["source_count_success"] > 0


def test_pipeline_all_failed_registry(tmp_path):
    """All-failed registry should produce failed pipeline with clear error."""
    # Create a registry with all bad fixtures
    bad_registry = tmp_path / "bad_registry.json"
    bad_registry.write_text(json.dumps([
        {
            "source_id": "bad1",
            "name": "Bad 1",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        },
        {
            "source_id": "bad2",
            "name": "Bad 2",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        },
    ]), encoding="utf-8")

    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True, source_registry=bad_registry)
    assert result["status"] == "failed"
    assert result["failed_step"] == "rank"
    assert "All enabled sources failed" in str(result)


def test_pipeline_default_fixture_no_regression(tmp_path):
    """Default dry-run should still work without registry."""
    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }
    result = run_daily_pipeline(cfg=cfg, dry_run=True)
    assert result["status"] == "success"
    assert result["input_mode"] == "fixture_json"
    assert result["item_count"] == 5
