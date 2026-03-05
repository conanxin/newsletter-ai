#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
S = BASE / 'scripts'
LOG_DIR = BASE / 'output' / 'logs'
STATE_DIR = BASE / 'output' / 'state'
ALERT_DIR = BASE / 'output' / 'alerts'
for d in [LOG_DIR, STATE_DIR, ALERT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DAY = datetime.now().strftime('%Y%m%d')
LOG_FILE = LOG_DIR / f'daily-{DAY}.log'
STATUS_FILE = STATE_DIR / 'last-run-status.json'
ALERT_FILE = ALERT_DIR / f'alert-{DAY}.txt'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(text: str):
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(text + '\n')


def run(cmd: list[str]):
    log(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.stdout:
        log(p.stdout.rstrip())
    if p.stderr:
        log('[stderr]')
        log(p.stderr.rstrip())
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}")


def write_status(ok: bool, failed_step: str = '', error: str = ''):
    payload = {
        'time': now_iso(),
        'ok': ok,
        'failed_step': failed_step,
        'error': error,
        'log_file': str(LOG_FILE),
    }
    STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def write_alert(failed_step: str, error: str):
    text = (
        '⚠️ Newsletter Daily Pipeline 失败\n\n'
        f'- 时间: {now_iso()}\n'
        f'- 失败步骤: {failed_step}\n'
        f'- 错误: {error}\n'
        f'- 日志: {LOG_FILE}\n\n'
        '建议: 检查日志后手动重跑\n'
        f'python3 {S / "run_daily_pipeline.py"}\n'
    )
    ALERT_FILE.write_text(text, encoding='utf-8')


def main():
    steps = [
        ('fetch', ['python3', str(S / 'fetch_rss_minimal.py')]),
        ('rank', ['python3', str(S / 'rank_items.py')]),
        ('digest', ['python3', str(S / 'build_digest_minimal.py')]),
        ('health_report', ['python3', str(S / 'build_health_report.py')]),
        ('feedback_map', ['python3', str(S / 'prepare_feedback_actions.py')]),
        ('publish', ['python3', str(S / 'publish_m1.py')]),
    ]

    try:
        for name, cmd in steps:
            log(f'== STEP: {name} ==')
            run(cmd)
        write_status(ok=True)
        print('DAILY_PIPELINE_DONE=1')
        print('LOG_FILE=' + str(LOG_FILE))
        print('STATUS_FILE=' + str(STATUS_FILE))
    except Exception as e:
        # identify failed step from log tail hint
        failed_step = 'unknown'
        for name, _ in steps:
            if f'== STEP: {name} ==' in LOG_FILE.read_text(encoding='utf-8', errors='ignore'):
                failed_step = name
        err = str(e)
        write_status(ok=False, failed_step=failed_step, error=err)
        write_alert(failed_step, err)
        print('DAILY_PIPELINE_DONE=0')
        print('FAILED_STEP=' + failed_step)
        print('ERROR=' + err)
        print('ALERT_FILE=' + str(ALERT_FILE))
        raise


if __name__ == '__main__':
    main()
