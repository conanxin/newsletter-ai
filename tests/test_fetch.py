"""Tests for fetch.py — controlled real RSS fetcher (v0.3.12).

All tests mock network access. No real HTTP requests are made.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from newsletter_ai.fetch import fetch_url, fetch_rss_url_source, FetchResult


class TestFetchUrl:
    """Tests for fetch_url() with mocked urllib.request."""

    def test_fetch_url_success(self):
        class MockResponse:
            def getcode(self):
                return 200
            def read(self):
                return b"<rss><channel><title>Test</title></channel></rss>"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        with patch("newsletter_ai.fetch.urllib.request.urlopen", return_value=MockResponse()):
            result = fetch_url("https://example.com/feed.xml")

        assert result.ok is True
        assert result.status_code == 200
        assert "Test" in result.text
        assert result.url == "https://example.com/feed.xml"
        assert result.error == ""
        assert result.duration_sec >= 0

    def test_fetch_url_http_error(self):
        from urllib.error import HTTPError
        mock_error = HTTPError(
            url="https://example.com/feed.xml",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=mock_error):
            result = fetch_url("https://example.com/feed.xml")

        assert result.ok is False
        assert result.status_code == 404
        assert "HTTPError 404" in result.error

    def test_fetch_url_url_error(self):
        from urllib.error import URLError
        mock_error = URLError("Name or service not known")

        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=mock_error):
            result = fetch_url("https://example.com/feed.xml")

        assert result.ok is False
        assert result.status_code is None
        assert "URLError" in result.error

    def test_fetch_url_timeout(self):
        import socket
        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            result = fetch_url("https://example.com/feed.xml", timeout_sec=1)

        assert result.ok is False
        assert "FetchError" in result.error

    def test_fetch_url_user_agent(self):
        captured = {}
        def capture_request(req, **kwargs):
            captured["headers"] = dict(req.headers)
            return type("MockResponse", (), {
                "getcode": lambda self: 200,
                "read": lambda self: b"ok",
            })()

        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=capture_request):
            fetch_url("https://example.com/feed.xml", user_agent="newsletter-ai/test")

        assert captured["headers"].get("User-agent") == "newsletter-ai/test"


class TestFetchRssUrlSource:
    """Tests for fetch_rss_url_source() with mocked network."""

    def test_network_disabled_by_default(self):
        source = {
            "source_id": "test-feed",
            "url": "https://example.com/feed.xml",
            "timeout_sec": 5,
        }
        result = fetch_rss_url_source(source)

        assert result.ok is False
        assert result.error == "network_disabled"
        assert result.url == "https://example.com/feed.xml"

    def test_missing_url(self):
        source = {"source_id": "test-feed"}
        result = fetch_rss_url_source(source, allow_network=True)

        assert result.ok is False
        assert result.error == "missing_url"

    def test_allow_network_success(self):
        class MockResponse:
            def getcode(self):
                return 200
            def read(self):
                return b"<rss><channel><title>Test</title></channel></rss>"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        source = {
            "source_id": "test-feed",
            "url": "https://example.com/feed.xml",
            "timeout_sec": 5,
        }

        with patch("newsletter_ai.fetch.urllib.request.urlopen", return_value=MockResponse()):
            result = fetch_rss_url_source(source, allow_network=True)

        assert result.ok is True
        assert result.status_code == 200
        assert "Test" in result.text

    def test_allow_network_failure(self):
        from urllib.error import HTTPError
        mock_error = HTTPError(
            url="https://example.com/feed.xml",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )

        source = {
            "source_id": "test-feed",
            "url": "https://example.com/feed.xml",
            "timeout_sec": 5,
        }

        with patch("newsletter_ai.fetch.urllib.request.urlopen", side_effect=mock_error):
            result = fetch_rss_url_source(source, allow_network=True)

        assert result.ok is False
        assert result.status_code == 500
        assert "HTTPError 500" in result.error


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_default_values(self):
        result = FetchResult()
        assert result.ok is False
        assert result.status_code is None
        assert result.text == ""
        assert result.error == ""
        assert result.from_cache is False

    def test_custom_values(self):
        result = FetchResult(
            ok=True,
            status_code=200,
            text="hello",
            error="",
            fetched_at="2024-01-01T00:00:00Z",
            from_cache=True,
            duration_sec=0.5,
            url="https://example.com",
        )
        assert result.ok is True
        assert result.status_code == 200
        assert result.text == "hello"
        assert result.from_cache is True
        assert result.duration_sec == 0.5
