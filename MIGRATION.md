# v0.2.2 Migration

- Feedback is now real: writes events.jsonl + updates preferences.json + history
- Ranking respects learned weights
- make validate now uses new health/status
- Legacy validate moved to explicit `make legacy-validate`
- All feedback commands support --dry-run