"""Tests for dry-run fixture unification (v0.3.6)."""

import tempfile
from pathlib import Path

from newsletter_ai.pipeline import run_daily_pipeline


def test_dry_run_uses_fixture_loader(tmp_path):
    cfg = {
        "DATA_DIR": tmp_path / "data",
        "OUTPUT_DIR": tmp_path,
    }

    result = run_daily_pipeline(cfg=cfg, dry_run=True)

    assert result["status"] == "success"
    assert any(s["name"] == "rank" and s["status"] == "success" for s in result["steps"])

    # Check that digest step ran successfully (section_count may vary)
    digest_steps = [s for s in result["steps"] if s["name"] == "digest"]
    assert len(digest_steps) > 0
    assert digest_steps[0]["status"] == "success"

    # Verify snapshot was created
    latest = tmp_path / "snapshots" / "latest_items.json"
    assert latest.exists()