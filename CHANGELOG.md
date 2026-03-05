# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-05

### Added
- End-to-end daily pipeline for Newsletter generation (fetch/filter/rank/digest/publish).
- Source-specific filtering profiles (`data/state/source_profiles.json`).
- Feedback loop (`/fb`) with preference updates and reranking.
- Health reporting with trusted-snippet metrics and threshold alerts.
- One-command release validator (`scripts/validate_release.py`) with terminal/JSON/Markdown outputs.
- Make shortcuts (`make validate`, `validate-smoke`, `daily`, `status`).

### Improved
- Noise reduction heuristics for navigation/section-like entries.
- Site-aware snippet extraction/scoring for `sidebar.io`, `kottke.org`, `the-syllabus.com`.
- Readability cleanup for punctuation, entities, and snippet tails.

### Notes
- Runtime artifacts and personal state are excluded from git by default.
