"""Controlled real RSS fetcher (v0.3.12)

Provides network fetch primitives with explicit opt-in.
No network requests are made unless allow_network=True.
"""

import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_USER_AGENT = "newsletter-ai/dev"
DEFAULT_TIMEOUT_SEC = 10


@dataclass
class FetchResult:
    ok: bool = False
    status_code: Optional[int] = None
    text: str = ""
    error: str = ""
    fetched_at: str = ""
    from_cache: bool = False
    duration_sec: float = 0.0
    url: str = ""


def fetch_url(
    url: str,
    *,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    user_agent: str = DEFAULT_USER_AGENT,
) -> FetchResult:
    """Fetch a URL and return a structured FetchResult.

    Uses urllib.request (standard library only).
    """
    started = time.time()
    result = FetchResult(url=url)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            result.status_code = response.getcode()
            result.text = response.read().decode("utf-8", errors="replace")
            result.ok = True
    except urllib.error.HTTPError as exc:
        result.status_code = exc.code
        result.error = f"HTTPError {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        result.error = f"URLError: {exc.reason}"
    except Exception as exc:
        result.error = f"FetchError: {type(exc).__name__}: {exc}"

    result.duration_sec = round(time.time() - started, 3)
    result.fetched_at = _now_iso()
    return result


def fetch_rss_url_source(
    source: Dict[str, Any],
    *,
    allow_network: bool = False,
    cache_dir: Optional[Path] = None,
) -> FetchResult:
    """Fetch an rss_url source with explicit network opt-in.

    Args:
        source: Source dict with at least 'url', optional 'timeout_sec'.
        allow_network: Must be True to perform any network request.
        cache_dir: Optional directory for future cache support.

    Returns:
        FetchResult with ok=False and error set if network not allowed.
    """
    url = source.get("url", "")
    if not url:
        return FetchResult(ok=False, error="missing_url", url="")

    if not allow_network:
        return FetchResult(
            ok=False,
            error="network_disabled",
            url=url,
            fetched_at=_now_iso(),
        )

    timeout = source.get("timeout_sec", DEFAULT_TIMEOUT_SEC)
    return fetch_url(url, timeout_sec=timeout)


def _now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"
