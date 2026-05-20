"""Local static dashboard generator for newsletter-ai.

Reads latest run artifacts and renders a single-file HTML dashboard.
No network requests, no Telegram, no LLM.
"""

import json
import html
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_OUTPUT_DIR = Path("output/dashboard")
SNAPSHOT_PATH = Path("output/snapshots/latest_items.json")
QUALITY_PATH = Path("output/quality/latest_quality.json")
RUNS_INDEX_PATH = Path("output/runs/index.json")
LAST_RUN_STATUS_PATH = Path("output/state/last-run-status.json")
REPLAY_REGISTRY_PATH = Path("data/fixtures/replay_source_registry.json")
TRIAL_REGISTRY_PATH = Path("data/fixtures/real_source_trial_registry.json")


def _load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_dashboard_data(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load all data sources needed for the dashboard."""
    data: Dict[str, Any] = {
        "has_latest_run": False,
        "run_summary": {},
        "items": [],
        "quality": {},
        "runs": [],
        "replay_sources": [],
        "trial_sources": [],
        "feedback_commands": [],
    }

    last_run = _load_json(LAST_RUN_STATUS_PATH)
    items = _load_json(SNAPSHOT_PATH)
    quality = _load_json(QUALITY_PATH)
    runs_index = _load_json(RUNS_INDEX_PATH)
    replay_reg = _load_json(REPLAY_REGISTRY_PATH)
    trial_reg = _load_json(TRIAL_REGISTRY_PATH)

    if last_run:
        data["has_latest_run"] = True
        data["run_summary"] = {
            "run_id": last_run.get("run_record_path", "").split("/")[-1].replace(".json", "") if last_run.get("run_record_path") else "unknown",
            "created_at": last_run.get("started_at", "N/A"),
            "input_mode": last_run.get("input_mode", "N/A"),
            "item_count": last_run.get("item_count", 0),
            "source_count": last_run.get("source_count", 0),
            "section_count": 0,
            "status": last_run.get("status", "unknown"),
            "dry_run": last_run.get("dry_run", True),
        }
        # section_count from digest step
        steps = last_run.get("steps", [])
        for step in steps:
            if step.get("name") == "digest":
                data["run_summary"]["section_count"] = step.get("section_count", 0)
                break

    if items and isinstance(items, list):
        data["items"] = items
        # Build feedback commands for first 5 items
        for item in items[:5]:
            idx = item.get("item_index", 0)
            title = item.get("title", "")
            data["feedback_commands"].append({
                "index": idx,
                "title": title,
                "like": f"newsletter-ai feedback like {idx} --dry-run",
                "save": f'newsletter-ai feedback save {idx} --note "值得深挖" --dry-run',
            })

    if quality and isinstance(quality, dict):
        data["quality"] = quality

    if runs_index and isinstance(runs_index, dict):
        data["runs"] = runs_index.get("runs", [])[:10]

    if replay_reg and isinstance(replay_reg, list):
        data["replay_sources"] = replay_reg

    if trial_reg and isinstance(trial_reg, list):
        data["trial_sources"] = trial_reg

    return data


def _esc(text: str) -> str:
    return html.escape(str(text))


def _render_run_summary(data: Dict[str, Any]) -> str:
    if not data.get("has_latest_run"):
        return '<div class="empty-state">请先运行 <code>newsletter-ai daily --dry-run</code></div>'
    s = data["run_summary"]
    return f"""
    <div class="card">
      <h2>最新运行概览</h2>
      <div class="grid-4">
        <div class="metric"><div class="metric-value">{_esc(s.get("run_id", "N/A"))}</div><div class="metric-label">Run ID</div></div>
        <div class="metric"><div class="metric-value">{_esc(s.get("created_at", "N/A"))}</div><div class="metric-label">时间</div></div>
        <div class="metric"><div class="metric-value">{_esc(s.get("status", "N/A"))}</div><div class="metric-label">状态</div></div>
        <div class="metric"><div class="metric-value">{_esc(s.get("input_mode", "N/A"))}</div><div class="metric-label">输入模式</div></div>
        <div class="metric"><div class="metric-value">{s.get("item_count", 0)}</div><div class="metric-label">Item 数</div></div>
        <div class="metric"><div class="metric-value">{s.get("section_count", 0)}</div><div class="metric-label">Section 数</div></div>
        <div class="metric"><div class="metric-value">{s.get("source_count", 0)}</div><div class="metric-label">Source 数</div></div>
        <div class="metric"><div class="metric-value">{'是' if s.get('dry_run') else '否'}</div><div class="metric-label">Dry Run</div></div>
      </div>
    </div>
    """


def _render_items(data: Dict[str, Any]) -> str:
    items = data.get("items", [])
    if not items:
        return '<div class="empty-state">暂无 item 数据</div>'

    # Group by section using topic_tags
    sections: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        tags = item.get("topic_tags", [])
        sec = tags[0] if tags else "未分类"
        sections.setdefault(sec, []).append(item)

    html_parts = ['<div class="card"><h2>今日 Digest</h2>']
    for sec_name, sec_items in sections.items():
        html_parts.append(f'<div class="section"><h3>{_esc(sec_name)} ({len(sec_items)} items)</h3>')
        html_parts.append('<div class="item-list">')
        for item in sec_items:
            idx = item.get("item_index", 0)
            title = item.get("title", "")
            source = item.get("source", "")
            url = item.get("url", "")
            summary = item.get("summary", "")
            score = item.get("score", 0)
            html_parts.append(f"""
            <div class="item">
              <div class="item-header">
                <span class="item-index">#{idx}</span>
                <span class="item-title">{_esc(title)}</span>
                <span class="item-score">{score:.3f}</span>
              </div>
              <div class="item-meta">来源：{_esc(source)}</div>
              <div class="item-summary">{_esc(summary)}</div>
              <div class="item-url"><a href="{_esc(url)}" target="_blank">{_esc(url)}</a></div>
            </div>
            """)
        html_parts.append('</div></div>')
    html_parts.append('</div>')
    return "\n".join(html_parts)


def _render_quality(data: Dict[str, Any]) -> str:
    q = data.get("quality", {})
    if not q:
        return '<div class="empty-state">暂无 quality report</div>'

    sections = q.get("section_distribution", {})
    sources = q.get("source_details", [])
    dup_count = q.get("fuzzy_duplicate_count", 0)

    sec_rows = "\n".join(
        f'<tr><td>{_esc(k)}</td><td>{v}</td></tr>'
        for k, v in (sections or {}).items()
    )

    src_rows = "\n".join(
        f'<tr><td>{_esc(s.get("source", "N/A"))}</td><td>{s.get("score", 0):.3f}</td><td>{s.get("status", "N/A")}</td><td>{s.get("final_count", 0)}</td></tr>'
        for s in (sources or [])
    )

    return f"""
    <div class="card">
      <h2>Quality Report</h2>
      <div class="grid-2">
        <div>
          <h3>Section Distribution</h3>
          <table>
            <thead><tr><th>Section</th><th>Items</th></tr></thead>
            <tbody>{sec_rows}</tbody>
          </table>
        </div>
        <div>
          <h3>Duplicate Analysis</h3>
          <div class="metric"><div class="metric-value">{dup_count}</div><div class="metric-label">Fuzzy Duplicates</div></div>
        </div>
      </div>
      <h3>Source Quality</h3>
      <table>
        <thead><tr><th>Source</th><th>Score</th><th>Status</th><th>Items</th></tr></thead>
        <tbody>{src_rows}</tbody>
      </table>
    </div>
    """


def _render_sources(data: Dict[str, Any]) -> str:
    last_run = _load_json(LAST_RUN_STATUS_PATH) or {}
    ingestion = last_run.get("ingestion_report", {})
    if not ingestion:
        return '<div class="empty-state">暂无 source ingestion 数据</div>'

    summary = ingestion.get("source_count_total", 0)
    success = ingestion.get("source_count_success", 0)
    failed = ingestion.get("source_count_failed", 0)
    disabled = ingestion.get("source_count_disabled", 0)
    skipped = ingestion.get("source_count_skipped_network", 0)
    failed_ids = ingestion.get("failed_source_ids", [])

    failed_html = ""
    if failed_ids:
        failed_html = f'<div class="warning">失败来源：{", ".join(_esc(str(x)) for x in failed_ids)}</div>'

    return f"""
    <div class="card">
      <h2>Sources</h2>
      <div class="grid-4">
        <div class="metric"><div class="metric-value">{summary}</div><div class="metric-label">总计</div></div>
        <div class="metric"><div class="metric-value">{success}</div><div class="metric-label">成功</div></div>
        <div class="metric"><div class="metric-value">{failed}</div><div class="metric-label">失败</div></div>
        <div class="metric"><div class="metric-value">{skipped}</div><div class="metric-label">跳过(网络)</div></div>
      </div>
      {failed_html}
    </div>
    """


def _render_runs(data: Dict[str, Any]) -> str:
    runs = data.get("runs", [])
    if not runs:
        return '<div class="empty-state">暂无 runs 历史</div>'

    rows = "\n".join(
        f'<tr><td>{_esc(r.get("run_id", "N/A"))}</td><td>{_esc(r.get("created_at", "N/A"))}</td><td>{_esc(r.get("input_mode", "N/A"))}</td><td>{r.get("item_count", 0)}</td><td>{_esc(r.get("status", "N/A"))}</td></tr>'
        for r in runs
    )

    return f"""
    <div class="card">
      <h2>最近 Runs (最多 10 条)</h2>
      <table>
        <thead><tr><th>Run ID</th><th>时间</th><th>输入模式</th><th>Items</th><th>状态</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def _render_replay(data: Dict[str, Any]) -> str:
    replay = data.get("replay_sources", [])
    trial = data.get("trial_sources", [])
    all_sources = list(replay) + list(trial)
    if not all_sources:
        return '<div class="empty-state">暂无 replay source</div>'

    rows = "\n".join(
        f'<tr><td>{_esc(s.get("source_id", "N/A"))}</td><td>{_esc(s.get("name", "N/A"))}</td><td>{_esc(s.get("type", "N/A"))}</td><td>{"是" if s.get("enabled") else "否"}</td></tr>'
        for s in all_sources
    )

    return f"""
    <div class="card">
      <h2>Replay Sources</h2>
      <table>
        <thead><tr><th>Source ID</th><th>名称</th><th>类型</th><th>启用</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def _render_feedback_commands(data: Dict[str, Any]) -> str:
    cmds = data.get("feedback_commands", [])
    if not cmds:
        return ""

    rows = "\n".join(
        f'<tr><td>{c["index"]}</td><td>{_esc(c["title"])}</td><td><code>{_esc(c["like"])}</code></td><td><code>{_esc(c["save"])}</code></td></tr>'
        for c in cmds
    )

    return f"""
    <div class="card">
      <h2>Feedback 命令速查</h2>
      <table>
        <thead><tr><th>#</th><th>标题</th><th>Like</th><th>Save</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def render_dashboard_html(data: Dict[str, Any]) -> str:
    """Render complete dashboard HTML from data dict."""
    title = "newsletter-ai Dashboard"
    run_summary = _render_run_summary(data)
    items_html = _render_items(data)
    quality_html = _render_quality(data)
    sources_html = _render_sources(data)
    runs_html = _render_runs(data)
    replay_html = _render_replay(data)
    feedback_html = _render_feedback_commands(data)

    css = """
    :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --border: #334155; --success: #22c55e; --warning: #f59e0b; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
    header { border-bottom: 1px solid var(--border); margin-bottom: 24px; padding-bottom: 16px; }
    header h1 { margin: 0; font-size: 1.5rem; color: var(--accent); }
    header p { margin: 4px 0 0; color: var(--muted); font-size: 0.875rem; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .card h2 { margin: 0 0 16px; font-size: 1.125rem; color: var(--accent); }
    .card h3 { margin: 16px 0 8px; font-size: 1rem; color: var(--text); }
    .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; }
    .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
    .metric { text-align: center; padding: 12px; background: rgba(56,189,248,0.08); border-radius: 8px; }
    .metric-value { font-size: 1.25rem; font-weight: 600; color: var(--accent); word-break: break-all; }
    .metric-label { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 500; }
    .item { padding: 12px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; background: rgba(15,23,42,0.5); }
    .item-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
    .item-index { background: var(--accent); color: var(--bg); font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
    .item-title { font-weight: 600; flex: 1; }
    .item-score { color: var(--success); font-weight: 600; font-size: 0.875rem; }
    .item-meta { font-size: 0.8rem; color: var(--muted); margin-bottom: 4px; }
    .item-summary { font-size: 0.875rem; color: var(--text); margin-bottom: 6px; }
    .item-url { font-size: 0.8rem; }
    .item-url a { color: var(--accent); text-decoration: none; word-break: break-all; }
    .item-url a:hover { text-decoration: underline; }
    .section { margin-bottom: 20px; }
    .section h3 { margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
    .empty-state { padding: 24px; text-align: center; color: var(--muted); background: rgba(15,23,42,0.5); border-radius: 8px; border: 1px dashed var(--border); }
    .warning { padding: 10px 14px; background: rgba(245,158,11,0.12); border: 1px solid var(--warning); border-radius: 8px; color: var(--warning); margin-top: 12px; font-size: 0.875rem; }
    code { background: rgba(56,189,248,0.12); padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; color: var(--accent); }
    @media (max-width: 640px) { .grid-4 { grid-template-columns: repeat(2, 1fr); } }
    """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>{title}</h1>
    <p>本地静态预览 · 不联网 · 不发送 Telegram</p>
  </header>
  {run_summary}
  {items_html}
  {quality_html}
  {sources_html}
  {runs_html}
  {replay_html}
  {feedback_html}
  <footer style="text-align:center;color:var(--muted);font-size:0.75rem;padding:20px 0;">
    Generated by newsletter-ai v0.4.1 · <a href="https://github.com/conanxin/newsletter-ai" style="color:var(--accent);text-decoration:none;">GitHub</a>
  </footer>
</div>
</body>
</html>"""


def build_dashboard(output_dir: Optional[Path] = None) -> Path:
    """Build dashboard HTML and write to output_dir/index.html."""
    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    data = load_dashboard_data()
    html_content = render_dashboard_html(data)
    index_path = out / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return index_path
