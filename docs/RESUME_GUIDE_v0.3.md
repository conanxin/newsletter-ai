# Resume Guide v0.3

## v0.3 Goal: Content Quality Enhancement

1. Better summary structure
2. Source quality tracking
3. Duplicate similarity improvement
4. Topic/style classifier improvement
5. Real RSS adapter (behind safe no-publish)
6. Digest sections
7. Daily quality report

## Do Not Repeat
- LLM long-form generation
- Hosted backend
- GitHub Pages showcase
- Hermes wiki ingest
- Telegram interactive buttons

## Where to Start
1. Review tests/test_pipeline_rss_fixture_e2e.py
2. Look at src/newsletter_ai/rss.py + dedupe.py
3. Start with better dedupe similarity

## Key Files Index
- src/newsletter_ai/rss.py
- src/newsletter_ai/dedupe.py
- tests/fixtures/rss/
- docs/ARCHITECTURE.md

## Recommended First v0.3 Command
newsletter-ai daily --dry-run --fixtures tests/fixtures/rss/ --with-quality-report (future)