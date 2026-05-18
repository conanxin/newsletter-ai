"""Legacy script safety tests."""

import os
from pathlib import Path


def test_no_hardcoded_paths_in_active_scripts():
    scripts_dir = Path("scripts")
    for py in scripts_dir.glob("*.py"):
        content = py.read_text()
        assert "/mnt/d/obsidian_nov/nov/newsletter" not in content, f"Hardcoded path in {py}"


def test_active_scripts_use_wrapper_pattern():
    # run_daily_pipeline.py and check_pipeline_status.py should be thin wrappers
    for name in ["run_daily_pipeline.py", "check_pipeline_status.py"]:
        p = Path("scripts") / name
        assert p.exists()
        content = p.read_text()
        assert "DEPRECATION WARNING" in content or "newsletter_ai.cli" in content


def test_make_targets_use_new_cli():
    makefile = Path("Makefile").read_text()
    assert "PKG := newsletter-ai" in makefile
    assert "daily:" in makefile