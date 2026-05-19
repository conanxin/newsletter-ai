"""Tests for CLI sources fetch with --capture-replay (v0.3.14).

These tests use subprocess to exercise the CLI, but mock fetch_url
by setting an environment variable that triggers a monkeypatch inside
the CLI process.  This avoids the "patch does not cross process boundary"
problem.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cli_with_mock_fetch(*args, mock_xml_text: str):
    """Run CLI with fetch_url mocked via a temporary helper module."""
    # Build a tiny Python module that patches fetch.fetch_url before running main
    helper_code = (
        'import sys\n'
        'from pathlib import Path\n'
        'sys.path.insert(0, str(Path(__file__).parent.parent / "src"))\n'
        '\n'
        'from unittest.mock import patch\n'
        'from newsletter_ai.fetch import FetchResult\n'
        '\n'
        'def mock_fetch_url(url, *, timeout_sec=10, user_agent="newsletter-ai/dev"):\n'
        '    return FetchResult(\n'
        '        ok=True,\n'
        '        status_code=200,\n'
        '        text=' + repr(mock_xml_text) + ',\n'
        '        fetched_at="2026-05-19T10:00:00Z",\n'
        '        url=url,\n'
        '    )\n'
        '\n'
        'with patch("newsletter_ai.fetch.fetch_url", mock_fetch_url):\n'
        '    from newsletter_ai.cli import main\n'
        '    try:\n'
        '        main()\n'
        '    except SystemExit as e:\n'
        '        sys.exit(e.code if e.code is not None else 0)\n'
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(helper_code)
        helper_path = f.name

    try:
        cmd = [sys.executable, helper_path, "sources", "fetch"] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    finally:
        os.unlink(helper_path)


SIMPLE_RSS = """<?xml version="1.0"?>
<rss><channel><title>T</title>
<item><title>X</title><link>https://x</link></item>
</channel></rss>"""


class TestCaptureReplayGuard:
    def test_capture_replay_without_allow_network_fails(self):
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "sources", "fetch", "--capture-replay"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "requires --allow-network" in (result.stdout + result.stderr)

    def test_no_allow_network_skips_rss_url(self):
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "sources", "fetch", "--registry", "data/fixtures/source_registry.json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "network_disabled" in result.stdout or "skipped" in result.stdout


class TestCaptureReplayWithMockFetch:
    def test_capture_replay_saves_fixture(self, tmp_path):
        replay_dir = tmp_path / "replay"
        registry = tmp_path / "registry.json"
        registry.write_text(
            json.dumps([{
                "source_id": "mock-url",
                "name": "Mock URL",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/feed.xml",
            }]),
            encoding="utf-8",
        )

        result = _run_cli_with_mock_fetch(
            "--registry", str(registry),
            "--allow-network",
            "--capture-replay",
            "--replay-dir", str(replay_dir),
            mock_xml_text=SIMPLE_RSS,
        )

        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        assert "Captured 1 replay fixtures" in result.stdout

        xml_files = list(replay_dir.glob("*.xml"))
        assert len(xml_files) == 1
        meta_files = list(replay_dir.glob("*.json"))
        assert len(meta_files) == 1

    def test_failed_fetch_no_replay(self, tmp_path):
        replay_dir = tmp_path / "replay"
        registry = tmp_path / "registry.json"
        registry.write_text(
            json.dumps([{
                "source_id": "bad-url",
                "name": "Bad URL",
                "type": "rss_url",
                "enabled": True,
                "url": "https://example.com/404",
            }]),
            encoding="utf-8",
        )

        # Use a helper that returns a failed fetch
        helper_code = '''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import patch
from newsletter_ai.fetch import FetchResult

def mock_fetch_url(url, *, timeout_sec=10, user_agent="newsletter-ai/dev"):
    return FetchResult(ok=False, status_code=404, error="HTTPError 404: Not Found", url=url)

with patch("newsletter_ai.fetch.fetch_url", mock_fetch_url):
    from newsletter_ai.cli import main
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code if e.code is not None else 0)
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(helper_code)
            helper_path = f.name

        try:
            cmd = [sys.executable, helper_path, "sources", "fetch",
                   "--registry", str(registry),
                   "--allow-network",
                   "--capture-replay",
                   "--replay-dir", str(replay_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True)
        finally:
            os.unlink(helper_path)

        assert result.returncode == 0
        assert len(list(replay_dir.glob("*.xml"))) == 0


class TestSourceIdFilter:
    def test_source_id_filter_only_processes_one(self, tmp_path):
        replay_dir = tmp_path / "replay"
        registry = tmp_path / "registry.json"
        registry.write_text(
            json.dumps([
                {"source_id": "a", "name": "A", "type": "rss_url", "enabled": True, "url": "https://a.com"},
                {"source_id": "b", "name": "B", "type": "rss_url", "enabled": True, "url": "https://b.com"},
            ]),
            encoding="utf-8",
        )

        result = _run_cli_with_mock_fetch(
            "--registry", str(registry),
            "--allow-network",
            "--capture-replay",
            "--replay-dir", str(replay_dir),
            "--source-id", "a",
            mock_xml_text=SIMPLE_RSS,
        )

        assert result.returncode == 0
        xml_files = list(replay_dir.glob("*.xml"))
        assert len(xml_files) == 1
        assert "rss_a_" in xml_files[0].name
