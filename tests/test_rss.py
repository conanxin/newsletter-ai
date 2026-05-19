"""Tests for RSS fixture parser (v0.3.8)."""

from pathlib import Path

import pytest

from newsletter_ai.rss import parse_rss_xml, parse_rss_file
from newsletter_ai.normalize import normalize_items


RSS_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "e2e_rss_sample.xml"


def test_parse_rss_xml():
    xml_text = RSS_FIXTURE_PATH.read_text(encoding="utf-8")
    items = parse_rss_xml(xml_text)
    assert len(items) >= 5
    assert any("OpenAI" in item["title"] for item in items)


def test_parse_rss_file():
    items = parse_rss_file(RSS_FIXTURE_PATH)
    assert len(items) >= 5
    assert all("title" in item and "link" in item for item in items)


def test_rss_missing_description():
    """Ensure missing description does not crash."""
    xml = """<?xml version="1.0"?>
    <rss><channel>
      <item><title>Test</title><link>https://example.com</link></item>
    </channel></rss>"""
    items = parse_rss_xml(xml)
    assert len(items) == 1
    assert items[0]["description"] == ""


def test_rss_normalization():
    raw_items = parse_rss_file(RSS_FIXTURE_PATH)
    normalized = normalize_items(raw_items)
    assert len(normalized) >= 5
    for item in normalized:
        assert "item_id" in item
        assert "topic_tags" in item
        assert "style_tags" in item


def test_rss_duplicate_item():
    """Near-duplicate items should still be parsed."""
    items = parse_rss_file(RSS_FIXTURE_PATH)
    titles = [i["title"] for i in items]
    assert titles.count("OpenAI Releases New Reasoning Model") >= 1  # duplicate exists in fixture