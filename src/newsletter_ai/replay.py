"""Replay fixture capture for v0.3.14 / v0.3.15

Provides safe capture of RSS fetch results as local replay fixtures.
No secrets, tokens, or auth headers are persisted.

v0.3.15 adds:
- sanitize_replay_xml strips common tracking query params
- validate_replay_pair for integrity checks
- list_replay_fixtures for directory listing
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .rss import parse_rss_xml


# Tracking query params to strip from URLs inside RSS XML
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_replay_xml(xml_text: str) -> tuple[str, int]:
    """Sanitize RSS XML before saving as replay fixture.

    Strips common tracking query parameters from URLs while preserving
    the rest of the XML structure.

    Returns a tuple of (sanitized_xml_text, stripped_count).
    If the XML is unparseable after sanitization, returns the original
    text with stripped_count=0.
    """
    # Regex to find URLs inside XML text content
    # Matches http(s)://... up to whitespace or XML tag boundary
    # Also handles XML-escaped ampersands (&amp;)
    url_pattern = re.compile(r'https?://[^\s<>"\']+')

    stripped_count = 0

    def _strip_tracking_params(match: re.Match) -> str:
        nonlocal stripped_count
        url = match.group(0)
        # Decode XML-escaped ampersands for parsing
        url = url.replace("&amp;", "&")
        # Simple query param stripping
        if "?" not in url:
            return url
        base, query = url.split("?", 1)
        params = query.split("&")
        kept = []
        for p in params:
            if "=" in p:
                key = p.split("=", 1)[0]
                if key in _TRACKING_PARAMS:
                    stripped_count += 1
                    continue
            kept.append(p)
        if not kept:
            return base
        # Re-encode ampersands for XML
        return base + "?" + "&amp;".join(kept)

    sanitized = url_pattern.sub(_strip_tracking_params, xml_text)
    return sanitized, stripped_count


def build_replay_metadata(
    source: Dict[str, Any],
    fetch_result: Any,
    item_count: int,
    *,
    sanitized: bool = False,
    stripped_tracking_params_count: int = 0,
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
        "generated_by": "newsletter-ai/replay v0.3.15",
        "version": "1",
        "sanitized": sanitized,
        "stripped_tracking_params_count": stripped_tracking_params_count,
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

    xml_path.write_text(sanitize_replay_xml(xml_text)[0], encoding="utf-8")
    meta_path.write_text(json.dumps(metadata or {}, indent=2, ensure_ascii=False), encoding="utf-8")

    return xml_path


def load_rss_replay_fixture(path: Path) -> str:
    """Load RSS XML text from a replay fixture file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Replay fixture not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_replay_metadata(metadata: Dict[str, Any]) -> List[str]:
    """Validate replay metadata dict.

    Returns a list of error messages. Empty list means valid.
    """
    errors: List[str] = []
    required = ["source_id", "sha256", "generated_by"]
    for field in required:
        if field not in metadata or not metadata[field]:
            errors.append(f"missing_field:{field}")
    if "item_count" not in metadata:
        errors.append("missing_field:item_count")
    elif not isinstance(metadata["item_count"], int) or metadata["item_count"] < 0:
        errors.append("invalid_item_count")
    return errors


def validate_replay_pair(xml_path: Path, metadata_path: Path) -> Dict[str, Any]:
    """Validate a replay fixture pair (XML + metadata JSON).

    Returns a dict with:
    - valid: bool
    - errors: list of str
    - warnings: list of str
    - metadata: dict (loaded metadata)
    """
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

    if not xml_path.exists():
        errors.append(f"xml_not_found:{xml_path}")
    if not metadata_path.exists():
        errors.append(f"metadata_not_found:{metadata_path}")

    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"metadata_json_error:{exc}")

    meta_errors = validate_replay_metadata(metadata)
    errors.extend(meta_errors)

    if xml_path.exists() and metadata:
        xml_text = xml_path.read_text(encoding="utf-8")
        actual_sha256 = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
        expected_sha256 = metadata.get("sha256")
        if expected_sha256 and actual_sha256 != expected_sha256:
            errors.append("sha256_mismatch")

        try:
            raw_items = parse_rss_xml(xml_text)
            actual_count = len(raw_items)
            expected_count = metadata.get("item_count")
            if expected_count is not None and actual_count != expected_count:
                errors.append(f"item_count_mismatch:expected={expected_count}:actual={actual_count}")
        except Exception as exc:
            warnings.append(f"xml_parse_warning:{exc}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metadata": metadata,
    }


def list_replay_fixtures(replay_dir: Path) -> List[Dict[str, Any]]:
    """List all replay fixtures in a directory.

    Returns a list of dicts with source_id, xml_path, metadata_path,
    item_count, fetched_at, status, warnings/errors.
    """
    replay_dir = Path(replay_dir)
    if not replay_dir.exists():
        return []

    results: List[Dict[str, Any]] = []
    for xml_path in sorted(replay_dir.glob("*.xml")):
        meta_path = xml_path.with_suffix(".json")
        if not meta_path.exists():
            results.append({
                "source_id": xml_path.stem,
                "xml_path": str(xml_path),
                "metadata_path": None,
                "item_count": None,
                "fetched_at": None,
                "status": "missing_metadata",
                "errors": ["metadata_json_missing"],
                "warnings": [],
            })
            continue

        validation = validate_replay_pair(xml_path, meta_path)
        meta = validation["metadata"]
        results.append({
            "source_id": meta.get("source_id", xml_path.stem),
            "xml_path": str(xml_path),
            "metadata_path": str(meta_path),
            "item_count": meta.get("item_count"),
            "fetched_at": meta.get("fetched_at"),
            "status": "valid" if validation["valid"] else "invalid",
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        })

    return results
