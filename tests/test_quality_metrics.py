"""Test quality metrics schema and calculation."""

import pytest
from src.newsletter_ai.quality import QualityReport, SourceQuality, generate_quality_report

def test_global_metrics():
    sources = [
        {"source": "tech", "status": "ok", "raw_item_count": 5, "normalized_item_count": 4},
        {"source": "strategy", "status": "ok", "raw_item_count": 3, "normalized_item_count": 3},
    ]
    items = [{"id": "1", "topic": "ai"}, {"id": "2", "topic": "tech"}]
    report = generate_quality_report("test-run", sources, items, duplicate_count=2, malformed_count=1, empty_count=1)

    assert report.run_id == "test-run"
    assert report.sources_checked == 2
    assert report.items_raw == 8
    assert report.items_after_dedupe == 2
    assert report.duplicate_count == 2
    assert report.malformed_feed_count == 1
    assert report.empty_feed_count == 1
    assert "ai" in report.topic_distribution

def test_source_metrics():
    sources = [{"source": "ai-news", "status": "ok", "raw_item_count": 10, "final_item_count": 7}]
    items = []
    report = generate_quality_report("r1", sources, items)
    assert len(report.source_details) == 1
    assert report.source_details[0].source == "ai-news"
    assert report.source_details[0].raw_item_count == 10

def test_distribution_exists():
    sources = [{"source": "s1", "status": "ok"}]
    items = [{"topic": "ai", "source": "s1"}]
    report = generate_quality_report("r2", sources, items)
    assert report.topic_distribution
    assert report.source_distribution