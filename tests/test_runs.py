"""Tests for run artifact index (v0.3.19)."""

import json
from pathlib import Path

import pytest

from newsletter_ai.runs import (
    RunIndexError,
    append_run_record,
    get_latest_run,
    list_runs,
    load_run_index,
    load_run_record,
    make_run_record,
)


def test_make_run_record_basic(tmp_path):
    base = tmp_path
    out = tmp_path / "output"
    record = make_run_record(
        run_id="run-001",
        created_at="2026-05-20T10:00:00",
        status="success",
        input_mode="fixture_json",
        output_dir=out,
        base_dir=base,
        item_count=5,
        section_count=2,
        source_count=1,
        snapshot_path=out / "snapshots" / "latest_items.json",
        quality_report_path=out / "quality" / "latest_quality.json",
    )
    assert record["run_id"] == "run-001"
    assert record["status"] == "success"
    assert record["input_mode"] == "fixture_json"
    assert record["item_count"] == 5
    assert record["section_count"] == 2
    assert record["snapshot_path"] == "output/snapshots/latest_items.json"
    assert record["quality_report_path"] == "output/quality/latest_quality.json"


def test_make_run_record_no_secrets(tmp_path):
    record = make_run_record(
        run_id="run-002",
        created_at="2026-05-20T10:00:00",
        status="success",
        input_mode="fixture_json",
        output_dir=tmp_path / "output",
        base_dir=tmp_path,
    )
    forbidden = {"token", "auth", "cookie", "password", "secret", "api_key"}
    keys = {k.lower() for k in record.keys()}
    assert not any(f in keys for f in forbidden)


def test_append_run_record_creates_index(tmp_path):
    out = tmp_path / "output"
    base = tmp_path
    record = make_run_record(
        run_id="run-003",
        created_at="2026-05-20T10:00:00",
        status="success",
        input_mode="fixture_json",
        output_dir=out,
        base_dir=base,
        item_count=3,
    )
    path = append_run_record(record, out, base)
    assert path.exists()
    assert (out / "runs" / "index.json").exists()

    index = json.loads((out / "runs" / "index.json").read_text())
    assert "runs" in index
    assert len(index["runs"]) == 1
    assert index["runs"][0]["run_id"] == "run-003"
    assert index["runs"][0]["record_path"] == "output/runs/run-003.json"


def test_load_run_record(tmp_path):
    out = tmp_path / "output"
    base = tmp_path
    record = make_run_record(
        run_id="run-004",
        created_at="2026-05-20T10:00:00",
        status="failed",
        input_mode="source_registry",
        output_dir=out,
        base_dir=base,
        item_count=0,
        errors=["Failed step: rank"],
    )
    append_run_record(record, out, base)

    loaded = load_run_record("run-004", out)
    assert loaded["run_id"] == "run-004"
    assert loaded["status"] == "failed"
    assert loaded["errors"] == ["Failed step: rank"]


def test_load_run_record_missing_raises(tmp_path):
    out = tmp_path / "output"
    with pytest.raises(RunIndexError):
        load_run_record("nonexistent", out)


def test_list_runs_newest_first(tmp_path):
    out = tmp_path / "output"
    base = tmp_path
    for i in range(3):
        record = make_run_record(
            run_id=f"run-{i:03d}",
            created_at=f"2026-05-20T10:00:0{i}",
            status="success",
            input_mode="fixture_json",
            output_dir=out,
            base_dir=base,
            item_count=i,
        )
        append_run_record(record, out, base)

    runs = list_runs(out, limit=10)
    assert len(runs) == 3
    # Newest first
    assert runs[0]["run_id"] == "run-002"
    assert runs[1]["run_id"] == "run-001"
    assert runs[2]["run_id"] == "run-000"


def test_get_latest_run(tmp_path):
    out = tmp_path / "output"
    base = tmp_path
    record = make_run_record(
        run_id="run-latest",
        created_at="2026-05-20T10:00:00",
        status="success",
        input_mode="fixture_json",
        output_dir=out,
        base_dir=base,
        item_count=7,
    )
    append_run_record(record, out, base)

    latest = get_latest_run(out)
    assert latest is not None
    assert latest["run_id"] == "run-latest"
    assert latest["item_count"] == 7


def test_get_latest_run_empty(tmp_path):
    out = tmp_path / "output"
    assert get_latest_run(out) is None


def test_index_trims_old_entries(tmp_path):
    out = tmp_path / "output"
    base = tmp_path
    for i in range(55):
        record = make_run_record(
            run_id=f"run-{i:03d}",
            created_at=f"2026-05-20T10:00:0{i % 10}",
            status="success",
            input_mode="fixture_json",
            output_dir=out,
            base_dir=base,
            item_count=i,
        )
        append_run_record(record, out, base)

    index = load_run_index(out)
    assert len(index["runs"]) == 50  # MAX_INDEX_ENTRIES
