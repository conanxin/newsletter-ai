"""Tests for replay fixture capture (v0.3.14)."""

import hashlib
import json
from pathlib import Path

from newsletter_ai.replay import (
    build_replay_metadata,
    load_rss_replay_fixture,
    sanitize_replay_xml,
    save_rss_replay_fixture,
)
from newsletter_ai.rss import parse_rss_xml


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


class TestSanitizeReplayXml:
    def test_no_op_on_clean_xml(self):
        result, count = sanitize_replay_xml(SAMPLE_RSS)
        assert result == SAMPLE_RSS
        assert count == 0


class TestBuildReplayMetadata:
    def test_metadata_fields(self):
        source = {
            "source_id": "test-source",
            "name": "Test Source",
            "url": "https://example.com/feed.xml",
        }

        class FakeResult:
            ok = True
            status_code = 200
            text = SAMPLE_RSS
            fetched_at = "2026-05-19T10:00:00Z"

        fetch_result = FakeResult()
        meta = build_replay_metadata(source, fetch_result, item_count=2)

        assert meta["source_id"] == "test-source"
        assert meta["url"] == "https://example.com/feed.xml"
        assert meta["status_code"] == 200
        assert meta["item_count"] == 2
        assert meta["generated_by"].startswith("newsletter-ai/replay")
        assert meta["sha256"] == hashlib.sha256(SAMPLE_RSS.encode("utf-8")).hexdigest()
        assert "fetched_at" in meta

    def test_no_sensitive_headers(self):
        source = {"source_id": "s", "name": "S", "url": "https://x.com"}

        class FakeResult:
            ok = True
            status_code = 200
            text = ""
            fetched_at = "2026-05-19T10:00:00Z"

        meta = build_replay_metadata(source, FakeResult(), item_count=0)
        keys = set(meta.keys())
        assert "auth" not in keys
        assert "cookie" not in keys
        assert "token" not in keys
        assert "header" not in keys


class TestSaveRssReplayFixture:
    def test_writes_xml_and_json(self, tmp_path):
        meta = {"source_id": "abc", "item_count": 2}
        xml_path = save_rss_replay_fixture(
            source_id="abc",
            xml_text=SAMPLE_RSS,
            output_dir=tmp_path,
            metadata=meta,
        )
        assert xml_path.exists()
        assert xml_path.suffix == ".xml"

        meta_path = xml_path.with_suffix(".json")
        assert meta_path.exists()

        saved_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert saved_meta["source_id"] == "abc"

    def test_saved_xml_is_parseable(self, tmp_path):
        xml_path = save_rss_replay_fixture(
            source_id="abc",
            xml_text=SAMPLE_RSS,
            output_dir=tmp_path,
            metadata={},
        )
        items = parse_rss_xml(xml_path.read_text(encoding="utf-8"))
        assert len(items) == 2
        assert items[0]["title"] == "Item One"


class TestLoadRssReplayFixture:
    def test_loads_xml(self, tmp_path):
        xml_path = save_rss_replay_fixture(
            source_id="abc",
            xml_text=SAMPLE_RSS,
            output_dir=tmp_path,
            metadata={},
        )
        text = load_rss_replay_fixture(xml_path)
        assert "<title>Test Channel</title>" in text

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.xml"
        try:
            load_rss_replay_fixture(missing)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass
