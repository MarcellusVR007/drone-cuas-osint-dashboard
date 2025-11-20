#!/usr/bin/env python3
"""
Advanced Telegram Scraper using Official API (Telethon)
Scrapes target channels with full message history and keyword filtering
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel
from telethon.errors import SessionPasswordNeededError
import re

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')

# Session file (stores authentication)
SESSION_NAME = 'osint_session'

# Target channels from research
TARGET_CHANNELS = [
    'grey_zone',          # Grey Zone - Wagner affiliated, 550k subs
    'intelslava',         # Intel Slava Z - Russian news aggregator
    'Warhronika',         # Military Chronicle
    'neuesausrussland',   # Alina Lipp - 175k followers
    'rybar',              # Rybar - OSINT/military analysis
    'voenacher',          # Voenkor - military correspondent
    'reverse_side_medal', # Wagner-linked media
]

# Keywords for filtering
LOCATION_KEYWORDS = [
    'belgium', 'belgië', 'belgique', 'belgian', 'бельгия',
    'doel', 'liège', 'liege', 'luik', 'льеж',
    'brunssum', 'maastricht', 'limburg',
    'brussels', 'bruxelles', 'brussel', 'брюссель',
    'antwerp', 'antwerpen', 'антверпен',
    'netherlands', 'nederland', 'нидерланды',
    'germany', 'deutschland', 'германия',
]

INTEL_KEYWORDS = [
    'surveillance', 'reconnaissance', 'bounty', 'наблюдение',
    'payment', 'bitcoin', 'btc', 'crypto', 'cryptocurrency', 'оплата',
    'recruit', 'recruitment', 'task', 'mission', 'рекрут', 'работа',
    'photograph', 'photo', 'video', 'intel', 'intelligence', 'фото',
    'nato', 'otan', 'нато',
    'nuclear', 'airport', 'аэропорт', 'military',
    'bot', 'бот', 'contact', 'контакт',
]

# Payment patterns
PAYMENT_PATTERNS = [
    r'\$\d+[,\d]*',           # $1000, $10,000
    r'€\d+[,\d]*',            # €1500
    r'\d+\s*(USD|EUR|BTC)',   # 1000 USD
    r'bitcoin',
    r'cryptocurrency',
    r'bc1[a-zA-Z0-9]{20,}',   # Bitcoin bech32 addresses
    r'3[a-zA-Z0-9]{25,}',     # Bitcoin P2SH addresses
    r'1[a-zA-Z0-9]{25,}',     # Bitcoin P2PKH addresses
]


async def authenticate(client: TelegramClient, phone_number: str = None):
    """Authenticate with Telegram"""

    # Function to get phone interactively
    def get_phone():
        return phone_number if phone_number else input("Enter your phone number (with country code, e.g., +31612345678): ")

    # Function to get code interactively
    def get_code():
        return input("Enter the code you received: ")

    # Function to get password if needed
    def get_password():
        return input("Two-step verification enabled. Enter your password: ")

    await client.start(
        phone=get_phone,
        code_callback=get_code,
        password=get_password
    )

    print("✓ Authenticated successfully")


async def get_channel_info(client: TelegramClient, channel_username: str) -> Optional[Dict]:
    """Get basic channel information"""
    try:
        entity = await client.get_entity(channel_username)
        if isinstance(entity, Channel):
            return {
                'id': entity.id,
                'title': entity.title,
                'username': entity.username,
                'participants_count': getattr(entity, 'participants_count', 0),
            }
    except Exception as e:
        print(f"   ✗ Error getting channel info: {e}")
    return None


def matches_keywords(text: str, keywords: List[str]) -> List[str]:
    """Check if text contains any keywords"""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def extract_payment_info(text: str) -> Dict:
    """Extract payment/bounty information"""
    payment_info = {
        'has_payment': False,
        'amounts': [],
        'crypto_addresses': []
    }

    if not text:
        return payment_info

    for pattern in PAYMENT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            payment_info['has_payment'] = True
            payment_info['amounts'].extend(matches)

    return payment_info


async def scrape_channel(client: TelegramClient, channel_username: str,
                        start_date: datetime, end_date: datetime,
                        limit: int = 1000) -> List[Dict]:
    """
    Scrape messages from a Telegram channel
    """
    print(f"\n📡 Scraping @{channel_username}")

    posts = []

    try:
        # Get channel entity
        channel = await client.get_entity(channel_username)
        channel_info = await get_channel_info(client, channel_username)

        if channel_info:
            print(f"   📊 {channel_info['title']}")
            if channel_info.get('participants_count'):
                print(f"   👥 {channel_info['participants_count']:,} members")

        # Iterate through messages
        count = 0
        relevant_count = 0

        async for message in client.iter_messages(channel, limit=limit):
            count += 1

            # Skip if no date
            if not message.date:
                continue

            # Filter by date range
            msg_date = message.date.replace(tzinfo=None)
            if not (start_date <= msg_date <= end_date):
                continue

            # Get message text
            text = message.message or ""

            # Check for location keywords
            location_matches = matches_keywords(text, LOCATION_KEYWORDS)

            # Check for intel keywords
            intel_matches = matches_keywords(text, INTEL_KEYWORDS)

            # Extract payment info
            payment_info = extract_payment_info(text)

            # Only store if relevant
            if location_matches or intel_matches or payment_info['has_payment']:
                relevant_count += 1

                post = {
                    'channel': channel_username,
                    'channel_title': channel_info['title'] if channel_info else channel_username,
                    'message_id': message.id,
                    'post_date': message.date.isoformat(),
                    'post_url': f"https://t.me/{channel_username}/{message.id}",
                    'content': text,
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                    'location_keywords': location_matches,
                    'intel_keywords': intel_matches,
                    'payment_info': payment_info,
                    'relevance_score': len(location_matches) * 2 + len(intel_matches) + (5 if payment_info['has_payment'] else 0),
                }

                posts.append(post)

        print(f"   ✓ Scraped {count} messages, found {relevant_count} relevant posts")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    return posts


async def main():
    print("=" * 80)
    print("TELEGRAM API SCRAPER (Telethon)")
    print("=" * 80)
    print(f"\n🎯 Target: Belgium/Netherlands drone incident intelligence")
    print(f"📅 Timeframe: September 1 - November 13, 2025")
    print(f"📺 Channels: {len(TARGET_CHANNELS)}")

    # Date range
    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 11, 13, 23, 59, 59)

    # Create client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        # Authenticate
        await authenticate(client)

        # Get user info
        me = await client.get_me()
        print(f"   Logged in as: {me.first_name} (@{me.username})")

        all_posts = []

        # Scrape each channel
        for channel in TARGET_CHANNELS:
            posts = await scrape_channel(client, channel, start_date, end_date, limit=2000)
            all_posts.extend(posts)
            await asyncio.sleep(2)  # Rate limiting

        # Sort by relevance
        all_posts.sort(key=lambda x: x['relevance_score'], reverse=True)

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"   Total relevant posts: {len(all_posts)}")

        if all_posts:
            location_posts = [p for p in all_posts if p['location_keywords']]
            intel_posts = [p for p in all_posts if p['intel_keywords']]
            payment_posts = [p for p in all_posts if p['payment_info']['has_payment']]

            print(f"   Posts mentioning locations: {len(location_posts)}")
            print(f"   Posts with intel keywords: {len(intel_posts)}")
            print(f"   Posts with payment info: {len(payment_posts)}")

        # Save results
        output_file = 'data/telegram_api_scraped.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'channels_scraped': TARGET_CHANNELS,
                'total_posts': len(all_posts),
                'posts': all_posts[:100]  # Top 100 most relevant
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved to: {output_file}")

        # Display top results
        if all_posts:
            print("\n" + "=" * 80)
            print("TOP 10 MOST RELEVANT POSTS")
            print("=" * 80)

            for i, post in enumerate(all_posts[:10], 1):
                print(f"\n{i}. @{post['channel']} - {post['post_date'][:10]}")
                print(f"   Relevance: {post['relevance_score']}")
                print(f"   Views: {post['views']:,}")
                if post['location_keywords']:
                    print(f"   🌍 Locations: {', '.join(post['location_keywords'][:5])}")
                if post['intel_keywords']:
                    print(f"   🔍 Intel: {', '.join(post['intel_keywords'][:5])}")
                if post['payment_info']['has_payment']:
                    print(f"   💰 Payment: {', '.join(post['payment_info']['amounts'][:3])}")
                print(f"   🔗 {post['post_url']}")
                print(f"   📝 {post['content'][:200]}...")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
