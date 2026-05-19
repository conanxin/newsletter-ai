"""Source Quality Tracking, Scoring and Digest Quality Report for newsletter-ai v0.3.2 + v0.3.3 section_distribution"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

@dataclass
class SourceQuality:
    source: str
    feed_path: str
    status: str = "ok"
    raw_item_count: int = 0
    normalized_item_count: int = 0
    duplicate_removed_count: int = 0
    final_item_count: int = 0
    top_item_titles: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_quality_score: float = 0.0
    source_score_breakdown: Dict[str, float] = field(default_factory=dict)
    recommended_action: str = "keep"

@dataclass
class QualityReport:
    run_id: str
    created_at: str
    sources_checked: int = 0
    feeds_loaded: int = 0
    feeds_failed: int = 0
    items_raw: int = 0
    items_normalized: int = 0
    items_after_dedupe: int = 0
    duplicate_count: int = 0
    malformed_feed_count: int = 0
    empty_feed_count: int = 0
    output_item_count: int = 0
    topic_distribution: Dict[str, int] = field(default_factory=dict)
    style_distribution: Dict[str, int] = field(default_factory=dict)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    source_details: List[SourceQuality] = field(default_factory=list)
    duplicate_reason_counts: Dict[str, int] = field(default_factory=dict)
    fuzzy_duplicate_count: int = 0
    section_distribution: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "source_details": [asdict(s) for s in self.source_details]
        }

def _calculate_source_score(sq: SourceQuality) -> tuple[float, Dict[str, float], str]:
    """Calculate source quality score 0.0-1.0 with breakdown."""
    feed_status_score = {
        "ok": 1.0,
        "empty": 0.45,
        "malformed": 0.15,
        "failed": 0.0
    }.get(sq.status, 0.5)

    item_yield = sq.normalized_item_count / max(sq.raw_item_count, 1)
    item_yield_score = min(1.0, item_yield * 1.1)

    dedupe_penalty = max(0.0, 0.25 * (sq.duplicate_removed_count / max(sq.raw_item_count, 1)))
    final_item_score = 0.15 if sq.final_item_count > 0 else 0.0
    warning_penalty = max(0.0, 0.1 * len(sq.warnings))

    score = feed_status_score + item_yield_score + final_item_score - dedupe_penalty - warning_penalty
    score = max(0.0, min(1.0, round(score, 3)))

    breakdown = {
        "feed_status_score": round(feed_status_score, 3),
        "item_yield_score": round(item_yield_score, 3),
        "dedupe_penalty": round(dedupe_penalty, 3),
        "final_item_score": round(final_item_score, 3),
        "warning_penalty": round(warning_penalty, 3)
    }

    if score >= 0.75:
        action = "keep"
    elif score >= 0.45:
        action = "watch"
    elif score >= 0.25:
        action = "review"
    else:
        action = "disable_candidate"

    return score, breakdown, action

def generate_quality_report(
    run_id: str,
    sources: List[Dict[str, Any]],
    items_after_dedupe: List[Dict[str, Any]],
    duplicate_records: List[Dict[str, Any]] = None,
    duplicate_count: int = 0,
    malformed_count: int = 0,
    empty_count: int = 0,
) -> QualityReport:
    """Generate quality report with source scoring and duplicate reasons."""
    now = datetime.now().isoformat()
    duplicate_records = duplicate_records or []

    report = QualityReport(
        run_id=run_id,
        created_at=now,
        sources_checked=len(sources),
        feeds_loaded=len([s for s in sources if s.get("status") == "ok"]),
        feeds_failed=len([s for s in sources if s.get("status") == "failed"]),
        items_raw=sum(s.get("raw_item_count", 0) for s in sources),
        items_normalized=sum(s.get("normalized_item_count", 0) for s in sources),
        items_after_dedupe=len(items_after_dedupe),
        duplicate_count=duplicate_count,
        malformed_feed_count=malformed_count,
        empty_feed_count=empty_count,
    )

    # Calculate duplicate reason counts
    reason_counts = {}
    fuzzy_count = 0
    for rec in duplicate_records:
        reason = rec.get("duplicate_reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if reason == "fuzzy_title_source":
            fuzzy_count += 1

    report.duplicate_reason_counts = reason_counts
    report.fuzzy_duplicate_count = fuzzy_count

    # Topic and source distribution
    topic_dist, source_dist = {}, {}
    for item in items_after_dedupe:
        topic = item.get("topic", "unknown")
        src = item.get("source", "unknown")
        topic_dist[topic] = topic_dist.get(topic, 0) + 1
        source_dist[src] = source_dist.get(src, 0) + 1

    report.topic_distribution = topic_dist
    report.source_distribution = source_dist
    report.output_item_count = len(items_after_dedupe)

    # Build source details with scoring
    for s in sources:
        sq = SourceQuality(
            source=s.get("source", "unknown"),
            feed_path=s.get("feed_path", ""),
            status=s.get("status", "ok"),
            raw_item_count=s.get("raw_item_count", 0),
            normalized_item_count=s.get("normalized_item_count", 0),
            duplicate_removed_count=s.get("duplicate_removed_count", 0),
            final_item_count=s.get("final_item_count", 0),
            top_item_titles=s.get("top_item_titles", [])[:3],
            warnings=s.get("warnings", []),
        )
        score, breakdown, action = _calculate_source_score(sq)
        sq.source_quality_score = score
        sq.source_score_breakdown = breakdown
        sq.recommended_action = action
        report.source_details.append(sq)

    # v0.3.3: populate section_distribution
    try:
        from .sections import group_items_into_sections
        sections = group_items_into_sections(items_after_dedupe)
        report.section_distribution = {
            sec.section_id: {
                "section_label": sec.section_label,
                "item_count": sec.item_count,
                "sources": sec.top_sources,
                "topic_tags": list({tag for item in sec.items for tag in item.get("topic_tags", [])})
            }
            for sec in sections
        }
    except Exception:
        report.section_distribution = {}

    return report

def save_quality_report(report: QualityReport, output_dir: Path) -> Dict[str, Path]:
    quality_dir = output_dir / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    latest_json = quality_dir / "latest_quality.json"
    hist_json = quality_dir / f"quality-{timestamp}.json"
    latest_md = quality_dir / "latest_quality.md"

    data = report.to_dict()
    latest_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    hist_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    md_content = generate_quality_md(report)
    latest_md.write_text(md_content, encoding="utf-8")

    return {"json": latest_json, "historical": hist_json, "md": latest_md}

def generate_quality_md(report: QualityReport) -> str:
    lines = [
        "# Newsletter Quality Report",
        "",
        f"- Run ID: {report.run_id}",
        f"- Created: {report.created_at}",
        f"- Sources checked: {report.sources_checked}",
        f"- Items raw: {report.items_raw}",
        f"- Items after dedupe: {report.items_after_dedupe}",
        f"- Duplicate removed: {report.duplicate_count}",
        f"- Fuzzy duplicates: {report.fuzzy_duplicate_count}",
        f"- Empty feeds: {report.empty_feed_count}",
        f"- Malformed feeds: {report.malformed_feed_count}",
        "",
        "## Source quality scores",
        "",
        "| Source | Score | Status | Final items | Duplicate removed | Action |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for s in report.source_details:
        lines.append(
            f"| {s.source} | {s.source_quality_score:.3f} | {s.status} | {s.final_item_count} | {s.duplicate_removed_count} | {s.recommended_action} |"
        )

    lines.extend([
        "",
        "## Duplicate reasons",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ])

    for reason, count in sorted(report.duplicate_reason_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {reason} | {count} |")

    lines.extend([
        "",
        "## Source status",
        "",
        "| Source | Status | Raw | Normalized | Final | Warnings |",
        "|---|---|---:|---:|---:|---|",
    ])

    for s in report.source_details:
        warn_str = "; ".join(s.warnings) if s.warnings else "-"
        lines.append(f"| {s.source} | {s.status} | {s.raw_item_count} | {s.normalized_item_count} | {s.final_item_count} | {warn_str} |")

    lines.extend([
        "",
        "## Topic distribution",
        "",
    ])

    for topic, count in sorted(report.topic_distribution.items(), key=lambda x: -x[1]):
        lines.append(f"- {topic}: {count}")

    lines.extend([
        "",
        "## Why this order",
        "",
        "前 5 条内容排序依据（简化版）：",
    ])

    for i, s in enumerate(report.source_details[:5], 1):
        if s.top_item_titles:
            lines.append(f"{i}. {s.top_item_titles[0]} (source: {s.source})")

    lines.append("")
    lines.append("质量报告仅基于本地 fixture 数据生成，未请求外网。")

    return "\n".join(lines)