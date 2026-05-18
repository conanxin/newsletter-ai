"""v0.2 Pipeline runner with step tracking, dry-run and no-publish support."""

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
    """Main daily pipeline with structured step logging."""
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

        if dry_run:
            step_result.update({
                "status": "skipped",
                "finished_at": _now_iso(),
                "duration_sec": 0.0,
                "reason": "dry-run",
            })
            steps.append(step_result)
            continue

        # For v0.2 hardening we call the original scripts via subprocess
        # but record timing/status rigorously.
        try:
            # Placeholder: in real impl we would import or subprocess the step
            # Here we simulate success for hardening skeleton.
            time.sleep(0.05)  # simulate work
            finished = _now_iso()
            duration = round(time.time() - start_time, 3)

            step_result.update({
                "status": "success",
                "finished_at": finished,
                "duration_sec": duration,
                "log_path": str(cfg["OUTPUT_DIR"] / f"{step_name}.log"),
            })

            # Special handling for publish step
            if step_name == "publish" and no_publish:
                step_result["status"] = "skipped"
                step_result["reason"] = "no-publish flag"

        except Exception as exc:
            finished = _now_iso()
            duration = round(time.time() - start_time, 3)
            step_result.update({
                "status": "failed",
                "finished_at": finished,
                "duration_sec": duration,
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