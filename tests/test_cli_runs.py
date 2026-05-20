"""Tests for CLI runs commands (v0.3.19)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.cli import main


def test_cli_runs_list_no_runs(capsys, monkeypatch):
    """runs list with no index shows graceful message."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "output"
        out.mkdir()
        data = Path(td) / "data"
        data.mkdir()

        # Minimal config
        def mock_load_config():
            return {"OUTPUT_DIR": out, "DATA_DIR": data, "BASE_DIR": Path(td)}

        monkeypatch.setattr("newsletter_ai.cli.load_config", mock_load_config)
        monkeypatch.setattr("sys.argv", ["newsletter-ai", "runs", "list"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No runs found" in captured.out or "Run: newsletter-ai daily --dry-run" in captured.out


def test_cli_runs_list_with_runs(capsys, monkeypatch):
    """runs list shows runs from index."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "output"
        out.mkdir()
        data = Path(td) / "data"
        data.mkdir()
        runs_dir = out / "runs"
        runs_dir.mkdir()

        index = {
            "runs": [
                {
                    "run_id": "run-001",
                    "created_at": "2026-05-20T10:00:00",
                    "status": "success",
                    "input_mode": "fixture_json",
                    "item_count": 3,
                    "quality_report_path": "output/quality/latest_quality.json",
                    "record_path": "output/runs/run-001.json",
                }
            ],
            "updated_at": "2026-05-20T10:00:00",
        }
        (runs_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
        (runs_dir / "run-001.json").write_text(json.dumps({"run_id": "run-001"}), encoding="utf-8")

        def mock_load_config():
            return {"OUTPUT_DIR": out, "DATA_DIR": data, "BASE_DIR": Path(td)}

        monkeypatch.setattr("newsletter_ai.cli.load_config", mock_load_config)
        monkeypatch.setattr("sys.argv", ["newsletter-ai", "runs", "list"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "run-001" in captured.out
        assert "success" in captured.out
        assert "fixture_json" in captured.out


def test_cli_runs_latest(capsys, monkeypatch):
    """runs latest shows latest run summary."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "output"
        out.mkdir()
        data = Path(td) / "data"
        data.mkdir()
        runs_dir = out / "runs"
        runs_dir.mkdir()

        index = {
            "runs": [
                {
                    "run_id": "run-latest",
                    "created_at": "2026-05-20T11:00:00",
                    "status": "success",
                    "input_mode": "source_registry",
                    "item_count": 5,
                    "quality_report_path": "output/quality/latest_quality.json",
                    "record_path": "output/runs/run-latest.json",
                }
            ],
            "updated_at": "2026-05-20T11:00:00",
        }
        (runs_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
        (runs_dir / "run-latest.json").write_text(json.dumps({"run_id": "run-latest", "item_count": 5}), encoding="utf-8")

        def mock_load_config():
            return {"OUTPUT_DIR": out, "DATA_DIR": data, "BASE_DIR": Path(td)}

        monkeypatch.setattr("newsletter_ai.cli.load_config", mock_load_config)
        monkeypatch.setattr("sys.argv", ["newsletter-ai", "runs", "latest"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "run-latest" in captured.out
        assert "source_registry" in captured.out
        assert "5" in captured.out


def test_cli_runs_inspect(capsys, monkeypatch):
    """runs inspect <run_id> shows full record."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "output"
        out.mkdir()
        data = Path(td) / "data"
        data.mkdir()
        runs_dir = out / "runs"
        runs_dir.mkdir()

        record = {
            "run_id": "run-inspect",
            "status": "failed",
            "errors": ["Failed step: rank"],
            "item_count": 0,
        }
        (runs_dir / "run-inspect.json").write_text(json.dumps(record), encoding="utf-8")

        def mock_load_config():
            return {"OUTPUT_DIR": out, "DATA_DIR": data, "BASE_DIR": Path(td)}

        monkeypatch.setattr("newsletter_ai.cli.load_config", mock_load_config)
        monkeypatch.setattr("sys.argv", ["newsletter-ai", "runs", "inspect", "run-inspect"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "run-inspect" in captured.out
        assert "failed" in captured.out


def test_cli_runs_inspect_missing(capsys, monkeypatch):
    """runs inspect with missing run_id exits with error."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "output"
        out.mkdir()
        data = Path(td) / "data"
        data.mkdir()

        def mock_load_config():
            return {"OUTPUT_DIR": out, "DATA_DIR": data, "BASE_DIR": Path(td)}

        monkeypatch.setattr("newsletter_ai.cli.load_config", mock_load_config)
        monkeypatch.setattr("sys.argv", ["newsletter-ai", "runs", "inspect", "missing"])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out or "Error" in captured.out
