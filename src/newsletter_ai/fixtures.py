"""Fixture loader for dry-run and E2E testing (v0.3.7).

Now integrated with the normalization layer.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from .normalize import normalize_items


DEFAULT_DRY_RUN_FIXTURE = Path(__file__).parent.parent.parent / "data" / "fixtures" / "dry_run_items.json"


def load_fixture_items_from_path(path: Path) -> List[Dict[str, Any]]:
    """Load raw items from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    with open(path, encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError(f"Fixture must be a JSON array, got {type(items)}")

    return items


def load_dry_run_items() -> List[Dict[str, Any]]:
    """Load and normalize the default dry-run fixture items.

    This is the recommended source for `newsletter-ai daily --dry-run`.
    All items are passed through normalize_items() to ensure schema consistency.
    """
    raw_items = load_fixture_items_from_path(DEFAULT_DRY_RUN_FIXTURE)
    return normalize_items(raw_items, source_hint="dry_run_fixture")


def normalize_fixture_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy helper - now delegates to normalize_items."""
    return normalize_items([item])[0]