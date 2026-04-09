"""
TrendPulse - Task 1: Data Collection
Fetches live trending data from multiple public APIs and saves raw data to JSON files.
"""

import requests
import json
import os
from datetime import datetime

def save_json(data, filename):
    """Save data as a JSON file in the 'raw_data' directory."""
    os.makedirs("raw_data", exist_ok=True)
    filepath = os.path.join("raw_data", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved → {filepath}")
    return filepath


def fetch_github_trending():
    """
    Fetch trending GitHub repositories using the public GitHub Search API.
    Returns repos sorted by stars created in the last 7 days.
    """
    print("\n[1/3] Fetching GitHub trending repositories...")
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "created:>2024-01-01",
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["name"],
                "full_name": item["full_name"],
                "description": item.get("description", ""),
                "language": item.get("language", "Unknown"),
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "open_issues": item["open_issues_count"],
                "created_at": item["created_at"],
                "url": item["html_url"],
            })

        result = {
            "source": "GitHub Search API",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "total_count": data.get("total_count", 0),
            "repos": repos,
        }
        save_json(result, "github_trending.json")
        print(f"  Retrieved {len(repos)} repositories.")
        return result

    except requests.RequestException as e:
        print(f"  ERROR fetching GitHub data: {e}")
        return None


def fetch_hacker_news_top():
    """
    Fetch top stories from Hacker News using the official Firebase API.
    Retrieves the top 30 story IDs then fetches each story's metadata.
    """
    print("\n[2/3] Fetching Hacker News top stories...")
    base_url = "https://hacker-news.firebaseio.com/v0"

    try:
        # Step 1 – get list of top story IDs
        ids_response = requests.get(f"{base_url}/topstories.json", timeout=10)
        ids_response.raise_for_status()
        story_ids = ids_response.json()[:30]   # top 30

        # Step 2 – fetch each story
        stories = []
        for story_id in story_ids:
            try:
                story_response = requests.get(
                    f"{base_url}/item/{story_id}.json", timeout=10
                )
                story_response.raise_for_status()
                item = story_response.json()
                if item and item.get("type") == "story":
                    stories.append({
                        "id": item["id"],
                        "title": item.get("title", ""),
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                        "score": item.get("score", 0),
                        "by": item.get("by", ""),
                        "time": item.get("time", 0),
                        "descendants": item.get("descendants", 0),  
                    })
            except requests.RequestException:
                continue   

        result = {
            "source": "Hacker News Firebase API",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "stories": stories,
        }
        save_json(result, "hackernews_top.json")
        print(f"  Retrieved {len(stories)} stories.")
        return result

    except requests.RequestException as e:
        print(f"  ERROR fetching Hacker News data: {e}")
        return None


def fetch_open_meteo_weather():
    """
    Fetch current weather data for 5 major world cities from the Open-Meteo API.
    No API key required — fully free and public.
    """
    print("\n[3/3] Fetching Open-Meteo weather data...")

    cities = [
        {"name": "New York",  "lat": 40.71,  "lon": -74.01},
        {"name": "London",    "lat": 51.51,  "lon": -0.13},
        {"name": "Tokyo",     "lat": 35.68,  "lon": 139.69},
        {"name": "Sydney",    "lat": -33.87, "lon": 151.21},
        {"name": "Mumbai",    "lat": 19.08,  "lon": 72.88},
    ]

    url = "https://api.open-meteo.com/v1/forecast"
    weather_data = []

    for city in cities:
        try:
            params = {
                "latitude": city["lat"],
                "longitude": city["lon"],
                "current_weather": True,
                "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m",
                "forecast_days": 1,
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current_weather", {})
            weather_data.append({
                "city": city["name"],
                "latitude": city["lat"],
                "longitude": city["lon"],
                "temperature_c": current.get("temperature"),
                "windspeed_kmh": current.get("windspeed"),
                "weathercode": current.get("weathercode"),
                "is_day": current.get("is_day"),
                "time": current.get("time"),
            })
            print(f"  {city['name']}: {current.get('temperature')}°C")

        except requests.RequestException as e:
            print(f"  ERROR fetching weather for {city['name']}: {e}")

    result = {
        "source": "Open-Meteo API",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "cities": weather_data,
    }
    save_json(result, "weather_data.json")
    print(f"  Retrieved weather for {len(weather_data)} cities.")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   TrendPulse — Task 1: Data Collection")
    print("=" * 55)

    results = {
        "github": fetch_github_trending(),
        "hackernews": fetch_hacker_news_top(),
        "weather": fetch_open_meteo_weather(),
    }

    # Save a summary manifest so downstream tasks know what was collected
    manifest = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "github":      "raw_data/github_trending.json",
            "hackernews":  "raw_data/hackernews_top.json",
            "weather":     "raw_data/weather_data.json",
        },
        "status": {
            source: "ok" if data else "failed"
            for source, data in results.items()
        },
    }
    save_json(manifest, "manifest.json")

    print("\n" + "=" * 55)
    print("   Collection complete.  Raw data saved to raw_data/")
    print("=" * 55)


if __name__ == "__main__":
    main()
