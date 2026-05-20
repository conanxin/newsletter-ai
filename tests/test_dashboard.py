"""Tests for dashboard.py — static dashboard generator."""

import json
import tempfile
from pathlib import Path

import pytest

from newsletter_ai.dashboard import (
    load_dashboard_data,
    render_dashboard_html,
    build_dashboard,
    DEFAULT_OUTPUT_DIR,
)


@pytest.fixture
def mock_output_dir(tmp_path):
    """Create a temporary output directory with mock run artifacts."""
    out = tmp_path / "output"
    snapshots = out / "snapshots"
    quality = out / "quality"
    state = out / "state"
    runs = out / "runs"
    for d in (snapshots, quality, state, runs):
        d.mkdir(parents=True)

    # Mock latest_items.json
    items = [
        {
            "item_id": "item-1",
            "item_index": 1,
            "run_id": "run-1",
            "created_at": "2026-05-20T00:00:00Z",
            "source": "test-source",
            "title": "Test Title",
            "url": "https://example.com/1",
            "summary": "Test summary",
            "topic_tags": ["ai"],
            "style_tags": ["analysis"],
            "score": 0.8,
            "score_breakdown": {},
        }
    ]
    (snapshots / "latest_items.json").write_text(json.dumps(items), encoding="utf-8")

    # Mock latest_quality.json
    quality_data = {
        "run_id": "run-1",
        "created_at": "2026-05-20T00:00:00Z",
        "sources_checked": 1,
        "feeds_loaded": 1,
        "feeds_failed": 0,
        "items_raw": 1,
        "items_normalized": 1,
        "items_after_dedupe": 1,
        "duplicate_count": 0,
        "malformed_feed_count": 0,
        "empty_feed_count": 0,
        "output_item_count": 1,
        "topic_distribution": {"ai": 1},
        "style_distribution": {"analysis": 1},
        "source_distribution": {"test-source": 1},
        "warnings": [],
        "source_details": [
            {
                "source": "test-source",
                "score": 1.0,
                "status": "success",
                "final_count": 1,
                "duplicate_removed_count": 0,
                "recommended_action": "keep",
            }
        ],
        "duplicate_reason_counts": {},
        "fuzzy_duplicate_count": 0,
        "section_distribution": {
            "ai": {
                "section_label": "AI",
                "item_count": 1,
                "average_score": 0.8,
                "average_quality_score": 0.0,
                "sources": ["test-source"],
                "topic_tags": ["ai"],
                "warnings": [],
                "representative_titles": ["Test Title"],
            }
        },
    }
    (quality / "latest_quality.json").write_text(json.dumps(quality_data), encoding="utf-8")

    # Mock last-run-status.json
    last_run = {
        "pipeline": "daily",
        "status": "success",
        "started_at": "2026-05-20T00:00:00Z",
        "finished_at": "2026-05-20T00:00:01Z",
        "steps": [
            {"name": "fetch", "status": "success"},
            {"name": "rank", "status": "success"},
            {"name": "digest", "status": "success", "section_count": 1},
            {"name": "health", "status": "skipped"},
            {"name": "publish", "status": "skipped"},
        ],
        "failed_step": None,
        "dry_run": True,
        "no_publish": False,
        "input_mode": "fixture_json",
        "source_count": 0,
        "item_count": 1,
        "ingestion_report": {
            "source_count_total": 0,
            "source_count_enabled": 0,
            "source_count_success": 0,
            "source_count_failed": 0,
            "source_count_empty": 0,
            "total_items": 0,
            "failed_source_ids": [],
        },
        "quality_report_path": str(quality / "latest_quality.json"),
        "run_record_path": str(runs / "run-1.json"),
    }
    (state / "last-run-status.json").write_text(json.dumps(last_run), encoding="utf-8")

    # Mock runs index
    runs_index = {
        "runs": [
            {
                "run_id": "run-1",
                "created_at": "2026-05-20T00:00:00Z",
                "status": "success",
                "input_mode": "fixture_json",
                "item_count": 1,
                "quality_report_path": str(quality / "latest_quality.json"),
                "record_path": str(runs / "run-1.json"),
            }
        ],
        "updated_at": "2026-05-20T00:00:00Z",
    }
    (runs / "index.json").write_text(json.dumps(runs_index), encoding="utf-8")

    return out


class TestLoadDashboardData:
    def test_loads_all_data(self, mock_output_dir, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", mock_output_dir / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", mock_output_dir / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", mock_output_dir / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", mock_output_dir / "runs" / "index.json"
        )

        data = load_dashboard_data()
        assert data["has_latest_run"] is True
        assert data["run_summary"]["item_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["item_index"] == 1
        assert len(data["runs"]) == 1
        assert len(data["feedback_commands"]) == 1

    def test_graceful_when_missing_files(self, tmp_path, monkeypatch):
        # Point all paths to non-existent files
        monkeypatch.setattr("newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "none.json")

        data = load_dashboard_data()
        assert data["has_latest_run"] is False
        assert data["items"] == []
        assert data["runs"] == []


class TestRenderDashboardHtml:
    def test_contains_run_summary(self, mock_output_dir, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", mock_output_dir / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", mock_output_dir / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", mock_output_dir / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", mock_output_dir / "runs" / "index.json"
        )

        data = load_dashboard_data()
        html = render_dashboard_html(data)
        assert "newsletter-ai Dashboard" in html
        assert "Dashboard" in html
        assert "Test Title" in html
        assert "#1" in html  # item_index
        assert "ai" in html
        assert "Quality Report" in html
        assert "最近 Runs" in html
        assert "Feedback 命令速查" in html
        assert "newsletter-ai feedback like 1 --dry-run" in html

    def test_no_secrets_in_html(self, mock_output_dir, monkeypatch):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", mock_output_dir / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", mock_output_dir / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", mock_output_dir / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", mock_output_dir / "runs" / "index.json"
        )

        data = load_dashboard_data()
        html = render_dashboard_html(data)
        assert "TELEGRAM_BOT_TOKEN" not in html
        assert "auth.json" not in html
        assert "cookie" not in html.lower()

    def test_empty_state_when_no_run(self, tmp_path, monkeypatch):
        monkeypatch.setattr("newsletter_ai.dashboard.SNAPSHOT_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.QUALITY_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", tmp_path / "none.json")
        monkeypatch.setattr("newsletter_ai.dashboard.RUNS_INDEX_PATH", tmp_path / "none.json")

        data = load_dashboard_data()
        html = render_dashboard_html(data)
        assert "请先运行" in html


class TestBuildDashboard:
    def test_writes_index_html(self, mock_output_dir, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "newsletter_ai.dashboard.SNAPSHOT_PATH", mock_output_dir / "snapshots" / "latest_items.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.QUALITY_PATH", mock_output_dir / "quality" / "latest_quality.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.LAST_RUN_STATUS_PATH", mock_output_dir / "state" / "last-run-status.json"
        )
        monkeypatch.setattr(
            "newsletter_ai.dashboard.RUNS_INDEX_PATH", mock_output_dir / "runs" / "index.json"
        )

        out_dir = tmp_path / "dashboard"
        path = build_dashboard(output_dir=out_dir)
        assert path.exists()
        assert path.name == "index.html"
        content = path.read_text(encoding="utf-8")
        assert "newsletter-ai Dashboard" in content
