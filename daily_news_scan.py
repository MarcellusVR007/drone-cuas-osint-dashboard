#!/usr/bin/env python3
"""
Daily News Scanner for OSINT CUAS Dashboard

Automatically searches for new drone incidents in trusted news sources.
Run this script daily via cron job to keep database updated.

Usage:
    python3 daily_news_scan.py

Cron setup (run daily at 6 AM):
    0 6 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && python3 daily_news_scan.py >> logs/daily_scan.log 2>&1
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict

API_BASE = "http://localhost:8000/api"

# Countries to monitor with localized keywords
COUNTRY_KEYWORDS = {
    'NL': [
        "drone vliegbasis",
        "drone luchthaven",
        "drone kerncentrale",
        "onbemand vliegtuig",
        "drone luchtruim",
        "drone spionage"
    ],
    'BE': [
        "drone vliegbasis",
        "drone luchthaven",
        "drone kerncentrale",
        "drone luchtruim",
        "drone espionnage",
        "drones Kleine-Brogel"
    ],
    'DE': [
        "Drohne Militärbasis",
        "Drohne Flughafen",
        "Drohne Atomkraftwerk",
        "Drohne Luftraum",
        "Drohne Spionage"
    ],
    'FR': [
        "drone base militaire",
        "drone aéroport",
        "drone centrale nucléaire",
        "drone espace aérien",
        "drone espionnage"
    ],
    'DK': [
        "drone militærbase",
        "drone lufthavn",
        "drone atomkraftværk",
        "drone luftrum"
    ],
    'PL': [
        "dron baza wojskowa",
        "dron lotnisko",
        "dron elektrownia jądrowa",
        "dron szpiegostwo"
    ],
    'LT': [
        "dronas karinė bazė",
        "dronas oro uostas",
        "dronas branduolinė jėgainė"
    ],
    'EE': [
        "droon sõjaväebaas",
        "droon lennujaam",
        "droon tuumaelektrijaam"
    ],
    'ES': [
        "drone base militar",
        "drone aeropuerto",
        "drone central nuclear",
        "drone espionaje"
    ]
}

COUNTRIES = list(COUNTRY_KEYWORDS.keys())


def log(message: str):
    """Timestamped logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_recent_incidents(days: int = 7) -> List[Dict]:
    """Get incidents from last N days"""
    try:
        response = requests.get(f"{API_BASE}/incidents/?limit=100")
        response.raise_for_status()

        cutoff_date = datetime.now() - timedelta(days=days)
        all_incidents = response.json()['incidents']

        recent = [
            inc for inc in all_incidents
            if datetime.fromisoformat(inc['sighting_date']) >= cutoff_date
        ]

        return recent
    except Exception as e:
        log(f"❌ Error fetching incidents: {e}")
        return []


def search_news_for_incidents():
    """Search news sources for new drone incidents"""
    log("🔍 Starting daily news scan...")

    found_articles = []

    for country in COUNTRIES:
        log(f"📰 Scanning {country} news sources...")
        keywords = COUNTRY_KEYWORDS.get(country, [])

        for keyword in keywords:
            try:
                # Use intelligence API to search
                url = f"{API_BASE}/intelligence/articles/search"
                params = {
                    "query": keyword,
                    "country": country,
                    "limit": 5
                }

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])

                    if articles:
                        log(f"  ✓ Found {len(articles)} articles for '{keyword}'")
                        found_articles.extend(articles)

            except Exception as e:
                log(f"  ⚠ Error searching '{keyword}' in {country}: {e}")

    return found_articles


def analyze_articles_for_new_incidents(articles: List[Dict]) -> List[Dict]:
    """
    Analyze articles to identify potential new incidents.
    Returns list of potential incidents for manual review.
    """
    log(f"\n📊 Analyzing {len(articles)} articles...")

    # Filter for high-credibility, recent articles
    potential_incidents = []

    for article in articles:
        # Check credibility (0.0 - 1.0 scale, require at least 0.6 = 60%)
        if article.get('source_credibility', 0) < 0.6:
            continue

        # Check if recent (within last 60 days)
        pub_date = datetime.fromisoformat(article['publish_date'])
        # Make datetime.now() timezone-aware if pub_date has timezone info
        now = datetime.now(pub_date.tzinfo) if pub_date.tzinfo else datetime.now()
        if (now - pub_date).days > 60:
            continue

        # Check sentiment (avoid sensationalist articles)
        if article.get('bias', {}).get('sensational', 0) > 0.7:
            continue

        potential_incidents.append({
            'title': article['title'],
            'url': article['url'],
            'source': article['source_name'],
            'credibility': article['source_credibility'],
            'date': article['publish_date'],
            'summary': article.get('summary', 'No summary')
        })

    return potential_incidents


def save_scan_report(potential_incidents: List[Dict]):
    """Save scan results for manual review"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/scan_report_{timestamp}.json"

    report = {
        "scan_date": datetime.now().isoformat(),
        "potential_incidents_found": len(potential_incidents),
        "incidents": potential_incidents,
        "status": "requires_manual_review"
    }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    log(f"💾 Report saved: {filename}")
    return filename


def main():
    """Main scan workflow"""
    log("=" * 80)
    log("🚁 OSINT CUAS Daily News Scanner")
    log("=" * 80)

    # Step 1: Get recent incidents (to avoid duplicates)
    recent_incidents = get_recent_incidents(days=7)
    log(f"📋 Recent incidents in database: {len(recent_incidents)}")

    # Step 2: Search news sources
    articles = search_news_for_incidents()
    log(f"📰 Total articles found: {len(articles)}")

    if not articles:
        log("ℹ️  No new articles found. Scan complete.")
        return

    # Step 3: Analyze articles for potential new incidents
    potential = analyze_articles_for_new_incidents(articles)

    if potential:
        log(f"\n⚠️  {len(potential)} potential new incidents found!")
        log("─" * 80)

        for idx, incident in enumerate(potential[:5], 1):  # Show first 5
            log(f"{idx}. {incident['title']}")
            log(f"   Source: {incident['source']} (credibility: {incident['credibility']}/10)")
            log(f"   URL: {incident['url'][:80]}...")
            log("")

        # Save report for manual review
        report_file = save_scan_report(potential)
        log(f"\n✅ Review these incidents manually:")
        log(f"   cat {report_file}")
        log(f"   Then add via: python3 add_new_incident.py")
    else:
        log("✅ No new incidents detected. All sources checked.")

    log("=" * 80)
    log("✓ Daily scan complete")
    log("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n👋 Scan cancelled by user")
    except Exception as e:
        log(f"\n❌ Fatal error: {e}")
        raise
