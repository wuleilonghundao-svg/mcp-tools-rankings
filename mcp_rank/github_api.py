from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

GITHUB_API = "https://api.github.com"


class RateLimitError(Exception):
    pass


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "mcp-tools-rankings"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _check_rate_limit(resp: requests.Response):
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise RateLimitError("rate limit")


@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=20),
       retry=retry_if_exception_type((requests.RequestException, RateLimitError)))
def gh_get(url: str, token: Optional[str], params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    h = _auth_headers(token)
    if headers:
        h.update(headers)
    resp = requests.get(url, headers=h, params=params, timeout=30)
    _check_rate_limit(resp)
    resp.raise_for_status()
    return resp


def search_repos(query: str, token: Optional[str], per_page: int = 100) -> List[Dict]:
    url = f"{GITHUB_API}/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": min(per_page, 100)}
    data = gh_get(url, token, params=params).json()
    return data.get("items", [])


def count_stars_since(owner: str, repo: str, token: Optional[str], since_dt: datetime) -> int:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/stargazers"
    page, per_page, total = 1, 100, 0
    while True:
        params = {"per_page": per_page, "page": page}
        resp = gh_get(url, token, params=params, headers={"Accept": "application/vnd.github.star+json"})
        batch = resp.json()
        if not batch:
            break
        newer = 0
        older_hit = False
        for it in batch:
            ts_s = it.get("starred_at")
            if not ts_s:
                continue
            ts = datetime.fromisoformat(ts_s.replace("Z", "+00:00"))
            if ts >= since_dt:
                newer += 1
            else:
                older_hit = True
        total += newer
        if older_hit:
            break
        page += 1
        if page > 10:
            break
    return total


def days_since_push(pushed_at: str) -> int:
    try:
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except Exception:
        return 10**6
    return int((datetime.now(timezone.utc) - dt).days)

