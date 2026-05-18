"""Test pipeline status recording on failure."""

import json
import pytest
from newsletter_ai.pipeline import run_daily_pipeline


def test_failed_step_recorded(monkeypatch, tmp_path):
    # simulate failure in one step
    def fake_run(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("newsletter_ai.pipeline.time.sleep", fake_run)
    cfg = {
        "OUTPUT_DIR": tmp_path / "output",
        "DATA_DIR": tmp_path / "data",
    }
    status = run_daily_pipeline(cfg=cfg)
    assert status["status"] == "failed"
    assert status["failed_step"] is not None