"""Data models for v0.2.2 feedback and preferences."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FeedbackEvent:
    event_id: str
    created_at: str
    action: str
    item_id: Optional[str] = None
    item_index: Optional[int] = None
    source: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    topic_tags: List[str] = field(default_factory=list)
    style_tags: List[str] = field(default_factory=list)
    delta: float = 0.0
    note: Optional[str] = None
    run_id: Optional[str] = None


@dataclass
class Preferences:
    source_weights: dict = field(default_factory=dict)
    topic_weights: dict = field(default_factory=dict)
    style_weights: dict = field(default_factory=dict)
    version: str = "0.2.2"