"""v0.2.4S Pipeline runner with full dry-run snapshot support + v0.3.10 source registry mode + v0.3.11 ingestion report + v0.3.19 run artifact index."""

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


def _write_run_index(final_status: Dict[str, Any], cfg: Dict) -> None:
    """v0.3.19: Write run record to output/runs/ and update index."""
    from .runs import make_run_record, append_run_record

    started = final_status.get("started_at", _now_iso())
    steps = final_status.get("steps", [])
    digest_step = [s for s in steps if s.get("name") == "digest"]
    rank_step = [s for s in steps if s.get("name") == "rank"]

    snapshot_path = None
    digest_path = None
    telegram_path = None
    quality_report_path = final_status.get("quality_report_path")
    section_count = 0

    if digest_step:
        snap = digest_step[0].get("snapshot", {})
        snapshot_path = Path(snap["latest"]) if snap.get("latest") else None
        section_count = digest_step[0].get("section_count", 0)

    ingestion_summary = None
    if final_status.get("ingestion_report"):
        ir = final_status["ingestion_report"]
        ingestion_summary = {
            "source_count_total": ir.get("source_count_total", 0),
            "source_count_enabled": ir.get("source_count_enabled", 0),
            "source_count_success": ir.get("source_count_success", 0),
            "source_count_failed": ir.get("source_count_failed", 0),
            "total_items": ir.get("total_items", 0),
        }

    warnings = []
    errors = []
    if final_status.get("failed_step"):
        errors.append(f"Failed step: {final_status['failed_step']}")
    for s in steps:
        if s.get("status") == "failed" and s.get("error"):
            errors.append(f"{s['name']}: {s['error']}")
        if s.get("warnings"):
            warnings.extend(s["warnings"])

    base_dir = cfg.get("BASE_DIR", cfg["OUTPUT_DIR"].parent)
    last_run_status_path = cfg["OUTPUT_DIR"] / "state" / "last-run-status.json"

    record = make_run_record(
        run_id=started,
        created_at=started,
        status=final_status.get("status", "unknown"),
        input_mode=final_status.get("input_mode", "unknown"),
        output_dir=cfg["OUTPUT_DIR"],
        base_dir=base_dir,
        item_count=final_status.get("item_count", 0),
        section_count=section_count,
        source_count=final_status.get("source_count", 0),
        source_registry_path=final_status.get("source_registry_path"),
        snapshot_path=snapshot_path,
        digest_path=digest_path,
        telegram_path=telegram_path,
        quality_report_path=Path(quality_report_path) if quality_report_path else None,
        last_run_status_path=last_run_status_path,
        ingestion_report_summary=ingestion_summary,
        warnings=warnings or None,
        errors=errors or None,
    )

    record_path = append_run_record(record, cfg["OUTPUT_DIR"], base_dir)
    final_status["run_record_path"] = str(record_path)


def run_daily_pipeline(
    cfg: Optional[Dict] = None,
    dry_run: bool = False,
    no_publish: bool = False,
    source_registry: Optional[Path] = None,
    allow_network: bool = False,
) -> Dict[str, Any]:
    """Main daily pipeline with structured step logging and dry-run snapshot support.

    Args:
        source_registry: Optional path to a source registry JSON file.
                         When provided and dry_run is True, pipeline reads
                         enabled rss_fixture sources instead of default dry_run_items.json.
        allow_network: If True, allows rss_url sources to perform real network requests.
                       Only effective when source_registry is provided.
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
                    from .sources import load_source_registry, validate_source_registry, enabled_sources, ingest_sources_with_report

                    if source_registry is not None and source_registry.exists():
                        # v0.3.12: controlled source registry mode with optional network
                        registry_sources = load_source_registry(source_registry)
                        validation = validate_source_registry(registry_sources)
                        if not validation["valid"]:
                            raise ValueError(f"Source registry invalid: {validation['errors']}")

                        result = ingest_sources_with_report(registry_sources, allow_network=allow_network)
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
                    # Ensure item_count reflects what was actually ranked
                    item_count = len(ranked)

                    # v0.3.11: attach ingestion report summary to rank step
                    if ingestion_report is not None:
                        step_result["ingestion_report_summary"] = {
                            "source_count_total": ingestion_report["source_count_total"],
                            "source_count_enabled": ingestion_report["source_count_enabled"],
                            "source_count_success": ingestion_report["source_count_success"],
                            "source_count_failed": ingestion_report["source_count_failed"],
                            "source_count_empty": ingestion_report["source_count_empty"],
                            "source_count_skipped_network": ingestion_report.get("source_count_skipped_network", 0),
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
                    from .quality import generate_quality_report, save_quality_report

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

                    # v0.3.18: generate current-run quality report
                    try:
                        # Build source info from ingestion report or fallback
                        source_infos = []
                        if ingestion_report is not None:
                            for s in ingestion_report.get("sources", []):
                                source_infos.append({
                                    "source": s.get("source_id", "unknown"),
                                    "feed_path": s.get("fixture_path", s.get("url", "")),
                                    "status": s.get("status", "ok"),
                                    "raw_item_count": s.get("item_count_raw", 0),
                                    "normalized_item_count": s.get("item_count_normalized", 0),
                                    "final_item_count": s.get("item_count_normalized", 0),
                                    "warnings": s.get("warnings", []),
                                })
                        else:
                            # Fallback for default fixture mode
                            source_infos = [
                                {"source": "fixture", "status": "ok", "raw_item_count": len(ranked_items), "normalized_item_count": len(ranked_items), "final_item_count": len(ranked_items), "warnings": []}
                            ]

                        quality_report = generate_quality_report(
                            run_id=started,
                            sources=source_infos,
                            items_after_dedupe=ranked_items,
                            duplicate_count=0,
                            malformed_count=0,
                            empty_count=0,
                        )
                        quality_paths = save_quality_report(quality_report, cfg["OUTPUT_DIR"])
                        step_result["quality_report_path"] = str(quality_paths["json"])
                    except Exception as qexc:
                        step_result["quality_report_error"] = str(qexc)

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

    # v0.3.18: record quality report path if generated
    digest_step = [s for s in steps if s.get("name") == "digest"]
    if digest_step and digest_step[0].get("quality_report_path"):
        final_status["quality_report_path"] = digest_step[0]["quality_report_path"]

    # v0.3.19: write run artifact index
    _write_run_index(final_status, cfg)

    _write_last_run_status(final_status, cfg)
    return final_status
