"""Configuration loader for newsletter-ai v0.2.

Loading order:
1. NEWSLETTER_BASE_DIR env var
2. Git repo root (detected via git rev-parse)
3. Current working directory
"""

import os
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """Try to find git repo root."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )
        return Path(result.stdout.strip())
    except Exception:
        return Path.cwd()


def load_config() -> dict:
    """Load and return configuration dict."""
    env_base = os.environ.get("NEWSLETTER_BASE_DIR")
    if env_base:
        base_dir = Path(env_base).expanduser().resolve()
    else:
        base_dir = get_repo_root()

    tz = os.environ.get("NEWSLETTER_TZ", "Asia/Shanghai")
    output_dir = Path(os.environ.get(
        "NEWSLETTER_OUTPUT_DIR", str(base_dir / "output")
    )).resolve()
    data_dir = Path(os.environ.get(
        "NEWSLETTER_DATA_DIR", str(base_dir / "data")
    )).resolve()

    return {
        "BASE_DIR": base_dir,
        "TZ": tz,
        "OUTPUT_DIR": output_dir,
        "DATA_DIR": data_dir,
        "STATE_DIR": data_dir / "state",
        "NORMALIZED_DIR": output_dir / "normalized",
        "DIGEST_DIR": output_dir / "digest",
        "ALERTS_DIR": output_dir / "alerts",
    }


def get_config_value(key: str, default: Optional[str] = None) -> str:
    """Convenience accessor."""
    cfg = load_config()
    return str(cfg.get(key, default or ""))