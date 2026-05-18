"""Ranking respects learned preferences."""

from newsletter_ai.ranking import score_item


def test_source_weight_affects_score():
    item = {"source": "goodsource", "base_score": 0.5, "topic_tags": [], "style_tags": []}
    prefs = {"source_weights": {"goodsource": 2.0}, "topic_weights": {}, "style_weights": {}}
    scored = score_item(item, prefs)
    assert scored["score"] > 0.9
    assert scored["source_weight"] == 2.0
    assert "score_breakdown" in scored


def test_dislike_lowers_score():
    item = {"source": "badsource", "base_score": 0.5, "topic_tags": ["crypto"], "style_tags": []}
    prefs = {"source_weights": {"badsource": 0.5}, "topic_weights": {"crypto": 0.3}, "style_weights": {}}
    scored = score_item(item, prefs)
    assert scored["score"] < 0.2