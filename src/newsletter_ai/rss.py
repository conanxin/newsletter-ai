"""RSS Fixture Parser (v0.3.8)

This module parses local RSS XML fixtures only.
It does not perform any network requests.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_text(element: Optional[ET.Element], tag: str) -> str:
    """Safely get text content from a child element."""
    if element is None:
        return ""
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def parse_rss_xml(xml_text: str) -> List[Dict[str, Any]]:
    """Parse RSS XML text and return a list of raw items."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"Invalid RSS XML: {e}")

    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS XML missing <channel> element")

    channel_title = _get_text(channel, "title")
    items: List[Dict[str, Any]] = []

    for item_elem in channel.findall("item"):
        title = _get_text(item_elem, "title")
        link = _get_text(item_elem, "link")
        description = _get_text(item_elem, "description")
        pub_date = _get_text(item_elem, "pubDate")
        author = _get_text(item_elem, "author")
        category = _get_text(item_elem, "category")

        raw_item = {
            "title": title,
            "link": link,
            "description": description,
            "pubDate": pub_date,
            "author": author,
            "category": category,
            "source": channel_title,
            "raw_source_type": "rss",
        }
        items.append(raw_item)

    return items


def parse_rss_file(path: Path) -> List[Dict[str, Any]]:
    """Parse an RSS XML file from disk."""
    if not path.exists():
        raise FileNotFoundError(f"RSS fixture not found: {path}")

    xml_text = path.read_text(encoding="utf-8")
    return parse_rss_xml(xml_text)