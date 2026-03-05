#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
RANKED = BASE / 'data' / 'normalized' / 'ranked-latest.json'
OUT = BASE / 'output'


def main(top_n: int = 8):
    data = json.loads(RANKED.read_text(encoding='utf-8'))
    items = data.get('items', [])[:top_n]

    action_map = []
    lines = [
        '📌 反馈指令（复制发送即可）',
        '格式：/fb <rank> <like|neutral|dislike> [备注]',
        '示例：/fb 1 like OpenAI竞争话题优先',
        ''
    ]

    for i, it in enumerate(items, 1):
        action_map.append({
            'rank': i,
            'item_id': it.get('id'),
            'title': it.get('title'),
        })
        lines.append(f"{i}. {it.get('title','(untitled)')}")
        lines.append(f"   like: /fb {i} like")
        lines.append(f"   neutral: /fb {i} neutral")
        lines.append(f"   dislike: /fb {i} dislike")

    OUT.mkdir(parents=True, exist_ok=True)
    map_file = OUT / 'latest-feedback-map.json'
    prompt_file = OUT / 'latest-feedback-prompt.txt'

    map_file.write_text(json.dumps({
        'generated_at': datetime.now().isoformat(),
        'items': action_map
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    prompt_file.write_text('\n'.join(lines), encoding='utf-8')

    print('MAP_FILE=' + str(map_file))
    print('PROMPT_FILE=' + str(prompt_file))
    print('COUNT=' + str(len(action_map)))


if __name__ == '__main__':
    main()
