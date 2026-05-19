"""Tests for sectioned rendering (v0.3.3)."""

from src.newsletter_ai.sections import group_items_into_sections
from src.newsletter_ai.render import render_markdown_digest, render_telegram_digest


def test_markdown_has_section_headings():
    items = [
        {"global_index": 1, "title": "AI News", "topic_tags": ["ai"], "source": "a"},
        {"global_index": 2, "title": "Culture Piece", "topic_tags": ["culture"], "source": "b"},
    ]
    sections = group_items_into_sections(items)
    md = render_markdown_digest(sections)

    assert "## ai" in md.lower() or "## AI" in md
    assert "## culture" in md.lower() or "## Culture" in md
    assert "1. AI News" in md


def test_telegram_has_section_headings():
    items = [
        {"global_index": 1, "title": "AI News", "topic_tags": ["ai"], "source": "a"},
    ]
    sections = group_items_into_sections(items)
    tg = render_telegram_digest(sections)

    assert "【ai】" in tg.lower() or "【AI】" in tg
    assert "1. AI News" in tg


def test_section_rendering_keeps_global_index():
    items = [
        {"global_index": 1, "title": "AI News", "topic_tags": ["ai"]},
        {"global_index": 2, "title": "Tech Deep Dive", "topic_tags": ["tech"]},
        {"global_index": 3, "title": "Another AI Paper", "topic_tags": ["ai"]},
    ]
    sections = group_items_into_sections(items)

    all_indices = [item["global_index"] for sec in sections for item in sec.items]
    assert set(all_indices) == {1, 2, 3}
    assert len(all_indices) == 3