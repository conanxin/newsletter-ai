#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
SCRIPTS = BASE / 'scripts'
OUT = BASE / 'output'
VALID_DIR = OUT / 'validation'

STATUS_FILE = OUT / 'state' / 'last-run-status.json'
LATEST_NORM = BASE / 'data' / 'normalized' / 'latest.json'
LATEST_RANKED = BASE / 'data' / 'normalized' / 'ranked-latest.json'
DIGEST_FILE = OUT / 'latest-digest.md'
TELEGRAM_FILE = OUT / 'latest-telegram.txt'
HEALTH_FILE = OUT / 'latest-health.txt'


@dataclass
class CheckResult:
    name: str
    ok: bool
    level: str  # pass|warn|fail
    detail: str


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def color(s: str, c: str) -> str:
    m = {'red': '\033[31m', 'green': '\033[32m', 'yellow': '\033[33m', 'blue': '\033[34m', 'reset': '\033[0m'}
    return f"{m.get(c,'')}{s}{m['reset']}"


def main():
    ap = argparse.ArgumentParser(description='Validate newsletter release pipeline end-to-end')
    ap.add_argument('--skip-run', action='store_true', help='Do not run daily pipeline before validating')
    ap.add_argument('--with-feedback-smoke', action='store_true', help='Run feedback smoke test')
    ap.add_argument('--soft-exit', action='store_true', help='Always exit 0 even on failure')
    ap.add_argument('--min-filtered', type=int, default=6)
    ap.add_argument('--min-sources', type=int, default=2)
    ap.add_argument('--max-errors', type=int, default=0)
    ap.add_argument('--strict-cron', action='store_true', help='Cron absence becomes blocking failure')
    args = ap.parse_args()

    VALID_DIR.mkdir(parents=True, exist_ok=True)
    checks: list[CheckResult] = []
    evidence = {}

    # 1) run pipeline
    if args.skip_run:
        checks.append(CheckResult('pipeline_run', True, 'pass', 'skipped by --skip-run'))
    else:
        code, out, err = run_cmd(['python3', str(SCRIPTS / 'run_daily_pipeline.py')])
        ok = code == 0 and 'DAILY_PIPELINE_DONE=1' in out
        checks.append(CheckResult('pipeline_run', ok, 'pass' if ok else 'fail', out.splitlines()[-1] if out else (err or 'no output')))
        evidence['pipeline_stdout'] = out
        evidence['pipeline_stderr'] = err

    # 2) status file
    if STATUS_FILE.exists():
        s = json.loads(STATUS_FILE.read_text(encoding='utf-8'))
        ok = bool(s.get('ok'))
        checks.append(CheckResult('status_file', ok, 'pass' if ok else 'fail', f"ok={s.get('ok')} failed_step={s.get('failed_step','') or ''}"))
        evidence['status'] = s
    else:
        checks.append(CheckResult('status_file', False, 'fail', f'missing {STATUS_FILE}'))

    # 3) artifacts
    required = [LATEST_NORM, LATEST_RANKED, DIGEST_FILE, TELEGRAM_FILE, HEALTH_FILE]
    miss = [str(p) for p in required if not p.exists()]
    if miss:
        checks.append(CheckResult('artifacts', False, 'fail', 'missing: ' + '; '.join(miss)))
    else:
        checks.append(CheckResult('artifacts', True, 'pass', 'all required artifacts exist'))

    # 4) quality gates
    quality_ok = True
    quality_msgs = []
    per_source = {}
    if LATEST_NORM.exists():
        d = json.loads(LATEST_NORM.read_text(encoding='utf-8'))
        filtered = int(d.get('filtered_count', 0))
        errs = len(d.get('errors', []))
        per_source = dict(Counter([x.get('source', 'unknown') for x in d.get('items', [])]))
        src_n = len(per_source)

        if filtered < args.min_filtered:
            quality_ok = False
            quality_msgs.append(f'filtered_count={filtered} < min_filtered={args.min_filtered}')
        if errs > args.max_errors:
            quality_ok = False
            quality_msgs.append(f'errors={errs} > max_errors={args.max_errors}')
        if src_n < args.min_sources:
            quality_ok = False
            quality_msgs.append(f'source_count={src_n} < min_sources={args.min_sources}')

        if not quality_msgs:
            quality_msgs.append(f"filtered={filtered}, errors={errs}, source_count={src_n}")

        evidence['quality'] = {
            'target_date': d.get('target_date'),
            'raw_count': d.get('raw_count'),
            'dedup_count': d.get('dedup_count'),
            'filtered_count': filtered,
            'errors_count': errs,
            'per_source': per_source,
            'dropped': d.get('dropped', {}),
            'thresholds': {
                'min_filtered': args.min_filtered,
                'max_errors': args.max_errors,
                'min_sources': args.min_sources,
            }
        }
    else:
        quality_ok = False
        quality_msgs.append('latest normalized file missing')

    checks.append(CheckResult('quality_gates', quality_ok, 'pass' if quality_ok else 'fail', '; '.join(quality_msgs)))

    # 5) feedback smoke
    if args.with_feedback_smoke:
        code, out, err = run_cmd(['python3', str(SCRIPTS / 'run_feedback_pipeline.py'), '--text', '/fb 1 neutral validate-smoke'])
        ok = code == 0 and 'PIPELINE_DONE=1' in out
        checks.append(CheckResult('feedback_smoke', ok, 'pass' if ok else 'fail', out.splitlines()[-1] if out else (err or 'no output')))
        evidence['feedback_smoke_stdout'] = out
        evidence['feedback_smoke_stderr'] = err
    else:
        checks.append(CheckResult('feedback_smoke', True, 'pass', 'skipped (enable with --with-feedback-smoke)'))

    # 6) cron presence
    ccode, cout, cerr = run_cmd(['bash', '-lc', 'crontab -l 2>/dev/null | grep run_daily_pipeline.py || true'])
    has_cron = bool(cout.strip())
    if has_cron:
        checks.append(CheckResult('cron_presence', True, 'pass', cout.strip()))
    else:
        lvl = 'fail' if args.strict_cron else 'warn'
        checks.append(CheckResult('cron_presence', False if args.strict_cron else True, lvl, 'cron entry not found'))
    evidence['cron_line'] = cout.strip()

    blocking_fail = any((c.level == 'fail' and not c.ok) for c in checks)

    # terminal summary
    print(color('=== Newsletter Release Validation ===', 'blue'))
    for c in checks:
        tag = 'PASS' if c.ok and c.level == 'pass' else ('WARN' if c.level == 'warn' else 'FAIL')
        col = 'green' if tag == 'PASS' else ('yellow' if tag == 'WARN' else 'red')
        print(f"[{color(tag,col)}] {c.name}: {c.detail}")

    final_tag = 'PASS' if not blocking_fail else 'FAIL'
    print(color(f"\nFINAL: {final_tag}", 'green' if final_tag == 'PASS' else 'red'))

    # write JSON + MD
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    payload = {
        'generated_at': datetime.now().isoformat(),
        'final': final_tag,
        'blocking_fail': blocking_fail,
        'checks': [asdict(c) for c in checks],
        'evidence': evidence,
    }
    json_file = VALID_DIR / f'validation-{ts}.json'
    md_file = VALID_DIR / f'validation-{ts}.md'
    latest_json = VALID_DIR / 'latest-validation.json'
    latest_md = VALID_DIR / 'latest-validation.md'

    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    latest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = [
        f"# Newsletter Validation Report ({ts})",
        '',
        f"- Final: **{final_tag}**",
        f"- Blocking fail: `{blocking_fail}`",
        '',
        '## Checks',
    ]
    for c in checks:
        icon = '✅' if c.ok and c.level == 'pass' else ('⚠️' if c.level == 'warn' else '❌')
        lines.append(f"- {icon} **{c.name}** ({c.level}): {c.detail}")

    if 'quality' in evidence:
        q = evidence['quality']
        lines += [
            '',
            '## Quality Snapshot',
            f"- target_date: `{q.get('target_date')}`",
            f"- raw_count: `{q.get('raw_count')}`",
            f"- dedup_count: `{q.get('dedup_count')}`",
            f"- filtered_count: `{q.get('filtered_count')}`",
            f"- errors_count: `{q.get('errors_count')}`",
            '- per_source:'
        ]
        for src, n in q.get('per_source', {}).items():
            lines.append(f"  - {src}: {n}")

    md_text = '\n'.join(lines) + '\n'
    md_file.write_text(md_text, encoding='utf-8')
    latest_md.write_text(md_text, encoding='utf-8')

    print(f"REPORT_JSON={latest_json}")
    print(f"REPORT_MD={latest_md}")

    if blocking_fail and not args.soft_exit:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
