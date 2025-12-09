#!/bin/bash
set -e

# ---------------- Install pip if missing ----------------
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip3..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# ---------------- Install required Python packages ----------------
echo "📦 Installing required Python packages..."
python3 -m pip install --user requests openai matplotlib

# ---------------- Set environment variables ----------------
# Replace these with your actual keys
export OPENWEATHER_KEY="YOUR_OPENWEATHER_KEY"
export TFL_APP_KEY="YOUR_TFL_KEY"
export EVENTBRITE_TOKEN="YOUR_EVENTBRITE_TOKEN"
export NEWS_API_KEY="YOUR_NEWS_API_KEY"
export GOOGLE_PLACES_KEY="YOUR_GOOGLE_PLACES_KEY"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# ---------------- Run fetch scripts ----------------
echo "🚀 Running fetch scripts..."
python3 scripts/fetch_weather.py
python3 scripts/fetch_tfl.py
python3/scripts/fetch_eventbrite.py
python3 scripts/fetch_places_reviews.py
python3 scripts/fetch_news.py

# ---------------- Generate dashboard ----------------
python3 scripts/generate_dashboard.py

echo "✅ All scripts ran successfully. Check data/ for JSON files."
