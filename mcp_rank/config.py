import os
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Settings:
    window_days: int
    top_n: int
    queries: List[str]
    weights: Dict[str, float]
    min_stars: int
    token: str | None


def load_settings(path: str) -> Settings:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    window_days = int(os.getenv('MCP_WINDOW_DAYS', cfg.get('window_days', 90)))
    top_n = int(os.getenv('MCP_TOP_N', cfg.get('top_n', 50)))
    queries = cfg.get('queries', [])
    weights = cfg.get('weights', {})
    min_stars = int(os.getenv('MCP_MIN_STARS', cfg.get('min_stars', 5)))
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    return Settings(window_days=window_days, top_n=top_n, queries=queries, weights=weights, min_stars=min_stars, token=token)

