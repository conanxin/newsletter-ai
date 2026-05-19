"""Source Registry + Offline Ingestion Bridge (v0.3.9)

This module provides a source registry and offline ingestion bridge
for newsletter-ai. It reads a local source registry JSON file,
parses RSS fixture sources, normalizes items, and returns them
for use in the pipeline.

No network requests are made.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .normalize import normalize_items
from .rss import parse_rss_file


DEFAULT_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "source_registry.json"


def load_source_registry(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the source registry from a JSON file.

    Returns a list of source dicts.
    """
    registry_path = path or DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        raise FileNotFoundError(f"Source registry not found: {registry_path}")

    with open(registry_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Source registry must be a JSON array, got {type(data)}")

    return data


def validate_source(source: Dict[str, Any]) -> List[str]:
    """Validate a single source entry.

    Returns a list of error messages. Empty list means valid.
    """
    errors: List[str] = []
    required_fields = ["source_id", "name", "type", "enabled"]
    for field in required_fields:
        if field not in source:
            errors.append(f"missing_field:{field}")

    if source.get("type") == "rss_fixture" and not source.get("fixture_path"):
        errors.append("missing_fixture_path")

    return errors


def validate_source_registry(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate the entire source registry.

    Returns a dict with 'valid' (bool) and 'errors' (list of str).
    """
    all_errors: List[str] = []
    for idx, source in enumerate(sources):
        errs = validate_source(source)
        for e in errs:
            all_errors.append(f"source[{idx}]: {e}")

    return {"valid": len(all_errors) == 0, "errors": all_errors}


def enabled_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to only enabled sources."""
    return [s for s in sources if s.get("enabled", True)]


def ingest_offline_sources(
    sources: List[Dict[str, Any]],
    *,
    base_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Ingest items from offline sources.

    Currently supports:
    - rss_fixture: reads local XML fixture file, parses RSS, normalizes items.

    Returns a flat list of normalized items.
    """
    base_dir = base_dir or Path(__file__).parent.parent.parent
    all_items: List[Dict[str, Any]] = []

    for source in sources:
        if not source.get("enabled", True):
            continue

        source_type = source.get("type")
        source_id = source.get("source_id", "unknown")
        source_name = source.get("name", source_id)
        topic_hints = source.get("topic_hints", [])
        style_hints = source.get("style_hints", [])

        if source_type == "rss_fixture":
            fixture_path = source.get("fixture_path")
            if not fixture_path:
                continue

            full_path = base_dir / fixture_path
            if not full_path.exists():
                continue

            raw_items = parse_rss_file(full_path)
            # Merge source metadata into raw items before normalization
            for raw in raw_items:
                raw["source_id"] = source_id
                raw["source_name"] = source_name
                if topic_hints and not raw.get("topic_tags"):
                    raw["topic_tags"] = topic_hints
                if style_hints and not raw.get("style_tags"):
                    raw["style_tags"] = style_hints

            normalized = normalize_items(raw_items, source_hint=source_id)
            all_items.extend(normalized)

    return all_items