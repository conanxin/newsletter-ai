"""E2E regression using real replay fixture (v0.3.17).

Uses the captured HN frontpage replay fixture without network.
No assertions on specific titles (time-sensitive content).
"""

import json
from pathlib import Path

import pytest

from newsletter_ai.replay import validate_replay_pair, list_replay_fixtures
from newsletter_ai.sources import load_source_registry, ingest_sources_with_report
from newsletter_ai.pipeline import run_daily_pipeline
from newsletter_ai.feedback import apply_feedback


REPLAY_DIR = Path(__file__).parent.parent / "data" / "fixtures" / "replay"
REPLAY_XML = REPLAY_DIR / "rss_hnrss-frontpage-smoke_20260519_111736.xml"
REPLAY_META = REPLAY_DIR / "rss_hnrss-frontpage-smoke_20260519_111736.json"
REPLAY_REGISTRY = Path(__file__).parent.parent / "data" / "fixtures" / "replay_source_registry.json"


class TestReplayFixtureValidate:
    """1. replay fixture validate"""

    def test_replay_pair_exists(self):
        assert REPLAY_XML.exists(), f"Replay XML missing: {REPLAY_XML}"
        assert REPLAY_META.exists(), f"Replay metadata missing: {REPLAY_META}"

    def test_replay_pair_valid(self):
        result = validate_replay_pair(REPLAY_XML, REPLAY_META)
        assert result["valid"], f"Validation failed: {result['errors']}"
        assert result["metadata"]["item_count"] > 0

    def test_replay_list_includes_fixture(self):
        fixtures = list_replay_fixtures(REPLAY_DIR)
        ids = [f["source_id"] for f in fixtures]
        assert "hnrss-frontpage-smoke" in ids

    def test_sha256_match(self):
        result = validate_replay_pair(REPLAY_XML, REPLAY_META)
        assert "sha256_mismatch" not in result["errors"]

    def test_item_count_positive(self):
        meta = json.loads(REPLAY_META.read_text(encoding="utf-8"))
        assert meta["item_count"] > 0


class TestReplayRegistryIngestion:
    """2. replay registry ingestion (offline)"""

    def test_registry_loads(self):
        sources = load_source_registry(REPLAY_REGISTRY)
        assert len(sources) == 1
        assert sources[0]["source_id"] == "hnrss-frontpage-replay"
        assert sources[0]["type"] == "rss_replay"

    def test_registry_ingest_offline(self):
        sources = load_source_registry(REPLAY_REGISTRY)
        result = ingest_sources_with_report(sources, allow_network=False)
        items = result["items"]
        report = result["report"]
        assert len(items) > 0, "Expected items from replay fixture"
        assert report["source_count_success"] == 1
        assert report["source_count_failed"] == 0

    def test_ingested_items_have_required_fields(self):
        sources = load_source_registry(REPLAY_REGISTRY)
        result = ingest_sources_with_report(sources, allow_network=False)
        for item in result["items"]:
            assert "source" in item
            assert "title" in item
            assert "url" in item
            assert "item_id" in item


class TestDailyPipelineWithReplayRegistry:
    """3. daily pipeline with replay registry (dry-run, offline)"""

    def test_daily_dry_run_replay_registry(self):
        status = run_daily_pipeline(
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        assert status["status"] == "success"
        assert status["input_mode"] == "source_registry"
        assert status["item_count"] > 0

    def test_snapshot_generated(self, tmp_path):
        from newsletter_ai.config import load_config
        cfg = load_config()
        # Point output to tmp_path to avoid polluting real output
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "snapshots" / "latest_items.json"
        assert latest.exists(), "latest_items.json should be generated"
        data = json.loads(latest.read_text(encoding="utf-8"))
        assert len(data) > 0

    def test_sectioned_digest_generated(self, tmp_path):
        from newsletter_ai.config import load_config
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        digest_step = [s for s in status["steps"] if s["name"] == "digest"][0]
        assert digest_step["status"] == "success"
        assert digest_step["section_count"] >= 1


class TestFeedbackRegression:
    """4. feedback regression on replay items"""

    def test_feedback_like_parses_replay_item(self, tmp_path):
        from newsletter_ai.config import load_config
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        result = apply_feedback("like 1", cfg, dry_run=True)
        assert "like" in result.lower() or "applied" in result.lower()

    def test_feedback_save_with_note(self, tmp_path):
        from newsletter_ai.config import load_config
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        result = apply_feedback("save 1", cfg, dry_run=True, note="值得深挖")
        assert "save" in result.lower() or "applied" in result.lower()


class TestQualityRegression:
    """5. quality regression"""

    def test_quality_report_structure(self, tmp_path):
        from newsletter_ai.config import load_config
        from newsletter_ai.quality import generate_quality_report, save_quality_report
        cfg = load_config()
        cfg["OUTPUT_DIR"] = tmp_path
        run_daily_pipeline(
            cfg=cfg,
            dry_run=True,
            source_registry=REPLAY_REGISTRY,
            allow_network=False,
        )
        latest = tmp_path / "snapshots" / "latest_items.json"
        items = json.loads(latest.read_text(encoding="utf-8"))
        report = generate_quality_report("test-run", [], items, duplicate_count=0, malformed_count=0, empty_count=0)
        save_quality_report(report, tmp_path)
        quality_json = tmp_path / "quality" / "latest_quality.json"
        assert quality_json.exists()
        data = json.loads(quality_json.read_text(encoding="utf-8"))
        assert "items_raw" in data
