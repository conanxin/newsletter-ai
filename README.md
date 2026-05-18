# Newsletter AI (v0.2.1 - Legacy Migration + Safe Publisher)

Local-first daily newsletter pipeline with full safety guarantees.

**Recommended entry points**:
- `newsletter-ai daily [--dry-run] [--no-publish]`
- `make smoke / make daily / make health / make status`

## Quick Safety Flow (new machine)

```bash
make install
make smoke                    # dry-run, zero risk
newsletter-ai daily --dry-run
newsletter-ai daily --no-publish
# Only after configuring TELEGRAM_* env vars:
newsletter-ai daily
```

## Modes

- `--dry-run`: No network, no Telegram, uses fixtures/simulation
- `--no-publish`: Generate digest + snapshot, skip Telegram send
- Default `daily`: Attempts publish only if token+chat_id present (otherwise fails safely)

## Telegram Configuration

Set in environment or .env:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Never commit these.

## Legacy Scripts

All original scripts have been moved to `legacy/v0.1/scripts/`.
Active `scripts/` now contain thin wrappers that delegate to `newsletter-ai` CLI.

Directly running legacy scripts is discouraged.

See MIGRATION.md and docs/OPERATIONS.md for details.