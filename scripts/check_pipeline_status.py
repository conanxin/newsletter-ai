#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

STATUS = Path('/mnt/d/obsidian_nov/nov/newsletter/output/state/last-run-status.json')
ALERTS = Path('/mnt/d/obsidian_nov/nov/newsletter/output/alerts')


def main():
    if not STATUS.exists():
        print('STATUS_MISSING=1')
        return
    s = json.loads(STATUS.read_text(encoding='utf-8'))
    ok = bool(s.get('ok'))
    print('OK=' + ('1' if ok else '0'))
    print('TIME=' + str(s.get('time','')))
    print('FAILED_STEP=' + str(s.get('failed_step','')))
    print('ERROR=' + str(s.get('error','')))
    print('LOG_FILE=' + str(s.get('log_file','')))

    if not ok:
        ALERTS.mkdir(parents=True, exist_ok=True)
        alert = ALERTS / 'latest-alert.txt'
        txt = (
            '⚠️ Newsletter Daily Pipeline 失败\n\n'
            f"- 时间: {s.get('time','')}\n"
            f"- 失败步骤: {s.get('failed_step','')}\n"
            f"- 错误: {s.get('error','')}\n"
            f"- 日志: {s.get('log_file','')}\n"
        )
        alert.write_text(txt, encoding='utf-8')
        print('ALERT_FILE=' + str(alert))


if __name__ == '__main__':
    main()
