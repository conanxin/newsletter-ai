"""Feedback event schema and JSONL tests."""

import tempfile
from pathlib import Path
from newsletter_ai.feedback import record_feedback_event


def test_feedback_event_schema_and_append():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        event = record_feedback_event(
            data_dir,
            action="like",
            item_index=1,
            source="example.com",
            topic_tags=["ai"],
        )
        assert event["event_id"]
        assert event["action"] == "like"
        assert event["source"] == "example.com"

        events_file = data_dir / "state" / "feedback_events.jsonl"
        assert events_file.exists()
        content = events_file.read_text()
        assert "like" in content