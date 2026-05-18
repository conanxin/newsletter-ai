#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import html as html_lib
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from urllib.parse import urlparse

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
LATEST = BASE / 'data' / 'normalized' / 'latest.json'
RANKED = BASE / 'data' / 'normalized' / 'ranked-latest.json'
PREF = BASE / 'data' / 'state' / 'preferences.json'
TEMPLATE = BASE / 'templates' / 'digest_template.md'
OUT = BASE / 'output'

UA = {'User-Agent': 'newsletter-bot/0.1'}
URL_SNIPPET_CACHE: dict[str, tuple[str, list[str]]] = {}


def _ensure_sentence_end(s: str) -> str:
    if not s:
        return s
    if s[-1] in '.!?。！？':
        return s
    has_cjk = bool(re.search(r'[\u4e00-\u9fff]', s))
    ascii_letters = len(re.findall(r'[A-Za-z]', s))
    # english-dominant snippets prefer '.', chinese-dominant prefer '。'
    if ascii_letters > 0 and not has_cjk:
        return s + '.'
    return s + ('。' if has_cjk else '.')


def _normalize_punctuation(s: str) -> str:
    # normalize common quote variants and noisy leading/trailing punctuation
    s = (s or '').strip()
    s = s.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    s = s.replace('..', '.').replace('。。', '。')
    s = s.strip(' \t\n\r"\'`-–—:;，,')
    s = _ensure_sentence_end(s)
    return s


def _clean_text(x: str) -> str:
    s = html_lib.unescape(x or '')
    s = ' '.join(s.replace('\n', ' ').split()).strip()
    return _normalize_punctuation(s)


def _first_snippet(x: str, max_len: int = 140) -> str:
    t = _clean_text(x)
    if not t:
        return ''
    for sep in ['. ', '。', '? ', '! ', '; ', '；']:
        if sep in t:
            t = t.split(sep)[0]
            break
    if len(t) > max_len:
        t = t[:max_len].rstrip()
        # avoid ending on a broken connector
        t = re.sub(r'(and|or|but|with|to|for|of|in|on)$', '', t, flags=re.I).strip()
        t = t.rstrip(',:;，、') + '...'
    t = _normalize_punctuation(t)
    return t


def _strip_html(s: str) -> str:
    s = re.sub(r'<script[\s\S]*?</script>', ' ', s, flags=re.I)
    s = re.sub(r'<style[\s\S]*?</style>', ' ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    return _clean_text(s)


def _host_key(url: str) -> str:
    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith('www.') else h
    except Exception:
        return ''


def _extract_candidates(html: str, host: str) -> list[str]:
    cands: list[str] = []

    # generic meta candidates
    for p in [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']+)["\']',
    ]:
        m = re.search(p, html, flags=re.I)
        if m:
            cands.append(m.group(1))

    # host-specific candidates
    if host in {'sidebar.io', 'kottke.org', 'the-syllabus.com'}:
        patterns = [
            r'<article[\s\S]*?<p[^>]*>([\s\S]{50,650}?)</p>',
            r'<main[\s\S]*?<p[^>]*>([\s\S]{50,650}?)</p>',
            r'<div[^>]+class=["\'][^"\']*(?:content|entry|post|article|prose|body)[^"\']*["\'][^>]*>[\s\S]*?<p[^>]*>([\s\S]{50,650}?)</p>',
        ]
        for p in patterns:
            m = re.search(p, html, flags=re.I)
            if m:
                cands.append(_strip_html(m.group(1)))

    # generic fallback paragraph
    pm = re.search(r'<p[^>]*>([\s\S]{40,500}?)</p>', html, flags=re.I)
    if pm:
        cands.append(_strip_html(pm.group(1)))

    # de-dup while preserving order
    out = []
    seen = set()
    for c in cands:
        cc = _clean_text(c)
        if not cc or cc in seen:
            continue
        seen.add(cc)
        out.append(cc)
    return out


def _score_candidate(snippet: str, title: str, host: str) -> tuple[int, list[str]]:
    reasons = _snippet_quality_issues(snippet, title)
    if reasons:
        return -999, reasons

    score = 0
    s = _clean_text(snippet)
    score += min(len(s), 220) // 20

    title_words = {w for w in re.findall(r'[a-zA-Z]{4,}', title.lower())}
    snip_words = {w for w in re.findall(r'[a-zA-Z]{4,}', s.lower())}
    overlap = len(title_words & snip_words)
    score += overlap * 3

    if host == 'kottke.org' and ('til' in s.lower() or 'kottke' in s.lower()):
        score += 1
    return score, []


def _snippet_quality_issues(snippet: str, title: str = '') -> list[str]:
    reasons = []
    s = _clean_text(snippet)
    if not s or len(s) < 35:
        reasons.append('too_short')

    bad_tokens = ['&rsquo;', '&nbsp;', 'cookie', 'javascript', 'subscribe', 'sign in', 'all rights reserved']
    if any(t in s.lower() for t in bad_tokens):
        reasons.append('noise_token')

    if 'â' in s or '�' in s:
        reasons.append('mojibake')

    title_words = {w for w in re.findall(r'[a-zA-Z]{4,}', title.lower())}
    if title_words:
        snip_words = {w for w in re.findall(r'[a-zA-Z]{4,}', s.lower())}
        if len(title_words & snip_words) == 0:
            reasons.append('no_title_overlap')

    return reasons


def _snippet_from_url(url: str, title: str = '') -> tuple[str, list[str]]:
    if not url:
        return '', ['fetch_failed']

    cache_key = f"{url}::{title}" if title else url
    if cache_key in URL_SNIPPET_CACHE:
        return URL_SNIPPET_CACHE[cache_key]

    all_reasons: list[str] = []
    snippet = ''
    try:
        r = requests.get(url, timeout=8, headers=UA)
        r.raise_for_status()
        html = r.text
        host = _host_key(url)

        candidates = _extract_candidates(html, host)
        best_score = -999
        best_reasons: list[str] = []

        for c in candidates:
            cand = _first_snippet(c, 180)
            score, reasons = _score_candidate(cand, title, host)
            if reasons:
                all_reasons.extend(reasons)
                continue
            if score > best_score:
                best_score = score
                snippet = cand
                best_reasons = []

        if not snippet and not all_reasons:
            all_reasons.append('no_candidate')

    except Exception:
        all_reasons.append('fetch_failed')

    uniq_reasons = sorted(set(all_reasons))
    URL_SNIPPET_CACHE[cache_key] = (snippet, uniq_reasons)
    return snippet, uniq_reasons


def build_content_summary(item: dict) -> tuple[str, str, list[str]]:
    title = (item.get('title') or '').strip()
    content_raw = item.get('content_raw') or ''
    url = item.get('url') or ''

    # source 1: content_raw
    snippet = _first_snippet(content_raw)
    if snippet and not _snippet_quality_issues(snippet, title):
        core = _ensure_sentence_end(snippet.rstrip("。.!?"))
        msg = f'核心观点：{core} 可执行启发：把“{title}”拆成「关键论点-证据-行动建议」三栏，快速判断是否值得纳入明日行动。'
        return msg, 'content_raw', []

    # source 2: url-derived
    url_snippet, reject_reasons = _snippet_from_url(url, title)
    if url_snippet:
        core = _ensure_sentence_end(url_snippet.rstrip("。.!?"))
        msg = f'核心观点：{core} 可执行启发：把“{title}”拆成「关键论点-证据-行动建议」三栏，快速判断是否值得纳入明日行动。'
        return msg, 'url_meta_or_p', reject_reasons

    # source 3: fallback
    text = ((title or '') + ' ' + (content_raw or '')).lower()
    if any(k in text for k in ['openai', 'ai', 'llm', 'model']):
        return '核心观点：内容聚焦 AI/模型能力与产品化方向。可执行启发：优先提取与你业务场景直接相关的落地步骤与成本影响。', 'fallback_template', reject_reasons
    if any(k in text for k in ['market', 'business', 'adoption', 'growth']):
        return '核心观点：讨论商业采用、增长或市场结构变化。可执行启发：对照你的渠道、转化与留存指标判断可复用性。', 'fallback_template', reject_reasons
    return '核心观点：该条目提供可进一步验证的观点线索。可执行启发：回到原文核对证据来源，再决定是否进入执行清单。', 'fallback_template', reject_reasons


def build_background(item: dict) -> str:
    title = (item.get('title') or '').strip()
    source = item.get('source', '')
    text = ((title or '') + ' ' + (item.get('content_raw') or '')).lower()

    if any(k in text for k in ['ai', 'openai', 'llm', 'model']):
        return '背景：AI 议题正从“能力演示”转向“工作流集成 + 成本收益验证”，落地价值取决于场景适配与流程改造。'
    if any(k in text for k in ['market', 'business', 'adoption', 'growth']):
        return '背景：相关讨论通常受宏观周期、分发渠道与用户留存机制共同影响，建议放进商业闭环验证。'
    if any(k in text for k in ['history', 'culture', 'society', 'politics']):
        return '背景：此类内容容易受叙事立场影响，建议同时核对时间线、样本来源与反例，避免单一叙事偏差。'
    return f'背景：来源站点 {source} 提供长期观察视角，建议结合原文链接核对论据与上下文。'


def load_items(top_n: int):
    if RANKED.exists():
        d = json.loads(RANKED.read_text(encoding='utf-8'))
        ranked_items = d.get('items', [])
        return ranked_items[:top_n], ranked_items, 'ranked'
    d = json.loads(LATEST.read_text(encoding='utf-8'))
    items = d.get('items', [])
    return items[:top_n], items, 'baseline'


def load_user_ratings():
    if not PREF.exists():
        return {}
    d = json.loads(PREF.read_text(encoding='utf-8'))
    mp = {}
    for fb in d.get('feedback_log', []):
        item_id = fb.get('item_id')
        label = fb.get('label')
        if not item_id or not label:
            continue
        if label == 'like':
            mp[item_id] = '5（你标记为 like）'
        elif label == 'neutral':
            mp[item_id] = '3（你标记为 neutral）'
        elif label == 'dislike':
            mp[item_id] = '1（你标记为 dislike）'
    return mp


def _calc_stats(meta_list: list[dict]) -> dict:
    total = len(meta_list)
    src_counter = Counter([x['snippet_source'] for x in meta_list])
    trusted_hits = src_counter.get('content_raw', 0) + src_counter.get('url_meta_or_p', 0)
    reject_counter = Counter()
    for x in meta_list:
        for r in x.get('snippet_quality_reject_reasons', []):
            reject_counter[r] += 1
    return {
        'total': total,
        'trusted_hits': trusted_hits,
        'trusted_hit_rate': round((trusted_hits / total), 4) if total else 0.0,
        'source_counts': dict(src_counter),
        'reject_reason_counts': dict(reject_counter),
    }


def main(top_n: int = 8):
    OUT.mkdir(parents=True, exist_ok=True)
    items_top, items_all, mode = load_items(top_n)
    user_ratings = load_user_ratings()

    lines = []
    top_meta = []
    for idx, it in enumerate(items_top, 1):
        title = (it.get('title') or '').strip() or '(untitled)'
        source = it.get('source', '')
        summary, snippet_source, reject_reasons = build_content_summary(it)
        bg = build_background(it)
        rating = user_ratings.get(it.get('id'), '-')

        top_meta.append({
            'id': it.get('id'),
            'title': title,
            'snippet_source': snippet_source,
            'snippet_quality_reject_reasons': reject_reasons,
        })

        lines.append(
            f"### {idx}. {title}\n"
            f"- 来源：{source}\n"
            f"- 内容梳理：{summary}\n"
            f"- 背景补充：{bg}\n"
            f"- 我的喜爱分（仅你的反馈）：{rating}\n"
        )

    # compute full-filtered stats
    all_meta = []
    for it in items_all:
        title = (it.get('title') or '').strip() or '(untitled)'
        _, snippet_source, reject_reasons = build_content_summary(it)
        all_meta.append({
            'id': it.get('id'),
            'title': title,
            'snippet_source': snippet_source,
            'snippet_quality_reject_reasons': reject_reasons,
        })

    stats = {
        'generated_at': datetime.now().isoformat(),
        'mode': mode,
        'top_n': top_n,
        'top8': _calc_stats(top_meta),
        'filtered_all': _calc_stats(all_meta),
        'top8_items': top_meta,
    }

    trend = f'今日主题偏向 AI 竞争、产品化与评估方法。当前排序模式：{mode}。'
    publish_ready = '今天的精选说明：我更偏好能沉淀方法论、且对真实业务有启发的内容。'

    tpl = TEMPLATE.read_text(encoding='utf-8')
    date_str = datetime.now().strftime('%Y-%m-%d')
    out_md = tpl.replace('{{date}}', date_str).replace('{{items}}', '\n'.join(lines)).replace('{{trend}}', trend).replace('{{publish_ready}}', publish_ready)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    out_file = OUT / f'digest-{ts}.md'
    latest_file = OUT / 'latest-digest.md'
    stats_file = OUT / 'latest-snippet-stats.json'

    out_file.write_text(out_md, encoding='utf-8')
    latest_file.write_text(out_md, encoding='utf-8')
    stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')

    print('DIGEST_FILE=' + str(out_file))
    print('LATEST_DIGEST=' + str(latest_file))
    print('SNIPPET_STATS=' + str(stats_file))
    print('ITEMS=' + str(len(items_top)))
    print('MODE=' + mode)


if __name__ == '__main__':
    main()
