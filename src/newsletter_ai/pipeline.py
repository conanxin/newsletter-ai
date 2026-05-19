"""v0.2.4S Pipeline runner with full dry-run snapshot support."""

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
    no_publish: bool = False
) -> Dict[str, Any]:
    """Main daily pipeline with structured step logging and dry-run snapshot support."""
    if cfg is None:
        cfg = load_config()

    steps: List[Dict[str, Any]] = []
    overall_status = "success"
    failed_step = None

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

        step_result = {
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
                    try:
                        raw_items = load_dry_run_items()
                    except FileNotFoundError:
                        raw_items = [
                            {"id": "1", "source": "techcrunch", "title": "AI Breakthrough", "base_score": 0.65, "topic_tags": ["ai"], "style_tags": ["analysis"]},
                            {"id": "2", "source": "stratechery", "title": "Deep Tech Analysis", "base_score": 0.72, "topic_tags": ["tech"], "style_tags": ["essay"]},
                        ]
                    normalized_items = [normalize_fixture_item(item) for item in raw_items]
                    ranked = rank_items(normalized_items, cfg)
                    step_result.update({
                        "status": "success",
                        "finished_at": _now_iso(),
                        "duration_sec": round(time.time() - start_time, 3),
                        "ranked_count": len(ranked),
                    })

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

                    step_result.update({
                        "status": "success",
                        "finished_at": _now_iso(),
                        "duration_sec": round(time.time() - start_time, 3),
                        "snapshot": snap,
                        "section_count": len(sections),
                        "markdown_digest": md_digest[:200] + "..." if len(md_digest) > 200 else md_digest,
                        "telegram_digest": tg_digest[:200] + "..." if len(tg_digest) > 200 else tg_digest,
                    })

                else:  # fetch
                    step_result.update({
                        "status": "success",
                        "finished_at": _now_iso(),
                        "duration_sec": 0.01,
                        "reason": "dry-run fixture",
                    })

            except Exception as exc:
                step_result.update({
                    "status": "failed",
                    "error": str(exc),
                })
                overall_status = "failed"
                failed_step = step_name

            steps.append(step_result)
            continue

        # Normal non-dry-run path (simplified for v0.2.4S)
        if dry_run:
            step_result.update({
                "status": "skipped",
                "finished_at": _now_iso(),
                "duration_sec": 0.0,
                "reason": "dry-run",
            })
            steps.append(step_result)
            continue

        # Real execution path (placeholder)
        try:
            time.sleep(0.02)
            finished = _now_iso()
            duration = round(time.time() - start_time, 3)

            step_result.update({
                "status": "success",
                "finished_at": finished,
                "duration_sec": duration,
                "log_path": str(cfg["OUTPUT_DIR"] / f"{step_name}.log"),
            })

            if step_name == "publish" and no_publish:
                step_result["status"] = "skipped"
                step_result["reason"] = "no-publish flag"

        except Exception as exc:
            step_result.update({
                "status": "failed",
                "error": str(exc),
            })
            overall_status = "failed"
            failed_step = step_name

        steps.append(step_result)
        if overall_status == "failed":
            break

    final_status = {
        "pipeline": "daily",
        "status": overall_status,
        "started_at": steps[0]["started_at"] if steps else _now_iso(),
        "finished_at": _now_iso(),
        "steps": steps,
        "failed_step": failed_step,
        "dry_run": dry_run,
        "no_publish": no_publish,
    }

    _write_last_run_status(final_status, cfg)
    return final_status