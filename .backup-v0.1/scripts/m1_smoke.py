#!/usr/bin/env python3
from pathlib import Path
import json

base = Path('/mnt/d/obsidian_nov/nov/newsletter')
required_dirs = [
    'data/raw', 'data/normalized', 'data/state', 'templates', 'output', 'scripts'
]
for d in required_dirs:
    p = base / d
    print(f"DIR {d}:", 'OK' if p.exists() else 'MISSING')

prefs = json.loads((base/'data/state/preferences.json').read_text(encoding='utf-8'))
sources = json.loads((base/'data/state/sources.json').read_text(encoding='utf-8'))
print('PREF_KEYS', sorted(prefs.keys()))
print('RSS_COUNT', len(sources.get('rss', [])))
print('TEMPLATE_EXISTS', (base/'templates/digest_template.md').exists())
