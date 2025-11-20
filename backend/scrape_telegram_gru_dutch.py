#!/usr/bin/env python3
"""
Telegram GRU Recruitment Monitor - Dutch Channels
Extends existing Telegram scraper with GRU recruitment detection

Based on DOCUMENTED GRU TTP's:
- AIVD 2024 Report: Telegram recruitment of Dutch teenagers
- Latvia 2024: Molotov attack via Telegram
- GRU "Defend The Motherland" recruitment bot (Melodiya Center)

Uses existing scrape_telegram_api.py infrastructure
Adds: Dutch channels + GRU recruitment patterns
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv
import sys

# Import existing scraper functions
sys.path.append(os.path.dirname(__file__))
from scrape_telegram_api import (
    TelegramClient, API_ID, API_HASH, SESSION_NAME,
    authenticate, scrape_channel, extract_payment_info
)

# Load environment variables
load_dotenv()

# DUTCH TARGET CHANNELS (Pro-Russia / Anti-NATO)
# Based on WEB RESEARCH (2025-11-16) - VERIFIED public channels
# Sources: UvA research (4,070 Dutch Telegram groups), news reports, Telegram search
DUTCH_TARGET_CHANNELS = [
    # ✅ VERIFIED - FvD-related (right-wing, pro-Russia sympathies)
    'FVDNL',              # Official Forum voor Democratie channel (VERIFIED @FVDNL)

    # ✅ VERIFIED - Alternative media (anti-establishment, conspiracy theories)
    'Cafe_Weltschmerz',   # Café Weltschmerz - alternative media platform (VERIFIED @Cafe_Weltschmerz)

    # NOTE: "FVD geluiden" supporter groups exist but may be private
    # Research shows 8,000+ members, extreme content, but unclear if public
    # If accessible, add: 'fvdgeluiden', 'fvdgeluid'

    # ⚠️ Additional channels to investigate (mentioned in UvA research):
    # - worldunity_me (World Unity - "Truth Revolution")
    # - kanalen_nl (Collection of Dutch channels)
    # - Various "waarheid" (truth) related channels

    # Research notes:
    # - 4,070 public Dutch Telegram groups identified (2022 UvA study)
    # - 215 far-right channels with 370k posts (2017-2021)
    # - Growth from 334 (2020) → 4,354 (2021) during COVID
    # - Content: QAnon, Great Reset, anti-NATO, anti-government
]

# Additional Russian channels that may recruit in Dutch/English
RUSSIAN_CHANNELS_WITH_DUTCH_RECRUITMENT = [
    'grey_zone',          # Wagner-affiliated (may recruit internationally)
    'intelslava',         # Intel Slava Z
    'rybar',              # Rybar
]

# GRU RECRUITMENT KEYWORDS (from documented cases)
# Based on AIVD reports and Latvia case

GRU_RECRUITMENT_DUTCH = [
    # Direct recruitment (Dutch)
    'zoeken mensen',           # looking for people
    'hulp nodig',              # need help
    'verdien geld',            # earn money
    'bijverdienen',            # side income
    'freelance werk',          # freelance work
    'simpele taken',           # simple tasks
    'betaling in bitcoin',     # payment in bitcoin
    'anoniem werk',            # anonymous work

    # Recruitment (English)
    'looking for people',
    'need someone',
    'earn money',
    'freelance work',
    'simple tasks',
    'bitcoin payment',
    'crypto payment',
]

GRU_TASKS_DUTCH = [
    # Intelligence gathering tasks (from documented cases)
    "foto's maken",            # take photos
    'fotograferen',            # photograph
    'documenteren',            # document
    'observeren',              # observe
    'informatie verzamelen',   # collect information
    'kaarten kopen',           # buy maps (documented GRU task!)
    'SIM kaarten',             # SIM cards (documented GRU task!)

    # English equivalents
    'take photos',
    'photograph',
    'document',
    'observe',
    'collect information',
    'buy maps',
    'SIM cards',
]

GRU_IDEOLOGICAL_DUTCH = [
    # Anti-NATO / Patriotic framing
    'tegen NAVO',              # against NATO
    'stop NAVO',               # stop NATO
    'verdedig Nederland',      # defend Netherlands
    'help Rusland',            # help Russia
    'waarheid tonen',          # show truth
    'onthul NAVO',             # expose NATO
    'patriotten',              # patriots

    # English
    'against NATO',
    'stop NATO',
    'defend Netherlands',
    'help Russia',
    'expose NATO',
    'patriots',
]

GRU_LOCATIONS_DUTCH = [
    # Strategic locations (military bases, airports)
    'Schiphol',
    'Eindhoven vliegveld',
    'Eindhoven airport',
    'Volkel',                  # Volkel Air Base (F-35s!)
    'Gilze-Rijen',             # Gilze-Rijen Air Base
    'Rotterdam haven',         # Rotterdam port
    'Rotterdam port',
    'Brunssum',                # NATO HQ
    'Den Haag',                # The Hague (government)
    'Woensdrecht',             # Air base
]

# Combine all keywords
ALL_GRU_KEYWORDS = (
    GRU_RECRUITMENT_DUTCH +
    GRU_TASKS_DUTCH +
    GRU_IDEOLOGICAL_DUTCH +
    GRU_LOCATIONS_DUTCH
)


def calculate_gru_recruitment_score(text: str, payment_info: Dict) -> int:
    """
    Calculate GRU recruitment likelihood score (0-100)

    Based on documented TTP's:
    - Recruitment language + tasks + payment = HIGH
    - Ideological framing + locations = MEDIUM
    - Single indicators = LOW
    """
    if not text:
        return 0

    text_lower = text.lower()
    score = 0

    # Check recruitment language
    recruitment_matches = sum(1 for kw in GRU_RECRUITMENT_DUTCH if kw.lower() in text_lower)
    if recruitment_matches > 0:
        score += 30  # CRITICAL indicator

    # Check task descriptions
    task_matches = sum(1 for kw in GRU_TASKS_DUTCH if kw.lower() in text_lower)
    if task_matches > 0:
        score += 25  # CRITICAL indicator

    # Check payment
    if payment_info.get('has_payment'):
        score += 20  # HIGH indicator

    # Check ideological framing
    ideology_matches = sum(1 for kw in GRU_IDEOLOGICAL_DUTCH if kw.lower() in text_lower)
    if ideology_matches > 0:
        score += 15  # MEDIUM indicator

    # Check location targeting
    location_matches = sum(1 for kw in GRU_LOCATIONS_DUTCH if kw.lower() in text_lower)
    if location_matches > 0:
        score += 20  # HIGH indicator (specific targeting)

    return min(score, 100)  # Cap at 100


async def scrape_dutch_gru_recruitment(days_back: int = 30):
    """
    Scrape Dutch Telegram channels for GRU recruitment activity

    Args:
        days_back: How many days of history to scrape (default 30)
    """
    print("="*70)
    print("🔍 TELEGRAM GRU RECRUITMENT MONITOR - DUTCH CHANNELS")
    print("Based on AIVD 2024 Report & documented GRU TTP's")
    print("="*70)

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    print(f"\n📅 Scraping period: {start_date.date()} to {end_date.date()}")
    print(f"🎯 Target: {len(DUTCH_TARGET_CHANNELS)} Dutch channels + {len(RUSSIAN_CHANNELS_WITH_DUTCH_RECRUITMENT)} Russian channels")

    if not DUTCH_TARGET_CHANNELS:
        print("\n⚠️  WARNING: No Dutch channels configured!")
        print("   Current targets are EXAMPLES. Need to:")
        print("   1. Manually research which Dutch pro-Russia channels exist")
        print("   2. Verify channels are PUBLIC (legal OSINT)")
        print("   3. Add channel usernames to DUTCH_TARGET_CHANNELS")
        print("\n   For now, scraping Russian channels only...")

    # Initialize Telegram client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    print("\n✅ Authenticated with Telegram\n")

    all_posts = []
    all_channels = DUTCH_TARGET_CHANNELS + RUSSIAN_CHANNELS_WITH_DUTCH_RECRUITMENT

    for channel in all_channels:
        try:
            posts = await scrape_channel(
                client,
                channel,
                start_date,
                end_date,
                limit=1000
            )

            # Add GRU recruitment scoring to each post
            for post in posts:
                payment_info = extract_payment_info(post.get('content', ''))
                gru_score = calculate_gru_recruitment_score(
                    post.get('content', ''),
                    payment_info
                )
                post['gru_recruitment_score'] = gru_score

                # Flag HIGH/CRITICAL
                if gru_score >= 50:
                    print(f"\n   🚨 CRITICAL: GRU Score {gru_score}/100")
                    print(f"      Channel: @{channel}")
                    print(f"      Preview: {post['content'][:100]}...")
                elif gru_score >= 30:
                    print(f"\n   ⚠️  HIGH: GRU Score {gru_score}/100")
                    print(f"      Channel: @{channel}")
                    print(f"      Preview: {post['content'][:100]}...")

            all_posts.extend(posts)

        except Exception as e:
            print(f"   ❌ Error scraping @{channel}: {e}")

    await client.disconnect()

    # Analysis
    print("\n" + "="*70)
    print("📊 SCRAPING COMPLETE")
    print("="*70)
    print(f"\nTotal posts collected: {len(all_posts)}")

    critical = sum(1 for p in all_posts if p.get('gru_recruitment_score', 0) >= 50)
    high = sum(1 for p in all_posts if 30 <= p.get('gru_recruitment_score', 0) < 50)
    medium = sum(1 for p in all_posts if 20 <= p.get('gru_recruitment_score', 0) < 30)

    print(f"\n🔴 CRITICAL (50+): {critical} posts")
    print(f"🟠 HIGH (30-49):   {high} posts")
    print(f"🟡 MEDIUM (20-29): {medium} posts")

    if critical > 0:
        print(f"\n⚠️  {critical} CRITICAL posts found - MANUAL REVIEW REQUIRED!")
        print("    These may be GRU recruitment attempts.")
        print("    Consider reporting to AIVD: https://www.aivd.nl/onderwerpen/melden")

    # Save results
    output_file = f"telegram_gru_dutch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    return all_posts


async def main():
    """Main function"""
    print("\n🇳🇱 Telegram GRU Recruitment Monitor - Dutch Channels")
    print("Based on documented GRU TTP's from AIVD reports\n")

    # Scrape last 30 days
    await scrape_dutch_gru_recruitment(days_back=30)


if __name__ == '__main__':
    asyncio.run(main())
