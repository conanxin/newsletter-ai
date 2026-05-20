"""Fixture loader for dry-run and E2E testing (v0.3.7+).

Now integrated with the normalization layer and RSS parser.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from .normalize import normalize_items
from .rss import parse_rss_file


DEFAULT_DRY_RUN_FIXTURE = Path(__file__).parent.parent.parent / "data" / "fixtures" / "dry_run_items.json"
DEFAULT_RSS_FIXTURE = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "e2e_rss_sample.xml"


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
    """Load and normalize the default dry-run JSON fixture items."""
    raw_items = load_fixture_items_from_path(DEFAULT_DRY_RUN_FIXTURE)
    return normalize_items(raw_items, source_hint="dry_run_fixture")


def load_rss_fixture_items(name: str = "e2e") -> List[Dict[str, Any]]:
    """Load and normalize RSS fixture items.

    Currently only supports "e2e" which points to tests/fixtures/e2e_rss_sample.xml.
    """
    if name != "e2e":
        raise ValueError(f"Unknown RSS fixture name: {name}")

    raw_items = parse_rss_file(DEFAULT_RSS_FIXTURE)
    return normalize_items(raw_items, source_hint="rss_fixture")


def load_rss_fixture_items_from_path(path: Path) -> List[Dict[str, Any]]:
    """Load and normalize RSS items from a specific XML file."""
    raw_items = parse_rss_file(path)
    return normalize_items(raw_items, source_hint="rss_fixture")


def normalize_fixture_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy helper - now delegates to normalize_items."""
    return normalize_items([item])[0]