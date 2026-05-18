"""Basic deduplication for v0.2.5."""

from typing import List, Dict, Any


def dedupe_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates by URL or (title + source). Keep first seen."""
    seen_urls = set()
    seen_titles = set()
    result = []

    for item in items:
        url = item.get("url", "")
        title_source = (item.get("title", ""), item.get("source", ""))

        if url and url in seen_urls:
            continue
        if not url and title_source in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        else:
            seen_titles.add(title_source)

        result.append(item)

    return result