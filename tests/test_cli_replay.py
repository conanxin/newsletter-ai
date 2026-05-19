"""Tests for CLI replay commands (v0.3.15)."""

import json
import subprocess
import sys
from pathlib import Path


def run_cli(*args):
    cmd = [sys.executable, "-m", "newsletter_ai.cli", "replay"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Replay Channel</title>
  <item>
    <title>Replay Item</title>
    <link>https://example.com/r</link>
    <description>Replay desc</description>
  </item>
</channel>
</rss>
"""


def _make_fixture(tmp_path, source_id="demo"):
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)
    xml_path = replay_dir / f"rss_{source_id}_20260519_100000.xml"
    meta_path = xml_path.with_suffix(".json")
    xml_path.write_text(SAMPLE_RSS, encoding="utf-8")
    meta = {
        "source_id": source_id,
        "sha256": "dummy",
        "item_count": 1,
        "generated_by": "newsletter-ai/replay v0.3.15",
        "fetched_at": "2026-05-19T10:00:00Z",
        "url": "https://example.com/feed.xml",
        "status_code": 200,
        "sanitized": True,
        "stripped_tracking_params_count": 0,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return replay_dir, xml_path, meta_path


class TestReplayList:
    def test_list_empty_directory(self, tmp_path):
        replay_dir = tmp_path / "replay"
        replay_dir.mkdir(parents=True, exist_ok=True)
        result = run_cli("list", "--replay-dir", str(replay_dir))
        assert result.returncode == 0
        assert "No replay fixtures" in result.stdout

    def test_list_shows_fixture(self, tmp_path):
        replay_dir, _, _ = _make_fixture(tmp_path, source_id="demo")
        result = run_cli("list", "--replay-dir", str(replay_dir))
        assert result.returncode == 0
        assert "demo" in result.stdout
        assert "1" in result.stdout


class TestReplayInspect:
    def test_inspect_shows_metadata_and_titles(self, tmp_path):
        replay_dir, xml_path, _ = _make_fixture(tmp_path, source_id="demo")
        result = run_cli("inspect", str(xml_path))
        assert result.returncode == 0
        assert "Replay: rss_demo_20260519_100000.xml" in result.stdout
        assert "source_id: demo" in result.stdout
        assert "Replay Item" in result.stdout

    def test_inspect_missing_path(self):
        result = run_cli("inspect")
        assert result.returncode == 1
        assert "requires a path" in (result.stdout + result.stderr)


class TestReplayValidate:
    def test_validate_empty_directory(self, tmp_path):
        replay_dir = tmp_path / "replay"
        replay_dir.mkdir(parents=True, exist_ok=True)
        result = run_cli("validate", "--replay-dir", str(replay_dir))
        assert result.returncode == 0
        assert "No replay fixtures" in result.stdout

    def test_validate_passes_valid_fixture(self, tmp_path):
        import hashlib
        replay_dir, xml_path, meta_path = _make_fixture(tmp_path, source_id="demo")
        # Fix sha256 to match
        xml_text = xml_path.read_text(encoding="utf-8")
        sha = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["sha256"] = sha
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        result = run_cli("validate", "--replay-dir", str(replay_dir))
        assert result.returncode == 0
        assert "PASS" in result.stdout
        assert "1 passed, 0 failed" in result.stdout


class TestReplayPromote:
    def test_promote_outputs_registry_entry(self, tmp_path):
        replay_dir, xml_path, _ = _make_fixture(tmp_path, source_id="demo")
        result = run_cli("promote", str(xml_path), "--source-id", "my-source", "--name", "My Source")
        assert result.returncode == 0
        assert "Proposed registry entry" in result.stdout
        assert "rss_replay" in result.stdout
        assert "my-source" in result.stdout
        assert "My Source" in result.stdout

    def test_promote_missing_args(self):
        result = run_cli("promote")
        assert result.returncode == 1
        assert "requires xml_path" in (result.stdout + result.stderr)
