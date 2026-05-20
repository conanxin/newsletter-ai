"""Tests for replay governance: validate/list/promote (v0.3.15)."""

import hashlib
import json
from pathlib import Path

from newsletter_ai.replay import (
    list_replay_fixtures,
    save_rss_replay_fixture,
    validate_replay_pair,
)


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Test Channel</title>
  <item>
    <title>Item One</title>
    <link>https://example.com/1</link>
    <description>First item</description>
  </item>
  <item>
    <title>Item Two</title>
    <link>https://example.com/2</link>
    <description>Second item</description>
  </item>
</channel>
</rss>
"""


def _make_meta(source_id: str, item_count: int, sha256: str):
    return {
        "source_id": source_id,
        "sha256": sha256,
        "item_count": item_count,
        "generated_by": "newsletter-ai/replay v0.3.15",
        "fetched_at": "2026-05-19T10:00:00Z",
    }


class TestValidateReplayPair:
    def test_valid_pair(self, tmp_path):
        sha = hashlib.sha256(SAMPLE_RSS.encode("utf-8")).hexdigest()
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        meta_path = tmp_path / "rss_test_20260519_100000.json"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
        meta_path.write_text(json.dumps(_make_meta("test", 2, sha)), encoding="utf-8")

        result = validate_replay_pair(xml_path, meta_path)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_sha256_mismatch(self, tmp_path):
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        meta_path = tmp_path / "rss_test_20260519_100000.json"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
        meta_path.write_text(json.dumps(_make_meta("test", 2, "badsha256")), encoding="utf-8")

        result = validate_replay_pair(xml_path, meta_path)
        assert result["valid"] is False
        assert any("sha256_mismatch" in e for e in result["errors"])

    def test_item_count_mismatch(self, tmp_path):
        sha = hashlib.sha256(SAMPLE_RSS.encode("utf-8")).hexdigest()
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        meta_path = tmp_path / "rss_test_20260519_100000.json"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
        meta_path.write_text(json.dumps(_make_meta("test", 99, sha)), encoding="utf-8")

        result = validate_replay_pair(xml_path, meta_path)
        assert result["valid"] is False
        assert any("item_count_mismatch" in e for e in result["errors"])

    def test_missing_metadata(self, tmp_path):
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
        meta_path = tmp_path / "rss_test_20260519_100000.json"

        result = validate_replay_pair(xml_path, meta_path)
        assert result["valid"] is False
        assert any("metadata_not_found" in e for e in result["errors"])


class TestListReplayFixtures:
    def test_lists_valid_fixture(self, tmp_path):
        sha = hashlib.sha256(SAMPLE_RSS.encode("utf-8")).hexdigest()
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        meta_path = tmp_path / "rss_test_20260519_100000.json"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
        meta_path.write_text(json.dumps(_make_meta("test", 2, sha)), encoding="utf-8")

        results = list_replay_fixtures(tmp_path)
        assert len(results) == 1
        assert results[0]["source_id"] == "test"
        assert results[0]["status"] == "valid"
        assert results[0]["item_count"] == 2

    def test_missing_metadata_flagged(self, tmp_path):
        xml_path = tmp_path / "rss_test_20260519_100000.xml"
        xml_path.write_text(SAMPLE_RSS, encoding="utf-8")

        results = list_replay_fixtures(tmp_path)
        assert len(results) == 1
        assert results[0]["status"] == "missing_metadata"
        assert any("metadata_json_missing" in e for e in results[0]["errors"])

    def test_empty_directory(self, tmp_path):
        results = list_replay_fixtures(tmp_path)
        assert results == []


class TestSaveReplayFixture:
    def test_save_writes_sanitized_xml_and_meta(self, tmp_path):
        xml_path = save_rss_replay_fixture(
            source_id="demo",
            xml_text=SAMPLE_RSS,
            output_dir=tmp_path,
            metadata={"item_count": 2},
        )
        assert xml_path.exists()
        meta_path = xml_path.with_suffix(".json")
        assert meta_path.exists()

        saved_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert saved_meta["item_count"] == 2
