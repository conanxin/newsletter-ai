# Command Card v0.3.4

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

## Quality (v0.3.4)
- newsletter-ai quality show
- newsletter-ai quality explain
- newsletter-ai quality sources
- newsletter-ai quality duplicates
- newsletter-ai quality sections          # NEW: section-aware quality + warnings

## v0.3.4 Section Quality
- newsletter-ai quality sections 显示每个 section 的：
  - item_count, average_score, sources, topic_tags, warnings
- Warnings 包括：other_section_too_large, single_source_section, fragmented_section, duplicate_heavy_section

## v0.3.3 Sectioning
- digest now outputs by topic sections
- global item_index preserved for feedback
- quality report includes enhanced section_distribution

## v0.3.2.1 Quality
- quality sources: shows source_quality_score table
- quality duplicates: shows duplicate_reason_counts + fuzzy_duplicate_count