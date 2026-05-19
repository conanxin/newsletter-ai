# Changelog

## v0.3.5 (2026-05)
- Fixture-based End-to-End Regression
- New fixture: tests/fixtures/e2e_items.json (7 items covering AI/LLM, Business/Strategy, Media/Culture, near-duplicate, missing topic_tags fallback, multiple sources, style_tags)
- New E2E test: tests/test_e2e_fixture_flow.py
- Full chain coverage:
  fixture → ranking → snapshot (global item_index) → sectioned digest (markdown + telegram) → quality report (section_distribution + warnings) → feedback resolution → preferences_history.jsonl
- Test runs completely offline (no network, no Telegram send, no LLM)
- Regresses quality sections / sources / duplicates
- Regresses feedback "like 1" item_index parsing and dry-run behavior
- All writes go to tmp_path during tests (no pollution of real data/state)
- make release-check and make validate now cover the full fixture flow

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