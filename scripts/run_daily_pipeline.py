#!/usr/bin/env python3
"""
Thin wrapper for backward compatibility.
Recommends using `newsletter-ai daily` instead.
"""

import subprocess
import sys

def main():
    print("[DEPRECATION WARNING] scripts/run_daily_pipeline.py is legacy.")
    print("Please use: newsletter-ai daily [--dry-run] [--no-publish]")
    print("Running new CLI for safety...\n")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "newsletter_ai.cli", "daily"] + sys.argv[1:],
            check=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Wrapper error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()