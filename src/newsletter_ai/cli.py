"""CLI entrypoint for newsletter-ai v0.2.4S."""

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
        description="newsletter-ai v0.2.4S acceptance fix"
    )
    subparsers = parser.add_subparsers(dest="command")

    # daily
    daily_p = subparsers.add_parser("daily", help="Run daily pipeline")
    daily_p.add_argument("--dry-run", action="store_true")
    daily_p.add_argument("--no-publish", action="store_true")

    # feedback - use a single string argument to avoid parser conflict
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

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()