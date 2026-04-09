"""
TrendPulse - Task 4: Visualization
Loads the analysis report from Task 3 and produces 5 charts
saved as PNG files in the 'visualizations/' directory.
"""

import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")   # non-interactive backend — works without a display
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ── Setup ─────────────────────────────────────────────────────────────────────

OUTPUT_DIR = "visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Shared style
PALETTE = ["#6C63FF", "#48C9B0", "#F39C12", "#E74C3C", "#3498DB",
           "#2ECC71", "#9B59B6", "#E67E22", "#1ABC9C", "#E91E63"]
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#F8F8F8",
    "axes.edgecolor":   "#CCCCCC",
    "axes.labelcolor":  "#333333",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "xtick.color":      "#555555",
    "ytick.color":      "#555555",
    "grid.color":       "#DDDDDD",
    "grid.linestyle":   "--",
    "grid.linewidth":   0.7,
    "font.family":      "DejaVu Sans",
})


def save_fig(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")
    return path


# ── Chart 1: GitHub — Top 10 repos by popularity score ───────────────────────

def chart_github_top_repos(github_data):
    """Horizontal bar chart of the top 10 GitHub repos by popularity score."""
    top10 = github_data.get("top10_repos", [])
    if not top10:
        print("  No GitHub top-10 data — skipping chart.")
        return

    labels = [r["full_name"].split("/")[-1][:25] for r in top10]
    scores = [r["popularity_score"] for r in top10]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels[::-1], scores[::-1], color=colors[::-1],
                   edgecolor="white", linewidth=0.5)

    # Value labels inside bars
    for bar, score in zip(bars, scores[::-1]):
        ax.text(
            bar.get_width() * 0.98, bar.get_y() + bar.get_height() / 2,
            f"{score:,}", va="center", ha="right",
            fontsize=9, color="white", fontweight="bold"
        )

    ax.set_xlabel("Popularity Score  (stars + forks × 2)", fontsize=11)
    ax.set_title("GitHub Trending — Top 10 Repositories", pad=14)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="x", alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save_fig(fig, "chart1_github_top_repos.png")


# ── Chart 2: GitHub — Programming language distribution ──────────────────────

def chart_github_languages(github_data):
    """Pie / donut chart of the top 8 programming languages."""
    top_langs = github_data.get("top_languages", [])
    if not top_langs:
        print("  No language data — skipping chart.")
        return

    top8 = top_langs[:8]
    labels = [item["language"] for item in top8]
    sizes  = [item["repo_count"] for item in top8]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=PALETTE[:len(top8)],
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5),
        pctdistance=0.75,
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    ax.set_title("GitHub Trending — Language Distribution (Top 8)", pad=16)
    fig.tight_layout()
    save_fig(fig, "chart2_github_languages.png")


# ── Chart 3: Hacker News — Top 10 stories engagement ────────────────────────

def chart_hn_engagement(hn_data):
    """
    Stacked horizontal bar chart showing score vs (comment * 3)
    contribution to the engagement score for top 10 HN stories.
    """
    top10 = hn_data.get("top10_stories", [])
    if not top10:
        print("  No HN top-10 data — skipping chart.")
        return

    labels   = [r["title"][:50] + ("…" if len(r["title"]) > 50 else "") for r in top10]
    scores   = [r["score"]            for r in top10]
    com_pts  = [r["comments"] * 3     for r in top10]   # comment contribution

    fig, ax = plt.subplots(figsize=(12, 7))
    y = range(len(labels))

    b1 = ax.barh(list(y)[::-1], scores[::-1],   color="#6C63FF", label="Score",           edgecolor="white")
    b2 = ax.barh(list(y)[::-1], com_pts[::-1],  color="#48C9B0", label="Comments × 3",
                 left=scores[::-1], edgecolor="white")

    ax.set_xlabel("Engagement Score", fontsize=11)
    ax.set_title("Hacker News — Top 10 Stories by Engagement", pad=14)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_yticks(list(range(len(labels))))
    ax.set_yticklabels(labels[::-1], fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="x", alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save_fig(fig, "chart3_hn_engagement.png")


# ── Chart 4: Weather — Temperature & wind comparison ─────────────────────────

def chart_weather_comparison(weather_data):
    """
    Grouped bar chart comparing temperature (°C) and wind speed (km/h)
    across all cities.  Two y-axes — temperature left, wind right.
    """
    cities_detail = weather_data.get("city_details", [])
    if not cities_detail:
        print("  No weather city details — skipping chart.")
        return

    cities = [c["city"]          for c in cities_detail]
    temps  = [c["temperature_c"] for c in cities_detail]
    winds  = [c["windspeed_kmh"] for c in cities_detail]

    x = range(len(cities))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(10, 6))

    bars1 = ax1.bar([xi - width / 2 for xi in x], temps,
                    width, label="Temperature (°C)", color="#E74C3C", alpha=0.85, edgecolor="white")

    ax2 = ax1.twinx()
    bars2 = ax2.bar([xi + width / 2 for xi in x], winds,
                    width, label="Wind Speed (km/h)", color="#3498DB", alpha=0.85, edgecolor="white")

    ax1.set_ylabel("Temperature (°C)", color="#E74C3C", fontsize=11)
    ax2.set_ylabel("Wind Speed (km/h)", color="#3498DB", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#E74C3C")
    ax2.tick_params(axis="y", labelcolor="#3498DB")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(cities, fontsize=11)
    ax1.set_title("Weather Comparison — Temperature & Wind Speed", pad=14)
    ax1.set_facecolor("#F8F8F8")

    # Combined legend
    lines = [bars1, bars2]
    labels = [bar.get_label() for bar in lines]
    ax1.legend(lines, labels, loc="upper right", fontsize=10)
    ax1.grid(axis="y", alpha=0.5)
    ax1.set_axisbelow(True)
    fig.tight_layout()
    save_fig(fig, "chart4_weather_comparison.png")


# ── Chart 5: Dashboard summary ────────────────────────────────────────────────

def chart_summary_dashboard(report):
    """
    A 2×2 summary dashboard combining key KPIs:
    - GitHub star distribution (histogram)
    - HN score distribution (histogram)
    - City temperatures (horizontal bar)
    - Top language bar chart
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        f"TrendPulse — Summary Dashboard\n"
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        fontsize=14, fontweight="bold", y=1.01
    )

    github_data  = report.get("github", {})
    hn_data      = report.get("hackernews", {})
    weather_data = report.get("weather", {})

    # ── Panel A: GitHub top 5 languages ──────────────────────────────────────
    ax = axes[0][0]
    top_langs = github_data.get("top_languages", [])[:6]
    if top_langs:
        langs  = [item["language"] for item in top_langs]
        counts = [item["repo_count"] for item in top_langs]
        ax.barh(langs[::-1], counts[::-1], color=PALETTE[:len(langs)], edgecolor="white")
        ax.set_title("GitHub — Top Languages", fontsize=12)
        ax.set_xlabel("Repo count", fontsize=10)
        ax.grid(axis="x", alpha=0.5)
        ax.set_axisbelow(True)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("GitHub — Top Languages", fontsize=12)

    # ── Panel B: HN — score vs comments scatter ───────────────────────────────
    ax = axes[0][1]
    top10_hn = hn_data.get("top10_stories", [])
    if top10_hn:
        sc = [r["score"]    for r in top10_hn]
        cm = [r["comments"] for r in top10_hn]
        scatter = ax.scatter(sc, cm, c=PALETTE[:len(sc)], s=100, edgecolors="white", linewidths=0.5, zorder=3)
        for i, r in enumerate(top10_hn):
            ax.annotate(str(r["rank"]),
                        (sc[i], cm[i]),
                        fontsize=8, ha="center", va="center", color="white", fontweight="bold")
        ax.set_xlabel("Score",    fontsize=10)
        ax.set_ylabel("Comments", fontsize=10)
        ax.set_title("Hacker News — Score vs Comments (top 10)", fontsize=12)
        ax.grid(alpha=0.5)
        ax.set_axisbelow(True)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("HN — Score vs Comments", fontsize=12)

    # ── Panel C: City temperature bar ─────────────────────────────────────────
    ax = axes[1][0]
    city_details = weather_data.get("city_details", [])
    if city_details:
        cities = [c["city"]          for c in city_details]
        temps  = [c["temperature_c"] for c in city_details]
        bar_colors = ["#E74C3C" if t >= 20 else "#3498DB" if t < 10 else "#F39C12"
                      for t in temps]
        ax.bar(cities, temps, color=bar_colors, edgecolor="white")
        ax.axhline(0, color="#555555", linewidth=0.8, linestyle="-")
        ax.set_ylabel("Temperature (°C)", fontsize=10)
        ax.set_title("Weather — City Temperatures", fontsize=12)
        ax.grid(axis="y", alpha=0.5)
        ax.set_axisbelow(True)

        # legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#E74C3C", label="Hot (≥20°C)"),
            Patch(facecolor="#F39C12", label="Mild (10–19°C)"),
            Patch(facecolor="#3498DB", label="Cold (<10°C)"),
        ]
        ax.legend(handles=legend_elements, fontsize=8, loc="upper right")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Weather — City Temperatures", fontsize=12)

    # ── Panel D: Key stats text summary ──────────────────────────────────────
    ax = axes[1][1]
    ax.axis("off")

    gh_stats = github_data.get("stars_stats", {})
    hn_stats = hn_data.get("score_stats", {})
    w_stats  = weather_data.get("temperature_stats", {})

    lines = [
        ("GitHub", ""),
        (f"  Repos collected  ", f"{github_data.get('total_repos', 0)}"),
        (f"  Avg stars        ", f"{gh_stats.get('mean', 'N/A'):,}"),
        (f"  Max stars        ", f"{gh_stats.get('max', 'N/A'):,}"),
        ("", ""),
        ("Hacker News", ""),
        (f"  Stories collected", f"{hn_data.get('total_stories', 0)}"),
        (f"  Avg score        ", f"{hn_stats.get('mean', 'N/A')}"),
        (f"  Max score        ", f"{hn_stats.get('max', 'N/A')}"),
        ("", ""),
        ("Weather", ""),
        (f"  Cities tracked   ", f"{weather_data.get('total_cities', 0)}"),
        (f"  Hottest city     ", f"{weather_data.get('hottest_city', 'N/A')}"),
        (f"  Coldest city     ", f"{weather_data.get('coldest_city', 'N/A')}"),
    ]

    y_pos = 0.96
    for label, value in lines:
        if value == "" and label in ("GitHub", "Hacker News", "Weather"):
            ax.text(0.05, y_pos, label, fontsize=11, fontweight="bold",
                    color="#333333", transform=ax.transAxes, va="top")
        else:
            ax.text(0.05, y_pos, label, fontsize=10, color="#555555",
                    transform=ax.transAxes, va="top", family="monospace")
            ax.text(0.72, y_pos, value, fontsize=10, color="#333333",
                    transform=ax.transAxes, va="top", fontweight="bold")
        y_pos -= 0.065

    ax.set_title("Key Statistics", fontsize=12, fontweight="bold")
    ax.set_facecolor("#F8F8F8")

    plt.subplots_adjust(hspace=0.42, wspace=0.38)
    save_fig(fig, "chart5_summary_dashboard.png")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   TrendPulse — Task 4: Visualization")
    print("=" * 55)

    report_path = "analysis/analysis_report.json"
    if not os.path.exists(report_path):
        print("ERROR: 'analysis/analysis_report.json' not found.")
        print("       Run task3_analysis.py first.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    github_data  = report.get("github",     {})
    hn_data      = report.get("hackernews", {})
    weather_data = report.get("weather",    {})

    print()
    chart_github_top_repos(github_data)
    chart_github_languages(github_data)
    chart_hn_engagement(hn_data)
    chart_weather_comparison(weather_data)
    chart_summary_dashboard(report)

    print("\n" + "=" * 55)
    print(f"   5 charts saved to '{OUTPUT_DIR}/'")
    print("=" * 55)
    charts = [
        "chart1_github_top_repos.png",
        "chart2_github_languages.png",
        "chart3_hn_engagement.png",
        "chart4_weather_comparison.png",
        "chart5_summary_dashboard.png",
    ]
    for chart in charts:
        print(f"   • {chart}")
    print("=" * 55)


if __name__ == "__main__":
    main()
    