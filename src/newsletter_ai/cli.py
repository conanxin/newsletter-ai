"""CLI entrypoint for newsletter-ai v0.2.4S + v0.3.1R quality fix + v0.3.4 section quality + v0.3.9 source registry + v0.3.10 controlled offline source pipeline + v0.3.11 source ingestion report + v0.3.12 controlled real RSS fetch."""

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
        description="newsletter-ai v0.2.4S + v0.3.1R quality CLI + v0.3.4 section quality + v0.3.9 source registry + v0.3.10 controlled offline source pipeline + v0.3.11 source ingestion report + v0.3.12 controlled real RSS fetch"
    )
    subparsers = parser.add_subparsers(dest="command")

    # daily (v0.3.10: added --source-registry; v0.3.12: added --allow-network)
    daily_p = subparsers.add_parser("daily", help="Run daily pipeline")
    daily_p.add_argument("--dry-run", action="store_true")
    daily_p.add_argument("--no-publish", action="store_true")
    daily_p.add_argument(
        "--source-registry",
        type=Path,
        default=None,
        help="Path to source registry JSON (only with --dry-run or --no-publish)."
    )
    daily_p.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow real network requests for rss_url sources (requires --dry-run or --no-publish)."
    )

    # feedback (v0.3.13: hardened parser)
    fb_p = subparsers.add_parser("feedback", help="Apply feedback using snapshot")
    fb_p.add_argument("tokens", nargs="*", help="Feedback tokens: like 1, source_up Stratechery, save 2 --note ...")
    fb_p.add_argument("--dry-run", action="store_true")
    fb_p.add_argument("--note", default=None, help="Optional note for save action")

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

    # quality (v0.3.4: added "sections")
    quality_p = subparsers.add_parser("quality", help="Quality report commands")
    quality_p.add_argument("subcmd", choices=["show", "json", "explain", "sources", "duplicates", "sections"])

    # sources (v0.3.9, v0.3.11: added "report"; v0.3.12: added "fetch"; v0.3.14: added "capture-replay")
    sources_p = subparsers.add_parser("sources", help="Source registry commands")
    sources_p.add_argument("subcmd", choices=["list", "validate", "ingest-fixtures", "report", "fetch"])
    sources_p.add_argument("--registry", type=Path, default=None, help="Path to source registry JSON")
    sources_p.add_argument("--allow-network", action="store_true", help="Allow real network requests for rss_url sources")
    sources_p.add_argument("--capture-replay", action="store_true", help="Save successful rss_url fetches as replay fixtures (requires --allow-network)")
    sources_p.add_argument("--replay-dir", type=Path, default=None, help="Directory for replay fixtures (default: data/fixtures/replay)")
    sources_p.add_argument("--source-id", default=None, help="Only process the specified source_id")

    # replay (v0.3.15: governance)
    replay_p = subparsers.add_parser("replay", help="Replay fixture governance commands")
    replay_p.add_argument("subcmd", choices=["list", "inspect", "validate", "promote"])
    replay_p.add_argument("path", nargs="?", help="Path to replay XML for inspect, or xml_path for promote")
    replay_p.add_argument("--replay-dir", type=Path, default=None, help="Directory for replay fixtures (default: data/fixtures/replay)")
    replay_p.add_argument("--source-id", default=None, help="Source ID for promote")
    replay_p.add_argument("--name", default=None, help="Source name for promote")

    args = parser.parse_args()
    cfg = load_config()

    if args.command == "daily":
        # v0.3.10: --source-registry only allowed with --dry-run or --no-publish
        source_registry = getattr(args, "source_registry", None)
        if source_registry is not None and not (args.dry_run or args.no_publish):
            print("Error: --source-registry requires --dry-run or --no-publish")
            sys.exit(1)

        # v0.3.12: --allow-network only allowed with --dry-run or --no-publish
        allow_network = getattr(args, "allow_network", False)
        if allow_network and not (args.dry_run or args.no_publish):
            print("Error: --allow-network requires --dry-run or --no-publish")
            sys.exit(1)

        if source_registry is not None and not source_registry.exists():
            print(f"Error: Source registry not found: {source_registry}")
            sys.exit(1)

        status = run_daily_pipeline(
            cfg=cfg,
            dry_run=args.dry_run,
            no_publish=args.no_publish,
            source_registry=source_registry,
            allow_network=allow_network,
        )
        print(status)
        sys.exit(0 if status.get("status") == "success" else 1)

    elif args.command == "feedback":
        tokens = getattr(args, "tokens", [])
        note = getattr(args, "note", None)

        # Normalize: join tokens and re-split to handle both quoted strings and token lists
        raw = " ".join(tokens).strip()

        # v0.3.13R: extract --note from inside quoted string if present
        # This handles: feedback "save 2 --note 值得深挖" --dry-run
        if "--note" in raw and note is None:
            note_parts = raw.split("--note", 1)
            if len(note_parts) == 2:
                raw = note_parts[0].strip()
                note = note_parts[1].strip()

        if not raw:
            print("ERROR: empty feedback command")
            print("Usage: newsletter-ai feedback <action> [<index>|<source>] [--note <text>] [--dry-run]")
            sys.exit(1)

        # Parse action and remaining args
        parts = raw.split()
        action = parts[0]

        # Known actions that take an index
        index_actions = {"like", "dislike", "save", "skip", "explain"}
        # Known actions that take a source/topic/style name
        name_actions = {"source_up", "source_down", "topic_up", "topic_down", "style_up", "style_down"}

        if action not in index_actions and action not in name_actions:
            print(f"ERROR: unknown feedback action '{action}'")
            print(f"Supported actions: {sorted(index_actions | name_actions)}")
            sys.exit(1)

        # Build command string for apply_feedback
        command_parts = [action]

        if action in index_actions:
            if len(parts) < 2:
                print(f"ERROR: '{action}' requires an item index (e.g., '{action} 1')")
                sys.exit(1)
            if not parts[1].isdigit():
                print(f"ERROR: '{action}' requires a numeric index, got '{parts[1]}'")
                sys.exit(1)
            command_parts.append(parts[1])
        elif action in name_actions:
            if len(parts) < 2:
                print(f"ERROR: '{action}' requires a target name (e.g., '{action} Stratechery')")
                sys.exit(1)
            command_parts.append(parts[1])

        command_str = " ".join(command_parts)
        dry_run = getattr(args, "dry_run", False)

        result = apply_feedback(command_str, cfg, dry_run=dry_run, note=note)
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

    elif args.command == "sources":
        from .sources import load_source_registry, validate_source_registry, ingest_sources_with_report, enabled_sources
        registry_path = getattr(args, "registry", None) or (Path(__file__).parent.parent.parent / "data" / "fixtures" / "source_registry.json")
        if not registry_path.exists():
            print(f"No source registry found at {registry_path}")
            print("Run daily --dry-run or create data/fixtures/source_registry.json")
            sys.exit(1)

        allow_network = getattr(args, "allow_network", False)

        if args.subcmd == "list":
            sources = load_source_registry(registry_path)
            print(f"{'Source ID':<20} {'Name':<25} {'Type':<15} {'Enabled':<8}")
            print("-" * 70)
            for s in sources:
                print(f"{s.get('source_id',''):<20} {s.get('name',''):<25} {s.get('type',''):<15} {str(s.get('enabled',True)):<8}")

        elif args.subcmd == "validate":
            sources = load_source_registry(registry_path)
            result = validate_source_registry(sources)
            if result["valid"]:
                print("Source registry is valid.")
                for s in sources:
                    fixture = s.get("fixture_path", "")
                    url = s.get("url", "")
                    if fixture:
                        exists = (Path(__file__).parent.parent.parent / fixture).exists()
                        status = "OK" if exists else "MISSING"
                        print(f"  {s['source_id']}: fixture {status}")
                    if url:
                        print(f"  {s['source_id']}: url {url}")
            else:
                print("Source registry has errors:")
                for e in result["errors"]:
                    print(f"  - {e}")
                sys.exit(1)

        elif args.subcmd == "ingest-fixtures":
            sources = load_source_registry(registry_path)
            result = ingest_sources_with_report(sources, allow_network=False)
            items = result["items"]
            report = result["report"]
            print(f"Ingested {len(items)} items from {report['source_count_enabled']} enabled sources.")
            print(f"Total: {report['source_count_total']} | Enabled: {report['source_count_enabled']} | Disabled: {report['source_count_disabled']} | Success: {report['source_count_success']} | Failed: {report['source_count_failed']} | Empty: {report['source_count_empty']}")
            print("\nPer-source status:")
            for s in report["sources"]:
                status_icon = "✓" if s["status"] == "success" else "✗" if s["status"] == "failed" else "-"
                print(f"  {status_icon} {s['source_id']:<20} {s['status']:<10} raw={s['item_count_raw']:<3} norm={s['item_count_normalized']:<3}  {s['name']}")
                if s.get("errors"):
                    for err in s["errors"]:
                        print(f"      ERROR: {err}")
                if s.get("warnings"):
                    for warn in s["warnings"]:
                        print(f"      WARN:  {warn}")
            # Save report for later retrieval
            report_dir = cfg["OUTPUT_DIR"] / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / "latest_source_ingestion_report.json"
            report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        elif args.subcmd == "fetch":
            sources = load_source_registry(registry_path)
            capture_replay = getattr(args, "capture_replay", False)
            replay_dir = getattr(args, "replay_dir", None) or (Path(__file__).parent.parent.parent / "data" / "fixtures" / "replay")
            source_id_filter = getattr(args, "source_id", None)

            if capture_replay and not allow_network:
                print("Error: --capture-replay requires --allow-network")
                sys.exit(1)

            if not allow_network:
                print("Note: --allow-network not set. rss_url sources will be skipped (network_disabled).")
                print("Use --allow-network to perform real network requests.\n")

            # Filter to specific source if requested
            if source_id_filter:
                sources = [s for s in sources if s.get("source_id") == source_id_filter]
                if not sources:
                    print(f"Error: source_id '{source_id_filter}' not found in registry")
                    sys.exit(1)

            result = ingest_sources_with_report(sources, allow_network=allow_network)
            items = result["items"]
            report = result["report"]
            captured_files = []

            # Capture replay fixtures for successful rss_url sources
            if capture_replay and allow_network:
                from .replay import save_rss_replay_fixture, build_replay_metadata
                from .rss import parse_rss_xml
                from .fetch import fetch_rss_url_source

                for source in sources:
                    if source.get("type") != "rss_url" or not source.get("enabled", True):
                        continue
                    source_id = source.get("source_id", "unknown")
                    fetch_result = fetch_rss_url_source(source, allow_network=True)
                    if fetch_result.ok:
                        raw_items = parse_rss_xml(fetch_result.text)
                        meta = build_replay_metadata(source, fetch_result, item_count=len(raw_items))
                        xml_path = save_rss_replay_fixture(
                            source_id=source_id,
                            xml_text=fetch_result.text,
                            output_dir=replay_dir,
                            metadata=meta,
                        )
                        captured_files.append(str(xml_path))

            print(f"Fetched {len(items)} items from {report['source_count_enabled']} enabled sources.")
            print(f"Total: {report['source_count_total']} | Enabled: {report['source_count_enabled']} | Disabled: {report['source_count_disabled']} | Success: {report['source_count_success']} | Failed: {report['source_count_failed']} | Empty: {report['source_count_empty']} | SkippedNetwork: {report.get('source_count_skipped_network', 0)}")
            if captured_files:
                print(f"Captured {len(captured_files)} replay fixtures:")
                for cf in captured_files:
                    print(f"  - {cf}")
            print("\nPer-source status:")
            for s in report["sources"]:
                status_icon = "✓" if s["status"] == "success" else "✗" if s["status"] == "failed" else "○" if s["status"] == "skipped" else "-"
                net_icon = "🌐" if s.get("network_allowed") else "🔒"
                print(f"  {status_icon} {net_icon} {s['source_id']:<20} {s['status']:<10} raw={s['item_count_raw']:<3} norm={s['item_count_normalized']:<3}  {s['name']}")
                if s.get("url"):
                    print(f"      URL: {s['url']}")
                if s.get("fetch_status"):
                    print(f"      fetch_status: {s['fetch_status']} http_code={s.get('http_status_code')}")
                if s.get("errors"):
                    for err in s["errors"]:
                        print(f"      ERROR: {err}")
                if s.get("warnings"):
                    for warn in s["warnings"]:
                        print(f"      WARN:  {warn}")
            # Save report
            report_dir = cfg["OUTPUT_DIR"] / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / "latest_source_ingestion_report.json"
            report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        elif args.subcmd == "report":
            report_dir = cfg["OUTPUT_DIR"] / "reports"
            report_file = report_dir / "latest_source_ingestion_report.json"
            if report_file.exists():
                report = json.loads(report_file.read_text(encoding="utf-8"))
                print(f"Source Ingestion Report ({report['created_at']})")
                print(f"Run ID: {report['run_id']}")
                print(f"Total: {report['source_count_total']} | Enabled: {report['source_count_enabled']} | Disabled: {report['source_count_disabled']}")
                print(f"Success: {report['source_count_success']} | Failed: {report['source_count_failed']} | Empty: {report['source_count_empty']}")
                print(f"Total items: {report['total_items']}")
                print("\nPer-source status:")
                for s in report["sources"]:
                    status_icon = "✓" if s["status"] == "success" else "✗" if s["status"] == "failed" else "-"
                    print(f"  {status_icon} {s['source_id']:<20} {s['status']:<10} raw={s['item_count_raw']:<3} norm={s['item_count_normalized']:<3}  {s['name']}")
                    if s.get("errors"):
                        for err in s["errors"]:
                            print(f"      ERROR: {err}")
                    if s.get("warnings"):
                        for warn in s["warnings"]:
                            print(f"      WARN:  {warn}")
            else:
                print("No source ingestion report found. Run: newsletter-ai sources ingest-fixtures")
                sys.exit(1)

        sys.exit(0)

    elif args.command == "quality":
        from .quality import generate_quality_report, save_quality_report
        import uuid
        output_dir = cfg["OUTPUT_DIR"]
        quality_dir = output_dir / "quality"
        latest_md = quality_dir / "latest_quality.md"
        latest_json = quality_dir / "latest_quality.json"

        # Only auto-generate demo for show/json/explain to preserve graceful error for sources/duplicates/sections
        if args.subcmd in ("show", "json", "explain"):
            if not latest_json.exists():
                demo_sources = [
                    {"source": "fixture", "status": "ok", "raw_item_count": 5, "normalized_item_count": 4, "final_item_count": 3, "warnings": []}
                ]
                demo_items = [{"id": "1", "topic": "ai", "source": "fixture", "base_score": 0.8}]
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
        elif args.subcmd == "sources":
            if latest_json.exists():
                data = json.loads(latest_json.read_text())
                sources = data.get("source_details", [])
                sorted_sources = sorted(sources, key=lambda x: x.get("source_quality_score", 0), reverse=True)
                print("Source Quality Scores (sorted by score desc):")
                print(f"{'Source':<20} {'Score':>8} {'Status':<10} {'Final':>6} {'DupRm':>6} {'Action':<18}")
                print("-" * 75)
                for s in sorted_sources:
                    print(f"{s.get('source',''):<20} {s.get('source_quality_score',0):>8.3f} {s.get('status',''):<10} {s.get('final_item_count',0):>6} {s.get('duplicate_removed_count',0):>6} {s.get('recommended_action',''):<18}")
            else:
                print("No quality report found. Run daily first.")
        elif args.subcmd == "duplicates":
            if latest_json.exists():
                data = json.loads(latest_json.read_text())
                print("Duplicate Reason Counts:")
                for reason, count in sorted(data.get("duplicate_reason_counts", {}).items(), key=lambda x: -x[1]):
                    print(f"  {reason}: {count}")
                print(f"Fuzzy duplicate count: {data.get('fuzzy_duplicate_count', 0)}")
            else:
                print("No quality report found. Run daily first.")
        elif args.subcmd == "sections":
            if latest_json.exists():
                data = json.loads(latest_json.read_text())
                sections = data.get("section_distribution", {})
                if not sections:
                    print("No section distribution found in quality report.")
                    sys.exit(0)

                print("Section Quality Report (v0.3.4)")
                print("=" * 60)
                for sid, sec in sections.items():
                    print(f"\n[{sec.get('section_label', sid)}] ({sid})")
                    print(f"  Items: {sec.get('item_count', 0)}")
                    print(f"  Avg Score: {sec.get('average_score', 0.0):.3f}")
                    print(f"  Avg Quality Score: {sec.get('average_quality_score', 0.0):.3f}")
                    print(f"  Sources ({sec.get('source_count', 0)}): {', '.join(sec.get('sources', [])[:5])}")
                    print(f"  Topic Tags: {', '.join(sec.get('topic_tags', [])[:5])}")
                    if sec.get('warnings'):
                        print(f"  Warnings: {', '.join(sec['warnings'])}")
                    titles = sec.get('representative_titles', [])
                    if titles:
                        print(f"  Representative Titles:")
                        for t in titles:
                            print(f"    - {t}")
                print("\n" + "=" * 60)
            else:
                print("No quality report found. Please run: newsletter-ai daily --dry-run")
        sys.exit(0)

    elif args.command == "replay":
        from .replay import list_replay_fixtures, validate_replay_pair, load_rss_replay_fixture
        from .rss import parse_rss_xml

        replay_dir = getattr(args, "replay_dir", None) or (Path(__file__).parent.parent.parent / "data" / "fixtures" / "replay")
        replay_dir = Path(replay_dir)

        if args.subcmd == "list":
            fixtures = list_replay_fixtures(replay_dir)
            if not fixtures:
                print(f"No replay fixtures found in {replay_dir}")
                print("Run: newsletter-ai sources fetch --allow-network --capture-replay")
                sys.exit(0)
            print(f"{'Source ID':<20} {'Items':>6} {'Status':<10} {'Fetched At':<25} {'XML Path'}")
            print("-" * 90)
            for f in fixtures:
                print(f"{f['source_id']:<20} {f['item_count'] or 0:>6} {f['status']:<10} {f['fetched_at'] or '':<25} {f['xml_path']}")
                if f.get("errors"):
                    for err in f["errors"]:
                        print(f"  ERROR: {err}")
                if f.get("warnings"):
                    for warn in f["warnings"]:
                        print(f"  WARN:  {warn}")
            sys.exit(0)

        elif args.subcmd == "inspect":
            xml_path = getattr(args, "path", None)
            if not xml_path:
                print("Error: inspect requires a path to replay XML")
                print("Usage: newsletter-ai replay inspect data/fixtures/replay/rss_xxx.xml")
                sys.exit(1)
            xml_path = Path(xml_path)
            meta_path = xml_path.with_suffix(".json")
            if not xml_path.exists():
                print(f"Error: XML not found: {xml_path}")
                sys.exit(1)
            if not meta_path.exists():
                print(f"Error: Metadata not found: {meta_path}")
                sys.exit(1)

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            xml_text = load_rss_replay_fixture(xml_path)
            items = parse_rss_xml(xml_text)

            print(f"Replay: {xml_path.name}")
            print(f"  source_id: {meta.get('source_id', 'unknown')}")
            print(f"  url: {meta.get('url', 'N/A')}")
            print(f"  fetched_at: {meta.get('fetched_at', 'N/A')}")
            print(f"  status_code: {meta.get('status_code', 'N/A')}")
            print(f"  item_count: {meta.get('item_count', len(items))}")
            print(f"  sha256: {meta.get('sha256', 'N/A')}")
            print(f"  sanitized: {meta.get('sanitized', False)}")
            print(f"  stripped_tracking_params: {meta.get('stripped_tracking_params_count', 0)}")
            print(f"\nFirst {min(3, len(items))} items:")
            for i, item in enumerate(items[:3], 1):
                print(f"  {i}. {item.get('title', '(untitled)')}")
            sys.exit(0)

        elif args.subcmd == "validate":
            fixtures = list_replay_fixtures(replay_dir)
            if not fixtures:
                print(f"No replay fixtures found in {replay_dir}")
                sys.exit(0)
            pass_count = 0
            fail_count = 0
            for f in fixtures:
                xml_path = Path(f["xml_path"])
                meta_path = Path(f["metadata_path"]) if f["metadata_path"] else xml_path.with_suffix(".json")
                result = validate_replay_pair(xml_path, meta_path)
                status = "PASS" if result["valid"] else "FAIL"
                if result["valid"]:
                    pass_count += 1
                else:
                    fail_count += 1
                print(f"[{status}] {f['source_id']}")
                for err in result["errors"]:
                    print(f"  ERROR: {err}")
                for warn in result["warnings"]:
                    print(f"  WARN:  {warn}")
            print(f"\nSummary: {pass_count} passed, {fail_count} failed, {len(fixtures)} total")
            sys.exit(0 if fail_count == 0 else 1)

        elif args.subcmd == "promote":
            xml_path = getattr(args, "path", None)
            source_id = getattr(args, "source_id", None)
            name = getattr(args, "name", None)
            if not xml_path or not source_id or not name:
                print("Error: promote requires xml_path, --source-id, and --name")
                print("Usage: newsletter-ai replay promote data/fixtures/replay/rss_xxx.xml --source-id my-source --name 'My Source'")
                sys.exit(1)
            xml_path = Path(xml_path)
            meta_path = xml_path.with_suffix(".json")
            if not xml_path.exists():
                print(f"Error: XML not found: {xml_path}")
                sys.exit(1)

            entry = {
                "source_id": source_id,
                "name": name,
                "type": "rss_replay",
                "enabled": True,
                "fixture_path": str(xml_path),
                "topic_hints": [],
                "style_hints": [],
                "quality_weight": 1.0,
            }
            print("Proposed registry entry (dry-run, not written):")
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            print("\nTo add to registry, append this to data/fixtures/source_registry.json")
            sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
