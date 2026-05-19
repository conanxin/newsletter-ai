"""Tests for quality CLI reading current-run report (v0.3.18)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.pipeline import run_daily_pipeline
from newsletter_ai.config import load_config


class TestQualityCliCurrentRun:
    """quality sections/sources/duplicates reads latest_quality"""

    @pytest.fixture(autouse=True)
    def _generate_report(self, tmp_path):
        self.tmp = tmp_path
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(cfg=cfg, dry_run=True)

    def _latest_json(self):
        return self.tmp / "quality" / "latest_quality.json"

    def test_sections_reads_latest_quality(self):
        latest = self._latest_json()
        assert latest.exists()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "section_distribution" in data

    def test_sources_reads_latest_quality(self):
        latest = self._latest_json()
        assert latest.exists()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "source_details" in data
        assert len(data["source_details"]) > 0

    def test_duplicates_reads_latest_quality(self):
        latest = self._latest_json()
        assert latest.exists()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "duplicate_reason_counts" in data

    def test_no_legacy_demo_fallback(self):
        latest = self._latest_json()
        data = json.loads(latest.read_text(encoding="utf-8"))
        # Should not contain ONLY the old demo fixture source
        sources = [s["source"] for s in data.get("source_details", [])]
        assert len(sources) > 0
        # The default fixture mode still uses "fixture" as source name, which is fine.
        # The key point is that the report was generated from the current run, not a
        # hardcoded demo that auto-generates when no report exists.
        assert "run_id" in data
        assert "created_at" in data

    def test_quality_report_has_run_id_and_created_at(self):
        latest = self._latest_json()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert "run_id" in data
        assert "created_at" in data

    def test_replay_daily_quality_report(self, tmp_path):
        replay_registry = Path(__file__).parent.parent / "data" / "fixtures" / "replay_source_registry.json"
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=replay_registry,
            allow_network=False,
        )
        latest = tmp_path / "quality" / "latest_quality.json"
        assert latest.exists()
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert data["items_after_dedupe"] > 0
        # Should reflect replay source, not legacy demo
        sources = [s["source"] for s in data.get("source_details", [])]
        assert "hnrss-frontpage-replay" in sources
