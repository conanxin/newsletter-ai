# Newsletter AI (Telegram-first)

A lightweight daily newsletter pipeline that:

- Fetches from configured RSS/web sources
- Keeps only yesterday's items
- Applies noise filtering, de-dup, and per-source caps
- Ranks items with feedback-driven preferences
- Builds digest for Telegram + Obsidian backup
- Produces health/validation reports

## Quick Start

```bash
python3 scripts/run_daily_pipeline.py
python3 scripts/check_pipeline_status.py
python3 scripts/validate_release.py --with-feedback-smoke
```

Or use Make targets:

```bash
make validate
make validate-smoke
make daily
make status
```

## Data & Config

- Source config: `data/state/sources.json`
- Source profile rules: `data/state/source_profiles.json`
- Preferences template: `data/state/preferences.example.json`

Create your local `preferences.json` from the example:

```bash
cp data/state/preferences.example.json data/state/preferences.json
```

## Core Scripts

- `scripts/fetch_rss_minimal.py` — fetch + normalize + filter
- `scripts/rank_items.py` — preference-based ranking
- `scripts/build_digest_minimal.py` — digest generation with snippet quality gates
- `scripts/build_health_report.py` — health + trusted-snippet metrics
- `scripts/validate_release.py` — one-command release validation (terminal + md + json)
- `scripts/run_feedback_pipeline.py` — apply `/fb` feedback and refresh outputs

## Notes

- Runtime artifacts (`data/normalized/`, `output/`) are excluded from git.
- Personal feedback (`data/state/preferences.json`) is excluded from git.
