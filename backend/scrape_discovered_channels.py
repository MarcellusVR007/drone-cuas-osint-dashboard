#!/usr/bin/env python3
"""
Scrape Discovered Channels
Collect messages from Tier 1 and Tier 2 discovered channels
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List
from dotenv import load_dotenv
from telethon import TelegramClient
import sys

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'osint_session'

# Tier 1 channels (critical - 200 messages)
TIER1_CHANNELS = [
    'MedvedevVesti',
    'SolovievLive',
    'belarusian_silovik',
    'rusich_army',
    'patricklancasternewstoday',
    'rybar_stan',
    'dva_majors',
    'wybrenvanhaga',
    'voin_dv',
    'geopolitics_prime',
    'deanderekrant'
]

# Tier 2 channels (high - 100 messages)
TIER2_CHANNELS = [
    'mikayelbad',
    'ne_rybar',
    'rybar_africa',
    'rybar_latam',
    'evropar',
    'caucasar',
    'rybar_mena',
    'rybar_pacific',
    'lidewij_devos',
    'NeoficialniyBeZsonoV',
    'pezdicide'
]

# Intelligence keywords
INTEL_KEYWORDS = [
    'drone', 'fpv', 'uav', 'quadcopter', 'дрон',
    'schiphol', 'eindhoven', 'rotterdam', 'amsterdam', 'nederland', 'netherlands', 'dutch',
    'belgium', 'belgië', 'brussels', 'antwerp',
    'nato', 'нато', 'military base', 'airport',
    'reconnaissance', 'surveillance', 'операция'
]

async def scrape_channels(channels: List[str], messages_per_channel: int, tier_name: str):
    """
    Scrape list of channels
    """
    print(f"\n{'='*70}")
    print(f"SCRAPING {tier_name}")
    print('='*70)
    print(f"Channels: {len(channels)}")
    print(f"Messages per channel: {messages_per_channel}\n")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not authorized")
        return []

    all_messages = []
    total_scraped = 0
    total_relevant = 0

    for channel_username in channels:
        print(f"📡 Scraping @{channel_username}...")

        try:
            entity = await client.get_entity(channel_username)

            # Get messages
            messages = await client.get_messages(entity, limit=messages_per_channel)

            channel_messages = []
            relevant_count = 0

            for msg in messages:
                if not msg.message:
                    continue

                # Check for intel keywords
                text_lower = msg.message.lower()
                intel_kw = [kw for kw in INTEL_KEYWORDS if kw.lower() in text_lower]

                msg_data = {
                    'message_id': msg.id,
                    'channel': channel_username,
                    'channel_title': entity.title if hasattr(entity, 'title') else channel_username,
                    'post_date': msg.date.isoformat(),
                    'content': msg.message,
                    'views': msg.views or 0,
                    'forwards': msg.forwards or 0,
                    'intel_keywords': intel_kw,
                    'tier': tier_name
                }

                channel_messages.append(msg_data)

                if intel_kw:
                    relevant_count += 1

            all_messages.extend(channel_messages)
            total_scraped += len(channel_messages)
            total_relevant += relevant_count

            print(f"   ✓ {len(channel_messages)} messages, {relevant_count} with intel keywords")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        await asyncio.sleep(2)  # Rate limiting

    await client.disconnect()

    print(f"\n{'='*70}")
    print(f"{tier_name} COMPLETE")
    print('='*70)
    print(f"Total messages: {total_scraped}")
    print(f"With intel keywords: {total_relevant} ({total_relevant/total_scraped*100:.1f}%)\n")

    return all_messages


async def main():
    """Main scraping pipeline"""
    print("="*70)
    print("DISCOVERED CHANNELS DATA COLLECTION")
    print("="*70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Scrape Tier 1
    tier1_data = await scrape_channels(TIER1_CHANNELS, 200, "TIER 1")

    # Scrape Tier 2
    tier2_data = await scrape_channels(TIER2_CHANNELS, 100, "TIER 2")

    # Combine
    all_data = tier1_data + tier2_data

    # Save
    output_file = f"discovered_channels_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print("="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70)
    print(f"\n💾 Saved: {output_file}")
    print(f"📊 Total messages: {len(all_data)}")
    print(f"📡 Tier 1: {len(tier1_data)} messages from {len(TIER1_CHANNELS)} channels")
    print(f"📡 Tier 2: {len(tier2_data)} messages from {len(TIER2_CHANNELS)} channels")

    # Intel summary
    total_with_intel = sum(1 for m in all_data if m.get('intel_keywords'))
    print(f"🎯 Messages with intel keywords: {total_with_intel} ({total_with_intel/len(all_data)*100:.1f}%)")

    # Top keywords
    all_keywords = []
    for msg in all_data:
        all_keywords.extend(msg.get('intel_keywords', []))

    if all_keywords:
        from collections import Counter
        top_keywords = Counter(all_keywords).most_common(10)
        print(f"\n🔝 Top keywords:")
        for kw, count in top_keywords:
            print(f"   {kw}: {count}")

    print(f"\n✅ Ready for database import and correlation analysis\n")


if __name__ == '__main__':
    asyncio.run(main())
