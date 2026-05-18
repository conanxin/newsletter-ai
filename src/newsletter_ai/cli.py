"""CLI entrypoint for newsletter-ai v0.2.2."""

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .pipeline import run_daily_pipeline
from .feedback import apply_feedback, load_preferences


def main():
    parser = argparse.ArgumentParser(
        prog="newsletter-ai",
        description="newsletter-ai v0.2.2 local daily pipeline + feedback engine"
    )
    subparsers = parser.add_subparsers(dest="command")

    # daily
    daily_p = subparsers.add_parser("daily", help="Run daily pipeline")
    daily_p.add_argument("--dry-run", action="store_true", help="Plan only, no publish")
    daily_p.add_argument("--no-publish", action="store_true", help="Generate but skip Telegram")

    # feedback
    fb_p = subparsers.add_parser("feedback", help="Apply feedback (like 1, source_up xxx, etc.)")
    fb_p.add_argument("command", help='e.g. "like 1" or "source_up Stratechery --note ..."')
    fb_p.add_argument("--dry-run", action="store_true")

    # prefs
    prefs_p = subparsers.add_parser("prefs", help="Preferences commands")
    prefs_p.add_argument("subcmd", choices=["show", "explain", "reset"])

    # health / status
    subparsers.add_parser("health", help="Print health report")
    subparsers.add_parser("status", help="Show last pipeline status")

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
            prefs = load_preferences(cfg["DATA_DIR"])
            print(json.dumps(prefs, indent=2, ensure_ascii=False))
        elif args.subcmd == "explain":
            print("Preferences explain: source/topic/style weights learned from feedback")
        elif args.subcmd == "reset":
            print("[DRY-RUN] would reset preferences (not implemented)")
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