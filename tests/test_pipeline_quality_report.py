"""Tests for pipeline quality report generation (v0.3.18)."""

import json
from pathlib import Path

from newsletter_ai.pipeline import run_daily_pipeline
from newsletter_ai.config import load_config


class TestPipelineQualityReport:
    """daily dry-run writes output/quality/latest_quality.json"""

    def test_daily_generates_quality_report(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(cfg=cfg, dry_run=True)
        assert status["status"] == "success"
        latest = tmp_path / "quality" / "latest_quality.json"
        assert latest.exists(), "latest_quality.json should be generated"

    def test_quality_report_item_count_matches_snapshot(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(cfg=cfg, dry_run=True)
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        snapshot = tmp_path / "snapshots" / "latest_items.json"
        items = json.loads(snapshot.read_text(encoding="utf-8"))
        assert data["items_after_dedupe"] == len(items)

    def test_quality_report_has_section_distribution(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(cfg=cfg, dry_run=True)
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "section_distribution" in data

    def test_quality_report_has_source_details(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(cfg=cfg, dry_run=True)
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "source_details" in data
        assert len(data["source_details"]) > 0

    def test_last_run_status_records_quality_report_path(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(cfg=cfg, dry_run=True)
        status_file = tmp_path / "state" / "last-run-status.json"
        data = json.loads(status_file.read_text(encoding="utf-8"))
        assert "quality_report_path" in data
        assert Path(data["quality_report_path"]).exists()

    def test_replay_registry_daily_generates_quality_report(self, tmp_path):
        replay_registry = Path(__file__).parent.parent / "data" / "fixtures" / "replay_source_registry.json"
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=replay_registry,
            allow_network=False,
        )
        assert status["status"] == "success"
        latest = tmp_path / "quality" / "latest_quality.json"
        assert latest.exists()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert data["items_after_dedupe"] > 0
