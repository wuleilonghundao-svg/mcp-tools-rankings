from __future__ import annotations

import json
import math
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from jinja2 import Template

from .config import load_settings
from .github_api import search_repos, count_stars_since, days_since_push


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
README_PATH = ROOT / "README.md"
CONFIG_PATH = ROOT / "mcp_rank" / "config.yml"


README_TPL = Template(
    """
MCP 工具项目排行（近三个月）

最近更新时间：{{ ts }} UTC
检索窗口：{{ window_days }} 天，Top {{ top_n }}

说明
- 总分 = 10*log10(总星标+1) + 0.7*近90天新增 + 0.2*(100 - 最近活跃天数，最小0) + 0.05*Forks
- 标注“收集”：最近活跃天数 > 90 天（仅收录但不算为“活跃”）

## 近三个月飙升榜（按新增星排序）
| # | 项目 | 近90天新增 | 总星标 | 最近活跃天数 | 备注 |
|---:|:-----|-----------:|-------:|------------:|:-----|
{% for r in hot %}| {{ loop.index }} | [{{ r.full_name }}]({{ r.html_url }}) | {{ r.growth_90d }} | {{ r.stars }} | {{ r.days_since_push }} | {{ '收集' if r.collected else '' }} |
{% endfor %}

## 总分排行榜
| # | 项目 | 总分 | 近90天新增 | 总星标 | Forks | 最近活跃天数 | 备注 |
|---:|:-----|----:|-----------:|-------:|------:|------------:|:-----|
{% for r in scored %}| {{ loop.index }} | [{{ r.full_name }}]({{ r.html_url }}) | {{ '%.2f'|format(r.score) }} | {{ r.growth_90d }} | {{ r.stars }} | {{ r.forks }} | {{ r.days_since_push }} | {{ '收集' if r.collected else '' }} |
{% endfor %}

""".strip()
)


def compute(settings):
    window = settings.window_days
    since_dt = datetime.now(timezone.utc) - timedelta(days=window)

    # 1) 搜索并去重
    seen = set()
    candidates: List[Dict] = []
    for q in settings.queries:
        items = search_repos(q, settings.token, per_page=settings.top_n * 3)
        for it in items:
            full = it.get("full_name")
            if not full or full in seen:
                continue
            if it.get("stargazers_count", 0) < settings.min_stars:
                continue
            seen.add(full)
            candidates.append(it)

    # 2) 计算指标
    enriched: List[Dict] = []
    for it in candidates:
        full = it.get("full_name", "")
        owner, repo = full.split("/") if "/" in full else (None, None)
        growth = 0
        if owner and repo:
            try:
                growth = count_stars_since(owner, repo, settings.token, since_dt)
            except Exception:
                growth = 0
        dsp = days_since_push(it.get("pushed_at", ""))
        collected = dsp > 90
        # 评分（可调权重）
        score = (
            10.0 * math.log10(it.get("stargazers_count", 0) + 1)
            + 0.7 * growth
            + 0.2 * max(0, 100 - dsp)
            + 0.05 * it.get("forks_count", 0)
        )
        enriched.append(
            {
                "full_name": full,
                "html_url": it.get("html_url"),
                "description": it.get("description"),
                "stars": it.get("stargazers_count", 0),
                "forks": it.get("forks_count", 0),
                "growth_90d": int(growth),
                "days_since_push": dsp,
                "collected": collected,
                "score": score,
            }
        )

    # 3) 排行
    hot = sorted(enriched, key=lambda x: (x["growth_90d"], x["stars"]), reverse=True)[: settings.top_n]
    scored = sorted(enriched, key=lambda x: x["score"], reverse=True)[: settings.top_n]

    return {"hot": hot, "scored": scored}


def write_outputs(data, settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "window_days": settings.window_days,
        "top_n": settings.top_n,
        "data": data,
    }
    (DATA_DIR / "latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = README_TPL.render(
        ts=out["generated_at"], window_days=settings.window_days, top_n=settings.top_n, hot=data["hot"], scored=data["scored"]
    )
    README_PATH.write_text(md, encoding="utf-8")


def main():
    settings = load_settings(str(CONFIG_PATH))
    data = compute(settings)
    write_outputs(data, settings)


if __name__ == "__main__":
    main()

