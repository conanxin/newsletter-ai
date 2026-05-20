# Release Notes v0.2.5

## Stable Capabilities
- Local RSS fixture dry-run (no network)
- Full pipeline: normalize → rank → snapshot → render
- Feedback with preference learning
- items show / explain / feedback closed loop
- Release gate (make release-check)

## Available Commands
- make release-check
- newsletter-ai daily --dry-run --fixtures tests/fixtures/rss/
- newsletter-ai items show
- newsletter-ai feedback "like 1" --dry-run

## Safety Boundaries
- Never sends Telegram without token
- All tests use fixtures
- output/ and data/state/ git-ignored
- No real network in dry-run

## Not Included
- Real RSS fetch
- LLM content generation
- Hosted backend

## Known Risks
- None critical

## Recommended Daily Flow
1. make release-check
2. newsletter-ai daily --dry-run --fixtures tests/fixtures/rss/
3. newsletter-ai items show
4. newsletter-ai feedback "like 1" --dry-run
5. newsletter-ai prefs explain