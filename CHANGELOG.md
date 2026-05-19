# Changelog

## v0.3.13 (2026-05)
- CLI Feedback Parser Hardening
- Fixed `feedback` subcommand to accept both quoted and unquoted command forms:
  - `newsletter-ai feedback "like 1" --dry-run`
  - `newsletter-ai feedback like 1 --dry-run`
  - `newsletter-ai feedback "source_up Stratechery" --dry-run`
  - `newsletter-ai feedback source_up Stratechery --dry-run`
- Added `--note` support for `save` action:
  - `newsletter-ai feedback save 2 --note "值得深挖" --dry-run`
  - `newsletter-ai feedback "save 2 --note 值得深挖" --dry-run` (quoted string with inline --note)
- Note is persisted to feedback event as optional field; preferences update logic unaffected
- Hardened parser with clear error messages for invalid actions and missing arguments (no traceback)
- Added `tests/test_cli_feedback_parser.py` with 11 tests covering quoted/unquoted forms, --note, and graceful errors
- No changes to underlying feedback event schema or preferences update logic
- No network access, no Telegram sending

## v0.3.12 (2026-05)
- Controlled Real RSS Fetch Prototype
- Added `src/newsletter_ai/fetch.py`: `fetch_url()` and `fetch_rss_url_source()`
  - Uses standard library `urllib.request` only (no new heavy dependencies)
  - Explicit `allow_network=False` by default — no network requests without opt-in
  - Structured `FetchResult` with `ok`, `status_code`, `text`, `error`, `duration_sec`, `from_cache`
  - Supports timeout and custom User-Agent (`newsletter-ai/dev`)
- Extended source registry schema to support `rss_url` source type:
  - Required fields: `source_id`, `name`, `type`, `enabled`, `url`
  - Optional: `timeout_sec` (default 10), `cache_ttl_minutes`, `topic_hints`, `style_hints`
  - `rss_fixture` type remains fully backward-compatible
- Added `ingest_sources_with_report()` in `src/newsletter_ai/sources.py`:
  - Unified ingestion for both `rss_fixture` (offline) and `rss_url` (network, opt-in)
  - `allow_network=False` → rss_url sources marked `skipped` with `network_disabled` warning
  - `allow_network=True` → fetches URL, parses RSS XML, normalizes items
  - Per-source report now includes: `url`, `fetch_status`, `http_status_code`, `from_cache`, `network_allowed`
  - Single source failure does not affect other sources
  - All-fallback/skipped registry → graceful empty result (no crash)
- CLI enhancements:
  - `newsletter-ai sources fetch --registry <path> [--allow-network]`
  - `newsletter-ai daily --dry-run --source-registry <path> [--allow-network]`
  - `--allow-network` requires `--dry-run` or `--no-publish` for safety
  - Without `--allow-network`, clear prompt: "rss_url sources will be skipped"
  - `newsletter-ai sources ingest-fixtures` behavior unchanged (offline only)
- Pipeline guard:
  - `run_daily_pipeline()` accepts `allow_network` parameter
  - Default `allow_network=False` — daily dry-run never implicitly fetches real URLs
  - Publish step never triggers network fetch
- Tests (all mock network, no real HTTP requests):
  - `tests/test_fetch.py`: 11 tests covering success, HTTP error, URL error, timeout, User-Agent
  - `tests/test_sources_rss_url.py`: 9 tests covering validate, skipped, mocked success, failure, mixed sources, backward compat
- Documentation:
  - Updated `docs/COMMAND_CARD.md` with v0.3.12 commands
  - Updated `CHANGELOG.md`

## v0.3.11 (2026-05)
- Source Ingestion Report + Failure Resilience
- Added `ingest_offline_sources_with_report()` returning items + per-source report
- Per-source status tracking: success / failed / disabled / empty
- Single source failure no longer crashes entire ingestion
- Missing fixture_path → failed report
- Fixture file not found → failed report
- Empty parsed items → empty report with warning
- All-failed registry → pipeline graceful fail with clear error
- `last-run-status.json` records `ingestion_report` summary
- `newsletter-ai sources ingest-fixtures` shows per-source status table
- `newsletter-ai sources report` displays latest ingestion report
- `newsletter-ai status` shows ingestion summary from last run
- Added `tests/test_source_ingestion_report.py`
- Added `tests/test_pipeline_source_failure_resilience.py`
- Added `tests/test_cli_sources_report.py`

## v0.3.10 (2026-05)
- Controlled Offline Source Pipeline
- Added `--source-registry` CLI argument to `daily --dry-run`
- Pipeline supports two offline input modes:
  - `fixture_json` (default): data/fixtures/dry_run_items.json
  - `source_registry`: reads enabled rss_fixture sources from registry
- `last-run-status.json` records `input_mode`, `source_count`, `item_count`
- `--source-registry` requires `--dry-run` or `--no-publish` for safety
- Invalid registry path falls back to default fixture mode gracefully
- Added `tests/test_pipeline_source_registry.py`
- Added `tests/test_cli_daily_source_registry.py`

## v0.3.9 (2026-05)
- Source Registry + Offline Ingestion Bridge
- Added `src/newsletter_ai/sources.py` with source registry loader and offline ingestion
- Added `data/fixtures/source_registry.json` with sample RSS fixture sources
- Added CLI commands:
  - `newsletter-ai sources list`
  - `newsletter-ai sources validate`
  - `newsletter-ai sources ingest-fixtures`
- Source registry supports `rss_fixture` type with topic_hints/style_hints merging
- Disabled sources are filtered out during ingestion
- Graceful error handling for missing fixtures and invalid registry entries
- All operations are offline-only (no network requests)

## v0.3.8 (2026-05)
- RSS Fixture Parser + Ingestion Normalization
- Added `src/newsletter_ai/rss.py`: `parse_rss_xml()` and `parse_rss_file()`
- Added `tests/fixtures/e2e_rss_sample.xml` with 7 items (including duplicates and missing fields)
- Extended `src/newsletter_ai/fixtures.py` with `load_rss_fixture_items()` and `load_rss_fixture_items_from_path()`
- RSS items are normalized via `normalize_items()` before entering the pipeline
- JSON dry-run fixture remains the default for `daily --dry-run`
- Added `tests/test_rss.py`
- All changes are offline-only (no network requests)

## v0.3.7 (2026-05)
- Source Normalization Layer
- Added `src/newsletter_ai/normalize.py` with `normalize_item()`, `normalize_items()`, and `validate_normalized_item()`
- Stable `item_id` generation based on URL or source+title
- Integrated normalization into fixture loading
- Added `tests/test_normalize.py`

## v0.3.6 (2026-05)
- Dry-run Fixture Source Unification
- Created `src/newsletter_ai/fixtures.py`
- Created `data/fixtures/dry_run_items.json`
- Unified dry-run and E2E fixture sources

## v0.3.5 (2026-05)
- Fixture-based End-to-End Regression
- Added `tests/test_e2e_fixture_flow.py`
- Full chain coverage from fixture to feedback and preferences history

## v0.3.4 (2026-05)
- Section-aware Quality Polish
- Enhanced `section_distribution` and added `quality sections` command
