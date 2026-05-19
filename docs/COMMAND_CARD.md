# Command Card v0.3.8

## Release Gate
- make release-check
- make validate

## Daily Dry-Run
- newsletter-ai daily --dry-run
- Uses data/fixtures/dry_run_items.json by default (normalized)

## Inspection
- newsletter-ai items show
- newsletter-ai items explain 1

## Feedback
- newsletter-ai feedback "like 1" --dry-run
- newsletter-ai prefs explain

## Status
- newsletter-ai health
- newsletter-ai status

## Quality
- newsletter-ai quality show
- newsletter-ai quality explain
- newsletter-ai quality sources
- newsletter-ai quality duplicates
- newsletter-ai quality sections

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