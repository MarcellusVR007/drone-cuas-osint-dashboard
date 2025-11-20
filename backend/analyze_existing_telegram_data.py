#!/usr/bin/env python3
"""
Analyze Existing Telegram Data
Inventory, analyze patterns, import to database, and generate intelligence leads
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import (
    TelegramChannel, TelegramMessage, Incident
)
from backend.linguistic_fingerprint_detector import LinguisticFingerprintDetector

def load_telegram_json(file_path):
    """Load and parse Telegram JSON export"""
    print(f"📂 Loading: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data)} messages")
    return data

def analyze_data_quality(messages):
    """Analyze data quality and completeness"""
    print("\n" + "="*70)
    print("DATA QUALITY ANALYSIS")
    print("="*70)

    total = len(messages)

    # Count fields
    has_content = sum(1 for m in messages if m.get('content'))
    has_views = sum(1 for m in messages if m.get('views'))
    has_forwards = sum(1 for m in messages if m.get('forwards'))
    has_intel_keywords = sum(1 for m in messages if m.get('intel_keywords'))
    has_location_keywords = sum(1 for m in messages if m.get('location_keywords'))

    print(f"Total messages: {total}")
    print(f"With content: {has_content} ({has_content/total*100:.1f}%)")
    print(f"With views: {has_views} ({has_views/total*100:.1f}%)")
    print(f"With forwards: {has_forwards} ({has_forwards/total*100:.1f}%)")
    print(f"With intel keywords: {has_intel_keywords} ({has_intel_keywords/total*100:.1f}%)")
    print(f"With location keywords: {has_location_keywords} ({has_location_keywords/total*100:.1f}%)")

    return {
        'total': total,
        'completeness_score': has_content/total if total > 0 else 0
    }

def analyze_channels(messages):
    """Analyze channel distribution"""
    print("\n" + "="*70)
    print("CHANNEL ANALYSIS")
    print("="*70)

    channel_stats = defaultdict(lambda: {
        'count': 0,
        'total_views': 0,
        'total_forwards': 0,
        'intel_messages': 0
    })

    for msg in messages:
        channel = msg.get('channel', 'unknown')
        channel_stats[channel]['count'] += 1
        channel_stats[channel]['total_views'] += msg.get('views', 0)
        channel_stats[channel]['total_forwards'] += msg.get('forwards', 0)
        if msg.get('intel_keywords'):
            channel_stats[channel]['intel_messages'] += 1

    # Sort by message count
    sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['count'], reverse=True)

    print(f"\n📊 {len(sorted_channels)} channels detected\n")
    print(f"{'Channel':<30} {'Messages':<10} {'Intel':<8} {'Views':<10} {'Forwards':<10}")
    print("-" * 70)

    for channel, stats in sorted_channels[:20]:  # Top 20
        print(f"{channel:<30} {stats['count']:<10} {stats['intel_messages']:<8} {stats['total_views']:<10} {stats['total_forwards']:<10}")

    return channel_stats

def analyze_temporal_patterns(messages):
    """Analyze posting patterns over time"""
    print("\n" + "="*70)
    print("TEMPORAL ANALYSIS")
    print("="*70)

    dates = []
    hours = []

    for msg in messages:
        if msg.get('post_date'):
            try:
                dt = datetime.fromisoformat(msg['post_date'].replace('Z', '+00:00'))
                dates.append(dt.date())
                hours.append(dt.hour)
            except:
                pass

    # Date distribution
    date_counts = Counter(dates)
    print(f"\nDate range: {min(dates)} to {max(dates)}")
    print(f"Total days: {len(date_counts)}")
    print(f"Average messages per day: {len(messages) / len(date_counts):.1f}")

    # Hour distribution (detect timezone patterns)
    hour_counts = Counter(hours)
    print(f"\nMost active hours (UTC):")
    for hour, count in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {hour:02d}:00 - {count} messages")

    # Detect potential Russian working hours (6-15 UTC = 9-18 Moscow)
    russian_hours = sum(count for hour, count in hour_counts.items() if 6 <= hour <= 15)
    print(f"\nMessages during Russian business hours (9-18 MSK): {russian_hours} ({russian_hours/len(messages)*100:.1f}%)")

    return {
        'date_range': (min(dates), max(dates)),
        'russian_hours_percentage': russian_hours/len(messages) if messages else 0
    }

def analyze_keywords(messages):
    """Analyze keyword patterns"""
    print("\n" + "="*70)
    print("KEYWORD ANALYSIS")
    print("="*70)

    all_intel_keywords = []
    all_location_keywords = []

    for msg in messages:
        if msg.get('intel_keywords'):
            all_intel_keywords.extend(msg['intel_keywords'])
        if msg.get('location_keywords'):
            all_location_keywords.extend(msg['location_keywords'])

    intel_counts = Counter(all_intel_keywords)
    location_counts = Counter(all_location_keywords)

    print(f"\nTop Intelligence Keywords:")
    for keyword, count in intel_counts.most_common(15):
        print(f"  {keyword}: {count}")

    print(f"\nTop Location Keywords:")
    for keyword, count in location_counts.most_common(15):
        print(f"  {keyword}: {count}")

    return {
        'intel_keywords': intel_counts,
        'location_keywords': location_counts
    }

def linguistic_analysis(messages, sample_size=100):
    """Run linguistic fingerprint detection on sample"""
    print("\n" + "="*70)
    print("LINGUISTIC FINGERPRINT ANALYSIS")
    print("="*70)

    detector = LinguisticFingerprintDetector()

    # Sample messages with content
    messages_with_content = [m for m in messages if m.get('content')]
    sample = messages_with_content[:min(sample_size, len(messages_with_content))]

    suspicious_messages = []

    for msg in sample:
        analysis = detector.analyze_text(msg['content'])
        if analysis['score'] >= 30:  # Suspicious threshold
            suspicious_messages.append({
                'channel': msg.get('channel'),
                'date': msg.get('post_date'),
                'content': msg['content'][:100],
                'score': analysis['score'],
                'flags': analysis['flags']
            })

    print(f"\nAnalyzed {len(sample)} messages")
    print(f"Suspicious messages (score ≥30): {len(suspicious_messages)}")
    print(f"Suspicion rate: {len(suspicious_messages)/len(sample)*100:.1f}%")

    if suspicious_messages:
        print(f"\nTop 5 Most Suspicious:")
        for i, msg in enumerate(sorted(suspicious_messages, key=lambda x: x['score'], reverse=True)[:5], 1):
            print(f"\n{i}. Score: {msg['score']}/100 - Channel: {msg['channel']}")
            print(f"   {msg['content']}...")
            print(f"   Flags: {len(msg['flags'])} patterns detected")

    return suspicious_messages

def import_to_database(messages, db):
    """Import messages to database"""
    print("\n" + "="*70)
    print("DATABASE IMPORT")
    print("="*70)

    channels_created = 0
    messages_imported = 0

    # Track channels
    channel_map = {}

    for msg_data in messages:
        channel_name = msg_data.get('channel', 'unknown')

        # Get or create channel
        if channel_name not in channel_map:
            existing_channel = db.query(TelegramChannel).filter(
                TelegramChannel.username == channel_name
            ).first()

            if not existing_channel:
                new_channel = TelegramChannel(
                    channel_id=f"scraped_{channel_name}_{datetime.now().timestamp()}",
                    username=channel_name,
                    title=msg_data.get('channel_title', channel_name),
                    channel_type='public',
                    language_primary='nl',
                    first_discovered=datetime.now()
                )
                db.add(new_channel)
                db.flush()
                channel_map[channel_name] = new_channel.id
                channels_created += 1
            else:
                channel_map[channel_name] = existing_channel.id

        # Import message
        existing_msg = db.query(TelegramMessage).filter(
            TelegramMessage.message_id == str(msg_data.get('message_id')),
            TelegramMessage.channel_id == channel_map[channel_name]
        ).first()

        if not existing_msg:
            try:
                post_date = datetime.fromisoformat(msg_data['post_date'].replace('Z', '+00:00'))
            except:
                post_date = datetime.now()

            new_message = TelegramMessage(
                message_id=str(msg_data.get('message_id', f"msg_{messages_imported}")),
                channel_id=channel_map[channel_name],
                timestamp=post_date,
                text_content=msg_data.get('content', ''),
                views=msg_data.get('views', 0),
                engagement_score=float(msg_data.get('forwards', 0) + msg_data.get('views', 0))
            )
            db.add(new_message)
            messages_imported += 1

            if messages_imported % 100 == 0:
                db.commit()
                print(f"  Imported {messages_imported} messages...")

    db.commit()

    print(f"\n✓ Channels created: {channels_created}")
    print(f"✓ Messages imported: {messages_imported}")

    return {
        'channels': channels_created,
        'messages': messages_imported
    }

def generate_intelligence_leads(messages, channel_stats):
    """Generate actionable intelligence leads"""
    print("\n" + "="*70)
    print("INTELLIGENCE LEADS")
    print("="*70)

    leads = []

    # Lead 1: High-activity channels with intel keywords
    for channel, stats in channel_stats.items():
        if stats['intel_messages'] >= 5:
            lead = {
                'type': 'high_value_channel',
                'channel': channel,
                'confidence': min(stats['intel_messages'] / 20, 1.0),
                'reason': f"{stats['intel_messages']} messages with intel keywords",
                'action': 'Increase collection frequency to every 1 hour'
            }
            leads.append(lead)

    # Lead 2: Messages with drone + location keywords
    for msg in messages:
        intel_kw = msg.get('intel_keywords', [])
        loc_kw = msg.get('location_keywords', [])

        drone_keywords = ['drone', 'uav', 'fpv', 'quadcopter']
        if any(kw in intel_kw for kw in drone_keywords) and loc_kw:
            lead = {
                'type': 'potential_incident_precursor',
                'channel': msg.get('channel'),
                'date': msg.get('post_date'),
                'content': msg.get('content', '')[:100],
                'confidence': 0.6,
                'reason': 'Drone keyword + location mention',
                'action': 'Cross-reference with incident database'
            }
            leads.append(lead)

    # Lead 3: High forward count (viral/coordinated)
    high_forward_msgs = [m for m in messages if m.get('forwards', 0) > 50]
    if high_forward_msgs:
        lead = {
            'type': 'potential_coordination',
            'count': len(high_forward_msgs),
            'confidence': 0.5,
            'reason': f"{len(high_forward_msgs)} messages with >50 forwards",
            'action': 'Investigate forward chains for coordination'
        }
        leads.append(lead)

    # Sort by confidence
    leads.sort(key=lambda x: x.get('confidence', 0), reverse=True)

    print(f"\n🎯 Generated {len(leads)} intelligence leads\n")

    for i, lead in enumerate(leads[:10], 1):
        print(f"{i}. [{lead['type'].upper()}] Confidence: {lead['confidence']:.1%}")
        print(f"   {lead['reason']}")
        print(f"   → {lead['action']}")
        print()

    return leads

def main():
    """Main analysis pipeline"""
    print("=" * 70)
    print("TELEGRAM DATA ANALYSIS & INTELLIGENCE EXTRACTION")
    print("=" * 70)

    # Load data
    json_file = 'telegram_gru_dutch_20251117_084031.json'
    messages = load_telegram_json(json_file)

    # Run analyses
    quality_stats = analyze_data_quality(messages)
    channel_stats = analyze_channels(messages)
    temporal_stats = analyze_temporal_patterns(messages)
    keyword_stats = analyze_keywords(messages)
    suspicious_msgs = linguistic_analysis(messages, sample_size=200)

    # Import to database
    db = SessionLocal()
    try:
        import_stats = import_to_database(messages, db)
    finally:
        db.close()

    # Generate leads
    leads = generate_intelligence_leads(messages, channel_stats)

    # Save report
    report = {
        'analysis_date': datetime.now().isoformat(),
        'source_file': json_file,
        'quality_stats': quality_stats,
        'temporal_stats': {
            'date_range': [str(d) for d in temporal_stats['date_range']],
            'russian_hours_pct': temporal_stats['russian_hours_percentage']
        },
        'suspicious_messages_count': len(suspicious_msgs),
        'import_stats': import_stats,
        'leads_count': len(leads),
        'top_leads': leads[:10]
    }

    report_file = f"telegram_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"📊 Report saved: {report_file}")
    print(f"💾 Database updated with {import_stats['messages']} messages")
    print(f"🎯 {len(leads)} intelligence leads generated")
    print("\n✅ Ready for adaptive learning phase")

if __name__ == "__main__":
    main()
