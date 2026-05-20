# Newsletter AI (v0.2.2 - Feedback + Preference Engine)

Local-first daily newsletter with real feedback-driven ranking.

## v0.2.2 Highlights
- Real feedback engine (like/dislike/source_up/topic_down etc.)
- Preferences learned from user actions
- Ranking now uses source/topic/style weights
- Health report shows feedback count and safety status
- All feedback writes audit trail (events + history)

## Feedback Usage
```bash
newsletter-ai feedback "like 1"
newsletter-ai feedback "dislike 2"
newsletter-ai feedback "source_up Stratechery"
newsletter-ai feedback "topic_down crypto"
newsletter-ai feedback "save 3 --note 'deep dive'"
newsletter-ai prefs show
newsletter-ai prefs explain
```

## Safety
- `--dry-run` on feedback never writes
- No real Telegram send without credentials
- Weights clamped 0.1~3.0

See docs/OPERATIONS.md for full workflow.