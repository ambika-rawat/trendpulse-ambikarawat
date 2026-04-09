"""
TrendPulse - Task 3: Analysis
Loads processed CSVs from Task 2, performs statistical analysis,
and saves a structured analysis report as JSON.
"""

import csv
import json
import os
from collections import Counter
from datetime import datetime
def load_csv(filepath):
    """Load a CSV file and return a list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def safe_float(value, default=0.0):
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """Convert value to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def mean(values):
    """Return arithmetic mean of a list of numbers."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values):
    """Return median of a list of numbers."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return float(sorted_vals[mid])


def stdev(values):
    """Return population standard deviation."""
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    return variance ** 0.5


def percentile(values, p):
    """Return the p-th percentile of a sorted list."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    index = (p / 100) * (len(sorted_vals) - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_vals):
        return float(sorted_vals[-1])
    fraction = index - lower
    return sorted_vals[lower] + fraction * (sorted_vals[upper] - sorted_vals[lower])
def analyse_github(rows):
    """
    Analyse GitHub trending repositories.

    Insights:
    - Language distribution (top 10)
    - Star / fork / popularity statistics
    - Top 10 repos by popularity score
    - Average forks-per-language
    - Issue-to-star ratio (proxy for community activity)
    """
    print("\n[1/3] Analysing GitHub data...")

    stars           = [safe_int(r["stars"])            for r in rows]
    forks           = [safe_int(r["forks"])            for r in rows]
    pop_scores      = [safe_int(r["popularity_score"]) for r in rows]
    open_issues     = [safe_int(r["open_issues"])      for r in rows]
    languages       = [r["language"] for r in rows if r["language"] != "Unknown"]

    # Language distribution
    lang_counts = Counter(languages)
    top_languages = [
        {"language": lang, "repo_count": count}
        for lang, count in lang_counts.most_common(10)
    ]

    # Average popularity per language
    lang_popularity = {}
    for row in rows:
        lang = row["language"]
        if lang == "Unknown":
            continue
        lang_popularity.setdefault(lang, []).append(safe_int(row["popularity_score"]))
    avg_pop_by_lang = [
        {"language": lang, "avg_popularity": round(mean(scores), 1)}
        for lang, scores in sorted(lang_popularity.items(),
                                   key=lambda x: mean(x[1]), reverse=True)
    ][:10]
for row in rows:
        s = safe_int(row["stars"])
        row["_issue_ratio"] = safe_int(row["open_issues"]) / s if s > 0 else 0.0

    top_by_issues = sorted(rows, key=lambda x: x["_issue_ratio"], reverse=True)[:5]
    most_active = [
        {"full_name": r["full_name"], "stars": safe_int(r["stars"]),
         "open_issues": safe_int(r["open_issues"]),
         "issue_ratio": round(r["_issue_ratio"], 4)}
        for r in top_by_issues
    ]

    top_repos = sorted(rows, key=lambda x: safe_int(x["popularity_score"]), reverse=True)[:10]
    top10 = [
        {
            "rank":             i + 1,
            "full_name":        r["full_name"],
            "language":         r["language"],
            "stars":            safe_int(r["stars"]),
            "forks":            safe_int(r["forks"]),
            "popularity_score": safe_int(r["popularity_score"]),
        }
        for i, r in enumerate(top_repos)
    ]

    analysis = {
        "total_repos": len(rows),
        "stars_stats": {
            "min":    min(stars) if stars else 0,
            "max":    max(stars) if stars else 0,
            "mean":   round(mean(stars), 1),
            "median": round(median(stars), 1),
            "stdev":  round(stdev(stars), 1),
            "p75":    round(percentile(stars, 75), 1),
            "p90":    round(percentile(stars, 90), 1),
        },
        "popularity_score_stats": {
            "mean":   round(mean(pop_scores), 1),
            "median": round(median(pop_scores), 1),
            "max":    max(pop_scores) if pop_scores else 0,
        },
        "top_languages":         top_languages,
        "avg_popularity_by_lang": avg_pop_by_lang,
        "most_active_by_issues": most_active,
        "top10_repos":           top10,
    }

    print(f"  Repos analysed : {len(rows)}")
    print(f"  Avg stars      : {round(mean(stars), 1)}")
    print(f"  Most popular   : {top10[0]['full_name'] if top10 else 'N/A'}")
    return analysis


def analyse_hackernews(rows):
    """
    Analyse Hacker News top stories.

    Insights:
    - Score / comment / engagement statistics
    - Top 10 stories by engagement score
    - Most prolific authors
    - Hourly posting distribution
    - Domain frequency (if URL available)
    """
    print("\n[2/3] Analysing Hacker News data...")

    scores      = [safe_int(r["score"])            for r in rows]
    comments    = [safe_int(r["comments"])         for r in rows]
    eng_scores  = [safe_int(r["engagement_score"]) for r in rows]

    # Author frequency
    authors = [r["author"] for r in rows if r["author"]]
    top_authors = [
        {"author": author, "story_count": count}
        for author, count in Counter(authors).most_common(10)
    ]

    hours = []
    for row in rows:
        posted = row.get("posted_at", "")
        if "T" in posted:
            try:
                hour = int(posted.split("T")[1][:2])
                hours.append(hour)
            except (IndexError, ValueError):
                pass
    hour_dist = dict(sorted(Counter(hours).items()))

    # Domain extraction
    domains = []
    for row in rows:
        url = row.get("url", "")
        if url.startswith("http"):
            try:
                domain = url.split("/")[2].replace("www.", "")
                domains.append(domain)
            except IndexError:
                pass
    top_domains = [
        {"domain": d, "count": c}
        for d, c in Counter(domains).most_common(10)
    ]

    # Top 10 stories
    top_stories = sorted(rows, key=lambda x: safe_int(x["engagement_score"]), reverse=True)[:10]
    top10 = [
        {
            "rank":             i + 1,
            "title":            r["title"],
            "score":            safe_int(r["score"]),
            "comments":         safe_int(r["comments"]),
            "engagement_score": safe_int(r["engagement_score"]),
            "author":           r["author"],
        }
        for i, r in enumerate(top_stories)
    ]

    analysis = {
        "total_stories": len(rows),
        "score_stats": {
            "min":    min(scores) if scores else 0,
            "max":    max(scores) if scores else 0,
            "mean":   round(mean(scores), 1),
            "median": round(median(scores), 1),
            "stdev":  round(stdev(scores), 1),
        },
        "comment_stats": {
            "mean":   round(mean(comments), 1),
            "median": round(median(comments), 1),
            "max":    max(comments) if comments else 0,
        },
        "engagement_stats": {
            "mean":   round(mean(eng_scores), 1),
            "max":    max(eng_scores) if eng_scores else 0,
        },
        "top_authors":   top_authors,
        "top_domains":   top_domains,
        "hour_distribution": hour_dist,
        "top10_stories": top10,
    }

    print(f"  Stories analysed: {len(rows)}")
    print(f"  Avg score       : {round(mean(scores), 1)}")
    print(f"  Top story       : {top10[0]['title'][:60] if top10 else 'N/A'}")
    return analysis


def analyse_weather(rows):
    """
    Analyse weather data across 5 cities.

    Insights:
    - Temperature & wind speed statistics
    - Coldest / hottest / windiest city
    - Hemisphere comparison
    - Condition distribution
    """
    print("\n[3/3] Analysing weather data...")

    temps  = [safe_float(r["temperature_c"])  for r in rows]
    winds  = [safe_float(r["windspeed_kmh"])  for r in rows]

    # City rankings
    sorted_by_temp = sorted(rows, key=lambda x: safe_float(x["temperature_c"]))
    sorted_by_wind = sorted(rows, key=lambda x: safe_float(x["windspeed_kmh"]))

    # Hemisphere averages
    northern = [safe_float(r["temperature_c"]) for r in rows if r["hemisphere"] == "Northern"]
    southern = [safe_float(r["temperature_c"]) for r in rows if r["hemisphere"] == "Southern"]

    condition_dist = Counter(r["condition"] for r in rows)

    analysis = {
        "total_cities": len(rows),
        "temperature_stats": {
            "min_c":    round(min(temps), 1) if temps else 0,
            "max_c":    round(max(temps), 1) if temps else 0,
            "mean_c":   round(mean(temps), 1),
            "range_c":  round(max(temps) - min(temps), 1) if temps else 0,
        },
        "wind_stats": {
            "min_kmh":  round(min(winds), 1) if winds else 0,
            "max_kmh":  round(max(winds), 1) if winds else 0,
            "mean_kmh": round(mean(winds), 1),
        },
        "coldest_city":  sorted_by_temp[0]["city"]  if sorted_by_temp else "",
        "hottest_city":  sorted_by_temp[-1]["city"] if sorted_by_temp else "",
        "windiest_city": sorted_by_wind[-1]["city"] if sorted_by_wind else "",
        "hemisphere_avg_temp": {
            "northern": round(mean(northern), 1) if northern else None,
            "southern": round(mean(southern), 1) if southern else None,
        },
        "condition_distribution": dict(condition_dist),
        "city_details": [
            {
                "city":          r["city"],
                "temperature_c": safe_float(r["temperature_c"]),
                "windspeed_kmh": safe_float(r["windspeed_kmh"]),
                "condition":     r["condition"],
                "hemisphere":    r["hemisphere"],
            }
            for r in rows
        ],
    }

    print(f"  Cities analysed : {len(rows)}")
    print(f"  Hottest         : {analysis['hottest_city']}")
    print(f"  Coldest         : {analysis['coldest_city']}")
    return analysis


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   TrendPulse — Task 3: Analysis")
    print("=" * 55)

    proc_dir = "processed_data"
    if not os.path.isdir(proc_dir):
        print("ERROR: 'processed_data/' directory not found.")
        print("       Run task2_data_processing.py first.")
        return

    datasets = {
        "github":     ("github_trending.csv",  analyse_github),
        "hackernews": ("hackernews_top.csv",   analyse_hackernews),
        "weather":    ("weather_data.csv",     analyse_weather),
    }

    report = {"generated_at": datetime.utcnow().isoformat() + "Z"}

    for key, (filename, analyser) in datasets.items():
        filepath = os.path.join(proc_dir, filename)
        if os.path.exists(filepath):
            rows = load_csv(filepath)
            report[key] = analyser(rows)
        else:
            print(f"\n  WARNING: {filepath} not found — skipping {key}.")
            report[key] = {}
    os.makedirs("analysis", exist_ok=True)
    report_path = "analysis/analysis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 55)
    print("   Analysis complete.  Report saved to analysis/")
    print("=" * 55)
    print(f"   Full report → {report_path}")
    print("=" * 55)


if __name__ == "__main__":
    main()
