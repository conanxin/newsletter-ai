# v0.2.1 Migration Notes

## Legacy Script Handling
- All scripts containing hard-coded `/mnt/d/...` paths moved to `legacy/v0.1/scripts/`
- Active `scripts/run_daily_pipeline.py` and `check_pipeline_status.py` are now thin wrappers
- Wrappers print deprecation warning and delegate to `newsletter-ai` CLI
- Makefile targets updated to prefer new CLI

## Publisher Layer
- New `src/newsletter_ai/publisher.py` provides DryRunPublisher and TelegramPublisher
- Real Telegram send only happens when both token and chat_id are present
- `--dry-run` and `--no-publish` never attempt real send

## Recommended Commands
Always start with:
1. make smoke
2. newsletter-ai daily --dry-run
3. newsletter-ai daily --no-publish

Only then consider real publish after setting TELEGRAM_* variables.