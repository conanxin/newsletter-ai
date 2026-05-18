# Operations v0.2.1

## Safe Daily Run Order
1. `make install`
2. `make smoke` (or `newsletter-ai daily --dry-run`)
3. `newsletter-ai daily --no-publish`
4. Configure TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
5. `newsletter-ai daily` (only when ready)

## Publisher Modes
- DryRunPublisher: always safe snapshot
- TelegramPublisher: real send only with valid credentials and explicit call

## Legacy
Old scripts live in legacy/v0.1/scripts/. Do not run them directly in production.