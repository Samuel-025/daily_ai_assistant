"""News module — NewsAPI integration with graceful fallback"""

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
    Returns [] if no key or request fails — caller should handle gracefully.
    Free key: https://newsapi.org/
    """
    if not api_key:
        return []   # Caller will use AI fallback instead

    categories = categories or ["technology"]
    headlines  = []
    try:
        for category in categories[:2]:   # free tier: max 2 categories
            r = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={
                    "apiKey":   api_key,
                    "country":  country,
                    "category": category,
                    "pageSize": max_headlines,
                },
                timeout=5,
            )
            if r.ok:
                articles  = r.json().get("articles", [])
                headlines += [a["title"] for a in articles if a.get("title")]
            elif r.status_code == 401:
                print("  \u26a0 NewsAPI: Invalid or expired API key. Using AI-generated briefing.")
                return []
            elif r.status_code == 429:
                print("  \u26a0 NewsAPI: Rate limit reached. Using AI-generated briefing.")
                return []
    except requests.exceptions.Timeout:
        print("  \u26a0 NewsAPI: Request timed out. Using AI-generated briefing.")
        return []
    except requests.exceptions.ConnectionError:
        print("  \u26a0 NewsAPI: No internet connection. Using AI-generated briefing.")
        return []
    except Exception as e:
        print(f"  \u26a0 NewsAPI: {e}. Using AI-generated briefing.")
        return []

    return headlines[:max_headlines]
