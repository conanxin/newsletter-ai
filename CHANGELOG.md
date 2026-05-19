# Changelog

## v0.3.4 (2026-05)
- Section-aware Quality Polish
- Enhanced section_distribution in quality report with rich metrics:
  section_id, section_label, item_count, average_score, average_quality_score,
  sources, source_count, topic_tags, style_tags, duplicate_count, fuzzy_duplicate_count,
  representative_titles, warnings
- New warnings: other_section_too_large, single_source_section, fragmented_section, duplicate_heavy_section
- New CLI: newsletter-ai quality sections
- quality sections reads from latest_quality.json and displays section quality + warnings
- Reuses sections.py partitioning logic
- No themes CLI added
- No change to global item_index or feedback mechanism
- Added tests/test_quality_section_distribution.py and test_cli_quality_sections.py

## v0.3.3 (2026-05)
- Digest Sectioning by Topic
- sections.py: assign_section + group_items_into_sections
- render.py: Markdown and Telegram sectioned output
- pipeline integration: sectioning after snapshot (global item_index preserved)
- quality report: added section_distribution
- items show / feedback "like 1" still use global index
- No themes CLI system implemented

## v0.3.2.1 (2026-05)
- fix: quality sources and quality duplicates CLI registration
- quality sources: shows source_quality_score table sorted by score
- quality duplicates: shows duplicate_reason_counts + fuzzy_duplicate_count
- graceful error when latest_quality.json is missing
- added tests/test_cli_quality_sources.py

## v0.2.5 (2026-05)
- RSS fixtures + E2E regression (no network)
- RSS parser, normalizer, dedupe
- fixture dry-run mode (`--fixtures`)
- full E2E: fetch/normalize/rank/snapshot/render/feedback
- 28/28 tests + release gate

## v0.2.4 / v0.2.4R / v0.2.4S
- Digest rendering unification
- Test gate + acceptance fixes
- dry-run snapshot writing
- CLI parser stability

## v0.2.3
- Snapshot + ranking integration
- items show / explain commands

## v0.2.2
- Feedback preferences engine
- Weight updates + history

## v0.2.1
- Safe publisher + legacy migration

## v0.2
- Hardening: config, pipeline, tests, docs