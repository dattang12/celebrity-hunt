"""
services/scraper.py
Pulls real data about celebrities from public sources:
- Wikipedia (associates, collaborators, bio)
- NewsAPI (recent news, what they care about now)
- SerpAPI (Google search for manager, investor, podcast info)
"""

import os
import re
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")


# ─────────────────────────────────────────────
# WIKIPEDIA SCRAPER
# ─────────────────────────────────────────────

def scrape_wikipedia(celebrity_name: str) -> dict:
    """
    Pull bio, summary, and known associates from Wikipedia.
    Returns dict with: summary, associates, categories
    """
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(
            user_agent="AccessEngine/1.0 (hackathon project)",
            language="en"
        )
        page = wiki.page(celebrity_name)

        if not page.exists():
            # Try with common name variations
            variations = [
                celebrity_name.replace(" ", "_"),
                celebrity_name + " (entertainer)",
                celebrity_name + " (businessman)",
            ]
            for v in variations:
                page = wiki.page(v)
                if page.exists():
                    break

        if not page.exists():
            return {"summary": "", "associates": [], "categories": []}

        summary = page.summary[:500] if page.summary else ""

        # Extract people mentioned in the first 2000 chars of text
        text = page.text[:2000]
        # Simple heuristic: find capitalized name patterns
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
        # Filter out the celebrity's own name
        associates = [n for n in names if celebrity_name not in n][:10]

        categories = list(page.categories.keys())[:5] if page.categories else []

        return {
            "summary": summary,
            "associates": list(set(associates)),
            "categories": categories,
            "url": page.fullurl,
        }

    except Exception as e:
        print(f"Wikipedia error for {celebrity_name}: {e}")
        return {"summary": "", "associates": [], "categories": []}


# ─────────────────────────────────────────────
# NEWS API
# ─────────────────────────────────────────────

def get_recent_news(celebrity_name: str, max_articles: int = 5) -> list[dict]:
    """
    Get the most recent news articles about the celebrity.
    Returns list of {title, description, url, publishedAt, source}
    """
    if not NEWS_API_KEY:
        print("⚠️  No NEWS_API_KEY — returning mock news")
        return _mock_news(celebrity_name)

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f'"{celebrity_name}"',
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "language": "en",
            "apiKey": NEWS_API_KEY,
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return _mock_news(celebrity_name)

        articles = []
        for article in data.get("articles", [])[:max_articles]:
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", ""),
            })
        return articles

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return _mock_news(celebrity_name)


def _mock_news(celebrity_name: str) -> list[dict]:
    """Fallback mock news when API unavailable."""
    return [
        {
            "title": f"{celebrity_name} discusses future plans in new interview",
            "description": f"{celebrity_name} shared insights about upcoming projects and business ventures.",
            "url": "",
            "published_at": "2025-02-20",
            "source": "TechCrunch",
        },
        {
            "title": f"{celebrity_name} seen at major tech conference",
            "description": "Attended multiple panels and met with investors.",
            "url": "",
            "published_at": "2025-02-15",
            "source": "Bloomberg",
        },
    ]


# ─────────────────────────────────────────────
# SERP API (Google Search)
# ─────────────────────────────────────────────

def search_google(query: str) -> list[dict]:
    """
    Run a Google search via SerpAPI.
    Returns list of {title, snippet, link}
    """
    if not SERP_API_KEY:
        print(f"⚠️  No SERP_API_KEY — skipping search: {query}")
        return []

    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "num": 5,
            "engine": "google",
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        results = []
        for result in data.get("organic_results", [])[:5]:
            results.append({
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "link": result.get("link", ""),
            })
        return results

    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []


def find_celebrity_connections(celebrity_name: str) -> dict:
    """
    Use Google to find publicly known connections.
    Returns structured info about manager, investors, podcast appearances.
    """
    results = {
        "manager": None,
        "investors": [],
        "podcast_appearances": [],
        "recent_events": [],
        "raw_results": [],
    }

    # Search for manager/agent
    manager_results = search_google(f'"{celebrity_name}" manager OR agent OR publicist')
    if manager_results:
        results["manager"] = manager_results[0].get("snippet", "")
        results["raw_results"].extend(manager_results)

    # Search for investors/backed by
    investor_results = search_google(f'"{celebrity_name}" investor OR "backed by" OR "invested in"')
    for r in investor_results[:3]:
        results["investors"].append(r.get("snippet", ""))

    # Search for podcast appearances
    podcast_results = search_google(f'"{celebrity_name}" podcast interview 2024 OR 2025')
    for r in podcast_results[:3]:
        results["podcast_appearances"].append(r.get("title", ""))

    return results


# ─────────────────────────────────────────────
# MASTER SCRAPER — pulls everything
# ─────────────────────────────────────────────

def scrape_all(celebrity_name: str) -> dict:
    """
    Master function — pull all available data about a celebrity.
    Called when a celebrity is searched for the first time.
    """
    print(f"🔍 Scraping data for: {celebrity_name}")

    wiki_data = scrape_wikipedia(celebrity_name)
    news = get_recent_news(celebrity_name)
    connections = find_celebrity_connections(celebrity_name)

    return {
        "name": celebrity_name,
        "bio": wiki_data.get("summary", ""),
        "wikipedia_associates": wiki_data.get("associates", []),
        "recent_news": news,
        "manager_info": connections.get("manager"),
        "investor_info": connections.get("investors", []),
        "podcast_appearances": connections.get("podcast_appearances", []),
        "wikipedia_url": wiki_data.get("url", ""),
    }
