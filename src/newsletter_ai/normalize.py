"""Source Item Normalization Layer (v0.3.7)

This module provides a unified normalization layer for all item sources
(fixture, RSS, future web sources, manual JSON, etc.) before they enter
ranking / snapshot / sectioning / quality / feedback.

All sources should go through normalize_item() or normalize_items()
to guarantee a stable internal schema.
"""

from typing import Any, Dict, List, Optional
import hashlib


def _stable_item_id(source: str, title: str, url: str = "") -> str:
    """Generate a stable item_id.

    Priority:
    1. url (if present)
    2. source + title
    """
    if url:
        key = url
    else:
        key = f"{source}::{title}"
    return "item-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def normalize_item(raw: Dict[str, Any], *, source_hint: Optional[str] = None) -> Dict[str, Any]:
    """Normalize a raw item into the canonical internal schema.

    This function is the single entry point for all item sources.
    """
    warnings: List[str] = []

    source = raw.get("source") or source_hint or "unknown"
    title = raw.get("title") or raw.get("headline") or ""
    url = raw.get("url") or raw.get("link") or ""
    summary = raw.get("summary") or raw.get("description") or raw.get("content", "")[:300]
    published_at = raw.get("published_at") or raw.get("pubDate") or raw.get("published") or None

    topic_tags = raw.get("topic_tags") or raw.get("topics") or []
    style_tags = raw.get("style_tags") or raw.get("styles") or []

    if not title:
        warnings.append("missing_title")
        title = "(untitled)"

    if not url:
        warnings.append("missing_url")

    if not topic_tags:
        warnings.append("missing_topic_tags")
        topic_tags = []

    if not style_tags:
        warnings.append("missing_style_tags")
        style_tags = []

    item_id = raw.get("id") or raw.get("item_id") or _stable_item_id(source, title, url)

    normalized = {
        "item_id": item_id,
        "source": source,
        "title": title,
        "url": url,
        "summary": summary,
        "published_at": published_at,
        "topic_tags": topic_tags if isinstance(topic_tags, list) else [],
        "style_tags": style_tags if isinstance(style_tags, list) else [],
        "raw_source_type": raw.get("raw_source_type", "unknown"),
        "raw": raw,  # keep original for debugging
        "warnings": warnings,
    }

    return normalized


def normalize_items(raw_items: List[Dict[str, Any]], *, source_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    """Normalize a list of raw items."""
    return [normalize_item(item, source_hint=source_hint) for item in raw_items]


def validate_normalized_item(item: Dict[str, Any]) -> List[str]:
    """Validate that an item follows the normalized schema.

    Returns a list of error/warning messages. Empty list means valid.
    """
    errors: List[str] = []

    required_fields = ["item_id", "source", "title", "url", "topic_tags", "style_tags"]
    for field in required_fields:
        if field not in item:
            errors.append(f"missing_field:{field}")

    if not isinstance(item.get("topic_tags"), list):
        errors.append("topic_tags_not_list")
    if not isinstance(item.get("style_tags"), list):
        errors.append("style_tags_not_list")

    return errors