#!/usr/bin/env python3
"""
Telegram Channel Expander
Uses Telethon API to actively discover new channels related to seeds

Discovery Methods:
1. Forward chain analysis (who forwards to/from seed channels)
2. Channel search by keywords extracted from messages
3. Related channels suggestions
4. User participation overlap analysis
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import asyncio
import re
from typing import List, Set, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from telethon import TelegramClient
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import InputMessagesFilterEmpty

# Telegram credentials - use from environment or existing session
from dotenv import load_dotenv
load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
PHONE = os.getenv('TELEGRAM_PHONE', '')
SESSION_NAME = 'osint_session'  # Use existing authenticated session

class TelegramChannelExpander:
    """
    Actively discover new Telegram channels using API
    """

    def __init__(self, seed_channels: List[str], output_file: str = 'discovered_channels.json'):
        self.seed_channels = seed_channels
        self.output_file = output_file
        self.discovered = {}
        self.client = None

    async def initialize(self):
        """Initialize Telegram client"""
        print("🔐 Initializing Telegram client...")
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            print("❌ Session not authorized. Please run scrape_telegram_api.py first to authenticate.")
            raise Exception("Not authenticated")

        print("✓ Connected to Telegram (using existing session)\n")

    async def discover_by_forwards(self, channel_username: str, limit: int = 100) -> Set[str]:
        """
        Method 1: Analyze forward chains
        Find channels that messages are forwarded to/from
        """
        print(f"📤 Analyzing forwards from @{channel_username}...")
        discovered = set()

        try:
            entity = await self.client.get_entity(channel_username)

            # Get recent messages
            messages = await self.client.get_messages(entity, limit=limit)

            for msg in messages:
                if msg.forward:
                    # Message was forwarded from another channel
                    if msg.forward.from_id:
                        try:
                            forward_from = await self.client.get_entity(msg.forward.from_id)
                            if hasattr(forward_from, 'username') and forward_from.username:
                                discovered.add(forward_from.username)
                                print(f"  ↩️  Found forward source: @{forward_from.username}")
                        except:
                            pass

            print(f"✓ Discovered {len(discovered)} channels via forwards\n")

        except Exception as e:
            print(f"❌ Error analyzing @{channel_username}: {e}\n")

        return discovered

    async def discover_by_search(self, keywords: List[str], limit_per_keyword: int = 10) -> Set[str]:
        """
        Method 2: Search Telegram for channels matching keywords
        """
        print(f"🔍 Searching for channels with keywords: {', '.join(keywords[:5])}...")
        discovered = set()

        for keyword in keywords:
            try:
                print(f"  Searching: {keyword}")

                # Search global for keyword
                result = await self.client(SearchGlobalRequest(
                    q=keyword,
                    filter=InputMessagesFilterEmpty(),
                    min_date=None,
                    max_date=None,
                    offset_rate=0,
                    offset_peer=None,
                    offset_id=0,
                    limit=limit_per_keyword
                ))

                # Extract channels from results
                for msg in result.messages:
                    try:
                        chat = await self.client.get_entity(msg.peer_id)
                        if hasattr(chat, 'username') and chat.username:
                            discovered.add(chat.username)
                            print(f"    📢 Found: @{chat.username}")
                    except:
                        pass

                # Rate limiting
                await asyncio.sleep(2)

            except Exception as e:
                print(f"  ⚠️  Search error for '{keyword}': {e}")

        print(f"✓ Discovered {len(discovered)} channels via search\n")
        return discovered

    async def discover_by_mentions(self, channel_username: str, limit: int = 200) -> Set[str]:
        """
        Method 3: Extract channel mentions from message content
        """
        print(f"📝 Extracting mentions from @{channel_username}...")
        discovered = set()

        try:
            entity = await self.client.get_entity(channel_username)
            messages = await self.client.get_messages(entity, limit=limit)

            for msg in messages:
                if msg.message:
                    # Find @mentions
                    mentions = re.findall(r'@(\w+)', msg.message)
                    for mention in mentions:
                        # Verify it's a real channel
                        try:
                            check = await self.client.get_entity(mention)
                            if hasattr(check, 'username') and check.broadcast:  # Is a channel
                                discovered.add(mention)
                                print(f"  👉 Found mention: @{mention}")
                        except:
                            pass

            print(f"✓ Discovered {len(discovered)} channels via mentions\n")

        except Exception as e:
            print(f"❌ Error: {e}\n")

        return discovered

    async def get_channel_metadata(self, username: str) -> Dict:
        """
        Get detailed channel metadata
        """
        try:
            entity = await self.client.get_entity(username)

            # Get participant count
            participants = 0
            try:
                full = await self.client.get_stats(entity)
                participants = full.followers.count if hasattr(full, 'followers') else 0
            except:
                try:
                    full = await self.client(GetFullChannelRequest(channel=entity))
                    participants = full.full_chat.participants_count
                except:
                    pass

            return {
                'username': username,
                'title': entity.title if hasattr(entity, 'title') else '',
                'description': entity.about if hasattr(entity, 'about') else '',
                'subscribers': participants,
                'verified': entity.verified if hasattr(entity, 'verified') else False,
                'restricted': entity.restricted if hasattr(entity, 'restricted') else False,
                'scam': entity.scam if hasattr(entity, 'scam') else False,
                'created': entity.date.isoformat() if hasattr(entity, 'date') else None
            }

        except Exception as e:
            return {
                'username': username,
                'error': str(e)
            }

    async def run_discovery(self, keywords: List[str] = None):
        """
        Run full discovery pipeline
        """
        print("=" * 70)
        print("TELEGRAM CHANNEL EXPANSION ENGINE")
        print("=" * 70)
        print(f"\n🌱 Seed channels: {', '.join(self.seed_channels)}")
        print(f"🎯 Target: Discover related channels\n")

        await self.initialize()

        all_discovered = set()

        # Method 1: Forward chain analysis
        print("\n" + "=" * 70)
        print("METHOD 1: FORWARD CHAIN ANALYSIS")
        print("=" * 70 + "\n")

        for seed in self.seed_channels:
            forwards = await self.discover_by_forwards(seed, limit=200)
            all_discovered.update(forwards)

        # Method 2: Channel mentions
        print("\n" + "=" * 70)
        print("METHOD 2: CHANNEL MENTION EXTRACTION")
        print("=" * 70 + "\n")

        for seed in self.seed_channels:
            mentions = await self.discover_by_mentions(seed, limit=300)
            all_discovered.update(mentions)

        # Method 3: Keyword search
        if keywords:
            print("\n" + "=" * 70)
            print("METHOD 3: KEYWORD-BASED SEARCH")
            print("=" * 70 + "\n")

            search_results = await self.discover_by_search(keywords, limit_per_keyword=20)
            all_discovered.update(search_results)

        # Remove seed channels from discovered
        all_discovered = all_discovered - set(self.seed_channels)

        # Get metadata for all discovered channels
        print("\n" + "=" * 70)
        print("ENRICHING CHANNEL METADATA")
        print("=" * 70 + "\n")

        for channel in all_discovered:
            print(f"📊 Getting metadata for @{channel}...")
            metadata = await self.get_channel_metadata(channel)
            self.discovered[channel] = metadata
            await asyncio.sleep(1)  # Rate limiting

        # Save results
        report = {
            'generated_at': datetime.now().isoformat(),
            'seed_channels': self.seed_channels,
            'discovery_methods': ['forwards', 'mentions', 'keyword_search'] if keywords else ['forwards', 'mentions'],
            'total_discovered': len(self.discovered),
            'channels': self.discovered
        }

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print("DISCOVERY COMPLETE")
        print("=" * 70)
        print(f"\n✅ Discovered {len(self.discovered)} new channels")
        print(f"💾 Saved to: {self.output_file}\n")

        # Print top discoveries
        print("🎯 TOP DISCOVERIES:\n")
        sorted_channels = sorted(
            self.discovered.items(),
            key=lambda x: x[1].get('subscribers', 0),
            reverse=True
        )

        for i, (username, data) in enumerate(sorted_channels[:15], 1):
            subs = data.get('subscribers', 0)
            title = data.get('title', 'N/A')
            verified = "✅" if data.get('verified') else ""
            scam = "⚠️ SCAM" if data.get('scam') else ""

            print(f"{i:2}. @{username:<20} {verified} {scam}")
            print(f"    {title}")
            print(f"    👥 {subs:,} subscribers\n")

        await self.client.disconnect()


async def main():
    """Main entry point"""

    # Seed channels (known threats)
    seeds = [
        'rybar',
        'intelslava',
        'FVDNL',
        'Cafe_Weltschmerz'
    ]

    # Keywords to search for
    keywords = [
        'drone Nederland',
        'FPV Nederland',
        'UAV Belgium',
        'GRU',
        'Schiphol drone',
        'Eindhoven incident',
        'militaire drone',
        'FVD Rusland',
        'Oekraïne Nederland'
    ]

    expander = TelegramChannelExpander(
        seed_channels=seeds,
        output_file='discovered_channels_20251119.json'
    )

    await expander.run_discovery(keywords=keywords)


if __name__ == '__main__':
    asyncio.run(main())
