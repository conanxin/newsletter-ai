# Command Card v0.3.6

## Release Gate
- make release-check
- make validate

## Daily Dry-Run (now uses unified fixture)
- newsletter-ai daily --dry-run
- Uses data/fixtures/dry_run_items.json by default
- Generates snapshot, sectioned digest, telegram text, and quality report

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

## v0.3.6 Fixture Unification
- src/newsletter_ai/fixtures.py: load_dry_run_items()
- data/fixtures/dry_run_items.json: official dry-run fixture
- E2E tests and CLI dry-run now share the same loader
- Reduced behavior drift between test and production dry-run

## v0.3.5 E2E Regression
- Full offline E2E test using fixture data