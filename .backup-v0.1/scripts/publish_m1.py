#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
DIGEST = BASE / 'output' / 'latest-digest.md'
FEEDBACK_PROMPT = BASE / 'output' / 'latest-feedback-prompt.txt'
HEALTH_TXT = BASE / 'output' / 'latest-health.txt'
OUT_DIR = Path('/mnt/d/obsidian_nov/nov/Inbox/每日总结')


def main():
    if not DIGEST.exists():
        raise SystemExit(f'missing digest: {DIGEST}')
    text = DIGEST.read_text(encoding='utf-8')

    health_block = ''
    if HEALTH_TXT.exists():
        health_block = '\n\n---\n\n' + HEALTH_TXT.read_text(encoding='utf-8')

    feedback_block = ''
    if FEEDBACK_PROMPT.exists():
        feedback_block = '\n\n---\n\n' + FEEDBACK_PROMPT.read_text(encoding='utf-8')

    final_text = text + health_block + feedback_block

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    out_file = OUT_DIR / f'{date_str}-newsletter.md'
    out_file.write_text(final_text, encoding='utf-8')

    # telegram payload (keep concise)
    preview = final_text
    if len(preview) > 3200:
        preview = preview[:3200] + '\n\n...(已截断，完整内容见 Obsidian 文件)'

    payload_file = BASE / 'output' / 'latest-telegram.txt'
    payload_file.write_text(preview, encoding='utf-8')

    print('OBSIDIAN_FILE=' + str(out_file))
    print('TELEGRAM_PAYLOAD=' + str(payload_file))
    print('CHARS=' + str(len(preview)))
    print('HAS_FEEDBACK_BLOCK=' + str(bool(feedback_block)))


if __name__ == '__main__':
    main()
