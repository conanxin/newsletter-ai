# Command Card v0.3.19

## Release Gate
- make release-check
- make validate

## v0.4.1 Static Dashboard Commands
- `newsletter-ai dashboard build` — generates `output/dashboard/index.html`
- `newsletter-ai dashboard show` — shows dashboard path
- Reads: `output/snapshots/latest_items.json`, `output/quality/latest_quality.json`, `output/runs/index.json`, `output/state/last-run-status.json`
- Single-file HTML with embedded CSS, no external CDN
- Chinese UI, dark theme
- Sections: run summary, digest by section, quality report, sources, runs history, replay sources, feedback commands
- Graceful empty state if no run data
- `output/dashboard/` is runtime artifact — do not commit

## v0.4.0 Real Source Trial Commands
- Real RSS source fetch + replay capture:
  - `newsletter-ai sources fetch --registry /tmp/newsletter_ai_v04_real_sources_registry.json --allow-network --capture-replay --source-id hnrss-frontpage`
- Trial replay registry (offline, HN only):
  - `newsletter-ai daily --dry-run --source-registry data/fixtures/real_source_trial_registry.json`
  - `newsletter-ai quality sections/sources/duplicates`
  - `newsletter-ai feedback like 1 --dry-run`
- Replay fixture:
  - `data/fixtures/replay/rss_hnrss-frontpage_20260520_015710.xml`
- arXiv replay (~1.1MB) captured locally but excluded from repo for size
- All real fetches require explicit `--allow-network`
- Default daily remains offline
- Replay sha256 now computed from sanitized XML (post-sanitize)

## Daily Dry-Run
- newsletter-ai daily --dry-run
- Uses data/fixtures/dry_run_items.json by default (normalized)
- Writes run record to output/runs/<run_id>.json and updates output/runs/index.json

## Daily with Source Registry (v0.3.10, v0.3.12)
- newsletter-ai daily --dry-run --source-registry data/fixtures/source_registry.json
- Reads enabled rss_fixture sources from registry (offline by default)
- rss_url sources are skipped unless --allow-network is provided
- Requires --dry-run or --no-publish
- Records input_mode / source_count / item_count / ingestion_report / run_record_path in last-run-status

## Daily with Network (v0.3.12 — explicit opt-in only)
- newsletter-ai daily --dry-run --source-registry data/fixtures/source_registry.json --allow-network
- Allows rss_url sources to perform real HTTP requests
- --allow-network requires --dry-run or --no-publish for safety
- Default is always offline — no implicit network access

## Run Artifact Index (v0.3.19)
- newsletter-ai runs list
- newsletter-ai runs latest
- newsletter-ai runs inspect <run_id>
- Run index location: output/runs/index.json
- Individual records: output/runs/<run_id>.json
- Each record links: snapshot, quality report, ingestion summary, last-run-status
- Graceful error if no runs: "Run: newsletter-ai daily --dry-run"
- output/runs/ is runtime artifact — do not commit

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

## Quality (v0.3.18)
- newsletter-ai quality show
- newsletter-ai quality json
- newsletter-ai quality explain
- newsletter-ai quality sources
- newsletter-ai quality duplicates
- newsletter-ai quality sections

### Quality report lifecycle (v0.3.18)
1. `daily --dry-run` → generates `output/quality/latest_quality.json` (current run)
2. `quality sections/sources/duplicates` → reads latest quality report
3. If no report exists: `Run: newsletter-ai daily --dry-run`
4. Legacy demo auto-generation removed — always current-run data

### Replay quality chain (v0.3.18)
- `daily --dry-run --source-registry data/fixtures/replay_source_registry.json`
- `quality sections` → shows replay section distribution
- `quality sources` → shows replay source quality
- `quality duplicates` → shows replay duplicate analysis

## Replay (v0.3.15 governance, v0.3.16 smoke fixture, v0.3.17 regression)
- newsletter-ai replay list
- newsletter-ai replay list --replay-dir data/fixtures/replay
- newsletter-ai replay inspect data/fixtures/replay/rss_xxx.xml
- newsletter-ai replay validate
- newsletter-ai replay promote data/fixtures/replay/rss_xxx.xml --source-id my-source --name "My Source"
- newsletter-ai replay promote data/fixtures/replay/rss_xxx.xml --source-id my-source --name "My Source" --as-json

### Replay commands
- `list` — show all replay fixtures with source_id, item_count, status, fetched_at
- `inspect` — display metadata + first 3 item titles
- `validate` — integrity check all replay pairs (sha256, item_count, parseability)
- `promote` — output proposed `rss_replay` registry entry (dry-run only, does not write registry)
  - `--as-json` outputs pure JSON for piping / redirecting

### Sanitization
- `sanitize_replay_xml()` strips tracking query params: utm_*, fbclid, gclid, mc_*
- Preserves non-tracking params
- Handles XML-escaped ampersands
- Sanitized XML remains parseable

### Smoke fixture (v0.3.16)
- First real-world replay fixture: `data/fixtures/replay/rss_hnrss-frontpage-smoke_20260519_111736.xml`
- Source: https://hnrss.org/frontpage (public HN frontpage RSS)
- 20 items, HTTP 200, no token/cookie/auth
- Used for offline replay / regression, not real-time HN
- Capture: `sources fetch --allow-network --capture-replay`

### Offline replay registry (v0.3.17)
- `data/fixtures/replay_source_registry.json` — dedicated offline replay registry
- Contains `rss_replay` source pointing at captured HN fixture
- Fully offline, no network required
- Recommended for regression testing:
  - `newsletter-ai daily --dry-run --source-registry data/fixtures/replay_source_registry.json`
  - `newsletter-ai items show`
  - `newsletter-ai feedback like 1 --dry-run`
  - `newsletter-ai quality sections`

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

## v0.3.12 Controlled Real RSS Fetch

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
