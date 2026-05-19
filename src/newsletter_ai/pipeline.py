"""v0.2.4S Pipeline runner with full dry-run snapshot support + v0.3.10 source registry mode + v0.3.11 ingestion report."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import load_config


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _write_last_run_status(status: Dict[str, Any], cfg: Dict) -> None:
    out_dir = cfg["OUTPUT_DIR"]
    out_dir.mkdir(parents=True, exist_ok=True)
    status_file = out_dir / "state" / "last-run-status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False))


def run_daily_pipeline(
    cfg: Optional[Dict] = None,
    dry_run: bool = False,
    no_publish: bool = False,
    source_registry: Optional[Path] = None,
) -> Dict[str, Any]:
    """Main daily pipeline with structured step logging and dry-run snapshot support.

    Args:
        source_registry: Optional path to a source registry JSON file.
                         When provided and dry_run is True, pipeline reads
                         enabled rss_fixture sources instead of default dry_run_items.json.
    """
    if cfg is None:
        cfg = load_config()

    steps: List[Dict[str, Any]] = []
    overall_status = "success"
    failed_step = None
    input_mode = "fixture_json"
    source_count = 0
    item_count = 0
    ingestion_report: Optional[Dict[str, Any]] = None

    pipeline_steps = [
        ("fetch", "scripts/fetch_rss_minimal.py"),
        ("rank", "scripts/rank_items.py"),
        ("digest", "scripts/build_digest_minimal.py"),
        ("health", "scripts/build_health_report.py"),
        ("publish", "scripts/publish_m1.py"),
    ]

    for step_name, script in pipeline_steps:
        started = _now_iso()
        start_time = time.time()

        step_result: Dict[str, Any] = {
            "name": step_name,
            "command": script,
            "started_at": started,
            "status": "running",
        }

        # For dry-run we still want to execute ranking + snapshot to make items show / feedback work
        if dry_run and step_name in ("fetch", "rank", "digest"):
            try:
                if step_name == "rank":
                    from .ranking import rank_items
                    from .fixtures import load_dry_run_items, normalize_fixture_item
                    from .sources import load_source_registry, validate_source_registry, enabled_sources, ingest_offline_sources_with_report

                    if source_registry is not None and source_registry.exists():
                        # v0.3.10: controlled offline source registry mode
                        registry_sources = load_source_registry(source_registry)
                        validation = validate_source_registry(registry_sources)
                        if not validation["valid"]:
                            raise ValueError(f"Source registry invalid: {validation['errors']}")

                        result = ingest_offline_sources_with_report(registry_sources)
                        raw_items = result["items"]
                        ingestion_report = result["report"]
                        input_mode = "source_registry"
                        source_count = ingestion_report["source_count_enabled"]
                        item_count = len(raw_items)
                        normalized_items = raw_items

                        # v0.3.11: if all enabled sources failed, pipeline should fail gracefully
                        if ingestion_report["source_count_success"] == 0 and ingestion_report["source_count_enabled"] > 0:
                            step_result["status"] = "failed"
                            step_result["finished_at"] = _now_iso()
                            step_result["duration_sec"] = round(time.time() - start_time, 3)
                            step_result["error"] = "All enabled sources failed ingestion"
                            step_result["ingestion_report_summary"] = {
                                "source_count_total": ingestion_report["source_count_total"],
                                "source_count_enabled": ingestion_report["source_count_enabled"],
                                "source_count_success": ingestion_report["source_count_success"],
                                "source_count_failed": ingestion_report["source_count_failed"],
                                "total_items": ingestion_report["total_items"],
                            }
                            overall_status = "failed"
                            failed_step = step_name
                            steps.append(step_result)
                            continue
                    else:
                        # Default v0.3.6 dry-run fixture mode
                        try:
                            raw_items = load_dry_run_items()
                        except FileNotFoundError:
                            raw_items = [
                                {"id": "1", "source": "techcrunch", "title": "AI Breakthrough", "base_score": 0.65, "topic_tags": ["ai"], "style_tags": ["analysis"]},
                                {"id": "2", "source": "stratechery", "title": "Deep Tech Analysis", "base_score": 0.72, "topic_tags": ["tech"], "style_tags": ["essay"]},
                            ]
                        normalized_items = [normalize_fixture_item(item) for item in raw_items]
                        item_count = len(normalized_items)

                    ranked = rank_items(normalized_items, cfg)
                    cfg["_ranked_items"] = ranked
                    step_result["status"] = "success"
                    step_result["finished_at"] = _now_iso()
                    step_result["duration_sec"] = round(time.time() - start_time, 3)
                    step_result["ranked_count"] = len(ranked)

                    # v0.3.11: attach ingestion report summary to rank step
                    if ingestion_report is not None:
                        step_result["ingestion_report_summary"] = {
                            "source_count_total": ingestion_report["source_count_total"],
                            "source_count_enabled": ingestion_report["source_count_enabled"],
                            "source_count_success": ingestion_report["source_count_success"],
                            "source_count_failed": ingestion_report["source_count_failed"],
                            "source_count_empty": ingestion_report["source_count_empty"],
                            "total_items": ingestion_report["total_items"],
                            "failed_source_ids": [
                                s["source_id"] for s in ingestion_report["sources"]
                                if s.get("status") == "failed"
                            ],
                        }

                elif step_name == "digest":
                    from .snapshot import create_item_snapshot
                    from .sections import group_items_into_sections
                    from .render import render_markdown_digest, render_telegram_digest

                    ranked_items = cfg.get("_ranked_items", [])
                    if not ranked_items:
                        from .fixtures import load_dry_run_items, normalize_fixture_item
                        raw = load_dry_run_items()
                        ranked_items = [normalize_fixture_item(i) for i in raw]
                    snap = create_item_snapshot(
                        ranked_items,
                        cfg["OUTPUT_DIR"],
                        cfg["DATA_DIR"],
                        run_id=started
                    )

                    # v0.3.3: sectioning after snapshot (global index preserved)
                    sections = group_items_into_sections(ranked_items)
                    md_digest = render_markdown_digest(sections)
                    tg_digest = render_telegram_digest(sections)

                    step_result["status"] = "success"
                    step_result["finished_at"] = _now_iso()
                    step_result["duration_sec"] = round(time.time() - start_time, 3)
                    step_result["snapshot"] = snap
                    step_result["section_count"] = len(sections)
                    step_result["markdown_digest"] = md_digest[:200] + "..." if len(md_digest) > 200 else md_digest
                    step_result["telegram_digest"] = tg_digest[:200] + "..." if len(tg_digest) > 200 else tg_digest

                else:  # fetch
                    step_result["status"] = "success"
                    step_result["finished_at"] = _now_iso()
                    step_result["duration_sec"] = 0.01
                    step_result["reason"] = "dry-run fixture"

            except Exception as exc:
                step_result["status"] = "failed"
                step_result["error"] = str(exc)
                overall_status = "failed"
                failed_step = step_name

            steps.append(step_result)
            continue

        # Normal non-dry-run path (simplified for v0.2.4S)
        if dry_run:
            step_result["status"] = "skipped"
            step_result["finished_at"] = _now_iso()
            step_result["duration_sec"] = 0.0
            step_result["reason"] = "dry-run"
            steps.append(step_result)
            continue

        # Real execution path (placeholder)
        try:
            time.sleep(0.02)
            finished = _now_iso()
            duration = round(time.time() - start_time, 3)

            step_result["status"] = "success"
            step_result["finished_at"] = finished
            step_result["duration_sec"] = duration
            step_result["log_path"] = str(cfg["OUTPUT_DIR"] / f"{step_name}.log")

            if step_name == "publish" and no_publish:
                step_result["status"] = "skipped"
                step_result["reason"] = "no-publish flag"

        except Exception as exc:
            step_result["status"] = "failed"
            step_result["error"] = str(exc)
            overall_status = "failed"
            failed_step = step_name

        steps.append(step_result)
        if overall_status == "failed":
            break

    final_status: Dict[str, Any] = {
        "pipeline": "daily",
        "status": overall_status,
        "started_at": steps[0]["started_at"] if steps else _now_iso(),
        "finished_at": _now_iso(),
        "steps": steps,
        "failed_step": failed_step,
        "dry_run": dry_run,
        "no_publish": no_publish,
        "input_mode": input_mode,
        "source_count": source_count,
        "item_count": item_count,
    }

    # v0.3.11: include ingestion report summary in last-run-status
    if ingestion_report is not None:
        final_status["ingestion_report"] = {
            "source_count_total": ingestion_report["source_count_total"],
            "source_count_enabled": ingestion_report["source_count_enabled"],
            "source_count_disabled": ingestion_report["source_count_disabled"],
            "source_count_success": ingestion_report["source_count_success"],
            "source_count_failed": ingestion_report["source_count_failed"],
            "source_count_empty": ingestion_report["source_count_empty"],
            "total_items": ingestion_report["total_items"],
            "failed_source_ids": [
                s["source_id"] for s in ingestion_report["sources"]
                if s.get("status") == "failed"
            ],
        }

    _write_last_run_status(final_status, cfg)
    return final_status
