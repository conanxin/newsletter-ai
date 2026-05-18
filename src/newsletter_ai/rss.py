"""RSS fixture parser for v0.2.5 (no network)."""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List
from hashlib import md5


def parse_rss(xml_content: str, source_name: str = "unknown") -> List[Dict[str, Any]]:
    """Parse RSS XML string into normalized items."""
    items: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return items  # graceful failure on malformed

    channel = root.find("channel")
    if channel is None:
        return items

    feed_title = (channel.findtext("title") or source_name).strip()

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        if not title and not link:
            continue

        # item_id priority: guid > link hash > title+source hash
        if guid:
            item_id = guid
        elif link:
            item_id = md5(link.encode()).hexdigest()[:12]
        else:
            item_id = md5(f"{title}{source_name}".encode()).hexdigest()[:12]

        items.append({
            "item_id": item_id,
            "source": feed_title,
            "title": title,
            "url": link,
            "summary": description[:300] if description else "",
            "published_at": pub_date,
            "topic_tags": [],
            "style_tags": [],
            "raw": {"guid": guid, "link": link},
        })

    return items


def load_rss_file(path: str, source_name: str = None) -> List[Dict[str, Any]]:
    """Load RSS from local file."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    name = source_name or path.split("/")[-1].replace(".xml", "")
    return parse_rss(content, name)