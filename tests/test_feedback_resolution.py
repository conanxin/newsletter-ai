"""Feedback item resolution from snapshot."""

import tempfile
from pathlib import Path
from newsletter_ai.feedback import resolve_item_from_snapshot
from newsletter_ai.snapshot import create_item_snapshot


def test_resolve_item_from_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "output"
        data_dir = Path(tmp) / "data"
        items = [{"source": "tc", "title": "Test", "item_index": 1}]
        create_item_snapshot(items, output_dir, data_dir)
        item = resolve_item_from_snapshot(data_dir, output_dir, 1)
        assert item is not None
        assert item["source"] == "tc"