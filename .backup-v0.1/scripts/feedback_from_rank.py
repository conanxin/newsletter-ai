#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
MAP_FILE = BASE / 'output' / 'latest-feedback-map.json'
UPDATER = BASE / 'scripts' / 'feedback_update.py'


def main():
    ap = argparse.ArgumentParser(description='Apply feedback by ranked index')
    ap.add_argument('--rank', type=int, required=True)
    ap.add_argument('--label', required=True, choices=['like', 'neutral', 'dislike'])
    ap.add_argument('--note', default='')
    args = ap.parse_args()

    m = json.loads(MAP_FILE.read_text(encoding='utf-8'))
    items = m.get('items', [])
    target = next((x for x in items if x.get('rank') == args.rank), None)
    if not target:
        raise SystemExit(f'rank not found: {args.rank}')

    cmd = [
        'python3', str(UPDATER),
        '--item-id', target['item_id'],
        '--label', args.label,
        '--note', args.note or f'from rank {args.rank}'
    ]
    print('RUN', ' '.join(cmd))
    subprocess.check_call(cmd)
    print('APPLIED rank=', args.rank, 'title=', target.get('title'))


if __name__ == '__main__':
    main()
