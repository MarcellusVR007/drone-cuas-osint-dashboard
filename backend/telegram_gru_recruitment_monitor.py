"""
Telegram GRU Recruitment Monitor
Based on DOCUMENTED GRU TTP's from AIVD reports and intelligence agencies

DOCUMENTED CASES:
- Latvia 2024: Man recruited via Telegram for Molotov attack
- Netherlands 2025: Two 17-year-olds recruited via Telegram to spy on Europol
- GRU Unit 29155 "Defend The Motherland" Telegram bot (Melodiya Intelligence Center)
- FSB recruiting migrants via Telegram for sabotage

TTP PROFILE:
1. Telegram is PRIMARY recruitment platform
2. Target "street agents" - untrained, refugees, students, petty criminals
3. Small tasks → escalation (photos → maps → sabotage)
4. Cryptocurrency payment
5. "Patriotic" framing ("help defend against NATO")
"""

import os
from telethon import TelegramClient, events
from telethon.tl.types import Channel, User
import sqlite3
from datetime import datetime
import re
from typing import List, Dict

class TelegramGRUMonitor:
    """
    Monitor Telegram for GRU-style recruitment activity

    Based on documented GRU TTP's:
    - "Defend The Motherland" style recruitment bots
    - Small task offers (photos, maps, SIM cards)
    - Cryptocurrency payment mentions
    - Anti-NATO / pro-Russia messaging
    - Targeting refugees, students, young people
    """

    def __init__(self, db_path='data/drone_cuas.db'):
        self.db_path = db_path

        # Telegram API credentials (get from https://my.telegram.org)
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')

        self.setup_instructions = """
╔═══════════════════════════════════════════════════════════════╗
║         TELEGRAM API SETUP INSTRUCTIONS                       ║
╚═══════════════════════════════════════════════════════════════╝

To monitor Telegram, you need API credentials:

1. Go to: https://my.telegram.org
2. Login with your phone number
3. Click "API development tools"
4. Create new application:
   - App title: "GRU Recruitment Monitor"
   - Short name: "gru_monitor"
   - Platform: Desktop
   - Description: "OSINT monitoring for security research"

5. You'll receive:
   - api_id: [number]
   - api_hash: [string]

6. Set environment variables:
   export TELEGRAM_API_ID="your_api_id"
   export TELEGRAM_API_HASH="your_api_hash"
   export TELEGRAM_PHONE="+31612345678"  # Your phone number

7. Run this script - it will send SMS verification code

IMPORTANT: This uses YOUR personal Telegram account to monitor channels.
Only join PUBLIC channels (legal OSINT). Do NOT infiltrate private groups
without legal authorization.
"""

        # Dutch/English recruitment keywords (from documented cases)
        self.recruitment_indicators = {
            # Direct recruitment language
            'recruitment_direct': [
                r'looking for people',
                r'zoeken mensen',
                r'need someone',
                r'hulp nodig',
                r'verdien geld',
                r'earn money',
                r'bijverdienen',
            ],

            # Task descriptions (from documented cases)
            'intelligence_tasks': [
                r'foto.*maken',  # take photos
                r'take.*photo',
                r'documenteren',  # document
                r'informatie.*verzamelen',  # collect information
                r'kaarten.*kopen',  # buy maps
                r'SIM.*card',
                r'observe.*base',
                r'monitor.*movement',
            ],

            # Payment indicators
            'payment_crypto': [
                r'bitcoin',
                r'crypto',
                r'BTC',
                r'XMR',
                r'monero',
                r'betaling.*anoniem',  # anonymous payment
                r'anonymous.*payment',
            ],

            # Anti-NATO / patriotic framing (GRU style)
            'ideological_framing': [
                r'stop.*NATO',
                r'tegen.*NAVO',
                r'verdedig.*vaderland',  # defend motherland
                r'defend.*motherland',
                r'help.*Rusland',
                r'help.*Russia',
                r'waarheid.*tonen',  # show truth
                r'expose.*NATO',
            ],

            # Geographic targeting (near incidents)
            'location_targeting': [
                r'(Schiphol|Eindhoven|Rotterdam|Volkel|Gilze-Rijen)',
                r'(vliegveld|airport|airbase)',
                r'(haven|port|harbor)',
                r'(militaire.*basis|military.*base)',
            ],

            # Bot/channel names (GRU patterns)
            'suspicious_names': [
                r'defend.*NL',
                r'defend.*netherlands',
                r'truth.*seeker',
                r'patriot.*NL',
                r'stop.*NAVO',
                r'against.*NATO',
            ],
        }

    def check_credentials(self) -> bool:
        """Check if Telegram API credentials available"""
        if not all([self.api_id, self.api_hash, self.phone]):
            print(self.setup_instructions)
            return False
        return True

    def setup_database(self):
        """Create telegram_messages table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                channel_id INTEGER,
                channel_username TEXT,
                channel_title TEXT,
                sender_id INTEGER,
                sender_username TEXT,
                message_date TIMESTAMP,
                message_text TEXT,
                recruitment_score INTEGER DEFAULT 0,
                matched_categories TEXT,
                is_bot BOOLEAN DEFAULT 0,
                has_crypto_mention BOOLEAN DEFAULT 0,
                has_location_mention BOOLEAN DEFAULT 0,
                flagged_critical BOOLEAN DEFAULT 0,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Telegram messages table ready")

    def score_message(self, text: str, channel_name: str = '') -> tuple:
        """
        Score message for GRU recruitment likelihood

        Returns: (score, matched_categories)
        """
        if not text:
            return 0, {}

        text_lower = text.lower()
        combined_text = f"{channel_name} {text}".lower()

        score = 0
        matches = {}

        for category, patterns in self.recruitment_indicators.items():
            category_matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    category_matches += 1

            if category_matches > 0:
                matches[category] = category_matches

                # Weighted scoring (based on importance)
                weights = {
                    'recruitment_direct': 30,  # CRITICAL
                    'intelligence_tasks': 25,  # CRITICAL
                    'payment_crypto': 20,      # HIGH
                    'ideological_framing': 15, # MEDIUM
                    'location_targeting': 20,  # HIGH
                    'suspicious_names': 10,    # LOW (channel name)
                }

                score += weights.get(category, 10) * min(category_matches, 3) / 3

        return int(score), matches

    async def monitor_channel(self, channel_username: str, limit: int = 100):
        """
        Monitor single Telegram channel for recruitment activity

        Args:
            channel_username: Username without @ (e.g., 'WaarheidsMedia_NL')
            limit: Number of recent messages to fetch
        """
        if not self.check_credentials():
            return []

        client = TelegramClient('gru_monitor_session', self.api_id, self.api_hash)
        await client.start(phone=self.phone)

        print(f"📡 Monitoring @{channel_username}...")

        messages_data = []

        try:
            entity = await client.get_entity(channel_username)

            async for message in client.iter_messages(entity, limit=limit):
                if not message.text:
                    continue

                # Score message
                score, matches = self.score_message(
                    message.text,
                    channel_username
                )

                # Extract metadata
                sender_id = message.sender_id if message.sender_id else None
                sender_username = None
                is_bot = False

                if message.sender:
                    if hasattr(message.sender, 'username'):
                        sender_username = message.sender.username
                    if hasattr(message.sender, 'bot'):
                        is_bot = message.sender.bot

                message_data = {
                    'message_id': message.id,
                    'channel_id': entity.id,
                    'channel_username': channel_username,
                    'channel_title': entity.title if hasattr(entity, 'title') else channel_username,
                    'sender_id': sender_id,
                    'sender_username': sender_username,
                    'message_date': message.date.isoformat() if message.date else None,
                    'message_text': message.text,
                    'recruitment_score': score,
                    'matched_categories': str(matches),
                    'is_bot': is_bot,
                    'has_crypto_mention': 'payment_crypto' in matches,
                    'has_location_mention': 'location_targeting' in matches,
                    'flagged_critical': score >= 50,
                }

                messages_data.append(message_data)

                # Print high-score messages immediately
                if score >= 30:
                    print(f"   🚨 HIGH SCORE ({score}): {message.text[:80]}...")

        except Exception as e:
            print(f"   ❌ Error monitoring @{channel_username}: {e}")

        finally:
            await client.disconnect()

        print(f"   ✅ Collected {len(messages_data)} messages from @{channel_username}")
        return messages_data

    def save_messages(self, messages: List[Dict]):
        """Save messages to database"""
        if not messages:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for msg in messages:
            cursor.execute("""
                INSERT OR IGNORE INTO telegram_messages
                (message_id, channel_id, channel_username, channel_title,
                 sender_id, sender_username, message_date, message_text,
                 recruitment_score, matched_categories, is_bot,
                 has_crypto_mention, has_location_mention, flagged_critical)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg['message_id'],
                msg['channel_id'],
                msg['channel_username'],
                msg['channel_title'],
                msg['sender_id'],
                msg['sender_username'],
                msg['message_date'],
                msg['message_text'],
                msg['recruitment_score'],
                msg['matched_categories'],
                msg['is_bot'],
                msg['has_crypto_mention'],
                msg['has_location_mention'],
                msg['flagged_critical'],
            ))

        conn.commit()
        conn.close()
        print(f"💾 Saved {len(messages)} messages to database")

    def generate_report(self) -> str:
        """Generate analysis report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Statistics
        cursor.execute("SELECT COUNT(*) FROM telegram_messages")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM telegram_messages WHERE recruitment_score >= 50")
        critical = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM telegram_messages WHERE recruitment_score >= 30")
        high = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM telegram_messages WHERE is_bot = 1")
        bots = cursor.fetchone()[0]

        # Top suspicious messages
        cursor.execute("""
            SELECT channel_username, message_text, recruitment_score, matched_categories
            FROM telegram_messages
            WHERE recruitment_score > 0
            ORDER BY recruitment_score DESC
            LIMIT 10
        """)
        top_messages = cursor.fetchall()

        conn.close()

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         TELEGRAM GRU RECRUITMENT MONITORING REPORT            ║
╚═══════════════════════════════════════════════════════════════╝

📊 STATISTICS:
   Total Messages:       {total}
   🔴 CRITICAL (50+):    {critical}
   🟠 HIGH (30-49):      {high - critical}
   🤖 Bot Messages:      {bots}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TOP 10 SUSPICIOUS MESSAGES:
"""

        for i, (channel, text, score, matches) in enumerate(top_messages, 1):
            report += f"""
{i}. Score: {score}/100 | @{channel}
   Text: {text[:150]}...
   Patterns: {matches}
"""

        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if critical > 0:
            report += f"\n⚠️  {critical} CRITICAL messages found - MANUAL REVIEW REQUIRED\n"

        return report


# Target Dutch Telegram channels (based on GRU TTP research)
DUTCH_CHANNELS_TO_MONITOR = [
    # Pro-Russia / Anti-NATO Dutch channels
    'WaarheidsMedia_NL',      # Truth Media NL (if exists)
    'GeenNATO',               # No NATO (if exists)
    'AlternativeMedia_NL',    # Alternative Media NL

    # Known from other agent's scraping (if public)
    # Add any public Dutch pro-Russia channels discovered

    # NOTE: Only PUBLIC channels! Private groups require legal authorization
]


async def main():
    """Main monitoring function"""
    monitor = TelegramGRUMonitor()

    print("🔍 Telegram GRU Recruitment Monitor")
    print("Based on documented GRU TTP's from AIVD reports\n")

    # Setup database
    monitor.setup_database()

    # Check credentials
    if not monitor.check_credentials():
        print("\n⚠️  Telegram API credentials not configured.")
        print("   Follow instructions above to setup.\n")
        return

    print("✅ Telegram API credentials found!\n")
    print(f"🎯 Monitoring {len(DUTCH_CHANNELS_TO_MONITOR)} channels...\n")

    all_messages = []

    for channel in DUTCH_CHANNELS_TO_MONITOR:
        try:
            messages = await monitor.monitor_channel(channel, limit=100)
            all_messages.extend(messages)
        except Exception as e:
            print(f"   ❌ Error with @{channel}: {e}")

    # Save to database
    if all_messages:
        monitor.save_messages(all_messages)

        # Generate report
        report = monitor.generate_report()
        print(report)

        # Save report to file
        with open('telegram_gru_monitoring_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("📄 Report saved to: telegram_gru_monitoring_report.txt")
    else:
        print("\n⚠️  No messages collected. Check channel usernames or credentials.")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
