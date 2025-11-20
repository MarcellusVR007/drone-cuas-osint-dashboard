#!/usr/bin/env python3
"""
Round 2: Enhanced Telegram Scraper - More Targeted Keywords
Focus on specific infrastructure targets and shorter timeframe
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

# ENHANCED KEYWORDS - More specific infrastructure targets
LOCATION_KEYWORDS = [
    # Belgium
    'belgium', 'belgië', 'belgique', 'belgian', 'бельгия',
    'doel', 'tihange', 'borssele',  # Nuclear plants
    'liège', 'liege', 'luik', 'льеж',
    'brunssum', 'maastricht', 'limburg',
    'brussels', 'bruxelles', 'brussel', 'брюссель',
    'antwerp', 'antwerpen', 'антверпен',
    'charleroi', 'zaventem',  # Belgium airports

    # Netherlands
    'netherlands', 'nederland', 'нидерланды', 'holland',
    'schiphol', 'amsterdam airport', 'eham',
    'rotterdam', 'rotterdam port', 'роттердам',
    'eindhoven', 'maastricht',

    # Poland
    'poland', 'polska', 'польша',
    'warsaw', 'warszawa', 'варшава',
    'gdansk', 'krakow', 'kraków', 'краков',
    'trzebinia', 'czechowice', 'jedlicze',  # Oil refineries from Post #397

    # Germany
    'germany', 'deutschland', 'германия',
    'frankfurt', 'berlin', 'munich',
]

# Enhanced intel keywords
INTEL_KEYWORDS = [
    # Surveillance/Intel gathering
    'surveillance', 'reconnaissance', 'наблюдение', 'разведка',
    'monitor', 'watch', 'observe', 'track', 'monitor',
    'photograph', 'photo', 'video', 'record', 'фото', 'видео',
    'location', 'coordinates', 'gps', 'map', 'координаты',

    # Payment/Bounty
    'payment', 'bounty', 'reward', 'оплата', 'вознаграждение',
    'bitcoin', 'btc', 'crypto', 'cryptocurrency', 'wallet',
    'euro', 'dollar', 'usd', 'eur', '€', '$',

    # Recruitment
    'recruit', 'recruitment', 'task', 'mission', 'рекрут', 'работа',
    'need', 'looking for', 'hire', 'ищу', 'нужен',
    'contact', 'apply', 'telegram', 'bot', 'бот', 'контакт',

    # Targets
    'nuclear', 'airport', 'аэропорт', 'refinery', 'нпз',
    'military', 'army', 'base', 'военный', 'база',
    'nato', 'otan', 'нато',
    'infrastructure', 'facility', 'infrastructure', 'объект',
    'drone', 'uav', 'бпла', 'дрон',

    # Vulnerability analysis
    'vulnerable', 'weakness', 'gap', 'security', 'уязвим',
    'attack', 'strike', 'target', 'hit', 'атака', 'удар',
]

# Payment patterns
PAYMENT_PATTERNS = [
    r'\$\s*\d+[,.]?\d*',           # $500, $1,000
    r'€\s*\d+[,.]?\d*',            # €500, €1.000
    r'\d+[,.]?\d*\s*(usd|eur|btc)', # 500 USD, 1000 EUR
    r'bitcoin\s+address',
    r'wallet\s*:\s*\w+',
    r'bc1[a-zA-Z0-9]{25,}',        # Bitcoin bech32
    r'[13][a-km-zA-HJ-NP-Z1-9]{25,}', # Bitcoin legacy
]

OUTPUT_DIR = "backend/scraped_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_payment_info(text: str) -> Dict:
    """Extract payment amounts and crypto addresses"""
    payment_info = {
        'amount': None,
        'currency': None,
        'crypto_address': None
    }

    text_lower = text.lower()

    # Check for payment amounts
    for pattern in PAYMENT_PATTERNS[:3]:
        match = re.search(pattern, text_lower)
        if match:
            amount_str = match.group(0)
            # Extract number
            numbers = re.findall(r'\d+[,.]?\d*', amount_str)
            if numbers:
                payment_info['amount'] = float(numbers[0].replace(',', ''))
            # Extract currency
            if '$' in amount_str or 'usd' in amount_str:
                payment_info['currency'] = 'USD'
            elif '€' in amount_str or 'eur' in amount_str:
                payment_info['currency'] = 'EUR'
            elif 'btc' in amount_str or 'bitcoin' in amount_str:
                payment_info['currency'] = 'BTC'
            break

    # Check for crypto addresses
    for pattern in PAYMENT_PATTERNS[3:]:
        match = re.search(pattern, text)
        if match:
            payment_info['crypto_address'] = match.group(0)
            break

    return payment_info


def message_is_relevant(text: str) -> tuple[bool, int]:
    """Check if message is relevant, return (is_relevant, score)"""
    if not text:
        return False, 0

    text_lower = text.lower()
    score = 0

    # Location keyword match
    location_matches = sum(1 for keyword in LOCATION_KEYWORDS if keyword.lower() in text_lower)
    score += location_matches * 3  # High weight for location

    # Intel keyword match
    intel_matches = sum(1 for keyword in INTEL_KEYWORDS if keyword.lower() in text_lower)
    score += intel_matches * 2

    # Payment info present
    payment = extract_payment_info(text)
    if payment['amount']:
        score += 5
    if payment['crypto_address']:
        score += 5

    # Relevance threshold
    is_relevant = score >= 3  # Need at least 1 location or intel match with payment

    return is_relevant, score


async def scrape_channel(client: TelegramClient, channel_username: str,
                        start_date: datetime, end_date: datetime) -> List[Dict]:
    """Scrape a single channel"""

    print(f"\n📡 Scraping @{channel_username}...")

    try:
        entity = await client.get_entity(channel_username)

        if not isinstance(entity, Channel):
            print(f"   ⚠️  Not a channel, skipping")
            return []

        posts = []
        total_messages = 0
        relevant_messages = 0

        # Get messages in date range
        async for message in client.iter_messages(entity, offset_date=end_date, reverse=False):
            total_messages += 1

            # Make timezone naive for comparison
            message_date = message.date.replace(tzinfo=None) if message.date.tzinfo else message.date
            start_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date

            # Stop if before start date
            if message_date < start_naive:
                break

            # Only process text messages
            if not message.text:
                continue

            # Check relevance
            is_relevant, relevance_score = message_is_relevant(message.text)

            if is_relevant:
                relevant_messages += 1

                # Extract payment info
                payment = extract_payment_info(message.text)

                post_data = {
                    'message_id': message.id,
                    'channel': channel_username,
                    'channel_name': entity.title,
                    'date': message.date.isoformat(),
                    'text': message.text,
                    'url': f"https://t.me/{channel_username}/{message.id}",
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                    'relevance_score': relevance_score,
                    'payment_amount': payment['amount'],
                    'payment_currency': payment['currency'],
                    'crypto_address': payment['crypto_address'],
                }

                posts.append(post_data)

        print(f"   ✅ Processed {total_messages} messages, {relevant_messages} relevant")
        return posts

    except Exception as e:
        print(f"   ❌ Error scraping {channel_username}: {e}")
        return []


async def main():
    """Main scraping function"""

    print("=" * 80)
    print("TELEGRAM OSINT SCRAPER - ROUND 2 (Enhanced Targeting)")
    print("=" * 80)

    # Date range - last 60 days only
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    print(f"\n📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 Location keywords: {len(LOCATION_KEYWORDS)}")
    print(f"📊 Intel keywords: {len(INTEL_KEYWORDS)}")
    print(f"📊 Target channels: {len(TARGET_CHANNELS)}")

    # Initialize Telegram client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    await client.start()
    print("\n✅ Telegram client authenticated")

    # Scrape all channels
    all_posts = []

    for channel in TARGET_CHANNELS:
        posts = await scrape_channel(client, channel, start_date, end_date)
        all_posts.extend(posts)
        await asyncio.sleep(2)  # Rate limiting

    # Sort by relevance score
    all_posts.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save ALL relevant posts (not just top 100)
    output_file = f"{OUTPUT_DIR}/telegram_round2_all_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)
    print(f"📊 Total relevant posts: {len(all_posts)}")
    print(f"💾 Saved to: {output_file}")

    if len(all_posts) > 0:
        print(f"\n📈 Top 5 by relevance score:")
        for i, post in enumerate(all_posts[:5], 1):
            print(f"{i}. [{post['relevance_score']}] {post['channel_name']} - {post['date'][:10]}")
            print(f"   {post['text'][:100]}...")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
