"""Section-aware rendering for v0.3.3 Digest Sectioning by Topic."""

from typing import List, Dict, Any
from .sections import Section, group_items_into_sections


def render_markdown_digest(sections: List[Section]) -> str:
    """Render digest as Markdown with section headings, using global item_index."""
    lines = ["# Newsletter Digest", ""]

    for section in sections:
        lines.append(f"## {section.section_label}")
        lines.append("")

        for item in section.items:
            idx = item.get("global_index") or item.get("index") or "?"
            title = item.get("title", "Untitled")
            source = item.get("source", "unknown")
            summary = item.get("summary", "")
            url = item.get("url", "")

            lines.append(f"{idx}. {title}")
            if source:
                lines.append(f"   来源：{source}")
            if summary:
                lines.append(f"   摘要：{summary}")
            if url:
                lines.append(f"   链接：{url}")
            lines.append("")

    return "\n".join(lines).strip()


def render_telegram_digest(sections: List[Section]) -> str:
    """Render concise Telegram text with section headings."""
    parts = []

    for section in sections:
        parts.append(f"【{section.section_label}】")

        for item in section.items:
            idx = item.get("global_index") or item.get("index") or "?"
            title = item.get("title", "Untitled")
            source = item.get("source", "")
            url = item.get("url", "")

            line = f"{idx}. {title}"
            if source:
                line += f" — {source}"
            parts.append(line)

            if url:
                parts.append(f"链接：{url}")

        parts.append("")

    return "\n".join(parts).strip()