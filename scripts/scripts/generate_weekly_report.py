import os, pandas as pd, datetime, glob, openai

openai.api_key = os.getenv("OPENAI_API_KEY")
OUT_DIR = "data"
today = datetime.date.today()

# Combine last 7 days of data
def combine_csvs(prefix):
    files = sorted(glob.glob(f"{OUT_DIR}/{prefix}_*.csv"))[-7:]
    if not files: return pd.DataFrame()
    dfs = [pd.read_csv(f) for f in files]
    return pd.concat(dfs, ignore_index=True)

events = combine_csvs("eventbrite")
weather = combine_csvs("weather")
places = combine_csvs("places")

summary_prompt = f"""
Summarize trends for hospitality in King's Cross for the past week:
- {len(events)} events listed
- Average temperature: {weather['temp'].mean() if not weather.empty else 'N/A'}
- Top 3 rated venues:
{places.nlargest(3, 'rating')[['name','rating']].to_string(index=False) if not places.empty else 'N/A'}

Give concise insights that a local restaurant or bar owner would find useful.
"""

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": "You are an analyst for local businesses."},
              {"role": "user", "content": summary_prompt}]
)

summary = response.choices[0].message.content
filename = os.path.join(OUT_DIR, f"weekly_report_{today}.txt")
with open(filename, "w") as f:
    f.write(summary)

print(f"✅ Weekly report saved to {filename}")
print(summary)
