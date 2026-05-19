"""Tests for sections.py (v0.3.3 Digest Sectioning)."""

from src.newsletter_ai.sections import (
    assign_section,
    group_items_into_sections,
    Section,
)


def test_assign_section_prefers_topic_tags():
    item = {"topic_tags": ["ai", "llm"], "source": "techcrunch", "style_tags": ["analysis"]}
    sid, label = assign_section(item)
    assert sid == "ai"
    assert label == "ai"


def test_assign_section_fallback_to_source():
    item = {"topic_tags": [], "source": "stratechery", "style_tags": []}
    sid, label = assign_section(item)
    assert sid == "stratechery"
    assert label == "stratechery"


def test_group_items_into_sections_preserves_order():
    items = [
        {"id": "1", "topic_tags": ["ai"], "source": "a"},
        {"id": "2", "topic_tags": ["tech"], "source": "b"},
        {"id": "3", "topic_tags": ["ai"], "source": "c"},
    ]
    sections = group_items_into_sections(items)
    assert len(sections) == 2
    assert sections[0].section_label == "ai"
    assert sections[0].item_count == 2
    assert sections[1].section_label == "tech"
    # Global indices preserved
    assert sections[0].items[0]["id"] == "1"
    assert sections[0].items[1]["id"] == "3"