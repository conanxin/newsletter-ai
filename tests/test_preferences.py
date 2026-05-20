"""Preferences update and history tests."""

import tempfile
from pathlib import Path
from newsletter_ai.feedback import update_preferences, load_preferences


def test_like_updates_weights_and_history():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        result = update_preferences(data_dir, "like", source="techcrunch", topic_tags=["ai"])
        assert len(result["changed"]) > 0
        assert "techcrunch" in result["after"]["source_weights"]

        prefs = load_preferences(data_dir)
        assert prefs["source_weights"]["techcrunch"] > 1.0

        history = (data_dir / "state" / "preferences_history.jsonl").read_text()
        assert "feedback:like" in history