"""Tests for rss_url source ingestion in sources.py (v0.3.12).

All tests mock network access. No real HTTP requests are made.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from newsletter_ai.sources import (
    validate_source,
    ingest_sources_with_report,
    ingest_offline_sources_with_report,
)


class TestValidateSourceRssUrl:
    """Tests for validate_source() with rss_url type."""

    def test_rss_url_valid(self):
        source = {
            "source_id": "test-rss",
            "name": "Test RSS",
            "type": "rss_url",
            "enabled": True,
            "url": "https://example.com/feed.xml",
        }
        errors = validate_source(source)
        assert errors == []

    def test_rss_url_missing_url(self):
        source = {
            "source_id": "test-rss",
            "name": "Test RSS",
            "type": "rss_url",
            "enabled": True,
        }
        errors = validate_source(source)
        assert "missing_url" in errors

    def test_rss_fixture_still_valid(self):
        source = {
            "source_id": "test-fixture",
            "name": "Test Fixture",
            "type": "rss_fixture",
            "enabled": True,
            "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
        }
        errors = validate_source(source)
        assert errors == []


class TestIngestSourcesWithReportRssUrl:
    """Tests for ingest_sources_with_report() with rss_url sources."""

    def test_rss_url_skipped_when_network_disabled(self):
        sources = [
            {
                "source_id": "test-rss",
                "name": "Test RSS",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
                "topic_hints": ["ai"],
            }
        ]
        result = ingest_sources_with_report(sources, allow_network=False)
        report = result["report"]

        assert report["source_count_skipped_network"] == 1
        assert report["source_count_success"] == 0
        assert report["source_count_failed"] == 0
        assert result["items"] == []

        source_report = report["sources"][0]
        assert source_report["status"] == "skipped"
        assert source_report["network_allowed"] is False
        assert "network_disabled" in source_report["warnings"][0]

    def test_rss_url_fetched_when_network_allowed(self):
        class MockResponse:
            def getcode(self):
                return 200
            def read(self):
                return b"""<?xml version="1.0"?>
                <rss><channel><title>Test</title>
                <item><title>Item 1</title><link>https://example.com/1</link>
                <description>Desc 1</description></item>
                </channel></rss>"""
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        sources = [
            {
                "source_id": "test-rss",
                "name": "Test RSS",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
                "topic_hints": ["ai"],
            }
        ]

        with patch("newsletter_ai.fetch.urllib.request.urlopen", return_value=MockResponse()):
            result = ingest_sources_with_report(sources, allow_network=True)

        report = result["report"]
        assert report["source_count_success"] == 1
        assert report["source_count_skipped_network"] == 0
        assert len(result["items"]) == 1

        source_report = report["sources"][0]
        assert source_report["status"] == "success"
        assert source_report["network_allowed"] is True
        assert source_report["fetch_status"] == "success"
        assert source_report["http_status_code"] == 200

    def test_rss_url_fetch_failure(self):
        from urllib.error import HTTPError
        mock_error = HTTPError(
            url="https://example.com/feed.xml",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=None,
        )

        sources = [
            {
                "source_id": "test-rss",
                "name": "Test RSS",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
            }
        ]

        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=mock_error):
            result = ingest_sources_with_report(sources, allow_network=True)

        report = result["report"]
        assert report["source_count_failed"] == 1
        assert result["items"] == []

        source_report = report["sources"][0]
        assert source_report["status"] == "failed"
        assert source_report["fetch_status"] == "failed"
        assert source_report["http_status_code"] == 503
        assert "HTTPError 503" in source_report["errors"][0]

    def test_mixed_fixture_and_rss_url(self):
        """rss_fixture succeeds, rss_url skipped when network disabled."""
        sources = [
            {
                "source_id": "fixture-source",
                "name": "Fixture",
                "type": "rss_fixture",
                "enabled": True,
                "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
            },
            {
                "source_id": "url-source",
                "name": "URL Source",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
            },
        ]
        result = ingest_sources_with_report(sources, allow_network=False)
        report = result["report"]

        assert report["source_count_success"] == 1
        assert report["source_count_skipped_network"] == 1
        assert len(result["items"]) > 0

    def test_all_sources_skipped_graceful(self):
        sources = [
            {
                "source_id": "url-source",
                "name": "URL Source",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
            }
        ]
        result = ingest_sources_with_report(sources, allow_network=False)
        report = result["report"]

        assert report["source_count_success"] == 0
        assert report["source_count_skipped_network"] == 1
        assert result["items"] == []

    def test_backward_compatible_offline_function(self):
        """ingest_offline_sources_with_report still works and does not network."""
        sources = [
            {
                "source_id": "fixture-source",
                "name": "Fixture",
                "type": "rss_fixture",
                "enabled": True,
                "fixture_path": "tests/fixtures/e2e_rss_sample.xml",
            }
        ]
        result = ingest_offline_sources_with_report(sources)
        report = result["report"]

        assert report["source_count_success"] == 1
        assert len(result["items"]) > 0
