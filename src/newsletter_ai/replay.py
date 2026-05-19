"""Replay fixture capture for v0.3.14

Provides safe capture of RSS fetch results as local replay fixtures.
No secrets, tokens, or auth headers are persisted.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_replay_xml(xml_text: str) -> str:
    """Sanitize RSS XML before saving as replay fixture.

    Currently a no-op that preserves original RSS content.
    Future: could strip tracking query params from URLs.
    """
    return xml_text


def build_replay_metadata(
    source: Dict[str, Any],
    fetch_result: Any,
    item_count: int,
) -> Dict[str, Any]:
    """Build metadata dict for a replay fixture.

    Does NOT include auth headers, cookies, or tokens.
    """
    xml_text = getattr(fetch_result, "text", "") or ""
    sha256 = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()

    return {
        "source_id": source.get("source_id", "unknown"),
        "name": source.get("name", ""),
        "url": source.get("url", ""),
        "fetched_at": getattr(fetch_result, "fetched_at", _now_iso()),
        "status_code": getattr(fetch_result, "status_code", None),
        "item_count": item_count,
        "sha256": sha256,
        "generated_by": "newsletter-ai/replay v0.3.14",
        "version": "1",
    }


def save_rss_replay_fixture(
    source_id: str,
    xml_text: str,
    *,
    output_dir: Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save RSS XML and metadata as a replay fixture pair.

    Returns the path to the saved XML file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"rss_{source_id}_{timestamp}"

    xml_path = output_dir / f"{base_name}.xml"
    meta_path = output_dir / f"{base_name}.json"

    xml_path.write_text(sanitize_replay_xml(xml_text), encoding="utf-8")
    meta_path.write_text(json.dumps(metadata or {}, indent=2, ensure_ascii=False), encoding="utf-8")

    return xml_path


def load_rss_replay_fixture(path: Path) -> str:
    """Load RSS XML text from a replay fixture file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Replay fixture not found: {path}")
    return path.read_text(encoding="utf-8")
