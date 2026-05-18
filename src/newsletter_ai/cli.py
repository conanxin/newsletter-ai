"""CLI entrypoint for newsletter-ai v0.2."""

import argparse
import sys
from pathlib import Path

from .config import load_config
from .pipeline import run_daily_pipeline


def main():
    parser = argparse.ArgumentParser(
        prog="newsletter-ai",
        description="newsletter-ai v0.2 local daily pipeline"
    )
    subparsers = parser.add_subparsers(dest="command")

    # daily
    daily_p = subparsers.add_parser("daily", help="Run daily pipeline")
    daily_p.add_argument("--dry-run", action="store_true", help="Plan only, no publish")
    daily_p.add_argument("--no-publish", action="store_true", help="Generate but skip Telegram")

    # feedback
    fb_p = subparsers.add_parser("feedback", help="Apply feedback command")
    fb_p.add_argument("command", help='e.g. "like 1" or "source_up example.com"')

    # health
    subparsers.add_parser("health", help="Print health report")

    # status
    subparsers.add_parser("status", help="Show last pipeline status")

    args = parser.parse_args()

    cfg = load_config()

    if args.command == "daily":
        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=args.dry_run,
            no_publish=args.no_publish
        )
        print(status)
        sys.exit(0 if status.get("status") == "success" else 1)

    elif args.command == "feedback":
        from .feedback import apply_feedback
        result = apply_feedback(args.command, cfg)
        print(result)
        sys.exit(0)

    elif args.command == "health":
        from .health import build_health_report
        report = build_health_report(cfg)
        print(report)
        sys.exit(0)

    elif args.command == "status":
        from .status import check_pipeline_status
        status = check_pipeline_status(cfg)
        print(status)
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()