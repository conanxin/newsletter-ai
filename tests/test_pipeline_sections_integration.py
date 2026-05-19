"""Integration test: sectioning + pipeline dry-run (v0.3.3)."""

from src.newsletter_ai.sections import group_items_into_sections
from src.newsletter_ai.render import render_markdown_digest


def test_daily_dry_run_generates_sectioned_digest():
    items = [
        {"global_index": 1, "title": "AI Breakthrough", "topic_tags": ["ai"], "source": "tech"},
        {"global_index": 2, "title": "Culture Essay", "topic_tags": ["culture"], "source": "medium"},
        {"global_index": 3, "title": "Another AI Paper", "topic_tags": ["ai"], "source": "arxiv"},
    ]

    sections = group_items_into_sections(items)
    md = render_markdown_digest(sections)

    # Should have section headings
    assert "## ai" in md.lower() or "## AI" in md
    # Should use global indices
    assert "1. AI Breakthrough" in md
    assert "3. Another AI Paper" in md


def test_sectioning_preserves_global_item_index():
    items = [
        {"id": "1", "title": "AI Breakthrough", "topic_tags": ["ai"], "global_index": 1},
        {"id": "2", "title": "Culture Essay", "topic_tags": ["culture"], "global_index": 2},
        {"id": "3", "title": "Another AI Story", "topic_tags": ["ai"], "global_index": 3},
    ]

    sections = group_items_into_sections(items)
    all_indices = [item.get("global_index") for sec in sections for item in sec.items]

    assert set(all_indices) == {1, 2, 3}
    assert len(all_indices) == 3
    assert len(sections) == 2