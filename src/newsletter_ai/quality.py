"""Source Quality Tracking and Digest Quality Report for newsletter-ai v0.3.1"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

@dataclass
class SourceQuality:
    source: str
    feed_path: str
    status: str = "ok"  # ok, empty, malformed, failed
    raw_item_count: int = 0
    normalized_item_count: int = 0
    duplicate_removed_count: int = 0
    final_item_count: int = 0
    top_item_titles: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "source_details": [asdict(s) for s in self.source_details]
        }

def generate_quality_report(
    run_id: str,
    sources: List[Dict[str, Any]],
    items_after_dedupe: List[Dict[str, Any]],
    duplicate_count: int = 0,
    malformed_count: int = 0,
    empty_count: int = 0,
) -> QualityReport:
    """Generate quality report from pipeline data."""
    now = datetime.now().isoformat()
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

    # Simple distributions
    topic_dist = {}
    source_dist = {}
    for item in items_after_dedupe:
        topic = item.get("topic", "unknown")
        source = item.get("source", "unknown")
        topic_dist[topic] = topic_dist.get(topic, 0) + 1
        source_dist[source] = source_dist.get(source, 0) + 1

    report.topic_distribution = topic_dist
    report.source_distribution = source_dist
    report.output_item_count = len(items_after_dedupe)

    # Build source details
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
        report.source_details.append(sq)

    return report

def save_quality_report(report: QualityReport, output_dir: Path) -> Dict[str, Path]:
    """Save quality report to json and md files."""
    quality_dir = output_dir / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    latest_json = quality_dir / "latest_quality.json"
    hist_json = quality_dir / f"quality-{timestamp}.json"
    latest_md = quality_dir / "latest_quality.md"

    data = report.to_dict()

    # Write JSON
    latest_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    hist_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write human-readable MD
    md_content = generate_quality_md(report)
    latest_md.write_text(md_content, encoding="utf-8")

    return {"json": latest_json, "historical": hist_json, "md": latest_md}

def generate_quality_md(report: QualityReport) -> str:
    """Generate human-readable markdown quality report."""
    lines = [
        "# Newsletter Quality Report",
        "",
        f"- Run ID: {report.run_id}",
        f"- Created: {report.created_at}",
        f"- Sources checked: {report.sources_checked}",
        f"- Items raw: {report.items_raw}",
        f"- Items after dedupe: {report.items_after_dedupe}",
        f"- Duplicate removed: {report.duplicate_count}",
        f"- Empty feeds: {report.empty_feed_count}",
        f"- Malformed feeds: {report.malformed_feed_count}",
        "",
        "## Source status",
        "",
        "| Source | Status | Raw | Normalized | Final | Warnings |",
        "|---|---|---:|---:|---:|---|",
    ]

    for s in report.source_details:
        warn_str = "; ".join(s.warnings) if s.warnings else "-"
        lines.append(
            f"| {s.source} | {s.status} | {s.raw_item_count} | {s.normalized_item_count} | {s.final_item_count} | {warn_str} |"
        )

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

    # Simplified top items explanation
    for i, s in enumerate(report.source_details[:5], 1):
        if s.top_item_titles:
            lines.append(f"{i}. {s.top_item_titles[0]} (source: {s.source})")

    lines.append("")
    lines.append("质量报告仅基于本地 fixture 数据生成，未请求外网。")

    return "\n".join(lines)