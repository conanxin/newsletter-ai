#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
import subprocess
from pathlib import Path

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
APPLY = BASE / 'scripts' / 'feedback_from_rank.py'


def parse_fb(text: str):
    # /fb <rank> <like|neutral|dislike> [note...]
    m = re.match(r"^\s*/fb\s+(\d+)\s+(like|neutral|dislike)(?:\s+(.*))?\s*$", text, re.I)
    if not m:
        raise ValueError('invalid command format')
    rank = int(m.group(1))
    label = m.group(2).lower()
    note = (m.group(3) or '').strip()
    return rank, label, note


def main():
    ap = argparse.ArgumentParser(description='Parse /fb command and apply preference update')
    ap.add_argument('--text', required=True, help='raw command text, e.g. "/fb 2 like reason"')
    args = ap.parse_args()

    rank, label, note = parse_fb(args.text)
    cmd = ['python3', str(APPLY), '--rank', str(rank), '--label', label]
    if note:
        cmd += ['--note', note]

    print('PARSED', {'rank': rank, 'label': label, 'note': note})
    subprocess.check_call(cmd)
    print('DONE')


if __name__ == '__main__':
    main()
