"""Source Registry + Offline Ingestion Bridge (v0.3.12)

This module provides a source registry and offline ingestion bridge
for newsletter-ai. It reads a local source registry JSON file,
parses RSS fixture sources, normalizes items, and returns them
for use in the pipeline.

v0.3.12 adds controlled real RSS fetch support via rss_url sources.
Network requests are only made when explicitly allowed.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .normalize import normalize_items
from .rss import parse_rss_file, parse_rss_xml


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

    source_type = source.get("type")
    if source_type == "rss_fixture" and not source.get("fixture_path"):
        errors.append("missing_fixture_path")
    if source_type == "rss_url" and not source.get("url"):
        errors.append("missing_url")

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


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ingest_sources_with_report(
    sources: List[Dict[str, Any]],
    *,
    base_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
    allow_network: bool = False,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ingest items from sources with per-source reporting.

    Supports both rss_fixture (offline) and rss_url (network, opt-in).

    Returns a dict with:
    - items: flat list of normalized items
    - report: ingestion report dict
    """
    from .fetch import fetch_rss_url_source

    base_dir = base_dir or Path(__file__).parent.parent.parent
    all_items: List[Dict[str, Any]] = []
    source_reports: List[Dict[str, Any]] = []

    total = len(sources)
    enabled = enabled_sources(sources)
    disabled = [s for s in sources if not s.get("enabled", True)]

    success_count = 0
    failed_count = 0
    empty_count = 0
    skipped_network_count = 0

    for source in sources:
        source_id = source.get("source_id", "unknown")
        source_name = source.get("name", source_id)
        source_type = source.get("type", "unknown")
        enabled_flag = source.get("enabled", True)
        topic_hints = source.get("topic_hints", [])
        style_hints = source.get("style_hints", [])

        if not enabled_flag:
            source_reports.append({
                "source_id": source_id,
                "name": source_name,
                "type": source_type,
                "enabled": False,
                "status": "disabled",
                "fixture_path": source.get("fixture_path"),
                "url": source.get("url"),
                "item_count_raw": 0,
                "item_count_normalized": 0,
                "warnings": [],
                "errors": [],
                "network_allowed": False,
            })
            continue

        start_time = time.time()
        status = "success"
        errors: List[str] = []
        warnings: List[str] = []
        raw_items: List[Dict[str, Any]] = []
        normalized_items: List[Dict[str, Any]] = []
        fetch_status: Optional[str] = None
        http_status_code: Optional[int] = None
        from_cache_flag: bool = False

        try:
            if source_type == "rss_fixture":
                fixture_path = source.get("fixture_path")
                if not fixture_path:
                    status = "failed"
                    errors.append("missing_fixture_path")
                else:
                    full_path = base_dir / fixture_path
                    if not full_path.exists():
                        status = "failed"
                        errors.append(f"fixture_not_found: {full_path}")
                    else:
                        raw_items = parse_rss_file(full_path)
                        if not raw_items:
                            status = "empty"
                            warnings.append("no_items_parsed")
                        else:
                            for raw in raw_items:
                                raw["source_id"] = source_id
                                raw["source_name"] = source_name
                                if topic_hints and not raw.get("topic_tags"):
                                    raw["topic_tags"] = topic_hints
                                if style_hints and not raw.get("style_tags"):
                                    raw["style_tags"] = style_hints

                            normalized_items = normalize_items(raw_items, source_hint=source_id)
                            if not normalized_items:
                                status = "empty"
                                warnings.append("all_items_filtered_during_normalization")
                            else:
                                all_items.extend(normalized_items)
                                success_count += 1

            elif source_type == "rss_url":
                fetch_result = fetch_rss_url_source(
                    source, allow_network=allow_network, cache_dir=cache_dir
                )
                fetch_status = "success" if fetch_result.ok else "failed"
                http_status_code = fetch_result.status_code
                from_cache_flag = fetch_result.from_cache

                if not allow_network:
                    status = "skipped"
                    warnings.append("network_disabled: use --allow-network to fetch")
                    skipped_network_count += 1
                elif not fetch_result.ok:
                    status = "failed"
                    errors.append(fetch_result.error or "fetch_failed")
                else:
                    raw_items = parse_rss_xml(fetch_result.text)
                    if not raw_items:
                        status = "empty"
                        warnings.append("no_items_parsed")
                    else:
                        for raw in raw_items:
                            raw["source_id"] = source_id
                            raw["source_name"] = source_name
                            if topic_hints and not raw.get("topic_tags"):
                                raw["topic_tags"] = topic_hints
                            if style_hints and not raw.get("style_tags"):
                                raw["style_tags"] = style_hints

                        normalized_items = normalize_items(raw_items, source_hint=source_id)
                        if not normalized_items:
                            status = "empty"
                            warnings.append("all_items_filtered_during_normalization")
                        else:
                            all_items.extend(normalized_items)
                            success_count += 1
            else:
                status = "failed"
                errors.append(f"unsupported_source_type: {source_type}")

        except Exception as exc:
            status = "failed"
            errors.append(str(exc))

        if status == "failed":
            failed_count += 1
        elif status == "empty":
            empty_count += 1

        source_reports.append({
            "source_id": source_id,
            "name": source_name,
            "type": source_type,
            "enabled": True,
            "status": status,
            "fixture_path": source.get("fixture_path"),
            "url": source.get("url"),
            "item_count_raw": len(raw_items),
            "item_count_normalized": len(normalized_items),
            "warnings": warnings,
            "errors": errors,
            "duration_sec": round(time.time() - start_time, 3),
            "topic_hints": topic_hints,
            "style_hints": style_hints,
            "fetch_status": fetch_status,
            "http_status_code": http_status_code,
            "from_cache": from_cache_flag,
            "network_allowed": allow_network,
        })

    report = {
        "run_id": run_id or _now_iso(),
        "created_at": _now_iso(),
        "input_mode": "source_registry",
        "registry_path": str(base_dir / "data" / "fixtures" / "source_registry.json"),
        "source_count_total": total,
        "source_count_enabled": len(enabled),
        "source_count_disabled": len(disabled),
        "source_count_success": success_count,
        "source_count_failed": failed_count,
        "source_count_empty": empty_count,
        "source_count_skipped_network": skipped_network_count,
        "total_items": len(all_items),
        "sources": source_reports,
    }

    return {"items": all_items, "report": report}


def ingest_offline_sources_with_report(
    sources: List[Dict[str, Any]],
    *,
    base_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Ingest items from offline sources with per-source reporting (backward-compatible).

    Returns a dict with:
    - items: flat list of normalized items
    - report: ingestion report dict
    """
    return ingest_sources_with_report(
        sources, base_dir=base_dir, run_id=run_id, allow_network=False
    )


def ingest_offline_sources(
    sources: List[Dict[str, Any]],
    *,
    base_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Ingest items from offline sources (backward-compatible).

    Returns a flat list of normalized items.
    """
    result = ingest_sources_with_report(sources, base_dir=base_dir, allow_network=False)
    return result["items"]
