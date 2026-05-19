"""Fixture loader for dry-run and E2E testing.

This module provides a unified way to load fixture items for
newsletter-ai daily --dry-run and regression tests.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DRY_RUN_FIXTURE = Path(__file__).parent.parent.parent / "data" / "fixtures" / "dry_run_items.json"


def load_fixture_items_from_path(path: Path) -> List[Dict[str, Any]]:
    """Load items from a JSON file.

    Args:
        path: Path to the JSON fixture file.

    Returns:
        List of item dictionaries.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    with open(path, encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError(f"Fixture must be a JSON array, got {type(items)}")

    return items


def load_dry_run_items() -> List[Dict[str, Any]]:
    """Load the default dry-run fixture items.

    This is the recommended source for `newsletter-ai daily --dry-run`.
    """
    return load_fixture_items_from_path(DEFAULT_DRY_RUN_FIXTURE)


def normalize_fixture_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure fixture item has all required fields with safe defaults."""
    normalized = {
        "id": item.get("id") or item.get("item_id") or f"item-{hash(str(item)) % 100000}",
        "source": item.get("source", "unknown"),
        "title": item.get("title", "Untitled"),
        "url": item.get("url", ""),
        "summary": item.get("summary", item.get("description", "")),
        "topic_tags": item.get("topic_tags", []) or [],
        "style_tags": item.get("style_tags", []) or [],
        "base_score": float(item.get("base_score", 0.5)),
    }
    return normalized