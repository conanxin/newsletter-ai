# Architecture v0.2.2

- feedback.py: event recording + preference update + history
- ranking.py: score_item with source/topic/style weights
- models.py: FeedbackEvent + Preferences dataclasses
- health.py: real status of feedback/preferences/publisher safety
- cli.py: feedback + prefs commands
- All writes go through DATA_DIR from config
- Legacy targets moved to explicit `legacy-validate`