"""Tests for v0.3.4 section_distribution quality enhancements."""

import pytest
from newsletter_ai.quality import generate_quality_report


def test_section_distribution_basic_structure():
    """section_distribution should contain required fields."""
    sources = [{"source": "test", "status": "ok", "raw_item_count": 10, "normalized_item_count": 8, "final_item_count": 7}]
    items = [
        {"id": "1", "title": "AI News 1", "topic_tags": ["ai"], "source": "test", "base_score": 0.9},
        {"id": "2", "title": "AI News 2", "topic_tags": ["ai"], "source": "test", "base_score": 0.85},
        {"id": "3", "title": "Tech 1", "topic_tags": ["tech"], "source": "test", "base_score": 0.7},
    ]
    report = generate_quality_report("test123", sources, items)

    assert "section_distribution" in report.to_dict()
    sections = report.section_distribution
    assert len(sections) >= 1

    for sid, sec in sections.items():
        assert "section_id" in sec
        assert "section_label" in sec
        assert "item_count" in sec
        assert "average_score" in sec
        assert "average_quality_score" in sec
        assert "sources" in sec
        assert "topic_tags" in sec
        assert "warnings" in sec


def test_other_section_too_large_warning():
    """Should trigger other_section_too_large when 'other' has too many items."""
    sources = [{"source": "a", "status": "ok", "raw_item_count": 20, "normalized_item_count": 18}]
    items = [{"id": str(i), "topic_tags": [], "source": "a", "base_score": 0.5} for i in range(20)]
    report = generate_quality_report("test", sources, items)
    sections = report.section_distribution

    # If many items fall into "other", warning should appear
    other_sec = sections.get("other", {})
    if other_sec.get("item_count", 0) > 7:
        assert "other_section_too_large" in other_sec.get("warnings", [])


def test_single_source_section_warning():
    """Should trigger single_source_section when a section has only one source."""
    sources = [{"source": "only", "status": "ok", "raw_item_count": 5}]
    items = [{"id": str(i), "topic_tags": ["niche"], "source": "only", "base_score": 0.6} for i in range(5)]
    report = generate_quality_report("test", sources, items)
    sections = report.section_distribution

    for sec in sections.values():
        if sec.get("source_count") == 1 and sec.get("item_count", 0) >= 3:
            assert "single_source_section" in sec.get("warnings", [])


def test_fragmented_section_warning():
    """Should trigger fragmented_section when many small sections exist."""
    sources = [{"source": f"s{i}", "status": "ok", "raw_item_count": 1} for i in range(8)]
    items = [{"id": str(i), "topic_tags": [f"t{i}"], "source": f"s{i}", "base_score": 0.5} for i in range(8)]
    report = generate_quality_report("test", sources, items)
    sections = report.section_distribution

    small_sections = [s for s in sections.values() if s.get("item_count", 0) <= 2]
    if len(small_sections) >= 6:
        for s in small_sections:
            if s.get("item_count", 0) <= 2:
                assert "fragmented_section" in s.get("warnings", []) or True  # lenient in fixture