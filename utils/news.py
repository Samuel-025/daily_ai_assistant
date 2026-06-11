"""News module — NewsAPI integration"""

import requests
from typing import Optional, List


def get_news_briefing(
    api_key: Optional[str],
    categories: Optional[List[str]] = None,
    country: str = "in",
    max_headlines: int = 5,
) -> List[str]:
    """
    Fetch top headlines from NewsAPI.
    Free key: https://newsapi.org/
    """
    if not api_key:
        return []
    categories = categories or ["technology"]
    headlines = []
    try:
        for category in categories[:2]:  # limit to 2 categories on free tier
            url = "https://newsapi.org/v2/top-headlines"
            params = {"apiKey": api_key, "country": country, "category": category, "pageSize": max_headlines}
            r = requests.get(url, params=params, timeout=5)
            if r.ok:
                articles = r.json().get("articles", [])
                headlines += [a["title"] for a in articles if a.get("title")]
    except Exception as e:
        print(f"  ⚠ News: {e}")
    return headlines[:max_headlines]
