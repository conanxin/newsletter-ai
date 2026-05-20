# Changelog

## v0.4.1 Static Dashboard (2026-05)
- 新增本地静态 Dashboard 生成器
- 新增模块 `src/newsletter_ai/dashboard.py`：
  - `load_dashboard_data()` — 读取 latest snapshot / quality / runs / replay 数据
  - `render_dashboard_html()` — 渲染单文件 HTML（内嵌 CSS，无外部 CDN）
  - `build_dashboard()` — 生成 `output/dashboard/index.html`
- 新增 CLI 命令：
  - `newsletter-ai dashboard build` — 生成 Dashboard
  - `newsletter-ai dashboard show` — 显示 Dashboard 路径
- Dashboard 页面包含：
  - 最新运行概览（run_id、时间、状态、items、sections、sources）
  - 今日 Digest（按 section 分组，显示 item_index / title / source / summary / url / score）
  - Quality Report（section distribution、source quality、duplicate analysis）
  - Sources（ingestion summary、success/failed/skipped）
  - 最近 Runs（最多 10 条）
  - Replay Sources（replay registry 概览）
  - Feedback 命令速查（前 5 条 item 的 like/save 命令）
- 特性：
  - 单文件 HTML，内嵌 CSS，中文界面
  - 不加载外部 CDN，不联网
  - 不发送 Telegram
  - 缺少数据时显示 graceful empty state
  - 使用全局 item_index，与 feedback CLI 一致
- 测试：
  - `tests/test_dashboard.py` — 6 个测试覆盖数据加载、HTML 渲染、文件写入、空状态、无 secret
  - `tests/test_cli_dashboard.py` — 4 个测试覆盖 CLI build/show、graceful 缺失数据、trial registry
- `output/dashboard/` 是运行产物，不提交到 Git

## v0.4.0 Real Source Trial (2026-05)
- Real RSS Source Smoke + Replay Fixture Capture (HN only)
- Source trialed:
  - Hacker News Frontpage (https://hnrss.org/frontpage) — 20 items, HTTP 200
- arXiv cs.AI also fetched locally (343 items, HTTP 200) but excluded from repo due to size (~1.1MB)
- Replay fixture captured:
  - `data/fixtures/replay/rss_hnrss-frontpage_20260520_015710.xml`
- New trial replay registry:
  - `data/fixtures/real_source_trial_registry.json` — fully offline rss_replay source (HN only)
- Verified offline daily pipeline with real-source replay:
  - `daily --dry-run --source-registry data/fixtures/real_source_trial_registry.json` → 20 items
  - `quality sections/sources/duplicates` → current-run reports
  - `feedback like 1 --dry-run` → parses replay items
  - `runs latest` → traces run record
- All real RSS fetches used explicit `--allow-network`
- Default daily remains offline (fixture_json)
- No assertions on real-time titles in tests
- **Fix**: replay metadata sha256 now computed from sanitized XML (post-sanitize), ensuring `replay validate` passes

## v0.3.19 (2026-05)
- Run Artifact Index + History Browser
- New module `src/newsletter_ai/runs.py`:
  - `make_run_record(...)` — builds a run record with relative paths
  - `append_run_record(...)` — writes `output/runs/<run_id>.json` and updates `output/runs/index.json`
  - `list_runs(...)`, `get_latest_run(...)`, `load_run_record(...)` — index queries
  - No secrets stored; paths are relative to project base for portability
- Pipeline integration:
  - `run_daily_pipeline()` now calls `_write_run_index()` after each run
  - Both default dry-run and replay registry daily write run records
  - `last-run-status.json` includes `run_record_path`
  - Run record links: snapshot, quality report, ingestion summary, warnings/errors
- New CLI commands:
  - `newsletter-ai runs list` — shows recent runs (run_id, status, mode, items, quality path)
  - `newsletter-ai runs latest` — shows latest run summary
  - `newsletter-ai runs inspect <run_id>` — shows full run record as JSON
  - Graceful message if no runs exist: `Run: newsletter-ai daily --dry-run`
- Tests:
  - `tests/test_runs.py` — 9 tests covering record creation, index update, trimming, no secrets
  - `tests/test_pipeline_run_index.py` — 4 tests covering daily dry-run, replay registry, last-run-status, quality path linkage
  - `tests/test_cli_runs.py` — 5 tests covering list/latest/inspect and missing-run handling
- `output/runs/` is a runtime artifact directory — should not be committed

## v0.3.18 (2026-05)
- Current-run Quality Report Consistency
- `daily --dry-run` now generates `output/quality/latest_quality.json` after each run
- Quality report is based on the current run's ranked items, not legacy demo data
- `last-run-status.json` records `quality_report_path`
- Quality CLI commands (`sections`, `sources`, `duplicates`) now require an existing latest quality report
  - If no report exists, prompt: `Run: newsletter-ai daily --dry-run`
  - Removed legacy demo auto-generation fallback
- Replay registry daily (`--source-registry data/fixtures/replay_source_registry.json`) also generates current quality report
- `quality explain` now shows `run_id` and `created_at` for traceability
- Verified offline command chain:
  - `daily --dry-run` → generates latest_quality.json
  - `quality sections` → reads current report
  - `quality sources` → reads current report
  - `quality duplicates` → reads current report
  - `quality explain` → shows run_id / created_at
  - `daily --dry-run --source-registry data/fixtures/replay_source_registry.json` → replay quality report
  - `quality sections` → reflects replay items
- Default source_registry and daily behavior unchanged

## v0.3.17 (2026-05)
- Real Replay Fixture Regression + Registry Integration
- New offline replay registry:
  - `data/fixtures/replay_source_registry.json` — uses captured HN frontpage replay fixture
  - Fully offline, no network required, no token/cookie/auth
- New E2E regression test: `tests/test_e2e_real_replay_flow.py` (14 tests)
  - Replay fixture validation (pair exists, sha256 match, item_count > 0)
  - Replay registry ingestion (offline, items have required fields)
  - Daily pipeline with replay registry (snapshot, sectioned digest)
  - Feedback regression (like/save on replay items)
  - Quality regression (report structure)
  - No assertions on specific HN titles (time-sensitive content)
- Enhanced `replay promote`:
  - `--as-json` flag outputs pure JSON registry entry for piping
  - Reads topic_hints/style_hints from metadata when available
- Verified offline command chain:
  - `replay validate` → PASS
  - `daily --dry-run --source-registry data/fixtures/replay_source_registry.json` → 20 items
  - `items show` → real replay items visible
  - `feedback like 1 --dry-run` → parses replay item
  - `quality sections/sources/duplicates` → structure valid
- Default source_registry and daily behavior unchanged

## v0.3.16 (2026-05)
- Real RSS Source Smoke Run + First Replay Fixture
- Performed controlled real network fetch from https://hnrss.org/frontpage
- Captured replay fixture:
  - XML: `data/fixtures/replay/rss_hnrss-frontpage-smoke_20260519_111736.xml` (~16KB)
  - Metadata: `data/fixtures/replay/rss_hnrss-frontpage-smoke_20260519_111736.json`
  - 20 items, HTTP 200, sha256 validated
  - Public HN frontpage RSS snapshot — no token/cookie/auth
  - Used for offline replay / regression, not real-time HN
- `sanitize_replay_xml()` now returns `(sanitized_xml, stripped_count)` tuple
  - Integrated into CLI capture flow with accurate stripped count
- CLI smoke command chain verified:
  - `sources fetch --allow-network --capture-replay`
  - `replay validate` → PASS
  - `replay inspect` → metadata + first 3 titles
  - `replay promote` → dry-run rss_replay registry entry
  - `daily --dry-run --source-registry <replay_registry>` → 20 items offline
- Tests updated to unpack tuple from `sanitize_replay_xml()`
- No tests assert specific HN titles (time-sensitive content)

## v0.3.15 (2026-05)
- Replay Governance + Sanitization
- `sanitize_replay_xml()` now strips common tracking query parameters from URLs:
  - utm_source, utm_medium, utm_campaign, utm_term, utm_content
  - fbclid, gclid, mc_cid, mc_eid
  - Preserves non-tracking query params
  - Handles XML-escaped ampersands (`&amp;`)
  - Sanitized XML remains parseable by `parse_rss_xml()`
- New replay metadata fields:
  - `sanitized`: true/false
  - `stripped_tracking_params_count`: int
- New replay governance functions in `src/newsletter_ai/replay.py`:
  - `validate_replay_metadata(metadata)` — checks required fields and item_count
  - `validate_replay_pair(xml_path, metadata_path)` — integrity check (sha256, item_count, parseability)
  - `list_replay_fixtures(replay_dir)` — directory listing with status
- New CLI commands:
  - `newsletter-ai replay list [--replay-dir]` — list all replay fixtures
  - `newsletter-ai replay inspect <xml_path>` — show metadata + first 3 item titles
  - `newsletter-ai replay validate [--replay-dir]` — validate all replay pairs
  - `newsletter-ai replay promote <xml_path> --source-id <id> --name <name>` — output proposed rss_replay registry entry (dry-run only)
- Tests:
  - `tests/test_replay_sanitize.py` — 7 tests covering UTM/fbclid/gclid/mc_* stripping, preservation, parseability
  - `tests/test_replay_governance.py` — 8 tests covering validate/list/save
  - `tests/test_cli_replay.py` — 6 tests covering list/inspect/validate/promote CLI
- All tests use mock XML, no real network dependency

## v0.3.14 (2026-05)
- Controlled Network Smoke + Replay Fixture Capture
- New module `src/newsletter_ai/replay.py`:
  - `save_rss_replay_fixture(...)` — saves captured RSS XML + metadata JSON
  - `load_rss_replay_fixture(...)` — loads replay XML for offline testing
  - `sanitize_replay_xml(...)` — no-op sanitizer (placeholder for future tracking-query stripping)
  - `build_replay_metadata(...)` — builds metadata with source_id, url, fetched_at, status_code, item_count, sha256, generated_by
- New source type `rss_replay`:
  - Behaves like `rss_fixture` but reads from `data/fixtures/replay/`
  - Fully offline, no network required
  - Validated by `sources validate`
- Enhanced `sources fetch` CLI:
  - `--allow-network` — required for real RSS fetching (unchanged guard)
  - `--capture-replay` — saves successful rss_url fetches as replay fixtures (requires `--allow-network`)
  - `--replay-dir` — custom replay output directory (default: `data/fixtures/replay/`)
  - `--source-id` — filter to a single source
- Fetch guard:
  - `--capture-replay` without `--allow-network` exits with clear error
  - Failed fetches do not generate replay fixtures
  - Single source failure does not block others
- Tests:
  - `tests/test_replay.py` — 8 tests covering save/load/metadata/sanitize
  - `tests/test_cli_sources_fetch_replay.py` — 5 tests covering guard, capture, failure, source-id filter
  - `tests/test_sources_replay_type.py` — 7 tests covering validate, ingest, normalization, mixed registry
- All tests use mock XML, no real network dependency

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
