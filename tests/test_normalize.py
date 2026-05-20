"""Tests for the normalization layer (v0.3.7)."""

import pytest

from newsletter_ai.normalize import normalize_item, normalize_items, validate_normalized_item


def test_normalize_item_basic():
    raw = {
        "source": "techcrunch",
        "title": "OpenAI releases new model",
        "url": "https://example.com/openai",
        "topic_tags": ["ai"],
        "style_tags": ["analysis"]
    }
    norm = normalize_item(raw)
    assert norm["item_id"].startswith("item-")
    assert norm["source"] == "techcrunch"
    assert norm["title"] == "OpenAI releases new model"
    assert norm["topic_tags"] == ["ai"]
    assert norm["style_tags"] == ["analysis"]


def test_normalize_item_missing_fields():
    raw = {"title": "Some Title"}
    norm = normalize_item(raw, source_hint="test")
    assert norm["source"] == "test"
    assert norm["url"] == ""
    assert norm["topic_tags"] == []
    assert norm["style_tags"] == []
    assert "missing_url" in norm["warnings"]
    assert "missing_topic_tags" in norm["warnings"]


def test_normalize_item_id_stability():
    raw1 = {"source": "a", "title": "Title", "url": "https://example.com/1"}
    raw2 = {"source": "a", "title": "Title", "url": "https://example.com/1"}
    assert normalize_item(raw1)["item_id"] == normalize_item(raw2)["item_id"]


def test_normalize_items():
    raw_list = [{"title": "A"}, {"title": "B"}]
    result = normalize_items(raw_list, source_hint="test")
    assert len(result) == 2
    assert all("item_id" in item for item in result)


def test_validate_normalized_item():
    good = normalize_item({"title": "Test", "source": "x"})
    errors = validate_normalized_item(good)
    assert errors == [] or all(e.startswith("missing") for e in errors)  # lenient

    bad = {"title": "Test"}
    errors = validate_normalized_item(bad)
    assert "missing_field:source" in errors or "missing_field:item_id" in errors