"""Fuzzy dedupe foundation for v0.3.2"""

import difflib
from typing import List, Dict, Any, Tuple

FUZZY_THRESHOLD = 0.92

def normalize_title(title: str) -> str:
    """Normalize title for fuzzy comparison."""
    t = title.lower().strip()
    # remove common punctuation
    for ch in ".,:;!?\"'()[]{}<>":
        t = t.replace(ch, " ")
    # collapse whitespace
    t = " ".join(t.split())
    # remove very common prefixes (optional)
    prefixes = ["the ", "a ", "an "]
    for p in prefixes:
        if t.startswith(p):
            t = t[len(p):]
    return t

def title_similarity(a: str, b: str) -> float:
    """Compute similarity using SequenceMatcher."""
    return difflib.SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()

def dedupe_items(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Perform fuzzy dedupe.
    Returns (kept_items, duplicate_records)
    """
    seen = {}
    kept = []
    duplicates = []

    for item in items:
        source = item.get("source", "unknown")
        title = item.get("title", "")
        url = item.get("url", "")
        item_id = item.get("id", str(len(kept)))

        key = (source, url)
        if key in seen:
            duplicates.append({
                "duplicate_reason": "url",
                "removed_item_id": item_id,
                "kept_item_id": seen[key]
            })
            continue

        # exact title + source
        exact_key = (source, title.lower().strip())
        if exact_key in seen:
            duplicates.append({
                "duplicate_reason": "exact_title_source",
                "removed_item_id": item_id,
                "kept_item_id": seen[exact_key]
            })
            continue

        # fuzzy within same source
        is_duplicate = False
        for (prev_source, prev_title), prev_id in seen.items():
            if prev_source == source:
                sim = title_similarity(title, prev_title)
                if sim >= FUZZY_THRESHOLD:
                    duplicates.append({
                        "duplicate_reason": "fuzzy_title_source",
                        "removed_item_id": item_id,
                        "kept_item_id": prev_id,
                        "similarity": round(sim, 3)
                    })
                    is_duplicate = True
                    break

        if not is_duplicate:
            kept.append(item)
            seen[(source, title)] = item_id
            seen[(source, url)] = item_id   # also track url

    return kept, duplicates