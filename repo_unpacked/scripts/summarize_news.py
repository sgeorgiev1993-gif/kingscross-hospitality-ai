# scripts/summarize_news.py
import os
import json
import openai
from pathlib import Path

openai.api_key = os.getenv("OPENAI_API_KEY")
NEWS_FILE = Path("data/news.json")

if not NEWS_FILE.exists():
    print("No news.json found.")
    exit()

with open(NEWS_FILE) as f:
    articles = json.load(f)

summaries = []
for article in articles:
    title = article.get("title", "")
    description = article.get("description", "")
    if not title and not description:
        continue
    prompt = f"Summarize this news in 1-2 sentences: {title}. {description}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role":"user","content":prompt}],
            temperature=0.5
        )
        summary = response.choices[0].message.content.strip()
        summaries.append({"title": title, "summary": summary, "url": article.get("url")})
    except Exception as e:
        print(f"Error summarizing '{title}': {e}")

with open("data/news_summaries.json", "w") as f:
    json.dump(summaries, f, indent=2)

print(f"✅ Summarized {len(summaries)} news articles")
