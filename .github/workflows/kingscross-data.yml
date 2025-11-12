name: KingsCross Dashboard Data

on:
  schedule:
    - cron: '0 * * * *' # Every hour
  workflow_dispatch:

jobs:
  fetch-and-generate:
    runs-on: ubuntu-latest
    env:
      EVENTBRITE_TOKEN: ${{ secrets.EVENTBRITE_TOKEN }}
      NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
      OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
      GOOGLE_PLACES_API_KEY: ${{ secrets.GOOGLE_PLACES_API_KEY }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pandas matplotlib

      - name: Fetch TfL & Rail status
        run: python scripts/fetch_tfl.py

      - name: Fetch Eventbrite events
        run: python scripts/fetch_eventbrite.py

      - name: Fetch Weather
        run: python scripts/fetch_weather.py

      - name: Fetch News
        run: python scripts/fetch_news.py

      - name: Fetch Restaurants (Google Places)
        run: python scripts/fetch_places_reviews.py

      - name: Generate Dashboard
        run: python scripts/generate_weekly_report.py

      - name: Configure Git for Actions
        run: |
          git config user.name "github-actions"
          git config user.email "github-actions@users.noreply.github.com"

      - name: Commit & Push dashboard
        run: |
          git checkout gh-pages || git checkout -b gh-pages
          git add data/ index.html
          git commit -m "🚀 Update dashboard + events + restaurants [skip ci]" || echo "No changes to commit"
          git push origin gh-pages --force
