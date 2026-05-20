"""Tests for pipeline run index integration (v0.3.19)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.config import load_config
from newsletter_ai.pipeline import run_daily_pipeline


def test_daily_dry_run_writes_run_index(tmp_path, monkeypatch):
    """Default daily dry-run writes output/runs/index.json and run record."""
    out = tmp_path / "output"
    data = tmp_path / "data"
    (data / "fixtures").mkdir(parents=True)
    (data / "fixtures" / "dry_run_items.json").write_text(
        json.dumps([
            {"id": "1", "source": "techcrunch", "title": "AI Breakthrough", "base_score": 0.65, "topic_tags": ["ai"], "style_tags": ["analysis"]},
            {"id": "2", "source": "stratechery", "title": "Deep Tech Analysis", "base_score": 0.72, "topic_tags": ["tech"], "style_tags": ["essay"]},
        ]),
        encoding="utf-8",
    )

    cfg = {
        "OUTPUT_DIR": out,
        "DATA_DIR": data,
        "BASE_DIR": tmp_path,
    }

    status = run_daily_pipeline(cfg=cfg, dry_run=True)
    assert status["status"] == "success"
    assert "run_record_path" in status

    index_path = out / "runs" / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    assert len(index["runs"]) >= 1

    record_path = Path(status["run_record_path"])
    assert record_path.exists()
    record = json.loads(record_path.read_text())
    assert record["input_mode"] == "fixture_json"
    # item_count reflects actual ranked items (fixture has 2 items, normalize may expand)
    assert record["item_count"] >= 2
    assert record["quality_report_path"] is not None


def test_replay_registry_daily_writes_run_index(tmp_path, monkeypatch):
    """Replay registry daily also writes run index with correct paths."""
    out = tmp_path / "output"
    data = tmp_path / "data"
    fixtures = data / "fixtures"
    fixtures.mkdir(parents=True)

    # Create a minimal replay fixture
    replay_dir = fixtures / "replay"
    replay_dir.mkdir()
    xml_path = replay_dir / "rss_test_20260520_120000.xml"
    xml_path.write_text("""<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Test</title>
<item><title>T1</title><link>http://example.com/1</link></item>
<item><title>T2</title><link>http://example.com/2</link></item>
</channel></rss>""", encoding="utf-8")

    meta = {
        "source_id": "test-replay",
        "url": "http://example.com/feed",
        "fetched_at": "2026-05-20T12:00:00",
        "status_code": 200,
        "item_count": 2,
        "sha256": "abc123",
    }
    xml_path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")

    registry = [
        {
            "source_id": "test-replay",
            "name": "Test Replay",
            "type": "rss_replay",
            "enabled": True,
            "fixture_path": str(xml_path),
        }
    ]
    registry_path = fixtures / "replay_source_registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    cfg = {
        "OUTPUT_DIR": out,
        "DATA_DIR": data,
        "BASE_DIR": tmp_path,
    }

    status = run_daily_pipeline(
        cfg=cfg,
        dry_run=True,
        source_registry=registry_path,
    )
    assert status["status"] == "success"
    assert "run_record_path" in status

    record_path = Path(status["run_record_path"])
    record = json.loads(record_path.read_text())
    assert record["input_mode"] == "source_registry"
    assert record["item_count"] == 2
    assert record["quality_report_path"] is not None
    assert "ingestion_report_summary" in record


def test_last_run_status_has_run_record_path(tmp_path):
    """last-run-status.json contains run_record_path."""
    out = tmp_path / "output"
    data = tmp_path / "data"
    (data / "fixtures").mkdir(parents=True)
    (data / "fixtures" / "dry_run_items.json").write_text(
        json.dumps([
            {"id": "1", "source": "s1", "title": "T1", "base_score": 0.5, "topic_tags": [], "style_tags": []},
        ]),
        encoding="utf-8",
    )

    cfg = {
        "OUTPUT_DIR": out,
        "DATA_DIR": data,
        "BASE_DIR": tmp_path,
    }

    status = run_daily_pipeline(cfg=cfg, dry_run=True)
    assert "run_record_path" in status

    last_run = json.loads((out / "state" / "last-run-status.json").read_text())
    assert "run_record_path" in last_run
    assert last_run["run_record_path"] == status["run_record_path"]


def test_run_record_quality_report_path_matches_latest_quality(tmp_path):
    """Run record quality_report_path points to existing latest_quality.json."""
    out = tmp_path / "output"
    data = tmp_path / "data"
    (data / "fixtures").mkdir(parents=True)
    (data / "fixtures" / "dry_run_items.json").write_text(
        json.dumps([
            {"id": "1", "source": "s1", "title": "T1", "base_score": 0.5, "topic_tags": [], "style_tags": []},
        ]),
        encoding="utf-8",
    )

    cfg = {
        "OUTPUT_DIR": out,
        "DATA_DIR": data,
        "BASE_DIR": tmp_path,
    }

    run_daily_pipeline(cfg=cfg, dry_run=True)
    latest_quality = out / "quality" / "latest_quality.json"
    assert latest_quality.exists()

    index = json.loads((out / "runs" / "index.json").read_text())
    latest_entry = index["runs"][-1]
    qpath = latest_entry.get("quality_report_path")
    assert qpath is not None
    assert (tmp_path / qpath).exists()
