#!/usr/bin/env python3
"""
Telegram Forward Tracking Scraper
Tracks message forwards to build social graph and detect coordination

Features:
- Forward chain analysis (trace messages back to origin)
- Coordinated forwarding detection (same message → multiple channels quickly)
- Social graph construction (channel influence mapping)
- Private channel leak detection
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
import json
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import (
    TelegramChannel, TelegramMessage, MessageForward,
    PrivateChannelLeak, TelegramParticipant, ChannelParticipation
)
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

try:
    from telethon import TelegramClient
    from telethon.tl.types import MessageService, MessageFwdHeader, Channel, User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("⚠️  Telethon not installed. Install with: pip install telethon")


class TelegramForwardTracker:
    """Tracks message forwards across Telegram channels"""

    def __init__(self, db: Session = None, api_id: str = None, api_hash: str = None):
        self.db = db or SessionLocal()
        self.api_id = api_id or os.getenv("TELEGRAM_API_ID")
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")

        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is required. Install with: pip install telethon")

        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

        self.client = None

    async def initialize_client(self, session_file: str = "osint_session"):
        """Initialize Telegram client"""
        self.client = TelegramClient(session_file, self.api_id, self.api_hash)
        await self.client.start()
        print("✓ Telegram client initialized")

    async def scrape_channel_with_forwards(self, channel_username: str, limit: int = 100) -> Dict:
        """
        Scrape channel and track all forward information

        Args:
            channel_username: Channel username (without @)
            limit: Maximum messages to fetch

        Returns:
            Dictionary with scrape results
        """
        print(f"\n🔍 Scraping: @{channel_username}")

        # Get or create channel in database
        channel_entity = await self.client.get_entity(channel_username)
        db_channel = self._get_or_create_channel(channel_entity)

        messages_processed = 0
        forwards_detected = 0
        private_leaks_detected = 0

        async for message in self.client.iter_messages(channel_username, limit=limit):
            # Skip service messages
            if isinstance(message, MessageService):
                continue

            # Save message
            db_message = self._save_message(message, db_channel.id)
            messages_processed += 1

            # Check if this is a forwarded message
            if message.fwd_from:
                forward_info = await self._process_forward(message, db_message, db_channel)

                if forward_info:
                    forwards_detected += 1

                    # Check for private channel leak
                    if forward_info.get("is_private_leak"):
                        private_leaks_detected += 1

            # Progress indicator
            if messages_processed % 10 == 0:
                print(f"  Processed {messages_processed} messages...", end='\r')

        print(f"\n  ✓ Processed {messages_processed} messages")
        print(f"  ⤵️  Detected {forwards_detected} forwards")
        if private_leaks_detected > 0:
            print(f"  🔓 Detected {private_leaks_detected} private channel leaks")

        return {
            "channel": channel_username,
            "messages_processed": messages_processed,
            "forwards_detected": forwards_detected,
            "private_leaks": private_leaks_detected
        }

    def _get_or_create_channel(self, channel_entity) -> TelegramChannel:
        """Get or create channel in database"""
        if hasattr(channel_entity, 'username'):
            username = channel_entity.username
        else:
            username = str(channel_entity.id)

        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.channel_id == str(channel_entity.id)
        ).first()

        if not channel:
            channel = TelegramChannel(
                channel_id=str(channel_entity.id),
                username=username,
                title=getattr(channel_entity, 'title', ''),
                description=getattr(channel_entity, 'about', ''),
                member_count=getattr(channel_entity, 'participants_count', 0),
                first_discovered=datetime.now(),
                channel_type='public' if hasattr(channel_entity, 'username') and channel_entity.username else 'private',
                language_primary='unknown'
            )
            self.db.add(channel)
            self.db.commit()
            self.db.refresh(channel)

        return channel

    def _save_message(self, message, channel_db_id: int) -> TelegramMessage:
        """Save message to database"""
        # Check if message already exists
        existing = self.db.query(TelegramMessage).filter(
            and_(
                TelegramMessage.message_id == str(message.id),
                TelegramMessage.channel_id == channel_db_id
            )
        ).first()

        if existing:
            return existing

        # Create new message
        db_message = TelegramMessage(
            message_id=str(message.id),
            channel_id=channel_db_id,
            timestamp=message.date,
            text_content=message.message if hasattr(message, 'message') else None,
            media_type=message.media.__class__.__name__ if message.media else None,
            views=message.views if hasattr(message, 'views') else 0,
            engagement_score=float(message.views or 0)
        )

        # Handle forwards
        if message.fwd_from:
            if hasattr(message.fwd_from, 'from_id'):
                if hasattr(message.fwd_from.from_id, 'channel_id'):
                    db_message.forward_from_channel_id = message.fwd_from.from_id.channel_id
                if hasattr(message.fwd_from, 'channel_post'):
                    db_message.forward_from_message_id = str(message.fwd_from.channel_post)

        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)

        return db_message

    async def _process_forward(self, message, db_message: TelegramMessage, destination_channel: TelegramChannel) -> Optional[Dict]:
        """Process a forwarded message and track the forward relationship"""
        fwd = message.fwd_from

        # Try to extract source channel info
        source_channel_id = None
        source_message_id = None
        is_private_leak = False

        if hasattr(fwd, 'from_id'):
            if hasattr(fwd.from_id, 'channel_id'):
                source_channel_id = fwd.from_id.channel_id
            elif hasattr(fwd.from_id, 'user_id'):
                # Forward from user (might be from private channel)
                is_private_leak = True

        if hasattr(fwd, 'channel_post'):
            source_message_id = fwd.channel_post

        # If we have source channel ID, get or create it
        source_db_channel = None
        if source_channel_id:
            try:
                # Try to get source channel info
                source_entity = await self.client.get_entity(source_channel_id)
                source_db_channel = self._get_or_create_channel(source_entity)
            except Exception as e:
                # Can't access source channel (private?)
                is_private_leak = True
                print(f"    ⚠️  Can't access source channel {source_channel_id}: {e}")

        # If this is a private channel leak, record it
        if is_private_leak:
            self._record_private_leak(
                private_channel_id=str(source_channel_id) if source_channel_id else "unknown",
                public_channel_id=destination_channel.id,
                leak_timestamp=message.date
            )

        # If we have both source and destination, record the forward
        if source_db_channel and source_message_id:
            # Find source message in database
            source_db_message = self.db.query(TelegramMessage).filter(
                and_(
                    TelegramMessage.message_id == str(source_message_id),
                    TelegramMessage.channel_id == source_db_channel.id
                )
            ).first()

            if source_db_message:
                # Calculate forward velocity (time between original and forward)
                time_delta = message.date - source_db_message.timestamp
                forward_velocity_seconds = int(time_delta.total_seconds())

                # Check if this forward already exists
                existing_forward = self.db.query(MessageForward).filter(
                    and_(
                        MessageForward.source_message_id == source_db_message.id,
                        MessageForward.destination_message_id == db_message.id
                    )
                ).first()

                if not existing_forward:
                    forward_record = MessageForward(
                        source_channel_id=source_db_channel.id,
                        source_message_id=source_db_message.id,
                        destination_channel_id=destination_channel.id,
                        destination_message_id=db_message.id,
                        forward_timestamp=message.date,
                        forward_velocity_seconds=forward_velocity_seconds
                    )
                    self.db.add(forward_record)
                    self.db.commit()

                    return {
                        "source_channel": source_db_channel.username,
                        "destination_channel": destination_channel.username,
                        "forward_velocity_seconds": forward_velocity_seconds,
                        "is_private_leak": is_private_leak
                    }

        return None

    def _record_private_leak(self, private_channel_id: str, public_channel_id: int, leak_timestamp: datetime):
        """Record a private channel leak"""
        existing = self.db.query(PrivateChannelLeak).filter(
            and_(
                PrivateChannelLeak.private_channel_id == private_channel_id,
                PrivateChannelLeak.public_channel_id == public_channel_id
            )
        ).first()

        if existing:
            # Update frequency
            existing.leak_frequency += 1
            existing.last_leak_timestamp = leak_timestamp
        else:
            # Create new leak record
            leak = PrivateChannelLeak(
                private_channel_id=private_channel_id,
                private_channel_name="Unknown (private)",
                public_channel_id=public_channel_id,
                first_leak_timestamp=leak_timestamp,
                leak_frequency=1,
                last_leak_timestamp=leak_timestamp
            )
            self.db.add(leak)

        self.db.commit()

    def detect_coordinated_forwarding(self, time_window_minutes: int = 30, min_channels: int = 5) -> List[Dict]:
        """
        Detect coordinated forwarding (same message forwarded to N+ channels quickly)

        Args:
            time_window_minutes: Time window for coordination detection
            min_channels: Minimum number of channels to flag as coordinated

        Returns:
            List of coordinated forwarding events
        """
        print(f"\n🔍 Detecting coordinated forwarding (≥{min_channels} channels in {time_window_minutes}min)...")

        # Group forwards by source message
        forwards = self.db.query(MessageForward).order_by(MessageForward.forward_timestamp).all()

        source_message_forwards = defaultdict(list)
        for forward in forwards:
            source_message_forwards[forward.source_message_id].append(forward)

        coordinated_events = []

        for source_msg_id, forward_list in source_message_forwards.items():
            if len(forward_list) < min_channels:
                continue

            # Sort by timestamp
            forward_list.sort(key=lambda f: f.forward_timestamp)

            # Check if all forwards happened within time window
            first_forward = forward_list[0].forward_timestamp
            last_forward = forward_list[-1].forward_timestamp
            time_diff = (last_forward - first_forward).total_seconds() / 60

            if time_diff <= time_window_minutes:
                # Get source message
                source_msg = self.db.query(TelegramMessage).get(source_msg_id)
                if not source_msg:
                    continue

                # Get all destination channels
                dest_channels = []
                for fwd in forward_list:
                    channel = self.db.query(TelegramChannel).get(fwd.destination_channel_id)
                    if channel:
                        dest_channels.append(channel.username or channel.channel_id)

                event = {
                    "source_message_id": source_msg_id,
                    "source_channel_id": source_msg.channel_id,
                    "destination_count": len(forward_list),
                    "destination_channels": dest_channels,
                    "time_window_minutes": time_diff,
                    "first_forward": first_forward.isoformat(),
                    "last_forward": last_forward.isoformat(),
                    "message_preview": source_msg.text_content[:100] if source_msg.text_content else ""
                }

                coordinated_events.append(event)
                print(f"  ⚡ Coordinated forward: {len(forward_list)} channels in {time_diff:.1f} min")

        return coordinated_events

    def build_influence_map(self) -> Dict:
        """
        Build channel influence map based on forward relationships

        Returns:
            Dictionary with influence metrics per channel
        """
        print("\n📊 Building channel influence map...")

        channels = self.db.query(TelegramChannel).all()
        influence_map = {}

        for channel in channels:
            # Count outgoing forwards (how many channels forward this channel's content)
            outgoing_forwards = self.db.query(MessageForward).filter(
                MessageForward.source_channel_id == channel.id
            ).count()

            # Count unique destination channels
            unique_destinations = self.db.query(func.count(func.distinct(MessageForward.destination_channel_id))).filter(
                MessageForward.source_channel_id == channel.id
            ).scalar()

            # Count incoming forwards (how much content this channel forwards)
            incoming_forwards = self.db.query(MessageForward).filter(
                MessageForward.destination_channel_id == channel.id
            ).count()

            # Calculate influence score (simple: outgoing forwards * unique destinations)
            influence_score = outgoing_forwards * (unique_destinations or 1)

            influence_map[channel.username or channel.channel_id] = {
                "channel_id": channel.id,
                "outgoing_forwards": outgoing_forwards,
                "unique_destinations": unique_destinations,
                "incoming_forwards": incoming_forwards,
                "influence_score": influence_score,
                "member_count": channel.member_count or 0
            }

        # Sort by influence score
        sorted_channels = sorted(influence_map.items(), key=lambda x: x[1]["influence_score"], reverse=True)

        print(f"\n📈 Top 10 Influential Channels:")
        for i, (channel_name, metrics) in enumerate(sorted_channels[:10], 1):
            print(f"  {i}. {channel_name}")
            print(f"     Influence Score: {metrics['influence_score']}")
            print(f"     Outgoing: {metrics['outgoing_forwards']}, Destinations: {metrics['unique_destinations']}")

        return dict(sorted_channels)

    async def close(self):
        """Close connections"""
        if self.client:
            await self.client.disconnect()
        if self.db:
            self.db.close()


async def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Forward Tracker")
    parser.add_argument("--channels", nargs="+", help="Channel usernames to scrape (without @)")
    parser.add_argument("--limit", type=int, default=100, help="Messages per channel")
    parser.add_argument("--detect-coordination", action="store_true", help="Detect coordinated forwarding")
    parser.add_argument("--influence-map", action="store_true", help="Build influence map")
    parser.add_argument("--time-window", type=int, default=30, help="Coordination time window (minutes)")
    parser.add_argument("--min-channels", type=int, default=5, help="Min channels for coordination detection")

    args = parser.parse_args()

    tracker = TelegramForwardTracker()

    if args.channels:
        await tracker.initialize_client()

        for channel in args.channels:
            try:
                result = await tracker.scrape_channel_with_forwards(channel, limit=args.limit)
                print(f"\n✓ Completed: {result}")
            except Exception as e:
                print(f"\n❌ Error scraping {channel}: {e}")

    if args.detect_coordination:
        coordinated = tracker.detect_coordinated_forwarding(
            time_window_minutes=args.time_window,
            min_channels=args.min_channels
        )
        print(f"\n🎯 Found {len(coordinated)} coordinated forwarding events")

        # Save to JSON
        output_file = f"coordinated_forwards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(coordinated, f, indent=2, default=str)
        print(f"💾 Saved to: {output_file}")

    if args.influence_map:
        influence = tracker.build_influence_map()

        # Save to JSON
        output_file = f"influence_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(influence, f, indent=2)
        print(f"\n💾 Influence map saved to: {output_file}")

    await tracker.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
