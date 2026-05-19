"""End-to-End Fixture-based Regression Test for v0.3.5"""

import json
import tempfile
from pathlib import Path

import pytest

from newsletter_ai.ranking import rank_items
from newsletter_ai.snapshot import create_item_snapshot
from newsletter_ai.sections import group_items_into_sections
from newsletter_ai.render import render_markdown_digest, render_telegram_digest
from newsletter_ai.quality import generate_quality_report
from newsletter_ai.feedback import resolve_item_from_snapshot, apply_feedback


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "e2e_items.json"


def load_e2e_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_e2e_full_fixture_flow(tmp_path):
    """Complete fixture-based E2E regression covering the entire daily chain."""
    items = load_e2e_fixture()

    # Provide minimal config
    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }

    # 1. Ranking
    ranked = rank_items(items, cfg)
    assert len(ranked) > 0

    # 2. Snapshot
    snap = create_item_snapshot(ranked, tmp_path, tmp_path / "data")
    latest_path = tmp_path / "snapshots" / "latest_items.json"
    assert latest_path.exists()

    snapshot_data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert len(snapshot_data) == len(ranked)

    for i, item in enumerate(snapshot_data, start=1):
        assert item["item_index"] == i
        assert "source" in item
        assert "title" in item
        assert "topic_tags" in item
        assert "style_tags" in item

    # 3. Sectioning
    sections = group_items_into_sections(ranked)
    assert len(sections) >= 2

    # 4. Render
    md = render_markdown_digest(sections)
    tg = render_telegram_digest(sections)
    assert "## " in md or "# " in md

    # 5. Quality Report
    quality_report = generate_quality_report(
        run_id="e2e-test",
        sources=[{"source": "techcrunch", "status": "ok"}, {"source": "stratechery", "status": "ok"}],
        items_after_dedupe=ranked,
        duplicate_count=1,
        malformed_count=0,
        empty_count=0
    )

    assert "section_distribution" in quality_report.to_dict()

    # 6. Feedback resolution
    resolved = resolve_item_from_snapshot(tmp_path / "data", tmp_path, item_index=1)
    assert resolved is not None

    # 7. Feedback apply (dry-run)
    result = apply_feedback("like 1", {"DATA_DIR": str(tmp_path / "data"), "OUTPUT_DIR": str(tmp_path)}, dry_run=True)
    assert "DRY-RUN" in result or "would apply" in result

    # Real feedback writes to tmp only
    result_real = apply_feedback("like 1", {"DATA_DIR": str(tmp_path / "data"), "OUTPUT_DIR": str(tmp_path)}, dry_run=False)
    assert "feedback applied" in result_real

    history_file = tmp_path / "data" / "state" / "preferences_history.jsonl"
    assert history_file.exists()

    print("✅ E2E Fixture Flow Regression PASSED")