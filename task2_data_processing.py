"""
TrendPulse - Task 2: Data Processing
Loads raw JSON files from Task 1, cleans and normalises the data,
then saves processed CSVs ready for analysis.
"""

import json
import os
import csv
from datetime import datetime, timezone


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(filepath):
    """Load a JSON file and return its contents."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(rows, fieldnames, filename):
    """Write a list-of-dicts to a CSV file in the 'processed_data' directory."""
    os.makedirs("processed_data", exist_ok=True)
    filepath = os.path.join("processed_data", filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved → {filepath}  ({len(rows)} rows)")
    return filepath


def clean_text(text):
    """Strip leading/trailing whitespace and replace None with empty string."""
    if text is None:
        return ""
    return str(text).strip()


def unix_to_iso(timestamp):
    """Convert a Unix epoch integer to an ISO-8601 datetime string (UTC)."""
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


# ── Processing functions ──────────────────────────────────────────────────────

def process_github(raw):
    """
    Clean GitHub trending repos.

    Steps:
    - Remove repos with missing name or zero stars
    - Normalise language field (None → 'Unknown')
    - Add a 'popularity_score' = stars + forks * 2
    - Truncate descriptions longer than 150 chars
    """
    print("\n[1/3] Processing GitHub trending data...")
    repos = raw.get("repos", [])
    cleaned = []

    for repo in repos:
        name = clean_text(repo.get("name"))
        stars = repo.get("stars", 0)

        # Drop rows missing essential data
        if not name or stars == 0:
            continue

        language = clean_text(repo.get("language")) or "Unknown"
        description = clean_text(repo.get("description"))
        if len(description) > 150:
            description = description[:147] + "..."

        forks = int(repo.get("forks", 0))
        open_issues = int(repo.get("open_issues", 0))
        popularity_score = stars + forks * 2

        cleaned.append({
            "full_name":        clean_text(repo.get("full_name")),
            "name":             name,
            "description":      description,
            "language":         language,
            "stars":            int(stars),
            "forks":            forks,
            "open_issues":      open_issues,
            "popularity_score": popularity_score,
            "created_at":       clean_text(repo.get("created_at")),
            "url":              clean_text(repo.get("url")),
        })

    # Sort by popularity score descending
    cleaned.sort(key=lambda x: x["popularity_score"], reverse=True)

    fieldnames = [
        "full_name", "name", "description", "language",
        "stars", "forks", "open_issues", "popularity_score",
        "created_at", "url",
    ]
    save_csv(cleaned, fieldnames, "github_trending.csv")
    print(f"  {len(repos) - len(cleaned)} rows dropped during cleaning.")
    return cleaned


def process_hackernews(raw):
    """
    Clean Hacker News top stories.

    Steps:
    - Remove stories with missing title or zero score
    - Convert Unix timestamp → ISO-8601
    - Add 'engagement_score' = score + comments * 3
    - Truncate long titles
    """
    print("\n[2/3] Processing Hacker News data...")
    stories = raw.get("stories", [])
    cleaned = []

    for story in stories:
        title = clean_text(story.get("title"))
        score = story.get("score", 0)

        if not title or score == 0:
            continue

        if len(title) > 120:
            title = title[:117] + "..."

        comments = int(story.get("descendants", 0))
        engagement_score = score + comments * 3

        cleaned.append({
            "id":               story.get("id", ""),
            "title":            title,
            "url":              clean_text(story.get("url")),
            "score":            int(score),
            "author":           clean_text(story.get("by")),
            "comments":         comments,
            "engagement_score": engagement_score,
            "posted_at":        unix_to_iso(story.get("time")),
        })

    cleaned.sort(key=lambda x: x["engagement_score"], reverse=True)

    fieldnames = [
        "id", "title", "url", "score", "author",
        "comments", "engagement_score", "posted_at",
    ]
    save_csv(cleaned, fieldnames, "hackernews_top.csv")
    print(f"  {len(stories) - len(cleaned)} rows dropped during cleaning.")
    return cleaned


def process_weather(raw):
    """
    Clean weather data.

    Steps:
    - Fill missing temperature / windspeed with 0.0
    - Add 'feels_cold' flag (temperature < 10°C)
    - Map numeric weathercode to a human-readable label
    - Add hemisphere field based on latitude
    """
    print("\n[3/3] Processing weather data...")

    # WMO Weather Interpretation Codes (simplified subset)
    WMO_CODES = {
        0:  "Clear sky",
        1:  "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm + hail", 99: "Thunderstorm + heavy hail",
    }

    cities = raw.get("cities", [])
    cleaned = []

    for city in cities:
        temp = city.get("temperature_c")
        wind = city.get("windspeed_kmh")
        code = city.get("weathercode", 0)
        lat  = city.get("latitude", 0)

        # Fill missing numeric values
        temp = float(temp) if temp is not None else 0.0
        wind = float(wind) if wind is not None else 0.0

        cleaned.append({
            "city":           clean_text(city.get("city")),
            "latitude":       lat,
            "longitude":      city.get("longitude"),
            "temperature_c":  round(temp, 1),
            "windspeed_kmh":  round(wind, 1),
            "weathercode":    int(code),
            "condition":      WMO_CODES.get(int(code), "Unknown"),
            "is_day":         bool(city.get("is_day", 1)),
            "feels_cold":     temp < 10.0,
            "hemisphere":     "Southern" if float(lat) < 0 else "Northern",
            "local_time":     clean_text(city.get("time")),
        })

    fieldnames = [
        "city", "latitude", "longitude", "temperature_c", "windspeed_kmh",
        "weathercode", "condition", "is_day", "feels_cold", "hemisphere", "local_time",
    ]
    save_csv(cleaned, fieldnames, "weather_data.csv")
    return cleaned


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   TrendPulse — Task 2: Data Processing")
    print("=" * 55)

    raw_dir = "raw_data"
    if not os.path.isdir(raw_dir):
        print("ERROR: 'raw_data/' directory not found.")
        print("       Run task1_data_collection.py first.")
        return

    # Load and process each dataset
    datasets = {
        "github":     ("github_trending.json",   process_github),
        "hackernews": ("hackernews_top.json",     process_hackernews),
        "weather":    ("weather_data.json",       process_weather),
    }

    summary = {}
    for key, (filename, processor) in datasets.items():
        filepath = os.path.join(raw_dir, filename)
        if os.path.exists(filepath):
            raw = load_json(filepath)
            result = processor(raw)
            summary[key] = len(result) if result else 0
        else:
            print(f"\n  WARNING: {filepath} not found — skipping {key}.")
            summary[key] = 0

    # Save a simple processing report
    report = {
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "rows_processed": summary,
        "output_files": {
            "github":     "processed_data/github_trending.csv",
            "hackernews": "processed_data/hackernews_top.csv",
            "weather":    "processed_data/weather_data.csv",
        },
    }
    os.makedirs("processed_data", exist_ok=True)
    with open("processed_data/processing_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 55)
    print("   Processing complete.  CSVs saved to processed_data/")
    print("=" * 55)
    for key, count in summary.items():
        print(f"   {key:<15} {count} rows")
    print("=" * 55)


if __name__ == "__main__":
    main()