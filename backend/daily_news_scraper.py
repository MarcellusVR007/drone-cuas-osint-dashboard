#!/usr/bin/env python3
"""
Daily News Scraper - Automated drone incident collection
Scrapes RSS feeds from all European news sources daily
"""

import feedparser
import sqlite3
from datetime import datetime, timedelta
import time
from typing import List, Dict
import re
import hashlib

# RSS Feeds per country
RSS_FEEDS = {
    'NL': [
        ('NOS News', 'https://feeds.nos.nl/nosnieuws'),
        ('NU.nl', 'https://www.nu.nl/rss/Algemeen'),
        ('RTL Nieuws', 'https://www.rtlnieuws.nl/rss/binnenland.xml'),
        ('AD.nl', 'https://www.ad.nl/binnenland/rss.xml'),
        ('De Telegraaf', 'https://www.telegraaf.nl/rss'),
        ('NL Times', 'https://nltimes.nl/feed'),
    ],
    'BE': [
        ('VRT News', 'https://www.vrt.be/vrtnws/nl.rss.articles.xml'),
    ],
    'DE': [
        ('Tagesschau', 'https://www.tagesschau.de/xml/rss2_beitrag.xml'),
    ],
    'DK': [
        ('DR Nyheder', 'https://www.dr.dk/nyheder/service/feeds/allenyheder'),
        ('The Local DK', 'https://www.thelocal.dk/feed/'),
    ],
    'UK': [
        ('BBC News', 'https://feeds.bbci.co.uk/news/rss.xml'),
        ('The Guardian', 'https://www.theguardian.com/uk/rss'),
        ('Sky News', 'https://feeds.skynews.com/feeds/rss/uk.xml'),
        ('The Telegraph', 'https://www.telegraph.co.uk/rss.xml'),
        ('Military Times UK', 'https://www.telegraph.co.uk/news/defence/rss'),
    ],
    'SE': [
        ('SVT Nyheter', 'https://www.svt.se/nyheter/rss.xml'),
        ('The Local SE', 'https://www.thelocal.se/feed/'),
    ],
    'NO': [
        ('NRK Nyheter', 'https://www.nrk.no/toppsaker.rss'),
        ('The Local NO', 'https://www.thelocal.no/feed/'),
    ],
    'FR': [
        ('France 24', 'https://www.france24.com/en/rss'),
    ],
}

# Keywords to search for drone incidents
DRONE_KEYWORDS = [
    'drone', 'drones', 'uav', 'unmanned',
    'drohne', 'drohnen',  # German
    'droner',  # Danish/Norwegian
    'drönare',  # Swedish
]

INCIDENT_KEYWORDS = [
    'airport', 'military base', 'air base', 'airspace',
    'sighting', 'spotted', 'detected', 'incident',
    'closed', 'shut down', 'disrupted', 'halted',
    # RAF bases (UK specific)
    'raf', 'lakenheath', 'mildenhall', 'fairford', 'brize norton',
    'waddington', 'marham', 'coningsby', 'lossiemouth',
    # Other locations
    'gatwick', 'heathrow', 'stansted', 'manchester airport',
    'birmingham airport', 'edinburgh airport',
    # Dutch locations
    'luchthaven', 'vliegveld', 'schiphol', 'rotterdam airport',
    'eindhoven airport', 'terneuzen', 'havengebied', 'dow',
    'north sea port', 'kerncentrale', 'doel',
    # Dutch words
    'gezien', 'gemeld', 'waargenomen',
    # German
    'flughafen', 'militärbasis',
    # Danish/Norwegian
    'lufthavn',
    # Swedish
    'flygplats',
]


def is_drone_incident(title: str, summary: str) -> bool:
    """Check if article is about a drone incident"""
    text = f"{title} {summary}".lower()

    has_drone = any(keyword in text for keyword in DRONE_KEYWORDS)
    has_incident = any(keyword in text for keyword in INCIDENT_KEYWORDS)

    return has_drone and has_incident


def generate_hash(title: str, url: str) -> str:
    """Generate unique hash for deduplication"""
    content = f"{title}{url}".encode()
    return hashlib.md5(content).hexdigest()


def scrape_feed(source_name: str, feed_url: str, country: str, days_back: int = 7) -> List[Dict]:
    """Scrape a single RSS feed"""
    print(f"  Scraping {source_name} ({country})...")

    try:
        feed = feedparser.parse(feed_url)
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for entry in feed.entries[:50]:  # Limit to 50 most recent
            # Parse publish date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # Skip if too old
            if pub_date and pub_date < cutoff_date:
                continue

            title = entry.get('title', '')
            summary = entry.get('summary', entry.get('description', ''))
            url = entry.get('link', '')

            # Check if it's a drone incident
            if is_drone_incident(title, summary):
                articles.append({
                    'title': title,
                    'url': url,
                    'source': source_name,
                    'country': country,
                    'pub_date': pub_date or datetime.now(),
                    'summary': summary[:500],
                    'hash': generate_hash(title, url)
                })

        return articles

    except Exception as e:
        print(f"    Error scraping {source_name}: {e}")
        return []


def save_to_database(articles: List[Dict], db_path: str = 'data/drone_cuas_staging.db'):
    """Save articles to incidents database"""

    if not articles:
        print("No articles to save")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create news_articles table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT,
            country TEXT,
            pub_date TEXT,
            summary TEXT,
            hash TEXT UNIQUE,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    new_count = 0
    duplicate_count = 0

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO news_articles (title, url, source, country, pub_date, summary, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article['title'],
                article['url'],
                article['source'],
                article['country'],
                article['pub_date'].isoformat(),
                article['summary'],
                article['hash']
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            # Duplicate hash
            duplicate_count += 1

    # Also import to incidents table for dashboard visibility
    imported = import_to_incidents(cursor, articles)

    conn.commit()
    conn.close()

    print(f"\n✅ Saved {new_count} new articles ({duplicate_count} duplicates skipped)")
    print(f"   Imported {imported} to incidents table")


def import_to_incidents(cursor, articles: List[Dict]) -> int:
    """Import news articles directly to incidents table"""
    imported = 0

    for article in articles:
        try:
            # Parse date
            if isinstance(article['pub_date'], str):
                pub_date = datetime.fromisoformat(article['pub_date'])
            else:
                pub_date = article['pub_date']

            # Create incident from article
            cursor.execute("""
                INSERT OR IGNORE INTO incidents (
                    sighting_date,
                    sighting_time,
                    latitude,
                    longitude,
                    source,
                    source_url,
                    confidence_score,
                    title,
                    description,
                    operational_class,
                    report_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pub_date.date().isoformat(),
                pub_date.time().isoformat()[:5],  # HH:MM
                0.0,  # Unknown lat/lon for now
                0.0,
                article['source'],
                article['url'],
                0.7,  # RSS source = medium confidence
                article['title'],
                article['summary'],
                'RSS_detected',
                datetime.now().isoformat()  # When we discovered it
            ))
            imported += 1
        except Exception as e:
            pass  # Skip if duplicate or error

    return imported


def main():
    """Main scraper function"""
    print("=" * 80)
    print("DAILY NEWS SCRAPER - Drone Incident Collection")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    all_articles = []

    for country, feeds in RSS_FEEDS.items():
        print(f"\n🌍 {country}:")
        for source_name, feed_url in feeds:
            articles = scrape_feed(source_name, feed_url, country, days_back=7)
            all_articles.extend(articles)
            print(f"    Found {len(articles)} potential incidents")
            time.sleep(1)  # Rate limiting

    print(f"\n📊 Total articles found: {len(all_articles)}")

    if all_articles:
        print("\n📰 Recent drone incidents:")
        for article in sorted(all_articles, key=lambda x: x['pub_date'], reverse=True)[:10]:
            print(f"  • [{article['country']}] {article['title'][:80]}...")
            print(f"    {article['source']} - {article['pub_date'].strftime('%Y-%m-%d %H:%M')}")
            print()

    # Save to database
    save_to_database(all_articles)

    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
