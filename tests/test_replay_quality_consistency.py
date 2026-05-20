"""Tests for replay quality consistency (v0.3.18)."""

import json
from pathlib import Path

from newsletter_ai.pipeline import run_daily_pipeline
from newsletter_ai.config import load_config


REPLAY_REGISTRY = Path(__file__).parent.parent / "data" / "fixtures" / "replay_source_registry.json"


class TestReplayQualityConsistency:
    """replay daily generates quality report with replay items"""

    def test_replay_daily_generates_quality_report(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        assert status["status"] == "success"
        latest = tmp_path / "quality" / "latest_quality.json"
        assert latest.exists()

    def test_quality_sections_reflects_replay_items(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert data["items_after_dedupe"] > 0
        assert "section_distribution" in data
        # At least one section should exist
        assert len(data["section_distribution"]) >= 1

    def test_quality_sources_reflects_replay_source(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        sources = [s["source"] for s in data.get("source_details", [])]
        assert "hnrss-frontpage-replay" in sources

    def test_quality_duplicates_runs_against_replay_items(self, tmp_path):
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "duplicate_reason_counts" in data
        assert "fuzzy_duplicate_count" in data

    def test_no_specific_hn_title_assertions(self, tmp_path):
        """Do not assert specific HN titles — time-sensitive content."""
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "quality" / "latest_quality.json"
        data = json.loads(latest.read_text(encoding="utf-8"))
        # Just verify structure, not content
        assert "section_distribution" in data
        for sec in data["section_distribution"].values():
            assert "representative_titles" in sec
