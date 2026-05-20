#!/usr/bin/env python3
from __future__ import annotations
import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import requests

BASE = Path('/mnt/d/obsidian_nov/nov/newsletter')
SOURCES = BASE / 'data' / 'state' / 'sources.json'
PROFILES = BASE / 'data' / 'state' / 'source_profiles.json'
OUT_DIR = BASE / 'data' / 'normalized'

GLOBAL_URL_BLACKLIST_PARTS = ['/about', '/privacy', '/terms', '/contact', '/submit', '/archive', '/feed', '/rss', '/tag/']


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def shanghai_today_date():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).date()


def shanghai_yesterday_date():
    return shanghai_today_date() - timedelta(days=1)


def text_or_empty(el):
    return (el.text or '').strip() if el is not None else ''


def host_key(url: str) -> str:
    h = urlparse(url).netloc.lower()
    return h[4:] if h.startswith('www.') else h


def load_profiles():
    if not PROFILES.exists():
        return {'default': {'enabled': True, 'priority': 50, 'max_items': 3, 'title_blacklist_contains': []}}
    return json.loads(PROFILES.read_text(encoding='utf-8'))


def get_profile(profiles: dict, source_url: str):
    hk = host_key(source_url)
    base = profiles.get('default', {}).copy()
    specific = profiles.get(hk, {}).copy()

    # merge scalar fields
    p = {**base, **specific}

    # merge blacklist lists (default + specific)
    base_bl = base.get('title_blacklist_contains', []) or []
    spec_bl = specific.get('title_blacklist_contains', []) or []
    merged_bl = []
    for x in base_bl + spec_bl:
        if x not in merged_bl:
            merged_bl.append(x)
    p['title_blacklist_contains'] = merged_bl

    p.setdefault('enabled', True)
    p.setdefault('priority', 50)
    p.setdefault('max_items', 3)
    p['host_key'] = hk
    return p


def normalize_item(source_url: str, title: str, link: str, content_raw: str = '', published_at: str = '', author: str = ''):
    sid = hashlib.sha1((link or title).encode('utf-8')).hexdigest()
    return {
        'id': sid,
        'title': (title or '').strip(),
        'source': source_url,
        'author': author,
        'published_at': published_at,
        'url': (link or '').strip(),
        'content_raw': (content_raw or '').strip(),
        'tags_auto': [],
        'lang': 'unknown',
        'fetched_at': now_iso(),
    }


def parse_rss(xml_text: str, source_url: str):
    items = []
    root = ET.fromstring(xml_text)
    for it in root.findall('.//channel/item'):
        items.append(normalize_item(source_url, text_or_empty(it.find('title')), text_or_empty(it.find('link')), text_or_empty(it.find('description')), text_or_empty(it.find('pubDate')), text_or_empty(it.find('author'))))
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    for ent in root.findall('.//a:entry', ns):
        link_el = ent.find('a:link', ns)
        link = (link_el.attrib.get('href', '').strip() if link_el is not None else '')
        items.append(normalize_item(source_url, text_or_empty(ent.find('a:title', ns)), link, text_or_empty(ent.find('a:summary', ns)), text_or_empty(ent.find('a:updated', ns)) or text_or_empty(ent.find('a:published', ns)), text_or_empty(ent.find('a:author/a:name', ns))))
    return [x for x in items if (x['title'] or x['url'])]


def strip_tags(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html or '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_webpage_links(html: str, source_url: str, limit: int = 80):
    items = []
    seen = set()
    for href, inner in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, flags=re.I | re.S):
        title = strip_tags(inner)
        if len(title) < 8:
            continue
        full = urljoin(source_url, href)
        if full in seen:
            continue
        seen.add(full)

        u = urlparse(full)
        if u.scheme not in ('http', 'https'):
            continue
        src_host = urlparse(source_url).netloc
        if u.netloc != src_host:
            continue

        low = full.lower()
        if any(x in low for x in GLOBAL_URL_BLACKLIST_PARTS):
            continue

        items.append(normalize_item(source_url, title, full))
        if len(items) >= limit:
            break
    return items


def parse_date_from_text(s: str):
    s = (s or '').strip()
    if not s:
        return None
    m = re.search(r'(\d{4}-\d{2}-\d{2})', s)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except Exception:
            pass
    m = re.search(r'(20\d{2})/(\d{1,2})/(\d{1,2})', s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except Exception:
            pass
    return None


def detect_published_date(url: str):
    d = parse_date_from_text(url)
    if d:
        return d, 'url'

    host = host_key(url)
    if host in {'sidebar.io', 'readup.org', 'thebrowser.com', 'the-syllabus.com', 'kottke.org'}:
        return shanghai_yesterday_date(), 'source_listing_fallback'

    try:
        r = requests.get(url, timeout=8, headers={'User-Agent': 'newsletter-bot/0.1'})
        r.raise_for_status()
        html = r.text
    except Exception:
        return None, 'fetch_failed'

    patterns = [
        r'property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
        r'property=["\']og:published_time["\'][^>]*content=["\']([^"\']+)["\']',
        r'name=["\']pubdate["\'][^>]*content=["\']([^"\']+)["\']',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'<time[^>]*datetime=["\']([^"\']+)["\']',
    ]
    for p in patterns:
        m = re.search(p, html, flags=re.I)
        if m:
            d = parse_date_from_text(m.group(1))
            if d:
                return d, 'meta'

    return None, 'unknown'


def is_source_specific_noise(title: str, source_url: str, profile: dict):
    t = (title or '').strip()
    # normalize common html entities for robust keyword matching
    t = t.replace('&amp;', '&')
    t_low = t.lower()

    # per-source blacklist contains
    for kw in profile.get('title_blacklist_contains', []):
        if kw and kw in t_low:
            return True

    # global nav-ish contains blacklist
    global_contains = ['click here to retry', 'retry']
    if any(k in t_low for k in global_contains):
        return True

    # readup-specific byline-ish noise
    if profile.get('host_key') == 'readup.org':
        words = re.split(r'\s+', t)
        if ',' in t and len(words) <= 14 and not any(ch in t for ch in [':', '?']):
            return True
        if 2 <= len(words) <= 5 and re.fullmatch(r"[A-Za-z\.\-\s,']+", t):
            title_case_words = sum(1 for w in words if w[:1].isupper())
            if title_case_words >= max(2, len(words)-2) and not any(ch in t for ch in [':', '?', '!', '"', ',']):
                return True

    return False


def is_quality_item(it: dict, profile: dict):
    title = (it.get('title') or '').strip()
    url = (it.get('url') or '').strip().lower()
    t_low = title.lower()

    if len(title) < 12:
        return False, 'title_too_short'
    if re.fullmatch(r'[A-Z\s\.-]+', title) and len(title.split()) <= 3:
        return False, 'title_all_caps_nav'
    if re.fullmatch(r'[a-z0-9\.-]+\.[a-z]{2,}(?:/[a-z0-9\.-]+)?', t_low):
        return False, 'title_domain_like'
    if len(title.split()) <= 2 and len(title) < 20:
        return False, 'title_nav_like'
    if any(x in url for x in GLOBAL_URL_BLACKLIST_PARTS):
        return False, 'url_blacklist'
    if 'javascript:' in url or 'mailto:' in url:
        return False, 'url_invalid'
    if is_source_specific_noise(title, it.get('source', ''), profile):
        return False, 'source_specific_noise'
    return True, ''


def keep_only_yesterday_and_quality(items: list[dict], profiles: dict):
    target = shanghai_yesterday_date()
    kept = []
    dropped = {'not_yesterday': 0, 'unknown_date': 0, 'title_too_short': 0, 'title_domain_like': 0, 'title_nav_like': 0, 'title_all_caps_nav': 0, 'url_blacklist': 0, 'url_invalid': 0, 'source_specific_noise': 0}

    for it in items:
        profile = get_profile(profiles, it.get('source', ''))
        if not profile.get('enabled', True):
            dropped['source_specific_noise'] += 1
            continue

        date_val = parse_date_from_text(it.get('published_at', ''))
        date_src = 'feed'
        if not date_val:
            date_val, date_src = detect_published_date(it.get('url', ''))
        if not date_val:
            dropped['unknown_date'] += 1
            continue
        if date_val != target:
            dropped['not_yesterday'] += 1
            continue

        ok, reason = is_quality_item(it, profile)
        if not ok:
            dropped[reason] += 1
            continue

        it['published_date'] = str(date_val)
        it['published_date_source'] = date_src
        it['source_priority'] = profile.get('priority', 50)
        it['source_cap_rule'] = profile.get('max_items', 3)
        kept.append(it)

    return kept, dropped, str(target)


def apply_title_dedup(items, dropped):
    title_seen, out = set(), []
    dropped.setdefault('title_dedup', 0)
    for it in items:
        key = re.sub(r'\s+', ' ', (it.get('title') or '').strip().lower())
        if key in title_seen:
            dropped['title_dedup'] += 1
            continue
        title_seen.add(key)
        out.append(it)
    return out


def apply_source_cap_and_priority(items, dropped, profiles):
    dropped.setdefault('source_cap', 0)
    # sort by source priority desc, then title for stable order
    items = sorted(items, key=lambda x: (-x.get('source_priority', 50), x.get('title', '')))
    source_counts, out = {}, []
    for it in items:
        src = it.get('source') or 'unknown'
        profile = get_profile(profiles, src)
        cap = int(profile.get('max_items', 3))
        c = source_counts.get(src, 0)
        if c >= cap:
            dropped['source_cap'] += 1
            continue
        source_counts[src] = c + 1
        out.append(it)
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(SOURCES.read_text(encoding='utf-8'))
    profiles = load_profiles()
    rss_list = cfg.get('rss', [])
    page_list = cfg.get('webpages', [])

    all_items, errors = [], []
    for u in rss_list:
        try:
            r = requests.get(u, timeout=20, headers={'User-Agent': 'newsletter-bot/0.1'})
            r.raise_for_status()
            all_items.extend(parse_rss(r.text, u))
        except Exception as e:
            errors.append({'source': u, 'type': 'rss', 'error': str(e)})

    for u in page_list:
        try:
            r = requests.get(u, timeout=25, headers={'User-Agent': 'newsletter-bot/0.1'})
            r.raise_for_status()
            all_items.extend(parse_webpage_links(r.text, u, limit=80))
        except Exception as e:
            errors.append({'source': u, 'type': 'webpage', 'error': str(e)})

    dedup = {}
    for x in all_items:
        if x.get('url'):
            dedup[x['id']] = x
    items = list(dedup.values())

    filtered, dropped, target_day = keep_only_yesterday_and_quality(items, profiles)
    filtered = apply_title_dedup(filtered, dropped)
    final_items = apply_source_cap_and_priority(filtered, dropped, profiles)

    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out_file = OUT_DIR / f'normalized-{stamp}.json'
    payload = {
        'generated_at': now_iso(),
        'target_date': target_day,
        'sources_count': len(rss_list) + len(page_list),
        'sources_rss': len(rss_list),
        'sources_webpages': len(page_list),
        'raw_count': len(all_items),
        'dedup_count': len(items),
        'filtered_count': len(final_items),
        'dropped': dropped,
        'errors': errors,
        'items': final_items,
    }
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT_DIR / 'latest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print('OUT_FILE=' + str(out_file))
    print('LATEST=' + str(OUT_DIR / 'latest.json'))
    print('TARGET_DATE=' + target_day)
    print('SOURCES_TOTAL=' + str(payload['sources_count']))
    print('RAW_COUNT=' + str(len(all_items)))
    print('DEDUP_COUNT=' + str(len(items)))
    print('FILTERED_COUNT=' + str(len(final_items)))
    print('DROPPED=' + json.dumps(dropped, ensure_ascii=False))
    print('ERRORS=' + str(len(errors)))


if __name__ == '__main__':
    main()
