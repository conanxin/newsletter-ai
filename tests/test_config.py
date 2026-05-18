"""Test config loading and path resolution."""

import os
from pathlib import Path
import pytest

from newsletter_ai.config import load_config, get_repo_root


def test_load_config_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("NEWSLETTER_BASE_DIR", raising=False)
    # force repo root to tmp for test isolation
    monkeypatch.setattr("newsletter_ai.config.get_repo_root", lambda: tmp_path)
    cfg = load_config()
    assert cfg["BASE_DIR"] == tmp_path
    assert cfg["TZ"] == "Asia/Shanghai"
    assert "output" in str(cfg["OUTPUT_DIR"])
    assert "data" in str(cfg["DATA_DIR"])


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("NEWSLETTER_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("NEWSLETTER_TZ", "UTC")
    cfg = load_config()
    assert cfg["BASE_DIR"] == tmp_path.resolve()
    assert cfg["TZ"] == "UTC"