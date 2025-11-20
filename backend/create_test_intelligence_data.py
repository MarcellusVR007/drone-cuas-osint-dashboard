#!/usr/bin/env python3
"""
Create Test Intelligence Data
Generates realistic sample data for testing the intelligence collection system
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import (
    TelegramChannel, TelegramMessage, MessageForward,
    PrivateChannelLeak, Incident, IncidentCorrelation
)

def create_test_data():
    """Create comprehensive test data"""
    db = SessionLocal()

    print("=" * 70)
    print("CREATING TEST INTELLIGENCE DATA")
    print("=" * 70)

    # Create test Telegram channels
    print("\n📱 Creating Telegram channels...")

    channels_data = [
        {
            "channel_id": "test_gru_dutch_001",
            "username": "gru_dutch_test",
            "title": "GRU Dutch Operations (Test)",
            "description": "Test channel for GRU recruitment monitoring",
            "member_count": 1247,
            "channel_type": "public",
            "language_primary": "nl",
            "risk_score": 85
        },
        {
            "channel_id": "test_drone_hobbyist_001",
            "username": "drone_fpv_nl_test",
            "title": "FPV Drone Nederland (Test)",
            "description": "Test channel for drone hobbyists",
            "member_count": 543,
            "channel_type": "public",
            "language_primary": "nl",
            "risk_score": 45
        },
        {
            "channel_id": "test_aviation_news_001",
            "username": "aviation_news_nl_test",
            "title": "Aviation News NL (Test)",
            "description": "Test channel for aviation news",
            "member_count": 2341,
            "channel_type": "public",
            "language_primary": "nl",
            "risk_score": 20
        },
        {
            "channel_id": "test_ukraine_war_001",
            "username": "ukraine_updates_test",
            "title": "Ukraine War Updates (Test)",
            "description": "Test channel for war updates",
            "member_count": 5678,
            "channel_type": "public",
            "language_primary": "en",
            "risk_score": 60
        },
        {
            "channel_id": "test_fvd_001",
            "username": "fvd_supporters_test",
            "title": "FVD Supporters (Test)",
            "description": "Test political channel",
            "member_count": 892,
            "channel_type": "public",
            "language_primary": "nl",
            "risk_score": 55
        }
    ]

    channels = []
    for ch_data in channels_data:
        # Check if exists
        existing = db.query(TelegramChannel).filter(
            TelegramChannel.channel_id == ch_data["channel_id"]
        ).first()

        if existing:
            print(f"  ⏭️  Channel already exists: {ch_data['username']}")
            channels.append(existing)
        else:
            channel = TelegramChannel(
                **ch_data,
                first_discovered=datetime.now() - timedelta(days=30),
                last_active=datetime.now()
            )
            db.add(channel)
            db.commit()
            db.refresh(channel)
            channels.append(channel)
            print(f"  ✓ Created channel: {ch_data['username']}")

    # Create test messages with various linguistic patterns
    print("\n💬 Creating test messages...")

    # Get a recent incident to correlate with
    recent_incident = db.query(Incident).order_by(Incident.sighting_date.desc()).first()

    if recent_incident:
        incident_date = datetime.combine(recent_incident.sighting_date, datetime.min.time())
        print(f"  📍 Using incident: {recent_incident.title} ({recent_incident.sighting_date})")
    else:
        incident_date = datetime.now() - timedelta(days=7)
        print(f"  ⚠️  No incidents found, using date: {incident_date}")

    # Messages with suspicious linguistic patterns (Russian→Dutch)
    suspicious_messages = [
        {
            "channel": channels[0],  # GRU channel
            "text": "Drone werd gezien boven vliegveld na 5 minuten. Operatie was succesvol.",
            "timestamp": incident_date - timedelta(hours=12),  # Before incident
            "linguistic_score": 0.75
        },
        {
            "channel": channels[0],
            "text": "We maken foto van militair terrein op het vliegveld. Evenement verliep zonder probleem.",
            "timestamp": incident_date - timedelta(hours=18),
            "linguistic_score": 0.85
        },
        {
            "channel": channels[0],
            "text": "Nieuwe opdracht: reconnaissance van Schiphol. Betaling in Bitcoin na voltooiing.",
            "timestamp": incident_date - timedelta(hours=36),
            "linguistic_score": 0.65
        },
        {
            "channel": channels[4],  # FVD channel
            "text": "Drone incident bij Eindhoven. Overheid vertelt niet hele verhaal over veiligheid.",
            "timestamp": incident_date + timedelta(hours=6),  # After incident
            "linguistic_score": 0.3
        },
        {
            "channel": channels[1],  # Drone hobbyist
            "text": "Heeft iemand gezien wat er gisteren bij het vliegveld gebeurde? Hele gebied was afgezet.",
            "timestamp": incident_date + timedelta(hours=14),
            "linguistic_score": 0.2
        }
    ]

    # Normal messages (activity spike around incident)
    normal_messages = [
        {
            "channel": channels[2],
            "text": "Breaking: onbemande drone gesignaleerd boven Nederlands vliegveld",
            "timestamp": incident_date + timedelta(hours=2)
        },
        {
            "channel": channels[2],
            "text": "UPDATE: Luchtverkeer tijdelijk stilgelegd na drone-incident",
            "timestamp": incident_date + timedelta(hours=3)
        },
        {
            "channel": channels[3],
            "text": "Reports of drone activity near Dutch airbase. Possible Russian intel gathering?",
            "timestamp": incident_date + timedelta(hours=5)
        },
        {
            "channel": channels[1],
            "text": "Weer zo'n incident. Wanneer gaan ze eindelijk drone hunters inzetten?",
            "timestamp": incident_date + timedelta(hours=8)
        },
        {
            "channel": channels[1],
            "text": "Ik denk DJI Matrice 300, heeft iemand beelden?",
            "timestamp": incident_date + timedelta(hours=9)
        }
    ]

    messages = []

    # Add suspicious messages
    for msg_data in suspicious_messages:
        existing = db.query(TelegramMessage).filter(
            TelegramMessage.channel_id == msg_data["channel"].id,
            TelegramMessage.text_content == msg_data["text"]
        ).first()

        if not existing:
            message = TelegramMessage(
                message_id=f"test_msg_{random.randint(10000, 99999)}",
                channel_id=msg_data["channel"].id,
                timestamp=msg_data["timestamp"],
                text_content=msg_data["text"],
                views=random.randint(100, 1000),
                engagement_score=random.uniform(0.1, 0.5),
                linguistic_suspicion_score=msg_data.get("linguistic_score", 0.0)
            )
            db.add(message)
            messages.append(message)
            print(f"  ✓ Suspicious message: {msg_data['text'][:50]}...")

    # Add normal messages
    for msg_data in normal_messages:
        existing = db.query(TelegramMessage).filter(
            TelegramMessage.channel_id == msg_data["channel"].id,
            TelegramMessage.text_content == msg_data["text"]
        ).first()

        if not existing:
            message = TelegramMessage(
                message_id=f"test_msg_{random.randint(10000, 99999)}",
                channel_id=msg_data["channel"].id,
                timestamp=msg_data["timestamp"],
                text_content=msg_data["text"],
                views=random.randint(500, 3000),
                engagement_score=random.uniform(0.3, 0.8)
            )
            db.add(message)
            messages.append(message)
            print(f"  ✓ Normal message: {msg_data['text'][:50]}...")

    db.commit()

    # Create some message forwards (social graph)
    print("\n⤵️  Creating message forwards...")

    if len(messages) >= 3:
        # Forward from GRU channel to FVD channel
        forward1 = MessageForward(
            source_channel_id=channels[0].id,
            source_message_id=messages[0].id,
            destination_channel_id=channels[4].id,
            destination_message_id=messages[3].id,
            forward_timestamp=incident_date + timedelta(hours=4),
            forward_velocity_seconds=int(timedelta(hours=16).total_seconds())
        )
        db.add(forward1)
        print(f"  ✓ Forward: {channels[0].username} → {channels[4].username}")

        # Coordinated forwards (same message to multiple channels quickly)
        forward2 = MessageForward(
            source_channel_id=channels[2].id,
            source_message_id=messages[5].id if len(messages) > 5 else messages[0].id,
            destination_channel_id=channels[1].id,
            destination_message_id=messages[6].id if len(messages) > 6 else messages[1].id,
            forward_timestamp=incident_date + timedelta(hours=2, minutes=15),
            forward_velocity_seconds=900  # 15 minutes
        )
        db.add(forward2)
        print(f"  ✓ Forward: {channels[2].username} → {channels[1].username}")

    db.commit()

    # Create private channel leak
    print("\n🔓 Creating private channel leak...")

    leak = PrivateChannelLeak(
        private_channel_id="private_gru_ops_001",
        private_channel_name="GRU Operations Private",
        public_channel_id=channels[0].id,
        first_leak_timestamp=incident_date - timedelta(days=5),
        leak_frequency=3,
        last_leak_timestamp=incident_date - timedelta(hours=12)
    )

    existing_leak = db.query(PrivateChannelLeak).filter(
        PrivateChannelLeak.private_channel_id == leak.private_channel_id
    ).first()

    if not existing_leak:
        db.add(leak)
        db.commit()
        print(f"  ✓ Private leak: private_gru_ops_001 → {channels[0].username}")
    else:
        print(f"  ⏭️  Private leak already exists")

    # Get statistics
    print("\n" + "=" * 70)
    print("TEST DATA SUMMARY")
    print("=" * 70)

    stats = {
        "channels": db.query(TelegramChannel).count(),
        "messages": db.query(TelegramMessage).count(),
        "forwards": db.query(MessageForward).count(),
        "private_leaks": db.query(PrivateChannelLeak).count(),
        "incidents": db.query(Incident).count()
    }

    print(f"📱 Telegram Channels: {stats['channels']}")
    print(f"💬 Messages: {stats['messages']}")
    print(f"⤵️  Forwards: {stats['forwards']}")
    print(f"🔓 Private Leaks: {stats['private_leaks']}")
    print(f"🚨 Incidents: {stats['incidents']}")

    db.close()

    print("\n✅ Test data creation complete!")
    print(f"🌐 Test on: http://127.0.0.1:8001/api/correlation/stats")

if __name__ == "__main__":
    create_test_data()
