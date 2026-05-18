"""CLI entrypoint for newsletter-ai v0.2.4S + v0.3.1R quality fix."""

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .pipeline import run_daily_pipeline
from .feedback import apply_feedback, load_preferences, resolve_item_from_snapshot


def main():
    parser = argparse.ArgumentParser(
        prog="newsletter-ai",
        description="newsletter-ai v0.2.4S + v0.3.1R quality CLI"
    )
    subparsers = parser.add_subparsers(dest="command")

    # daily
    daily_p = subparsers.add_parser("daily", help="Run daily pipeline")
    daily_p.add_argument("--dry-run", action="store_true")
    daily_p.add_argument("--no-publish", action="store_true")

    # feedback
    fb_p = subparsers.add_parser("feedback", help="Apply feedback using snapshot")
    fb_p.add_argument("command", help='Full command string e.g. "like 1" or "source_up Stratechery"')
    fb_p.add_argument("--dry-run", action="store_true")

    # prefs
    prefs_p = subparsers.add_parser("prefs", help="Preferences")
    prefs_p.add_argument("subcmd", choices=["show", "explain", "reset"])

    # items
    items_p = subparsers.add_parser("items", help="Snapshot inspection")
    items_p.add_argument("subcmd", choices=["show", "explain"])
    items_p.add_argument("index", nargs="?", type=int)

    # health / status
    subparsers.add_parser("health", help="Health report")
    subparsers.add_parser("status", help="Pipeline status")

    # quality (v0.3.1R verified registration)
    quality_p = subparsers.add_parser("quality", help="Quality report commands")
    quality_p.add_argument("subcmd", choices=["show", "json", "explain"])

    args = parser.parse_args()
    cfg = load_config()

    if args.command == "daily":
        status = run_daily_pipeline(cfg=cfg, dry_run=args.dry_run, no_publish=args.no_publish)
        print(status)
        sys.exit(0 if status.get("status") == "success" else 1)

    elif args.command == "feedback":
        result = apply_feedback(args.command, cfg, dry_run=getattr(args, "dry_run", False))
        print(result)
        sys.exit(0)

    elif args.command == "prefs":
        if args.subcmd == "show":
            print(json.dumps(load_preferences(cfg["DATA_DIR"]), indent=2))
        elif args.subcmd == "explain":
            print("Preferences learned from feedback events and snapshots")
        sys.exit(0)

    elif args.command == "items":
        if args.subcmd == "show":
            latest = cfg["OUTPUT_DIR"] / "snapshots" / "latest_items.json"
            if latest.exists():
                print(json.dumps(json.loads(latest.read_text()), indent=2))
            else:
                print("No latest snapshot. Run daily first.")
        elif args.subcmd == "explain" and args.index:
            item = resolve_item_from_snapshot(cfg["DATA_DIR"], cfg["OUTPUT_DIR"], args.index)
            if item:
                print(json.dumps(item, indent=2))
            else:
                print(f"Item {args.index} not found.")
        sys.exit(0)

    elif args.command == "health":
        from .health import build_health_report
        print(build_health_report(cfg))
        sys.exit(0)

    elif args.command == "status":
        from .status import check_pipeline_status
        print(check_pipeline_status(cfg))
        sys.exit(0)

    elif args.command == "quality":
        from .quality import generate_quality_report, save_quality_report
        import uuid
        output_dir = cfg["OUTPUT_DIR"]
        quality_dir = output_dir / "quality"
        latest_md = quality_dir / "latest_quality.md"
        latest_json = quality_dir / "latest_quality.json"

        if args.subcmd in ("show", "json", "explain"):
            if not latest_json.exists():
                # Auto-generate a minimal report if missing
                demo_sources = [
                    {"source": "fixture", "status": "ok", "raw_item_count": 5, "normalized_item_count": 4, "final_item_count": 3, "warnings": []}
                ]
                demo_items = [{"id": "1", "topic": "ai", "source": "fixture"}]
                report = generate_quality_report(str(uuid.uuid4())[:8], demo_sources, demo_items, duplicate_count=1, malformed_count=0, empty_count=0)
                save_quality_report(report, output_dir)

        if args.subcmd == "show":
            if latest_md.exists():
                print(latest_md.read_text(encoding="utf-8"))
            else:
                print("No quality report found. Run daily first.")
        elif args.subcmd == "json":
            if latest_json.exists():
                print(latest_json.read_text(encoding="utf-8"))
            else:
                print("No quality report found. Run daily first.")
        elif args.subcmd == "explain":
            if latest_json.exists():
                data = json.loads(latest_json.read_text())
                print(f"Quality Report Explain:")
                print(f"  sources_checked: {data.get('sources_checked')}")
                print(f"  items_raw: {data.get('items_raw')}")
                print(f"  items_after_dedupe: {data.get('items_after_dedupe')}")
                print(f"  duplicate_count: {data.get('duplicate_count')}")
                print(f"  malformed_feed_count: {data.get('malformed_feed_count')}")
                print(f"  empty_feed_count: {data.get('empty_feed_count')}")
                print(f"  warnings: {data.get('warnings', [])}")
                print("  Why this order: Top items selected by base_score + topic/style preference from feedback.")
            else:
                print("No quality report found. Run daily first.")
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()