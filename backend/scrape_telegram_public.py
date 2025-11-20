#!/usr/bin/env python3
"""
Public Telegram Channel Scraper
Scrapes public Telegram channels without requiring API credentials
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Target channels identified from research
TARGET_CHANNELS = [
    'grey_zone',          # Grey Zone - Wagner affiliated, 550k subs (may be blocked in EU)
    'intelslava',         # Intel Slava Z - Russian news aggregator
    'Warhronika',         # Military Chronicle
    'neuesausrussland',   # Alina Lipp - 175k followers, EU-sanctioned
    'rybar',              # Rybar - OSINT/military analysis
    'voenacher',          # Voenkor - military correspondent
    'reverse_side_medal', # Wagner-linked media
]

# Keywords related to Belgium drone incidents AND recruitment
KEYWORDS = [
    # Locations
    'belgium', 'belgië', 'belgique', 'belgian', 'bельгия',
    'doel', 'liège', 'liege', 'luik', 'льеж',
    'brunssum', 'maastricht', 'limburg',
    'brussels', 'bruxelles', 'brussel', 'брюссель',
    'antwerp', 'antwerpen', 'антверпен',
    'netherlands', 'nederland', 'нидерланды',
    'germany', 'deutschland', 'германия',

    # Infrastructure
    'nuclear', 'kerncentrale', 'airport', 'luchthaven', 'аэропорт',
    'nato', 'otan', 'нато', 'military base', 'airbase',
    'f-16', 'f-35', 'kleine-brogel',

    # Surveillance/Intel keywords
    'surveillance', 'reconnaissance', 'bounty', 'наблюдение',
    'payment', 'bitcoin', 'btc', 'crypto', 'cryptocurrency', 'оплата',
    'recruit', 'recruitment', 'task', 'mission', 'рекрут', 'работа',
    'photograph', 'photo', 'video', 'intel', 'intelligence', 'фото',

    # Bot/contact keywords
    'bot', 'бот', 'contact', 'контакт', '@', 'dm',
    'join', 'присоединяйся', 'write', 'пиши',
]

# Bounty/payment indicators
PAYMENT_PATTERNS = [
    r'\$\d+[,\d]*',           # $1000, $10,000
    r'€\d+[,\d]*',            # €1500
    r'\d+\s*(USD|EUR|BTC)',   # 1000 USD
    r'bitcoin',
    r'cryptocurrency',
    r'crypto\s+wallet',
    r'bc1[a-zA-Z0-9]{20,}',   # Bitcoin addresses
    r'3[a-zA-Z0-9]{25,}',     # Bitcoin addresses
]


def scrape_telegram_channel(channel: str, max_posts: int = 200) -> List[Dict]:
    """
    Scrape public Telegram channel using t.me/s/ endpoint
    """
    url = f"https://t.me/s/{channel}"
    posts = []

    print(f"\n📡 Scraping channel: @{channel}")
    print(f"   URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all message containers
        messages = soup.find_all('div', class_='tgme_widget_message')

        print(f"   Found {len(messages)} posts on page")

        for msg in messages[:max_posts]:
            try:
                post = parse_telegram_post(msg, channel)
                if post:
                    posts.append(post)
            except Exception as e:
                print(f"   ⚠️  Error parsing post: {e}")
                continue

        print(f"   ✓ Scraped {len(posts)} posts successfully")

    except Exception as e:
        print(f"   ✗ Error scraping channel: {e}")

    return posts


def parse_telegram_post(msg_element, channel: str) -> Optional[Dict]:
    """
    Parse individual Telegram post from HTML
    """
    try:
        # Extract post ID
        post_link = msg_element.find('a', class_='tgme_widget_message_date')
        if not post_link:
            return None

        post_url = post_link['href']
        post_id = post_url.split('/')[-1]

        # Extract timestamp
        time_elem = msg_element.find('time')
        if time_elem and time_elem.get('datetime'):
            post_date = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
        else:
            post_date = None

        # Extract message text
        text_elem = msg_element.find('div', class_='tgme_widget_message_text')
        content = text_elem.get_text(strip=True) if text_elem else ""

        # Extract views
        views_elem = msg_element.find('span', class_='tgme_widget_message_views')
        views = views_elem.get_text(strip=True) if views_elem else "0"

        post = {
            'channel': channel,
            'post_id': post_id,
            'post_url': post_url,
            'post_date': post_date.isoformat() if post_date else None,
            'content': content,
            'views': views,
        }

        return post

    except Exception as e:
        print(f"      Error parsing post: {e}")
        return None


def filter_relevant_posts(posts: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    Filter posts containing relevant keywords
    """
    relevant = []

    for post in posts:
        content_lower = post['content'].lower()

        # Check if any keyword is present
        matches = [kw for kw in keywords if kw.lower() in content_lower]

        if matches:
            post['matched_keywords'] = matches
            relevant.append(post)

    return relevant


def extract_payment_info(content: str) -> Dict:
    """
    Extract payment/bounty information from post content
    """
    payment_info = {
        'has_payment': False,
        'amounts': [],
        'crypto_addresses': []
    }

    for pattern in PAYMENT_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            payment_info['has_payment'] = True
            payment_info['amounts'].extend(matches)

    # Extract Bitcoin addresses
    btc_pattern = r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b'
    btc_matches = re.findall(btc_pattern, content)
    if btc_matches:
        payment_info['crypto_addresses'].extend(btc_matches)

    return payment_info


def analyze_posts_for_intel(posts: List[Dict]) -> List[Dict]:
    """
    Analyze posts for intelligence/surveillance/bounty indicators
    """
    intel_posts = []

    intel_keywords = [
        'surveillance', 'reconnaissance', 'intel', 'photo', 'video',
        'bounty', 'payment', 'recruit', 'task', 'mission', 'reward'
    ]

    for post in posts:
        content_lower = post['content'].lower()

        # Check for intel keywords
        intel_matches = [kw for kw in intel_keywords if kw in content_lower]

        # Extract payment info
        payment_info = extract_payment_info(post['content'])

        if intel_matches or payment_info['has_payment']:
            post['intel_keywords'] = intel_matches
            post['payment_info'] = payment_info
            post['relevance_score'] = len(intel_matches) + (5 if payment_info['has_payment'] else 0)
            intel_posts.append(post)

    # Sort by relevance
    intel_posts.sort(key=lambda x: x['relevance_score'], reverse=True)

    return intel_posts


def filter_by_date_range(posts: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """
    Filter posts within date range
    """
    from datetime import timezone
    start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

    filtered = []
    for post in posts:
        if post['post_date']:
            post_date = datetime.fromisoformat(post['post_date'])
            # Make timezone aware if needed
            if post_date.tzinfo is None:
                post_date = post_date.replace(tzinfo=timezone.utc)
            if start <= post_date <= end:
                filtered.append(post)

    return filtered


def main():
    print("=" * 80)
    print("TELEGRAM PUBLIC CHANNEL SCRAPER")
    print("=" * 80)
    print("\n🎯 Target: Belgium/Netherlands drone incident intelligence")
    print(f"📅 Timeframe: September - November 2025")
    print(f"📺 Channels: {len(TARGET_CHANNELS)}")
    print(f"🔍 Keywords: {len(KEYWORDS)}")

    all_posts = []

    # Scrape each channel
    for channel in TARGET_CHANNELS:
        posts = scrape_telegram_channel(channel, max_posts=200)
        all_posts.extend(posts)
        time.sleep(2)  # Be polite to Telegram servers

    print(f"\n📊 Total posts scraped: {len(all_posts)}")

    # Filter by date range (Sept 1 - Nov 13, 2025)
    date_filtered = filter_by_date_range(all_posts, "2025-09-01", "2025-11-13")
    print(f"   Posts in date range: {len(date_filtered)}")

    # Filter for Belgium/NATO keywords
    relevant = filter_relevant_posts(date_filtered, KEYWORDS)
    print(f"   Posts with relevant keywords: {len(relevant)}")

    # Analyze for intelligence/bounty posts
    intel_posts = analyze_posts_for_intel(relevant)
    print(f"   Intelligence/bounty posts: {len(intel_posts)}")

    # Save results
    output_file = 'data/telegram_scraped_posts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total_posts': len(all_posts),
            'relevant_posts': len(relevant),
            'intel_posts': len(intel_posts),
            'posts': intel_posts
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved to: {output_file}")

    # Display top results
    if intel_posts:
        print("\n" + "=" * 80)
        print("TOP INTELLIGENCE POSTS")
        print("=" * 80)

        for i, post in enumerate(intel_posts[:10], 1):
            print(f"\n{i}. @{post['channel']} - {post['post_date'][:10] if post['post_date'] else 'Unknown'}")
            print(f"   Relevance: {post['relevance_score']}")
            print(f"   Keywords: {', '.join(post.get('intel_keywords', []))}")
            if post['payment_info']['has_payment']:
                print(f"   💰 Payment indicators: {post['payment_info']['amounts']}")
            print(f"   URL: {post['post_url']}")
            print(f"   Content preview: {post['content'][:200]}...")

    return intel_posts


if __name__ == "__main__":
    main()
