#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
LATEST = BASE / 'data' / 'normalized' / 'latest.json'
PREF = BASE / 'data' / 'state' / 'preferences.json'
OUT = BASE / 'data' / 'normalized'


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def detect_topics(item: dict):
    text = ((item.get('title') or '') + ' ' + (item.get('content_raw') or '')).lower()
    topics = []
    if 'ai' in text or 'openai' in text or 'llm' in text or 'model' in text:
        topics.append('ai_tools')
    if 'adoption' in text or 'growth' in text or 'market' in text or 'business' in text:
        topics.append('business')
    if 'metrics' in text or 'benchmark' in text or 'evaluation' in text:
        topics.append('methodology')
    if not topics:
        topics.append('general')
    return topics


def detect_style(item: dict):
    title = (item.get('title') or '').lower()
    if any(k in title for k in ['how', 'guide', 'playbook']):
        return 'how_to'
    if any(k in title for k in ['why', 'analysis', 'puzzle', 'problem', 'metrics']):
        return 'analysis'
    return 'news'


def score_item(item: dict, prefs: dict):
    src = item.get('source') or 'unknown'
    style = detect_style(item)
    topics = detect_topics(item)

    source_w = prefs.get('source_weights', {}).get(src, 1.0)
    style_w = prefs.get('style_weights', {}).get(style, 1.0)
    topic_ws = [prefs.get('topic_weights', {}).get(t, 1.0) for t in topics]
    topic_w = sum(topic_ws)/len(topic_ws)

    # simple weighted sum (v1)
    score = topic_w * 0.5 + source_w * 0.3 + style_w * 0.2
    return round(score, 4), {
        'source_w': round(source_w, 3),
        'style': style,
        'style_w': round(style_w, 3),
        'topics': topics,
        'topic_w': round(topic_w, 3),
    }


def main(top_n: int = 12):
    data = load_json(LATEST)
    prefs = load_json(PREF)
    items = data.get('items', [])

    baseline = [x.get('title','') for x in items[:top_n]]

    scored = []
    for it in items:
        sc, detail = score_item(it, prefs)
        x = dict(it)
        x['score'] = sc
        x['score_detail'] = detail
        scored.append(x)

    ranked = sorted(scored, key=lambda x: x.get('score', 0), reverse=True)
    ranked_top = ranked[:top_n]

    out = {
        'generated_at': now_iso(),
        'top_n': top_n,
        'baseline_titles': baseline,
        'ranked_titles': [x.get('title','') for x in ranked_top],
        'items': ranked
    }
    out_file = OUT / 'ranked-latest.json'
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('RANKED_FILE=' + str(out_file))
    print('TOP1=' + (ranked_top[0].get('title','') if ranked_top else ''))
    print('BASELINE_TOP3=' + ' | '.join(baseline[:3]))
    print('RANKED_TOP3=' + ' | '.join([x.get('title','') for x in ranked_top[:3]]))


if __name__ == '__main__':
    main()
