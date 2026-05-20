"""Tests for source ingestion report and failure resilience (v0.3.11)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.sources import (
    ingest_offline_sources_with_report,
    enabled_sources,
)


def test_successful_rss_fixture_source():
    """A valid rss_fixture source should produce success report."""
    sources = [
        {
            "source_id": "test-ai",
            "name": "Test AI Feed",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
            "topic_hints": ["ai"],
            "style_hints": ["analysis"],
        }
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) > 0
    assert report["source_count_total"] == 1
    assert report["source_count_enabled"] == 1
    assert report["source_count_success"] == 1
    assert report["source_count_failed"] == 0
    assert report["total_items"] == len(items)

    src_report = report["sources"][0]
    assert src_report["status"] == "success"
    assert src_report["item_count_raw"] > 0
    assert src_report["item_count_normalized"] > 0
    assert src_report["errors"] == []


def test_disabled_source():
    """Disabled source should produce disabled report, no items."""
    sources = [
        {
            "source_id": "disabled",
            "name": "Disabled Feed",
            "type": "rss_fixture",
            "enabled": False,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
        }
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) == 0
    assert report["source_count_disabled"] == 1
    assert report["source_count_success"] == 0

    src_report = report["sources"][0]
    assert src_report["status"] == "disabled"
    assert src_report["enabled"] is False


def test_missing_fixture_path():
    """Missing fixture_path should produce failed report, not crash."""
    sources = [
        {
            "source_id": "missing-fixture",
            "name": "Missing Fixture",
            "type": "rss_fixture",
            "enabled": True,
            # no fixture_path
        }
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) == 0
    assert report["source_count_failed"] == 1

    src_report = report["sources"][0]
    assert src_report["status"] == "failed"
    assert "missing_fixture_path" in src_report["errors"]


def test_fixture_not_found():
    """Non-existent fixture file should produce failed report, not crash."""
    sources = [
        {
            "source_id": "bad-path",
            "name": "Bad Path",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        }
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) == 0
    assert report["source_count_failed"] == 1

    src_report = report["sources"][0]
    assert src_report["status"] == "failed"
    assert any("not_found" in e or "fixture_not_found" in e for e in src_report["errors"])


def test_mixed_success_failure():
    """Mixed success/failure sources should continue and return successful items."""
    sources = [
        {
            "source_id": "good",
            "name": "Good Feed",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
        },
        {
            "source_id": "bad",
            "name": "Bad Feed",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        },
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) > 0  # Good source still contributes
    assert report["source_count_success"] == 1
    assert report["source_count_failed"] == 1


def test_all_failed_graceful():
    """All sources failing should return empty items + all-failed report."""
    sources = [
        {
            "source_id": "bad1",
            "name": "Bad 1",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        },
        {
            "source_id": "bad2",
            "name": "Bad 2",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/nonexistent.xml",
        },
    ]
    result = ingest_offline_sources_with_report(sources)
    items = result["items"]
    report = result["report"]

    assert len(items) == 0
    assert report["source_count_success"] == 0
    assert report["source_count_failed"] == 2
    assert report["total_items"] == 0
