"""Digest Sectioning by Topic for v0.3.3.

Partitions items into sections based on topic_tags / source / style_tags.
Global item_index is preserved and never renumbered.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Section:
    section_id: str
    section_label: str
    items: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def top_sources(self) -> List[str]:
        sources = [item.get("source", "unknown") for item in self.items]
        return list(dict.fromkeys(sources))[:5]


def assign_section(item: Dict[str, Any]) -> tuple[str, str]:
    """
    Assign a section for an item.
    Priority:
    1. First topic in topic_tags
    2. Fallback to source
    3. Fallback to first style_tag
    4. "other"
    """
    topic_tags = item.get("topic_tags", []) or []
    source = item.get("source", "")
    style_tags = item.get("style_tags", []) or []

    if topic_tags:
        topic = topic_tags[0]
        return _normalize_section_id(topic), topic

    if source:
        return _normalize_section_id(source), source

    if style_tags:
        style = style_tags[0]
        return _normalize_section_id(style), style

    return "other", "其他值得关注"


def _normalize_section_id(label: str) -> str:
    """Normalize label to a safe section id."""
    label = label.strip().lower()
    label = label.replace(" ", "_").replace("/", "_")
    return label or "other"


def group_items_into_sections(items: List[Dict[str, Any]]) -> List[Section]:
    """Group items into sections while preserving original order and global index."""
    section_map: Dict[str, Section] = {}

    for item in items:
        section_id, section_label = assign_section(item)
        if section_id not in section_map:
            section_map[section_id] = Section(
                section_id=section_id,
                section_label=section_label
            )
        section_map[section_id].items.append(item)

    # Preserve the order sections first appear in the ranked list
    ordered_sections = []
    seen = set()
    for item in items:
        sid, _ = assign_section(item)
        if sid not in seen:
            seen.add(sid)
            ordered_sections.append(section_map[sid])

    return ordered_sections


def render_section_summary(sections: List[Section]) -> str:
    """Optional helper for section distribution summary."""
    lines = ["## Section Distribution", ""]
    for sec in sections:
        lines.append(f"- {sec.section_label}: {sec.item_count} items")
    return "\n".join(lines)