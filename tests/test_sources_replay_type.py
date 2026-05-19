"""Tests for rss_replay source type (v0.3.14)."""

import json
from pathlib import Path

from newsletter_ai.sources import (
    ingest_sources_with_report,
    validate_source,
    validate_source_registry,
)


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Replay Channel</title>
  <item>
    <title>Replay Item</title>
    <link>https://example.com/r</link>
    <description>Replay desc</description>
  </item>
</channel>
</rss>
"""


def _make_registry(fixture_path: str):
    return [
        {
            "source_id": "replay-sample",
            "name": "Replay Sample",
            "type": "rss_replay",
            "enabled": True,
            "fixture_path": fixture_path,
            "topic_hints": ["ai"],
            "style_hints": ["analysis"],
        }
    ]


class TestValidateReplaySource:
    def test_valid_replay_source(self):
        source = {
            "source_id": "r1",
            "name": "R1",
            "type": "rss_replay",
            "enabled": True,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
        }
        errors = validate_source(source)
        assert errors == []

    def test_missing_fixture_path(self):
        source = {
            "source_id": "r1",
            "name": "R1",
            "type": "rss_replay",
            "enabled": True,
        }
        errors = validate_source(source)
        assert any("missing_fixture_path" in e for e in errors)

    def test_registry_validation_accepts_replay(self, tmp_path):
        registry = tmp_path / "registry.json"
        registry.write_text(json.dumps(_make_registry("tests/fixtures/e2e_rss_sample.xml")), encoding="utf-8")
        sources = json.loads(registry.read_text(encoding="utf-8"))
        result = validate_source_registry(sources)
        assert result["valid"] is True


class TestIngestReplaySource:
    def test_replay_source_ingests_offline(self, tmp_path):
        fixture = tmp_path / "replay.xml"
        fixture.write_text(SAMPLE_RSS, encoding="utf-8")

        sources = _make_registry(str(fixture))
        result = ingest_sources_with_report(sources, base_dir=tmp_path, allow_network=False)
        items = result["items"]
        report = result["report"]

        assert len(items) >= 1
        assert report["source_count_success"] == 1
        assert report["sources"][0]["status"] == "success"
        assert report["sources"][0]["type"] == "rss_replay"

    def test_replay_source_missing_fixture_fails(self, tmp_path):
        sources = _make_registry("nonexistent.xml")
        result = ingest_sources_with_report(sources, base_dir=tmp_path, allow_network=False)
        report = result["report"]

        assert report["source_count_failed"] == 1
        assert report["sources"][0]["status"] == "failed"
        assert any("fixture_not_found" in e for e in report["sources"][0]["errors"])

    def test_replay_items_are_normalized(self, tmp_path):
        fixture = tmp_path / "replay.xml"
        fixture.write_text(SAMPLE_RSS, encoding="utf-8")

        sources = _make_registry(str(fixture))
        result = ingest_sources_with_report(sources, base_dir=tmp_path, allow_network=False)
        items = result["items"]

        assert len(items) >= 1
        # Normalized items should have stable item_id
        assert "item_id" in items[0]
        assert items[0].get("source") == "Replay Channel"


class TestMixedSourceTypes:
    def test_fixture_replay_url_mixed_registry(self, tmp_path):
        fixture = tmp_path / "replay.xml"
        fixture.write_text(SAMPLE_RSS, encoding="utf-8")

        sources = [
            {
                "source_id": "f1",
                "name": "Fixture",
                "type": "rss_fixture",
                "enabled": True,
                "fixture_path": str(fixture),
            },
            {
                "source_id": "r1",
                "name": "Replay",
                "type": "rss_replay",
                "enabled": True,
                "fixture_path": str(fixture),
            },
            {
                "source_id": "u1",
                "name": "URL",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
            },
        ]

        result = ingest_sources_with_report(sources, base_dir=tmp_path, allow_network=False)
        report = result["report"]

        assert report["source_count_total"] == 3
        assert report["source_count_success"] == 2  # fixture + replay
        assert report["source_count_skipped_network"] == 1  # url skipped
        statuses = {s["source_id"]: s["status"] for s in report["sources"]}
        assert statuses["f1"] == "success"
        assert statuses["r1"] == "success"
        assert statuses["u1"] == "skipped"
