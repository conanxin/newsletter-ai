# Changelog

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
