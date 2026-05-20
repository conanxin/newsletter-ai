"""Tests for dashboard export bundle functionality."""

import json
import pytest
from pathlib import Path

from newsletter_ai.dashboard import export_dashboard_bundle, load_dashboard_data


class TestExportDashboardBundle:
    def test_export_writes_index_html(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        # Create minimal fixtures
        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        result = export_dashboard_bundle(out_dir=out_dir)
        assert result.exists()
        assert (result / "index.html").exists()
        html = (result / "index.html").read_text(encoding="utf-8")
        assert "newsletter-ai Dashboard" in html
        assert "Test" in html
        assert "#1" in html

    def test_export_writes_metadata_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir, include_metadata=True)
        meta_path = out_dir / "metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["generated_by"] == "newsletter-ai v0.4.3"
        assert meta["item_count"] == 1
        assert "run_id" in meta

    def test_export_writes_readme_txt(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir)
        readme_path = out_dir / "README.txt"
        assert readme_path.exists()
        text = readme_path.read_text(encoding="utf-8")
        assert "Static Dashboard Bundle" in text
        assert "GitHub Pages" in text
        assert "Nginx" in text
        assert "no secrets" in text.lower()

    def test_export_no_metadata_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir, include_metadata=False)
        assert not (out_dir / "metadata.json").exists()
        assert (out_dir / "index.html").exists()
        assert (out_dir / "README.txt").exists()

    def test_export_graceful_error_on_missing_data(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        out_dir = tmp_path / "dist" / "dashboard"
        with pytest.raises(RuntimeError, match="daily --dry-run"):
            export_dashboard_bundle(out_dir=out_dir)

    def test_export_metadata_no_secrets(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

    def test_export_metadata_relative_paths(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir)
        meta = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
        meta_str = json.dumps(meta)
        assert "TELEGRAM_BOT_TOKEN" not in meta_str
        assert "auth.json" not in meta_str
        assert "cookie" not in meta_str.lower()
        assert "Authorization" not in meta_str

    def test_export_metadata_relative_paths(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        # Create the quality file so path exists check passes
        (tmp_path / "quality" / "latest_quality.json").write_text(
            json.dumps({"section_distribution": {}, "source_details": []}),
            encoding="utf-8",
        )

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir)
        meta = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
        meta_str = json.dumps(meta)

        # No absolute paths
        assert "/home/conanxin" not in meta_str
        assert "/mnt/d/" not in meta_str
        assert "C:\\" not in meta_str
        assert "Users\\" not in meta_str

        # Relative paths
        assert meta.get("quality_report_path") == "output/quality/latest_quality.json"
        assert meta.get("snapshot_path") == "output/snapshots/latest_items.json"

    def test_export_readme_no_local_paths(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir)
        readme = (out_dir / "README.txt").read_text(encoding="utf-8")
        assert "/home/conanxin" not in readme
        assert "/mnt/d/" not in readme
        assert "C:\\" not in readme
        assert "Users\\" not in readme

    def test_export_custom_out_still_works(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        custom_dir = tmp_path / "my-export"
        result = export_dashboard_bundle(out_dir=custom_dir)
        assert result == custom_dir
        assert (custom_dir / "index.html").exists()
        assert (custom_dir / "metadata.json").exists()
        assert (custom_dir / "README.txt").exists()
        meta = json.loads((custom_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("snapshot_path") == "output/snapshots/latest_items.json"
        assert meta.get("quality_report_path") == "output/quality/latest_quality.json"

    def test_export_readme_no_local_paths(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        out_dir = tmp_path / "dist" / "dashboard"
        export_dashboard_bundle(out_dir=out_dir)
        readme = (out_dir / "README.txt").read_text(encoding="utf-8")
        assert "/home/conanxin" not in readme
        assert "/mnt/d/" not in readme
        assert "C:\\" not in readme
        assert "Users\\" not in readme

    def test_export_custom_out_still_works(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "runs" / "index.json"
        )

        (tmp_path / "snapshots").mkdir(parents=True, exist_ok=True)
        (tmp_path / "quality").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

        (tmp_path / "snapshots" / "latest_items.json").write_text(
            json.dumps([
                {"item_index": 1, "title": "Test", "source": "src", "url": "http://example.com", "summary": "s", "score": 0.5, "topic_tags": ["ai"]}
            ]),
            encoding="utf-8",
        )
        (tmp_path / "state" / "last-run-status.json").write_text(
            json.dumps({"status": "success", "started_at": "2026-01-01", "input_mode": "fixture", "item_count": 1, "source_count": 1, "dry_run": True, "steps": [{"name": "digest", "section_count": 1}]}),
            encoding="utf-8",
        )
        (tmp_path / "runs" / "index.json").write_text(json.dumps({"runs": []}), encoding="utf-8")

        custom_dir = tmp_path / "my-export"
        result = export_dashboard_bundle(out_dir=custom_dir)
        assert result == custom_dir
        assert (custom_dir / "index.html").exists()
        assert (custom_dir / "metadata.json").exists()
        assert (custom_dir / "README.txt").exists()
        meta = json.loads((custom_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("snapshot_path") == "output/snapshots/latest_items.json"
