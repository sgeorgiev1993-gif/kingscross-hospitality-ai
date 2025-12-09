# King's Cross Hospitality AI

A small open-source MVP to collect public data around King's Cross (London) and summarize weekly insights for local hospitality venues using AI.

### Features
- Eventbrite events around King's Cross
- TfL arrivals & footfall proxy
- Weather data (OpenWeather)
- Local venue reviews (Google Places)
- Weekly OpenAI summary report

### Setup
1. Add API keys in GitHub → Settings → Secrets → Actions
2. The `.env.example` shows which keys you need.
3. GitHub Actions runs every morning at 6 AM UTC and updates CSVs in `/data`.
