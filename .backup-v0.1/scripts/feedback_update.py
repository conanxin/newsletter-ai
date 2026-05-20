#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
PREF = BASE / 'data' / 'state' / 'preferences.json'
LATEST = BASE / 'data' / 'normalized' / 'latest.json'

LABEL_DELTA = {
    'like': 0.20,
    'neutral': 0.00,
    'dislike': -0.20,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def ensure_pref_schema(prefs: dict):
    prefs.setdefault('updated_at', None)
    prefs.setdefault('topic_weights', {})
    prefs.setdefault('source_weights', {})
    prefs.setdefault('style_weights', {})
    prefs.setdefault('feedback_log', [])


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


def clamp(v: float, lo: float = 0.1, hi: float = 3.0):
    return max(lo, min(hi, v))


def apply_feedback(item_id: str, label: str, note: str = ''):
    if label not in LABEL_DELTA:
        raise SystemExit(f'invalid label: {label} (use like|neutral|dislike)')

    prefs = load_json(PREF)
    ensure_pref_schema(prefs)

    latest = load_json(LATEST)
    item = next((x for x in latest.get('items', []) if x.get('id') == item_id), None)
    if not item:
        raise SystemExit(f'item id not found in latest.json: {item_id}')

    delta = LABEL_DELTA[label]
    src = item.get('source') or 'unknown'
    style = detect_style(item)
    topics = detect_topics(item)

    sw = prefs['source_weights'].get(src, 1.0)
    prefs['source_weights'][src] = round(clamp(sw + delta), 3)

    stw = prefs['style_weights'].get(style, 1.0)
    prefs['style_weights'][style] = round(clamp(stw + delta), 3)

    for t in topics:
        tw = prefs['topic_weights'].get(t, 1.0)
        prefs['topic_weights'][t] = round(clamp(tw + delta), 3)

    entry = {
        'item_id': item_id,
        'label': label,
        'at': now_iso(),
        'source': src,
        'title': item.get('title', ''),
        'topics': topics,
        'style': style,
        'note': note,
    }
    prefs['feedback_log'].append(entry)
    prefs['updated_at'] = now_iso()

    PREF.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding='utf-8')

    print('UPDATED_PREF=' + str(PREF))
    print('ITEM=' + item.get('title', '')[:120])
    print('LABEL=' + label)
    print('SOURCE_WEIGHT=' + str(prefs['source_weights'][src]))
    print('STYLE=' + style)
    print('STYLE_WEIGHT=' + str(prefs['style_weights'][style]))
    for t in topics:
        print(f'TOPIC_{t}=' + str(prefs['topic_weights'][t]))


def main():
    ap = argparse.ArgumentParser(description='Record feedback and update preference weights')
    ap.add_argument('--item-id', required=True)
    ap.add_argument('--label', required=True, choices=['like', 'neutral', 'dislike'])
    ap.add_argument('--note', default='')
    args = ap.parse_args()
    apply_feedback(args.item_id, args.label, args.note)


if __name__ == '__main__':
    main()
