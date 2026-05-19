"""Tests for replay sanitization (v0.3.15)."""

from newsletter_ai.replay import sanitize_replay_xml
from newsletter_ai.rss import parse_rss_xml


RSS_WITH_TRACKING = """<?xml version="1.0"?>
<rss><channel><title>Tracked Feed</title>
<item>
  <title>Item A</title>
  <link>https://example.com/article?utm_source=newsletter&amp;utm_medium=email&amp;ref=keep</link>
  <description>Desc A</description>
</item>
<item>
  <title>Item B</title>
  <link>https://example.com/other?fbclid=abc123&amp;gclid=xyz&amp;page=2</link>
  <description>Desc B</description>
</item>
<item>
  <title>Item C</title>
  <link>https://example.com/clean?ref=keep&amp;page=3</link>
  <description>Desc C</description>
</item>
</channel></rss>
"""


def test_sanitize_strips_utm_params():
    result = sanitize_replay_xml(RSS_WITH_TRACKING)
    assert "utm_source" not in result
    assert "utm_medium" not in result
    assert "ref=keep" in result


def test_sanitize_strips_fbclid_and_gclid():
    result = sanitize_replay_xml(RSS_WITH_TRACKING)
    assert "fbclid" not in result
    assert "gclid" not in result
    assert "page=2" in result


def test_sanitize_preserves_non_tracking_params():
    result = sanitize_replay_xml(RSS_WITH_TRACKING)
    assert "ref=keep" in result
    assert "page=2" in result
    assert "page=3" in result


def test_sanitize_keeps_xml_structure():
    result = sanitize_replay_xml(RSS_WITH_TRACKING)
    assert "<title>Tracked Feed</title>" in result
    assert "<title>Item A</title>" in result
    assert "<title>Item B</title>" in result
    assert "<title>Item C</title>" in result


def test_sanitize_result_is_parseable():
    result = sanitize_replay_xml(RSS_WITH_TRACKING)
    items = parse_rss_xml(result)
    assert len(items) == 3
    assert items[0]["title"] == "Item A"
    assert items[1]["title"] == "Item B"
    assert items[2]["title"] == "Item C"


def test_sanitize_no_op_on_clean_xml():
    clean = """<?xml version="1.0"?>
<rss><channel><title>Clean</title>
<item><title>X</title><link>https://example.com/x?ref=1</link></item>
</channel></rss>
"""
    result = sanitize_replay_xml(clean)
    assert result == clean


def test_sanitize_strips_mc_params():
    xml = """<?xml version="1.0"?>
<rss><channel><title>Mailchimp</title>
<item><title>X</title><link>https://example.com/x?mc_cid=123&amp;mc_eid=456&amp;keep=1</link></item>
</channel></rss>
"""
    result = sanitize_replay_xml(xml)
    assert "mc_cid" not in result
    assert "mc_eid" not in result
    assert "keep=1" in result
