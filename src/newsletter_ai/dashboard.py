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
        steps = last_run.get("steps", [])
        for step in steps:
            if step.get("name") == "digest":
                data["run_summary"]["section_count"] = step.get("section_count", 0)
                break

    if items and isinstance(items, list):
        data["items"] = items
        for item in items[:5]:
            idx = item.get("item_index", 0)
            title = item.get("title", "")
            data["feedback_commands"].append({
                "index": idx,
                "title": title,
                "like": f"newsletter-ai feedback like {idx} --dry-run",
                "save": f'newsletter-ai feedback save {idx} --note "值得深挖" --dry-run',
                "dislike": f"newsletter-ai feedback dislike {idx} --dry-run",
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


def _render_nav() -> str:
    return """
    <nav class="nav">
      <a href="#digest">今日 Digest</a>
      <a href="#quality">Quality</a>
      <a href="#sources">Sources</a>
      <a href="#runs">Runs</a>
      <a href="#replay">Replay</a>
      <a href="#feedback">Feedback</a>
    </nav>
    """


def _render_run_summary(data: Dict[str, Any]) -> str:
    if not data.get("has_latest_run"):
        return '<div class="empty-state">请先运行 <code>newsletter-ai daily --dry-run</code></div>'
    s = data["run_summary"]
    status_class = "status-success" if s.get("status") == "success" else "status-warning"
    return f"""
    <div class="hero">
      <div class="hero-title">newsletter-ai Dashboard</div>
      <div class="hero-meta">本地静态预览 · 不联网 · 不发送 Telegram</div>
      <div class="hero-grid">
        <div class="hero-card">
          <div class="hero-value {status_class}">{_esc(s.get("status", "N/A"))}</div>
          <div class="hero-label">状态</div>
        </div>
        <div class="hero-card">
          <div class="hero-value">{s.get("item_count", 0)}</div>
          <div class="hero-label">Items</div>
        </div>
        <div class="hero-card">
          <div class="hero-value">{s.get("section_count", 0)}</div>
          <div class="hero-label">Sections</div>
        </div>
        <div class="hero-card">
          <div class="hero-value">{s.get("source_count", 0)}</div>
          <div class="hero-label">Sources</div>
        </div>
      </div>
      <div class="hero-detail">
        <span>Run: <code>{_esc(s.get("run_id", "N/A"))}</code></span>
        <span>Mode: {_esc(s.get("input_mode", "N/A"))}</span>
        <span>Time: {_esc(s.get("created_at", "N/A"))}</span>
        <span>Dry Run: {'是' if s.get('dry_run') else '否'}</span>
      </div>
    </div>
    """


def _render_items(data: Dict[str, Any]) -> str:
    items = data.get("items", [])
    if not items:
        return '<div class="empty-state">暂无 item 数据</div>'

    sections: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        tags = item.get("topic_tags", [])
        sec = tags[0] if tags else "未分类"
        sections.setdefault(sec, []).append(item)

    html_parts = ['<div class="card" id="digest"><h2>今日 Digest</h2>']
    for sec_name, sec_items in sections.items():
        top_n = 10
        shown = sec_items[:top_n]
        hidden_count = max(0, len(sec_items) - top_n)
        html_parts.append(f'<div class="section"><h3>{_esc(sec_name)} <span class="section-count">{len(sec_items)} items</span></h3>')
        html_parts.append('<div class="item-list">')
        for item in shown:
            idx = item.get("item_index", 0)
            title = item.get("title", "")
            source = item.get("source", "")
            url = item.get("url", "")
            summary = item.get("summary", "")
            score = item.get("score", 0)
            topic_tags = item.get("topic_tags", [])
            style_tags = item.get("style_tags", [])
            tags_html = ""
            if topic_tags or style_tags:
                all_tags = list(topic_tags) + list(style_tags)
                tags_html = '<div class="item-tags">' + "".join(f'<span class="tag">{_esc(t)}</span>' for t in all_tags[:5]) + '</div>'
            html_parts.append(f"""
            <div class="item" data-title="{_esc(title)}" data-source="{_esc(source)}">
              <div class="item-header">
                <span class="item-index">#{idx}</span>
                <span class="item-title">{_esc(title)}</span>
                <span class="item-score">{score:.3f}</span>
              </div>
              <div class="item-meta">来源：{_esc(source)}</div>
              {tags_html}
              <div class="item-summary">{_esc(summary)}</div>
              <div class="item-url"><a href="{_esc(url)}" target="_blank">{_esc(url)}</a></div>
            </div>
            """)
        if hidden_count > 0:
            html_parts.append(f'<div class="more-hint">另有 {hidden_count} 条未展开</div>')
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
    warnings = q.get("warnings", [])

    sec_rows = "\n".join(
        f'<tr><td>{_esc(k)}</td><td>{v.get("item_count", 0) if isinstance(v, dict) else v}</td></tr>'
        for k, v in (sections or {}).items()
    )

    src_rows = "\n".join(
        f'<tr><td>{_esc(s.get("source", "N/A"))}</td><td>{s.get("score", 0):.3f}</td><td>{_esc(s.get("status", "N/A"))}</td><td>{s.get("final_count", 0)}</td></tr>'
        for s in (sources or [])[:5]
    )

    warning_html = ""
    if warnings:
        warning_html = '<div class="warning-box">' + "".join(f'<div class="warning-item">{_esc(w)}</div>' for w in warnings) + '</div>'

    return f"""
    <div class="card" id="quality">
      <h2>Quality Report</h2>
      <div class="grid-2">
        <div class="subcard">
          <h3>Section Distribution</h3>
          <table class="mini-table">
            <thead><tr><th>Section</th><th>Items</th></tr></thead>
            <tbody>{sec_rows}</tbody>
          </table>
        </div>
        <div class="subcard">
          <h3>Duplicate Analysis</h3>
          <div class="big-metric">
            <div class="big-value">{dup_count}</div>
            <div class="big-label">Fuzzy Duplicates</div>
          </div>
          {warning_html}
        </div>
      </div>
      <div class="subcard">
        <h3>Source Quality (Top 5)</h3>
        <table class="mini-table">
          <thead><tr><th>Source</th><th>Score</th><th>Status</th><th>Items</th></tr></thead>
          <tbody>{src_rows}</tbody>
        </table>
      </div>
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
        failed_html = f'<div class="warning-box"><div class="warning-item">失败来源：{", ".join(_esc(str(x)) for x in failed_ids)}</div></div>'

    return f"""
    <div class="card" id="sources">
      <h2>Sources</h2>
      <div class="grid-4">
        <div class="stat-card stat-total"><div class="stat-value">{summary}</div><div class="stat-label">总计</div></div>
        <div class="stat-card stat-success"><div class="stat-value">{success}</div><div class="stat-label">成功</div></div>
        <div class="stat-card stat-failed"><div class="stat-value">{failed}</div><div class="stat-label">失败</div></div>
        <div class="stat-card stat-skipped"><div class="stat-value">{skipped}</div><div class="stat-label">跳过(网络)</div></div>
      </div>
      {failed_html}
    </div>
    """


def _render_runs(data: Dict[str, Any]) -> str:
    runs = data.get("runs", [])
    if not runs:
        return '<div class="empty-state">暂无 runs 历史</div>'

    rows = "\n".join(
        f'<tr><td><code>{_esc(r.get("run_id", "N/A"))}</code></td><td>{_esc(r.get("created_at", "N/A"))}</td><td>{_esc(r.get("input_mode", "N/A"))}</td><td>{r.get("item_count", 0)}</td><td><span class="badge badge-{_esc(r.get("status", "unknown"))}">{_esc(r.get("status", "N/A"))}</span></td></tr>'
        for r in runs
    )

    return f"""
    <div class="card" id="runs">
      <h2>最近 Runs</h2>
      <table class="mini-table">
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

    rows = []
    for s in all_sources:
        status_badge = '<span class="badge badge-success">启用</span>' if s.get("enabled") else '<span class="badge badge-muted">禁用</span>'
        rows.append(
            f'<tr><td>{_esc(s.get("source_id", "N/A"))}</td><td>{_esc(s.get("name", "N/A"))}</td><td>{_esc(s.get("type", "N/A"))}</td><td>{status_badge}</td></tr>'
        )
    rows_str = "\n".join(rows)

    return f"""
    <div class="card" id="replay">
      <h2>Replay Sources</h2>
      <table class="mini-table">
        <thead><tr><th>Source ID</th><th>名称</th><th>类型</th><th>状态</th></tr></thead>
        <tbody>{rows_str}</tbody>
      </table>
      <div class="hint">验证 replay： <code>newsletter-ai replay validate</code></div>
    </div>
    """


def _render_feedback_commands(data: Dict[str, Any]) -> str:
    cmds = data.get("feedback_commands", [])
    if not cmds:
        return ""

    rows = "\n".join(
        f"""<tr>
          <td><span class="item-index">#{c["index"]}</span></td>
          <td>{_esc(c["title"])}</td>
          <td><code class="cmd">{_esc(c["like"])}</code></td>
          <td><code class="cmd">{_esc(c["save"])}</code></td>
          <td><code class="cmd">{_esc(c["dislike"])}</code></td>
        </tr>"""
        for c in cmds
    )

    return f"""
    <div class="card" id="feedback">
      <h2>Feedback 命令速查</h2>
      <p class="hint">点击命令文本可复制（需浏览器支持）</p>
      <table class="mini-table">
        <thead><tr><th>#</th><th>标题</th><th>Like</th><th>Save</th><th>Dislike</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def render_dashboard_html(data: Dict[str, Any]) -> str:
    """Render complete dashboard HTML from data dict."""
    title = "newsletter-ai Dashboard"
    nav = _render_nav()
    run_summary = _render_run_summary(data)
    items_html = _render_items(data)
    quality_html = _render_quality(data)
    sources_html = _render_sources(data)
    runs_html = _render_runs(data)
    replay_html = _render_replay(data)
    feedback_html = _render_feedback_commands(data)

    css = """
    :root { --bg:#f8fafc; --surface:#ffffff; --text:#0f172a; --muted:#64748b; --accent:#0ea5e9; --accent-soft:#e0f2fe; --border:#e2e8f0; --success:#10b981; --success-soft:#d1fae5; --warning:#f59e0b; --warning-soft:#fef3c7; --danger:#ef4444; --danger-soft:#fee2e2; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }
    .container { max-width:1200px; margin:0 auto; padding:24px; }
    .nav { position:sticky; top:0; background:rgba(248,250,252,0.92); backdrop-filter:blur(8px); border-bottom:1px solid var(--border); padding:12px 0; margin-bottom:24px; z-index:10; display:flex; gap:16px; flex-wrap:wrap; }
    .nav a { color:var(--muted); text-decoration:none; font-size:0.875rem; font-weight:500; padding:4px 8px; border-radius:6px; transition:all 0.15s; }
    .nav a:hover { color:var(--accent); background:var(--accent-soft); }
    .hero { background:linear-gradient(135deg, var(--surface) 0%, var(--accent-soft) 100%); border:1px solid var(--border); border-radius:16px; padding:28px; margin-bottom:24px; }
    .hero-title { font-size:1.75rem; font-weight:700; margin-bottom:4px; }
    .hero-meta { color:var(--muted); font-size:0.875rem; margin-bottom:20px; }
    .hero-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:16px; margin-bottom:16px; }
    .hero-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; text-align:center; }
    .hero-value { font-size:1.5rem; font-weight:700; color:var(--accent); }
    .hero-label { font-size:0.75rem; color:var(--muted); margin-top:4px; }
    .status-success { color:var(--success); }
    .status-warning { color:var(--warning); }
    .hero-detail { display:flex; gap:16px; flex-wrap:wrap; font-size:0.8rem; color:var(--muted); }
    .hero-detail code { background:var(--surface); padding:2px 6px; border-radius:4px; border:1px solid var(--border); }
    .card { background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:24px; margin-bottom:20px; }
    .card h2 { margin:0 0 16px; font-size:1.125rem; color:var(--text); display:flex; align-items:center; gap:8px; }
    .card h2::before { content:""; display:inline-block; width:4px; height:20px; background:var(--accent); border-radius:2px; }
    .subcard { background:var(--bg); border:1px solid var(--border); border-radius:12px; padding:16px; }
    .subcard h3 { margin:0 0 12px; font-size:1rem; color:var(--text); }
    .grid-2 { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px; }
    .grid-4 { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:16px; }
    .stat-card { text-align:center; padding:16px; border-radius:12px; }
    .stat-total { background:var(--accent-soft); }
    .stat-success { background:var(--success-soft); }
    .stat-failed { background:var(--danger-soft); }
    .stat-skipped { background:var(--warning-soft); }
    .stat-value { font-size:1.5rem; font-weight:700; color:var(--text); }
    .stat-label { font-size:0.75rem; color:var(--muted); margin-top:4px; }
    .big-metric { text-align:center; padding:20px; }
    .big-value { font-size:2.5rem; font-weight:700; color:var(--accent); }
    .big-label { font-size:0.875rem; color:var(--muted); }
    .mini-table { width:100%; border-collapse:collapse; font-size:0.875rem; }
    .mini-table th, .mini-table td { padding:8px 12px; text-align:left; border-bottom:1px solid var(--border); }
    .mini-table th { color:var(--muted); font-weight:500; background:var(--bg); }
    .mini-table tr:hover { background:var(--bg); }
    .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:0.75rem; font-weight:600; }
    .badge-success { background:var(--success-soft); color:var(--success); }
    .badge-warning { background:var(--warning-soft); color:var(--warning); }
    .badge-danger { background:var(--danger-soft); color:var(--danger); }
    .badge-muted { background:var(--bg); color:var(--muted); }
    .section { margin-bottom:20px; }
    .section h3 { margin:0 0 12px; padding-bottom:8px; border-bottom:1px solid var(--border); font-size:1rem; display:flex; align-items:center; gap:8px; }
    .section-count { color:var(--muted); font-size:0.875rem; font-weight:400; }
    .item { padding:16px; border:1px solid var(--border); border-radius:12px; margin-bottom:12px; background:var(--surface); transition:box-shadow 0.15s; }
    .item:hover { box-shadow:0 2px 8px rgba(0,0,0,0.04); }
    .item-header { display:flex; align-items:center; gap:10px; margin-bottom:6px; flex-wrap:wrap; }
    .item-index { background:var(--accent); color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px; }
    .item-title { font-weight:600; flex:1; font-size:0.95rem; }
    .item-score { color:var(--success); font-weight:600; font-size:0.875rem; }
    .item-meta { font-size:0.8rem; color:var(--muted); margin-bottom:4px; }
    .item-tags { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px; }
    .tag { background:var(--accent-soft); color:var(--accent); font-size:0.75rem; padding:2px 8px; border-radius:999px; font-weight:500; }
    .item-summary { font-size:0.875rem; color:var(--text); margin-bottom:8px; line-height:1.6; }
    .item-url { font-size:0.8rem; }
    .item-url a { color:var(--accent); text-decoration:none; word-break:break-all; }
    .item-url a:hover { text-decoration:underline; }
    .more-hint { text-align:center; padding:12px; color:var(--muted); font-size:0.875rem; background:var(--bg); border-radius:8px; margin-top:8px; }
    .empty-state { padding:32px; text-align:center; color:var(--muted); background:var(--bg); border-radius:12px; border:1px dashed var(--border); font-size:0.875rem; }
    .warning-box { padding:12px 16px; background:var(--warning-soft); border:1px solid var(--warning); border-radius:8px; margin-top:12px; }
    .warning-item { color:var(--warning); font-size:0.875rem; }
    code { background:var(--bg); padding:2px 6px; border-radius:4px; font-size:0.8rem; color:var(--accent); border:1px solid var(--border); }
    .cmd { display:inline-block; padding:4px 8px; background:var(--surface); border:1px solid var(--border); border-radius:6px; font-size:0.8rem; color:var(--text); cursor:pointer; transition:all 0.15s; }
    .cmd:hover { background:var(--accent-soft); border-color:var(--accent); }
    .hint { color:var(--muted); font-size:0.8rem; margin-top:8px; }
    footer { text-align:center; color:var(--muted); font-size:0.75rem; padding:24px 0; }
    footer a { color:var(--accent); text-decoration:none; }
    @media (max-width: 640px) { .grid-4 { grid-template-columns: repeat(2, 1fr); } .hero-grid { grid-template-columns: repeat(2, 1fr); } .nav { gap:8px; } }
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
  {nav}
  {run_summary}
  {items_html}
  {quality_html}
  {sources_html}
  {runs_html}
  {replay_html}
  {feedback_html}
  <footer>
    Generated by newsletter-ai v0.4.2 · <a href="https://github.com/conanxin/newsletter-ai">GitHub</a>
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


def export_dashboard_bundle(
    out_dir: Optional[Path] = None,
    include_metadata: bool = True,
    public_title: Optional[str] = None,
) -> Path:
    """Export a deployable static dashboard bundle.

    Writes:
      - index.html (static page)
      - metadata.json (run metadata, no secrets)
      - README.txt (deployment notes)
    """
    out = Path(out_dir) if out_dir else Path("dist/dashboard")
    out.mkdir(parents=True, exist_ok=True)

    data = load_dashboard_data()
    if not data.get("has_latest_run"):
        raise RuntimeError("No latest run data found. Run: newsletter-ai daily --dry-run")

    # Write index.html
    html_content = render_dashboard_html(data)
    if public_title:
        html_content = html_content.replace(
            "<title>newsletter-ai Dashboard</title>",
            f"<title>{_esc(public_title)}</title>",
        )
    index_path = out / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Write metadata.json
    if include_metadata:
        s = data.get("run_summary", {})
        metadata = {
            "generated_at": s.get("created_at", "N/A"),
            "run_id": s.get("run_id", "unknown"),
            "input_mode": s.get("input_mode", "N/A"),
            "item_count": s.get("item_count", 0),
            "source_count": s.get("source_count", 0),
            "section_count": s.get("section_count", 0),
            "status": s.get("status", "unknown"),
            "quality_report_path": "output/quality/latest_quality.json" if QUALITY_PATH.exists() else None,
            "snapshot_path": "output/snapshots/latest_items.json" if SNAPSHOT_PATH.exists() else None,
            "generated_by": "newsletter-ai v0.4.3",
        }
        meta_path = out / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Write README.txt
    readme = """newsletter-ai Static Dashboard Bundle
=====================================

This is a static export of the newsletter-ai dashboard.
It contains no secrets, tokens, or runtime state.

Files:
  index.html      - Static dashboard page
  metadata.json   - Run metadata (generated_at, item_count, etc.)
  README.txt      - This file

Deployment:
  Copy this directory to any static file server:
    - GitHub Pages
    - Nginx
    - Cloudflare Pages
    - Netlify
    - Vercel (static)

  Example (Nginx):
    location /dashboard {
        alias /var/www/newsletter-ai/dashboard;
        index index.html;
    }

Notes:
  - This bundle does not auto-update. Re-run export after each daily run.
  - Do not expose private sources or feedback data publicly.
  - The page is self-contained: no external CDN, no network requests.

Generated by newsletter-ai v0.4.3
"""
    readme_path = out / "README.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    return out
