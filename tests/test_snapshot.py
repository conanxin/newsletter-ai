"""Snapshot writing tests for v0.2.3."""

import tempfile
from pathlib import Path
from newsletter_ai.snapshot import create_item_snapshot


def test_snapshot_writes_latest_and_historical():
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "output"
        data_dir = Path(tmp) / "data"
        items = [{"id": "1", "source": "tc", "title": "AI", "base_score": 0.6}]
        result = create_item_snapshot(items, output_dir, data_dir)
        assert (output_dir / "snapshots" / "latest_items.json").exists()
        assert result["count"] == 1
        assert "historical" in result