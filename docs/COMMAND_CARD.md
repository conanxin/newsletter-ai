# Command Card v0.3.12

## Release Gate
- make release-check
- make validate

## Daily Dry-Run
- newsletter-ai daily --dry-run
- Uses data/fixtures/dry_run_items.json by default (normalized)

## Daily with Source Registry (v0.3.10, v0.3.12)
- newsletter-ai daily --dry-run --source-registry data/fixtures/source_registry.json
- Reads enabled rss_fixture sources from registry (offline by default)
- rss_url sources are skipped unless --allow-network is provided
- Requires --dry-run or --no-publish
- Records input_mode / source_count / item_count / ingestion_report in last-run-status

## Daily with Network (v0.3.12 — explicit opt-in only)
- newsletter-ai daily --dry-run --source-registry data/fixtures/source_registry.json --allow-network
- Allows rss_url sources to perform real HTTP requests
- --allow-network requires --dry-run or --no-publish for safety
- Default is always offline — no implicit network access

## Source Registry (v0.3.9, v0.3.11, v0.3.12, v0.3.14)
- newsletter-ai sources list
- newsletter-ai sources validate
- newsletter-ai sources ingest-fixtures
- newsletter-ai sources report
- newsletter-ai sources fetch --registry data/fixtures/source_registry.json
- newsletter-ai sources fetch --registry data/fixtures/source_registry.json --allow-network --capture-replay
- newsletter-ai sources fetch --registry data/fixtures/source_registry.json --allow-network --capture-replay --source-id sample-ai-feed
- Registry: data/fixtures/source_registry.json
- Supports three source types:
  - rss_fixture: offline local XML file (default, safe)
  - rss_url: real RSS feed URL (requires --allow-network)
  - rss_replay: offline replay fixture from captured fetch (v0.3.14)
- Per-source status: success / failed / disabled / empty / skipped

### Fetch flags
- `--allow-network` — required for real RSS fetching (default: offline)
- `--capture-replay` — saves successful rss_url fetches as replay fixtures (requires `--allow-network`)
- `--replay-dir` — custom replay output directory (default: `data/fixtures/replay/`)
- `--source-id` — filter to a single source

### Replay workflow
1. `sources fetch --allow-network --capture-replay` → captures real RSS to `data/fixtures/replay/`
2. Add `rss_replay` source to registry pointing at captured fixture
3. Future runs use `rss_replay` — fully offline, no network required

## Feedback (v0.3.13 hardened)
  - rss_fixture: offline local XML file (default, safe)
  - rss_url: real RSS feed URL (requires --allow-network)
- Per-source status: success / failed / disabled / empty / skipped
- Single source failure does not crash entire ingestion
- fetch command shows network lock icon (🔒/🌐) per source

## Inspection
- newsletter-ai items show
- newsletter-ai items explain 1

## Feedback (v0.3.13 hardened)
- newsletter-ai feedback "like 1" --dry-run
- newsletter-ai feedback like 1 --dry-run
- newsletter-ai feedback "source_up Stratechery" --dry-run
- newsletter-ai feedback source_up Stratechery --dry-run
- newsletter-ai feedback save 2 --note "值得深挖" --dry-run
- newsletter-ai feedback "save 2 --note 值得深挖" --dry-run
- newsletter-ai prefs explain

### Parser behavior
- Accepts both quoted string and space-separated tokens
- `--dry-run` can appear at the end
- `--note` is a standalone flag, and also parsed from inside quoted strings
- Invalid actions and missing arguments produce clear error messages without traceback

## Status
- newsletter-ai health
- newsletter-ai status

## Quality
- newsletter-ai quality show
- newsletter-ai quality explain
- newsletter-ai quality sources
- newsletter-ai quality duplicates
- newsletter-ai quality sections

## v0.3.12 Controlled Real RSS Fetch
- src/newsletter_ai/fetch.py: fetch_url() / fetch_rss_url_source()
- Standard library only (urllib.request), no heavy dependencies
- Explicit allow_network=False default — no requests without opt-in
- Structured FetchResult with ok, status_code, text, error, duration_sec
- User-Agent: newsletter-ai/dev

## v0.3.8 RSS Fixture Parser
- src/newsletter_ai/rss.py: parse_rss_xml() / parse_rss_file()
- tests/fixtures/e2e_rss_sample.xml
- load_rss_fixture_items("e2e") in fixtures.py
- RSS items are normalized via normalize.py
- JSON dry-run fixture remains default (no breaking change)

## v0.3.7 Normalization Layer
- src/newsletter_ai/normalize.py
- Stable item_id, graceful missing field handling

## v0.3.6 Fixture Unification
- Unified dry-run and E2E fixture sources
