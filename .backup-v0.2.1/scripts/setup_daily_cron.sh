#!/usr/bin/env bash
set -euo pipefail

BASE="/mnt/d/obsidian_nov/nov/newsletter"
CMD="python3 ${BASE}/scripts/run_daily_pipeline.py"
# Asia/Shanghai 06:30 daily
CRON_LINE="30 6 * * * ${CMD} >> ${BASE}/output/logs/cron.log 2>&1"

TMP=$(mktemp)
crontab -l 2>/dev/null | grep -v "run_daily_pipeline.py" > "$TMP" || true
printf "%s\n" "$CRON_LINE" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"

echo "CRON_INSTALLED=${CRON_LINE}"
crontab -l | grep "run_daily_pipeline.py"
