"""Tests for v0.3.13/0.3.13R feedback CLI parser hardening.

Covers quoted/unquoted forms, --note support (quoted and separate flag),
note persistence to feedback event, and graceful errors.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_feedback(*args):
    """Run feedback CLI and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "newsletter_ai.cli", "feedback"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestQuotedForms:
    def test_quoted_like(self):
        rc, out, err = run_feedback("like 1", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out

    def test_quoted_source_up(self):
        rc, out, err = run_feedback("source_up Stratechery", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out
        assert "Stratechery" in out

    def test_quoted_save_with_note_in_string(self):
        rc, out, err = run_feedback("save 2 --note 值得深挖", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out
        assert "note: 值得深挖" in out


class TestUnquotedForms:
    def test_unquoted_like(self):
        rc, out, err = run_feedback("like", "1", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out

    def test_unquoted_source_up(self):
        rc, out, err = run_feedback("source_up", "Stratechery", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out
        assert "Stratechery" in out

    def test_unquoted_save(self):
        rc, out, err = run_feedback("save", "2", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out


class TestNoteSupport:
    def test_separate_note_flag(self):
        rc, out, err = run_feedback("save", "2", "--note", "值得深挖", "--dry-run")
        assert rc == 0, f"Expected 0, got {rc}. stderr: {err}"
        assert "DRY-RUN" in out or "would apply" in out
        assert "note: 值得深挖" in out

    def test_quoted_and_unquoted_note_equivalence(self):
        rc1, out1, _ = run_feedback("save 2 --note 值得深挖", "--dry-run")
        rc2, out2, _ = run_feedback("save", "2", "--note", "值得深挖", "--dry-run")
        assert rc1 == 0 and rc2 == 0
        assert "note: 值得深挖" in out1
        assert "note: 值得深挖" in out2


class TestNotePersistence:
    def test_note_written_to_feedback_events_jsonl(self, tmp_path):
        from newsletter_ai.feedback import apply_feedback

        data_dir = tmp_path / "data"
        output_dir = tmp_path / "output"
        snapshots = output_dir / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)

        items = [
            {"title": "Test Item", "source": "fixture", "url": "https://example.com", "topic_tags": [], "style_tags": []}
        ]
        latest = snapshots / "latest_items.json"
        latest.write_text(json.dumps(items), encoding="utf-8")

        cfg = {"DATA_DIR": str(data_dir), "OUTPUT_DIR": str(output_dir)}
        result = apply_feedback("save 1", cfg, dry_run=False, note="值得深挖")
        assert "feedback applied" in result

        events_file = data_dir / "state" / "feedback_events.jsonl"
        assert events_file.exists()
        lines = events_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event.get("note") == "值得深挖"
        assert event.get("action") == "save"
        assert event.get("item_index") == 1

    def test_no_note_for_like(self, tmp_path):
        from newsletter_ai.feedback import apply_feedback

        data_dir = tmp_path / "data"
        output_dir = tmp_path / "output"
        snapshots = output_dir / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)

        items = [
            {"title": "Test Item", "source": "fixture", "url": "https://example.com", "topic_tags": [], "style_tags": []}
        ]
        latest = snapshots / "latest_items.json"
        latest.write_text(json.dumps(items), encoding="utf-8")

        cfg = {"DATA_DIR": str(data_dir), "OUTPUT_DIR": str(output_dir)}
        result = apply_feedback("like 1", cfg, dry_run=False)
        assert "feedback applied" in result

        events_file = data_dir / "state" / "feedback_events.jsonl"
        lines = events_file.read_text(encoding="utf-8").strip().split("\n")
        event = json.loads(lines[0])
        assert event.get("note") is None


class TestGracefulErrors:
    def test_unknown_action(self):
        rc, out, err = run_feedback("badaction", "1", "--dry-run")
        assert rc == 1, f"Expected 1, got {rc}"
        assert "unknown feedback action" in out.lower() or "unknown feedback action" in err.lower()

    def test_missing_index(self):
        rc, out, err = run_feedback("like", "--dry-run")
        assert rc == 1, f"Expected 1, got {rc}"
        assert "requires an item index" in out.lower() or "requires an item index" in err.lower()

    def test_non_numeric_index(self):
        rc, out, err = run_feedback("like", "abc", "--dry-run")
        assert rc == 1, f"Expected 1, got {rc}"
        assert "numeric index" in out.lower() or "numeric index" in err.lower()

    def test_empty_command(self):
        rc, out, err = run_feedback("--dry-run")
        assert rc == 1, f"Expected 1, got {rc}"
        assert "empty" in out.lower() or "empty" in err.lower()
