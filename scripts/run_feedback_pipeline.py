#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
SCRIPTS = BASE / 'scripts'


def run(cmd: list[str]):
    print('RUN:', ' '.join(cmd))
    subprocess.check_call(cmd)


def main():
    ap = argparse.ArgumentParser(description='Apply /fb feedback and refresh ranked digest+publish outputs')
    ap.add_argument('--text', required=True, help='raw feedback command, e.g. "/fb 2 like note"')
    args = ap.parse_args()

    # 1) apply feedback command
    run(['python3', str(SCRIPTS / 'process_feedback_command.py'), '--text', args.text])

    # 2) rebuild ranking and digest outputs
    run(['python3', str(SCRIPTS / 'rank_items.py')])
    run(['python3', str(SCRIPTS / 'build_digest_minimal.py')])
    run(['python3', str(SCRIPTS / 'prepare_feedback_actions.py')])
    run(['python3', str(SCRIPTS / 'publish_m1.py')])

    print('PIPELINE_DONE=1')


if __name__ == '__main__':
    main()
