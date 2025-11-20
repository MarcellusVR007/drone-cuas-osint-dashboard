#!/usr/bin/env python3
"""
Tier 1 Channel Validation
Scrape sample messages from top priority channels to validate intelligence value
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
SESSION_NAME = 'osint_session'

# Top 5 Tier 1 channels for quick validation
TIER1_CHANNELS = [
    'MedvedevVesti',
    'SolovievLive',
    'belarusian_silovik',
    'rusich_army',
    'patricklancasternewstoday',
    'wybrenvanhaga',  # Dutch political
    'deanderekrant'   # Dutch political
]


async def validate_channels():
    """
    Quick validation scrape - 20 messages per channel
    """
    print("=" * 70)
    print("TIER 1 CHANNEL VALIDATION")
    print("=" * 70)
    print(f"\n🎯 Validating {len(TIER1_CHANNELS)} top-priority channels")
    print("📊 Scraping 20 recent messages per channel\n")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not authorized")
        return

    all_messages = []

    for channel_username in TIER1_CHANNELS:
        print(f"\n{'='*70}")
        print(f"📡 {channel_username}")
        print('='*70)

        try:
            entity = await client.get_entity(channel_username)

            # Get channel info
            print(f"\n📋 Channel: {entity.title}")

            # Get recent messages
            messages = await client.get_messages(entity, limit=20)

            channel_data = {
                'channel': channel_username,
                'title': entity.title,
                'messages': [],
                'intel_indicators': {
                    'ukraine_war': 0,
                    'nato': 0,
                    'dutch_locations': 0,
                    'military': 0,
                    'drone_fpv': 0
                }
            }

            for msg in messages:
                if msg.message:
                    msg_data = {
                        'id': msg.id,
                        'date': msg.date.isoformat(),
                        'text': msg.message[:200],  # First 200 chars
                        'views': msg.views,
                        'forwards': msg.forwards
                    }
                    channel_data['messages'].append(msg_data)

                    # Check intel indicators
                    text_lower = msg.message.lower()
                    if any(kw in text_lower for kw in ['ukraine', 'украин', 'kiev', 'kyiv']):
                        channel_data['intel_indicators']['ukraine_war'] += 1
                    if any(kw in text_lower for kw in ['nato', 'нато']):
                        channel_data['intel_indicators']['nato'] += 1
                    if any(kw in text_lower for kw in ['nederland', 'dutch', 'netherlands', 'schiphol', 'amsterdam']):
                        channel_data['intel_indicators']['dutch_locations'] += 1
                    if any(kw in text_lower for kw in ['drone', 'fpv', 'uav', 'дрон']):
                        channel_data['intel_indicators']['drone_fpv'] += 1
                    if any(kw in text_lower for kw in ['military', 'army', 'troops', 'вооруж', 'военн']):
                        channel_data['intel_indicators']['military'] += 1

            all_messages.append(channel_data)

            # Print indicators
            print(f"\n📊 Intelligence Indicators:")
            print(f"   Ukraine war references: {channel_data['intel_indicators']['ukraine_war']}")
            print(f"   NATO references: {channel_data['intel_indicators']['nato']}")
            print(f"   Dutch locations: {channel_data['intel_indicators']['dutch_locations']}")
            print(f"   Drone/FPV mentions: {channel_data['intel_indicators']['drone_fpv']}")
            print(f"   Military content: {channel_data['intel_indicators']['military']}")

            # Sample message
            if channel_data['messages']:
                print(f"\n💬 Sample message:")
                print(f"   {channel_data['messages'][0]['text']}...")

        except Exception as e:
            print(f"❌ Error: {e}")

        await asyncio.sleep(2)  # Rate limiting

    # Save validation report
    report = {
        'validation_date': datetime.now().isoformat(),
        'channels_validated': len(TIER1_CHANNELS),
        'total_messages_analyzed': sum(len(ch['messages']) for ch in all_messages),
        'channels': all_messages
    }

    output_file = f'tier1_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"\n💾 Report: {output_file}")

    # Summary
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Channels validated: {len(all_messages)}")
    print(f"   Total messages: {report['total_messages_analyzed']}")

    # Intelligence value assessment
    high_value = [ch for ch in all_messages if
                  sum(ch['intel_indicators'].values()) >= 5]
    print(f"   High intel value: {len(high_value)} channels")

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(validate_channels())
