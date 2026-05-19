# Command Card v0.2.5

## Release Gate
- make release-check
- make validate

## Daily Dry-Run
- newsletter-ai daily --dry-run
- newsletter-ai daily --dry-run --fixtures tests/fixtures/rss/

## Inspection
- newsletter-ai items show
- newsletter-ai items explain 1

## Feedback
- newsletter-ai feedback "like 1" --dry-run
- newsletter-ai prefs explain

## Status
- newsletter-ai health
- newsletter-ai status
## Quality (v0.3.2.1)
- newsletter-ai quality show
- newsletter-ai quality explain
- newsletter-ai quality sources
- newsletter-ai quality duplicates

## v0.3.3 Sectioning
- digest now outputs by topic sections
- global item_index preserved for feedback
- quality report includes section_distribution
