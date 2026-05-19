# Changelog

## v0.3.6 (2026-05)
- Dry-run Fixture Source Unification
- Created src/newsletter_ai/fixtures.py with load_dry_run_items() and normalize_fixture_item()
- Created data/fixtures/dry_run_items.json as the official dry-run fixture source
- pipeline.py now uses the shared fixture loader in dry-run mode instead of hardcoded mock
- E2E tests now reuse the production fixture loader
- newsletter-ai daily --dry-run now produces consistent output with E2E tests
- Added tests/test_fixtures.py and tests/test_dry_run_fixture_unification.py
- No breaking changes to existing CLI behavior

## v0.3.5 (2026-05)
- Fixture-based End-to-End Regression
- New fixture: tests/fixtures/e2e_items.json
- New E2E test: tests/test_e2e_fixture_flow.py
- Full chain coverage from fixture to feedback and preferences
- All tests remain offline

## v0.3.4 (2026-05)
- Section-aware Quality Polish
- Enhanced section_distribution and new CLI command quality sections