#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
LATEST = BASE / 'data' / 'normalized' / 'latest.json'
OUT = BASE / 'output'
SNIPPET_STATS = OUT / 'latest-snippet-stats.json'
TRUSTED_HITRATE_THRESHOLD = 0.5


def main():
    d = json.loads(LATEST.read_text(encoding='utf-8'))
    items = d.get('items', [])
    dropped = d.get('dropped', {})
    per_source = Counter([x.get('source','unknown') for x in items])

    report = {
        'generated_at': datetime.now().isoformat(),
        'target_date': d.get('target_date'),
        'raw_count': d.get('raw_count', 0),
        'dedup_count': d.get('dedup_count', 0),
        'filtered_count': d.get('filtered_count', 0),
        'errors_count': len(d.get('errors', [])),
        'dropped': dropped,
        'per_source': dict(per_source),
    }

    snippet_stats = None
    snippet_alert = None
    if SNIPPET_STATS.exists():
        try:
            snippet_stats = json.loads(SNIPPET_STATS.read_text(encoding='utf-8'))
            report['snippet_stats'] = snippet_stats

            top8_rate = float(snippet_stats.get('top8', {}).get('trusted_hit_rate', 0.0))
            all_rate = float(snippet_stats.get('filtered_all', {}).get('trusted_hit_rate', 0.0))
            need_alert = top8_rate < TRUSTED_HITRATE_THRESHOLD or all_rate < TRUSTED_HITRATE_THRESHOLD
            snippet_alert = {
                'enabled': True,
                'threshold': TRUSTED_HITRATE_THRESHOLD,
                'top8_rate': top8_rate,
                'filtered_rate': all_rate,
                'triggered': need_alert,
                'message': '可信片段命中率低于阈值，建议人工复核今日 Digest。' if need_alert else '可信片段命中率达标。'
            }
            report['snippet_alert'] = snippet_alert
        except Exception:
            snippet_stats = None

    OUT.mkdir(parents=True, exist_ok=True)
    j = OUT / 'latest-health.json'
    t = OUT / 'latest-health.txt'
    j.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = [
        '📊 今日抓取健康报告',
        f"- 目标日期: {report['target_date']}",
        f"- 原始条目: {report['raw_count']}",
        f"- 去重后: {report['dedup_count']}",
        f"- 最终保留: {report['filtered_count']}",
        f"- 错误数: {report['errors_count']}",
        '- 来源分布:'
    ]
    for src, n in per_source.items():
        lines.append(f"  - {src}: {n}")
    lines.append('- 主要过滤原因:')
    for k, v in sorted(dropped.items(), key=lambda kv: kv[1], reverse=True):
        if v:
            lines.append(f"  - {k}: {v}")

    if snippet_stats:
        top8 = snippet_stats.get('top8', {})
        alls = snippet_stats.get('filtered_all', {})
        lines.append('- 可信片段命中率:')
        lines.append(f"  - Top8: {top8.get('trusted_hits', 0)}/{top8.get('total', 0)} ({round(top8.get('trusted_hit_rate', 0)*100, 1)}%)")
        lines.append(f"  - Filtered全量: {alls.get('trusted_hits', 0)}/{alls.get('total', 0)} ({round(alls.get('trusted_hit_rate', 0)*100, 1)}%)")

        if snippet_alert:
            if snippet_alert.get('triggered'):
                lines.append(f"- ⚠️ 告警: {snippet_alert.get('message')} (阈值 {int(TRUSTED_HITRATE_THRESHOLD*100)}%)")
            else:
                lines.append(f"- ✅ 告警状态: {snippet_alert.get('message')} (阈值 {int(TRUSTED_HITRATE_THRESHOLD*100)}%)")

        lines.append('- 片段来源分布（Top8）:')
        for k, v in top8.get('source_counts', {}).items():
            lines.append(f"  - {k}: {v}")

        lines.append('- 片段来源分布（Filtered全量）:')
        for k, v in alls.get('source_counts', {}).items():
            lines.append(f"  - {k}: {v}")

        lines.append('- 片段拒绝原因（Top8）:')
        rr_top8 = top8.get('reject_reason_counts', {})
        if rr_top8:
            for k, v in rr_top8.items():
                lines.append(f"  - {k}: {v}")
        else:
            lines.append('  - 无')

        lines.append('- 片段拒绝原因（Filtered全量）:')
        rr_all = alls.get('reject_reason_counts', {})
        if rr_all:
            for k, v in rr_all.items():
                lines.append(f"  - {k}: {v}")
        else:
            lines.append('  - 无')

    t.write_text('\n'.join(lines), encoding='utf-8')
    print('HEALTH_JSON=' + str(j))
    print('HEALTH_TXT=' + str(t))


if __name__ == '__main__':
    main()
