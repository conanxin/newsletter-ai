"""Ranking engine v0.2.2 that respects learned preferences."""

from typing import Any, Dict, List
from .config import load_config
from .feedback import load_preferences


def score_item(item: Dict[str, Any], prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Compute score with breakdown."""
    source_w = prefs.get("source_weights", {}).get(item.get("source", ""), 1.0)
    topic_w = 1.0
    for tag in item.get("topic_tags", []):
        topic_w *= prefs.get("topic_weights", {}).get(tag, 1.0)
    style_w = 1.0
    for tag in item.get("style_tags", []):
        style_w *= prefs.get("style_weights", {}).get(tag, 1.0)

    base = item.get("base_score", 0.5)
    score = base * source_w * topic_w * style_w

    return {
        "score": round(score, 4),
        "score_breakdown": {
            "base": base,
            "source_weight": round(source_w, 3),
            "topic_weight": round(topic_w, 3),
            "style_weight": round(style_w, 3),
        },
        "source_weight": round(source_w, 3),
        "topic_weight": round(topic_w, 3),
        "style_weight": round(style_w, 3),
    }


def rank_items(items: List[Dict], cfg: Dict = None) -> List[Dict]:
    """Rank items using learned preferences."""
    if cfg is None:
        cfg = load_config()
    prefs = load_preferences(cfg["DATA_DIR"])

    scored = []
    for item in items:
        scored_item = item.copy()
        scored_item.update(score_item(item, prefs))
        scored.append(scored_item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored