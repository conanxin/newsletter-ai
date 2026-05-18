# Architecture v0.2.1

- config.py: dynamic base dir resolution (env > git root > cwd)
- pipeline.py: step-tracked runner + publisher integration
- publisher.py: DryRunPublisher + TelegramPublisher (safe by default)
- cli.py: unified command interface with --dry-run / --no-publish
- legacy/v0.1/scripts/: archived v0.1 implementations (read-only reference)
- scripts/: thin compatibility wrappers only

All network and publish operations go through publisher abstraction.
No real Telegram send without explicit token + non-dry-run.