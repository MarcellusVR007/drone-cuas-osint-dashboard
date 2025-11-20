#!/usr/bin/env python3
"""
Tier 1+2 Europa-Focused Telegram Scraper
Scrapes discovered channels with operator identification focus
"""

import os
import json
import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'osint_session'

# From PIJLER_1_RAPPORT
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

# Europa-focused keywords
EUROPA_KEYWORDS = [
    # Locations
    'belgium', 'belgië', 'belgique', 'бельгия',
    'netherlands', 'nederland', 'нидерланды',
    'germany', 'deutschland', 'германия',
    'france', 'frankrijk', 'франция',
    'raf', 'nato', 'нато',
    'airport', 'luchthaven', 'аэропорт',
    'terneuzen', 'schiphol', 'amsterdam', 'rotterdam',
    'brussels', 'bruxelles', 'брюссель',

    # Infrastructure
    'chemical plant', 'port', 'haven', 'nuclear', 'ядерн',
    'military base', 'militaire basis', 'военная база',

    # Incidents
    'drone', 'drones', 'дрон', 'бпла', 'uav', 'fpv',
    'swarm', 'рой',
    'sighting', 'gezien', 'наблюдение',
    'breach', 'hack', 'leak', 'взлом', 'утечка',

    # Operators
    'recruit', 'recruitment', 'набор', 'volunteer',
    'operator', 'pilot', 'оператор',
    'contact', 'контакт',
]

# Operator identification patterns
OPERATOR_PATTERNS = {
    'crypto_wallets': [
        r'0x[a-fA-F0-9]{40}',  # Ethereum
        r'bc1[a-zA-HJ-NP-Z0-9]{39,87}',  # Bitcoin Bech32
        r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Bitcoin Legacy
        r'T[a-zA-Z0-9]{33}',  # TRON
    ],
    'telegram_handles': [
        r'@[a-zA-Z0-9_]{5,32}',  # @username
        r't\.me/[a-zA-Z0-9_]{5,32}',  # t.me links
    ],
    'email_patterns': [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ],
    'recruitment_phrases': [
        r'join us',
        r'contact.*telegram',
        r'volunteers needed',
        r'ищем',  # searching for
        r'требуются',  # required
        r'набор',  # recruitment
    ]
}


class Tier12EuropaScraper:
    def __init__(self, db_path: str = 'data/drone_cuas_staging.db'):
        self.db_path = db_path
        self.client = None
        self.results = {
            'tier1': [],
            'tier2': [],
            'operator_intel': [],
            'high_value_messages': []
        }

    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            raise Exception("Not authorized. Run authorization script first.")

        me = await self.client.get_me()
        print(f"✓ Authenticated as: {me.first_name} (@{me.username})")

    def is_europa_relevant(self, text: str) -> bool:
        """Check if message is Europa-relevant"""
        if not text:
            return False

        text_lower = text.lower()
        return any(kw in text_lower for kw in EUROPA_KEYWORDS)

    def extract_operators(self, text: str, channel: str, msg_id: int) -> Optional[Dict]:
        """Extract operator identifiers from text"""
        if not text:
            return None

        operator_data = {
            'channel': channel,
            'message_id': msg_id,
            'wallets': [],
            'handles': [],
            'emails': [],
            'recruitment_indicators': []
        }

        # Extract crypto wallets
        for pattern in OPERATOR_PATTERNS['crypto_wallets']:
            wallets = re.findall(pattern, text)
            operator_data['wallets'].extend(wallets)

        # Extract Telegram handles
        for pattern in OPERATOR_PATTERNS['telegram_handles']:
            handles = re.findall(pattern, text, re.IGNORECASE)
            operator_data['handles'].extend(handles)

        # Extract emails
        for pattern in OPERATOR_PATTERNS['email_patterns']:
            emails = re.findall(pattern, text)
            operator_data['emails'].extend(emails)

        # Check recruitment language
        for pattern in OPERATOR_PATTERNS['recruitment_phrases']:
            if re.search(pattern, text, re.IGNORECASE):
                operator_data['recruitment_indicators'].append(pattern)

        # Return only if we found something
        if any([operator_data['wallets'], operator_data['handles'],
                operator_data['emails'], operator_data['recruitment_indicators']]):
            return operator_data

        return None

    def calculate_relevance_score(self, text: str) -> int:
        """Calculate Europa relevance score"""
        if not text:
            return 0

        score = 0
        text_lower = text.lower()

        # High value keywords
        high_value = [
            'raf lakenheath', 'terneuzen', 'dow chemical',
            'north sea port', 'дроны над европ', 'drones over europe',
            'military base', 'chemical plant', 'airport closed'
        ]
        for kw in high_value:
            if kw in text_lower:
                score += 5

        # Medium value keywords
        medium_value = ['drone', 'дрон', 'nato', 'нато', 'belgium', 'netherlands']
        for kw in medium_value:
            if kw in text_lower:
                score += 2

        # Operator indicators = high value
        if re.search(r'0x[a-fA-F0-9]{40}', text):  # Crypto wallet
            score += 10
        if re.search(r'@[a-zA-Z0-9_]{5,}', text):  # Telegram handle
            score += 3

        return score

    async def scrape_channel(self, channel_username: str, tier: str, limit: int = 200):
        """Scrape a single channel"""
        print(f"\n{'='*70}")
        print(f"📡 {channel_username} (Tier {tier})")
        print('='*70)

        try:
            entity = await self.client.get_entity(channel_username)
            print(f"📋 {entity.title}")

            # Get messages
            messages = await self.client.get_messages(entity, limit=limit)
            print(f"📥 Retrieved {len(messages)} messages")

            europa_count = 0
            operator_count = 0

            for msg in messages:
                if not msg.message:
                    continue

                # Check Europa relevance
                if self.is_europa_relevant(msg.message):
                    europa_count += 1

                    relevance_score = self.calculate_relevance_score(msg.message)

                    msg_data = {
                        'channel': channel_username,
                        'channel_title': entity.title,
                        'tier': tier,
                        'message_id': msg.id,
                        'date': msg.date.isoformat(),
                        'text': msg.message,
                        'views': msg.views,
                        'forwards': msg.forwards,
                        'relevance_score': relevance_score,
                        'url': f'https://t.me/{channel_username}/{msg.id}'
                    }

                    # Store in appropriate tier
                    if tier == '1':
                        self.results['tier1'].append(msg_data)
                    else:
                        self.results['tier2'].append(msg_data)

                    # High value messages (score >= 10)
                    if relevance_score >= 10:
                        self.results['high_value_messages'].append(msg_data)

                    # Check for operator intel
                    operator_data = self.extract_operators(msg.message, channel_username, msg.id)
                    if operator_data:
                        operator_count += 1
                        operator_data['message_text'] = msg.message[:500]
                        operator_data['date'] = msg.date.isoformat()
                        operator_data['url'] = msg_data['url']
                        self.results['operator_intel'].append(operator_data)

                    # Save to database
                    self.save_to_database(msg_data, operator_data)

            print(f"✅ Europa-relevant: {europa_count}/{len(messages)}")
            print(f"🎯 Operator intel: {operator_count}")

        except Exception as e:
            print(f"❌ Error: {e}")

        await asyncio.sleep(3)  # Rate limiting

    def save_to_database(self, msg_data: Dict, operator_data: Optional[Dict] = None):
        """Save message and operator data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Save social media post
        cursor.execute("""
            INSERT OR IGNORE INTO social_media_posts (
                platform, channel_name, post_id, post_url, post_date,
                content, credibility_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'telegram',
            msg_data['channel'],
            str(msg_data['message_id']),
            msg_data['url'],
            msg_data['date'],
            msg_data['text'],
            msg_data['relevance_score'] / 20.0  # Normalize to 0-1
        ))

        # If operator data, save to actors table
        if operator_data:
            for wallet in operator_data.get('wallets', []):
                cursor.execute("""
                    INSERT OR IGNORE INTO actors (
                        name, actor_type, notes, telegram_handle
                    ) VALUES (?, ?, ?, ?)
                """, (
                    f'Operator_{wallet[:8]}',
                    'suspected_handler',
                    f'Crypto wallet found in {msg_data["channel"]}',
                    msg_data['channel']
                ))

            for handle in operator_data.get('handles', []):
                cursor.execute("""
                    INSERT OR IGNORE INTO actors (
                        name, actor_type, telegram_handle
                    ) VALUES (?, ?, ?)
                """, (
                    handle,
                    'suspected_operator',
                    handle
                ))

        conn.commit()
        conn.close()

    async def scrape_all(self):
        """Scrape all Tier 1 and Tier 2 channels"""
        print("="*80)
        print("TIER 1+2 EUROPA-FOCUSED TELEGRAM SCRAPER")
        print("="*80)
        print(f"\n🎯 Target: Europa drone incidents + operator identification")
        print(f"📺 Channels: {len(TIER1_CHANNELS)} Tier 1 + {len(TIER2_CHANNELS)} Tier 2")

        await self.connect()

        # Tier 1 - 200 messages each
        print(f"\n{'='*80}")
        print("TIER 1 CHANNELS (Critical - 200 msgs)")
        print('='*80)
        for channel in TIER1_CHANNELS:
            await self.scrape_channel(channel, '1', limit=200)

        # Tier 2 - 100 messages each
        print(f"\n{'='*80}")
        print("TIER 2 CHANNELS (High Priority - 100 msgs)")
        print('='*80)
        for channel in TIER2_CHANNELS:
            await self.scrape_channel(channel, '2', limit=100)

        await self.client.disconnect()

        # Save results
        self.save_results()
        self.print_summary()

    def save_results(self):
        """Save results to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tier12_europa_scrape_{timestamp}.json'

        output = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'tier1_channels': len(TIER1_CHANNELS),
                'tier2_channels': len(TIER2_CHANNELS),
                'total_channels': len(TIER1_CHANNELS) + len(TIER2_CHANNELS)
            },
            'stats': {
                'tier1_messages': len(self.results['tier1']),
                'tier2_messages': len(self.results['tier2']),
                'high_value_messages': len(self.results['high_value_messages']),
                'operator_intel_found': len(self.results['operator_intel'])
            },
            'results': self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved: {filename}")
        return filename

    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*80)
        print("SCRAPING COMPLETE")
        print("="*80)

        print(f"\n📊 MESSAGES COLLECTED:")
        print(f"   Tier 1 (critical): {len(self.results['tier1'])}")
        print(f"   Tier 2 (high priority): {len(self.results['tier2'])}")
        print(f"   High-value (score ≥10): {len(self.results['high_value_messages'])}")

        print(f"\n🎯 OPERATOR INTELLIGENCE:")
        print(f"   Messages with operator intel: {len(self.results['operator_intel'])}")

        # Count unique identifiers
        wallets = []
        handles = []
        for op in self.results['operator_intel']:
            wallets.extend(op.get('wallets', []))
            handles.extend(op.get('handles', []))

        print(f"   Unique crypto wallets: {len(set(wallets))}")
        print(f"   Unique Telegram handles: {len(set(handles))}")

        # Top high-value messages
        if self.results['high_value_messages']:
            print(f"\n⭐ TOP 5 HIGH-VALUE MESSAGES:")
            sorted_msgs = sorted(
                self.results['high_value_messages'],
                key=lambda x: x['relevance_score'],
                reverse=True
            )[:5]

            for i, msg in enumerate(sorted_msgs, 1):
                print(f"\n{i}. Score: {msg['relevance_score']} | {msg['channel']}")
                print(f"   {msg['text'][:150]}...")
                print(f"   🔗 {msg['url']}")


async def main():
    scraper = Tier12EuropaScraper()
    await scraper.scrape_all()


if __name__ == '__main__':
    asyncio.run(main())
