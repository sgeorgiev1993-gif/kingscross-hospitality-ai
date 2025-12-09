# scripts/fetch_news.py
import requests
import json
from pathlib import Path
import os

# Output file
DATA_PATH = Path("data/news.json")

# Location-specific query
QUERY = "Kings Cross London"

# API key from environment
API_KEY = os.getenv("NEWS_API_KEY")
if not API_KEY:
    raise ValueError("NEWS_API_KEY environment variable is not set!")

# NewsAPI endpoint
URL = "https://newsapi.org/v2/everything"

params = {
    "q": QUERY,
    "language": "en",
    "pageSize": 10,
    "sortBy": "publishedAt",
    "apiKey": API_KEY
}

try:
    response = requests.get(URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Extract only what we need
    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "source": item.get("source", {}).get("name"),
            "publishedAt": item.get("publishedAt"),
            "description": item.get("description")
        })

    # Ensure data folder exists
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(DATA_PATH, "w") as f:
        json.dump(articles, f, indent=2)

    print(f"Saved {len(articles)} news articles to {DATA_PATH}")

except Exception as e:
    print(f"Error fetching news: {e}")
