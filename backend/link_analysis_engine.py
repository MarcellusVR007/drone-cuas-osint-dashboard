#!/usr/bin/env python3
"""
Link Analysis Engine - Palantir-style Intelligence Discovery

Automatically discovers relationships between entities:
- Incidents ↔ Telegram Messages (temporal)
- Incidents ↔ Locations (spatial)
- Messages ↔ Channels (social)
- Channels ↔ Channels (forward chains, mentions)
- Messages ↔ Keywords (content analysis)

Based on:
- Palantir Gotham link analysis
- FBI/NSA intelligence tradecraft
- CIA Analysis of Competing Hypotheses (ACH)
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import (
    Incident, TelegramMessage, TelegramChannel,
    IntelligenceLink, RestrictedArea
)
from sqlalchemy import func

class LinkAnalysisEngine:
    """
    Automated intelligence link discovery
    """

    def __init__(self):
        self.db = SessionLocal()
        self.links_discovered = 0

        # Intelligence keywords for link detection
        self.location_keywords = {
            'nederland': ['nederland', 'netherlands', 'dutch', 'holland', 'нидерланды'],
            'belgium': ['belgië', 'belgium', 'belgian', 'belgique', 'бельгия'],
            'schiphol': ['schiphol', 'амстердам аэропорт'],
            'eindhoven': ['eindhoven', 'эйндховен'],
            'rotterdam': ['rotterdam', 'роттердам'],
            'amsterdam': ['amsterdam', 'амстердам'],
            'brussels': ['brussels', 'brussel', 'bruxelles', 'брюссель'],
            'antwerp': ['antwerp', 'antwerpen', 'антверпен']
        }

        self.drone_keywords = [
            'drone', 'drones', 'дрон', 'дрона', 'дронов',
            'fpv', 'uav', 'quadcopter', 'квадрокоптер',
            'unmanned', 'беспилотник'
        ]

    def discover_all_links(self):
        """
        Run all link discovery algorithms
        """
        print("=" * 70)
        print("LINK ANALYSIS ENGINE - AUTOMATED INTELLIGENCE DISCOVERY")
        print("=" * 70)
        print(f"\nStarting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Algorithm 1: Temporal links (Messages ↔ Incidents)
        self.discover_temporal_links()

        # Algorithm 2: Spatial links (Messages ↔ Locations)
        self.discover_spatial_links()

        # Algorithm 3: Social links (Channels ↔ Channels)
        self.discover_social_links()

        # Algorithm 4: Content links (Messages ↔ Keywords)
        self.discover_content_links()

        # Algorithm 5: Network centrality (identify key nodes)
        self.analyze_network_centrality()

        print(f"\n{'='*70}")
        print(f"LINK DISCOVERY COMPLETE")
        print('='*70)
        print(f"\n✅ Total links discovered: {self.links_discovered}")
        print(f"💾 Links saved to database: intelligence_links table\n")

    def discover_temporal_links(self):
        """
        Algorithm 1: Temporal Correlation
        Find messages posted around incident times (±24h window)
        """
        print(f"\n{'='*70}")
        print("ALGORITHM 1: TEMPORAL CORRELATION (Messages ↔ Incidents)")
        print('='*70 + "\n")

        incidents = self.db.query(Incident).all()
        print(f"Analyzing {len(incidents)} incidents...")

        links_found = 0

        for incident in incidents:
            incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())

            # Get messages within ±24h window
            window_start = incident_dt - timedelta(hours=24)
            window_end = incident_dt + timedelta(hours=24)

            nearby_messages = self.db.query(TelegramMessage).filter(
                TelegramMessage.timestamp >= window_start,
                TelegramMessage.timestamp <= window_end
            ).all()

            for msg in nearby_messages:
                time_delta = abs((msg.timestamp - incident_dt).total_seconds() / 3600)

                # Calculate link strength (closer in time = stronger)
                link_strength = max(0, 1 - (time_delta / 24))  # 0-1 scale

                # Calculate confidence based on keyword matches
                text_lower = (msg.text_content or '').lower()
                keyword_matches = [kw for kw in self.drone_keywords if kw in text_lower]

                confidence = 0.3  # Base confidence
                if keyword_matches:
                    confidence += 0.4  # Boost for drone keywords
                if time_delta < 6:
                    confidence += 0.2  # Boost for very close timing
                if msg.views and msg.views > 1000:
                    confidence += 0.1  # Boost for high visibility

                confidence = min(confidence, 1.0)

                # Only create link if confidence > threshold
                if confidence >= 0.5:
                    location_name = incident.restricted_area.name if incident.restricted_area else f"({incident.latitude}, {incident.longitude})"
                    link = IntelligenceLink(
                        entity_a_type='incident',
                        entity_a_id=incident.id,
                        entity_a_identifier=f"{location_name} - {incident.sighting_date}",
                        entity_b_type='telegram_message',
                        entity_b_id=msg.id,
                        entity_b_identifier=f"@{msg.channel.username if msg.channel else 'unknown'} - msg {msg.message_id}",
                        relationship_type='temporal',
                        link_strength=link_strength,
                        confidence_score=confidence,
                        evidence=json.dumps({
                            'time_delta_hours': round(time_delta, 1),
                            'keyword_matches': keyword_matches,
                            'message_views': msg.views
                        }),
                        evidence_count=len(keyword_matches) + 1,
                        keywords_matched=json.dumps(keyword_matches),
                        earliest_evidence_date=msg.timestamp,
                        latest_evidence_date=msg.timestamp,
                        discovered_by='temporal_correlation_algorithm'
                    )
                    self.db.add(link)
                    links_found += 1

        self.db.commit()
        self.links_discovered += links_found
        print(f"✓ Discovered {links_found} temporal links\n")

    def discover_spatial_links(self):
        """
        Algorithm 2: Spatial Correlation
        Find messages mentioning locations near incidents
        """
        print(f"{'='*70}")
        print("ALGORITHM 2: SPATIAL CORRELATION (Messages ↔ Locations)")
        print('='*70 + "\n")

        incidents = self.db.query(Incident).all()
        links_found = 0

        for incident in incidents:
            location_name = incident.restricted_area.name if incident.restricted_area else ''
            location_lower = location_name.lower() if location_name else ''

            # Get all messages
            messages = self.db.query(TelegramMessage).filter(
                TelegramMessage.text_content.isnot(None)
            ).all()

            for msg in messages:
                text_lower = (msg.text_content or '').lower()

                # Check if message mentions incident location
                location_matches = []
                for loc_name, variants in self.location_keywords.items():
                    if any(variant in location_lower for variant in variants):
                        if any(variant in text_lower for variant in variants):
                            location_matches.append(loc_name)

                if location_matches:
                    # Calculate spatial link strength
                    link_strength = min(len(location_matches) * 0.5, 1.0)
                    confidence = 0.6 if len(location_matches) > 1 else 0.4

                    # Check for drone keywords too
                    drone_matches = [kw for kw in self.drone_keywords if kw in text_lower]
                    if drone_matches:
                        confidence = min(confidence + 0.3, 1.0)

                    if confidence >= 0.5:
                        link = IntelligenceLink(
                            entity_a_type='incident',
                            entity_a_id=incident.id,
                            entity_a_identifier=f"{location_name} - {incident.sighting_date}",
                            entity_b_type='telegram_message',
                            entity_b_id=msg.id,
                            entity_b_identifier=f"@{msg.channel.username if msg.channel else 'unknown'}",
                            relationship_type='spatial',
                            link_strength=link_strength,
                            confidence_score=confidence,
                            evidence=json.dumps({
                                'location_matches': location_matches,
                                'drone_keywords': drone_matches
                            }),
                            evidence_count=len(location_matches) + len(drone_matches),
                            keywords_matched=json.dumps(location_matches + drone_matches),
                            earliest_evidence_date=msg.timestamp,
                            latest_evidence_date=msg.timestamp,
                            discovered_by='spatial_correlation_algorithm'
                        )
                        self.db.add(link)
                        links_found += 1

        self.db.commit()
        self.links_discovered += links_found
        print(f"✓ Discovered {links_found} spatial links\n")

    def discover_social_links(self):
        """
        Algorithm 3: Social Network Analysis
        Find relationships between channels (mentions, similar content)
        """
        print(f"{'='*70}")
        print("ALGORITHM 3: SOCIAL NETWORK ANALYSIS (Channels ↔ Channels)")
        print('='*70 + "\n")

        channels = self.db.query(TelegramChannel).all()
        links_found = 0

        for channel_a in channels:
            # Get messages from this channel
            messages_a = self.db.query(TelegramMessage).filter(
                TelegramMessage.channel_id == channel_a.id
            ).all()

            # Look for mentions of other channels
            for msg in messages_a:
                text = msg.text_content or ''

                # Find @mentions
                import re
                mentions = re.findall(r'@(\w+)', text)

                for mentioned_username in mentions:
                    # Find if this is a tracked channel
                    channel_b = self.db.query(TelegramChannel).filter(
                        TelegramChannel.username == mentioned_username
                    ).first()

                    if channel_b and channel_b.id != channel_a.id:
                        # Check if link already exists
                        existing = self.db.query(IntelligenceLink).filter(
                            IntelligenceLink.entity_a_type == 'telegram_channel',
                            IntelligenceLink.entity_a_id == channel_a.id,
                            IntelligenceLink.entity_b_type == 'telegram_channel',
                            IntelligenceLink.entity_b_id == channel_b.id,
                            IntelligenceLink.relationship_type == 'social_mention'
                        ).first()

                        if not existing:
                            link = IntelligenceLink(
                                entity_a_type='telegram_channel',
                                entity_a_id=channel_a.id,
                                entity_a_identifier=f"@{channel_a.username}",
                                entity_b_type='telegram_channel',
                                entity_b_id=channel_b.id,
                                entity_b_identifier=f"@{channel_b.username}",
                                relationship_type='social_mention',
                                link_strength=0.7,
                                confidence_score=0.9,
                                evidence=json.dumps({
                                    'mention_message_id': msg.message_id,
                                    'mention_date': msg.timestamp.isoformat()
                                }),
                                evidence_count=1,
                                earliest_evidence_date=msg.timestamp,
                                latest_evidence_date=msg.timestamp,
                                discovered_by='social_network_analysis'
                            )
                            self.db.add(link)
                            links_found += 1

        self.db.commit()
        self.links_discovered += links_found
        print(f"✓ Discovered {links_found} social links\n")

    def discover_content_links(self):
        """
        Algorithm 4: Content Analysis
        Find messages with high intelligence keyword density
        """
        print(f"{'='*70}")
        print("ALGORITHM 4: CONTENT ANALYSIS (Messages ↔ Intelligence Keywords)")
        print('='*70 + "\n")

        messages = self.db.query(TelegramMessage).filter(
            TelegramMessage.text_content.isnot(None)
        ).all()

        links_found = 0

        for msg in messages:
            text_lower = (msg.text_content or '').lower()

            # Count keyword hits
            drone_hits = [kw for kw in self.drone_keywords if kw in text_lower]
            location_hits = []
            for loc_name, variants in self.location_keywords.items():
                if any(variant in text_lower for variant in variants):
                    location_hits.append(loc_name)

            total_hits = len(drone_hits) + len(location_hits)

            # High keyword density = intelligence value
            if total_hits >= 2:
                keyword_density = total_hits / max(len(text_lower.split()), 1)
                link_strength = min(keyword_density * 100, 1.0)
                confidence = min(0.5 + (total_hits * 0.1), 1.0)

                # Create "high_value_content" pseudo-entity
                link = IntelligenceLink(
                    entity_a_type='telegram_message',
                    entity_a_id=msg.id,
                    entity_a_identifier=f"@{msg.channel.username if msg.channel else 'unknown'}",
                    entity_b_type='intelligence_keyword_cluster',
                    entity_b_id=0,  # Pseudo-entity
                    entity_b_identifier='high_value_content',
                    relationship_type='content_analysis',
                    link_strength=link_strength,
                    confidence_score=confidence,
                    evidence=json.dumps({
                        'drone_keywords': drone_hits,
                        'location_keywords': location_hits,
                        'keyword_density': round(keyword_density, 4)
                    }),
                    evidence_count=total_hits,
                    keywords_matched=json.dumps(drone_hits + location_hits),
                    earliest_evidence_date=msg.timestamp,
                    latest_evidence_date=msg.timestamp,
                    discovered_by='content_analysis_algorithm'
                )
                self.db.add(link)
                links_found += 1

        self.db.commit()
        self.links_discovered += links_found
        print(f"✓ Discovered {links_found} high-value content links\n")

    def analyze_network_centrality(self):
        """
        Algorithm 5: Network Centrality Analysis
        Identify key nodes (most connected channels/messages)
        """
        print(f"{'='*70}")
        print("ALGORITHM 5: NETWORK CENTRALITY ANALYSIS")
        print('='*70 + "\n")

        # Count connections per channel
        channel_connections = defaultdict(int)

        links = self.db.query(IntelligenceLink).all()
        for link in links:
            if link.entity_a_type == 'telegram_channel':
                channel_connections[link.entity_a_id] += 1
            if link.entity_b_type == 'telegram_channel':
                channel_connections[link.entity_b_id] += 1

        # Identify hub channels (high centrality)
        sorted_channels = sorted(channel_connections.items(), key=lambda x: x[1], reverse=True)

        print("Top 10 Most Connected Channels:\n")
        for i, (channel_id, count) in enumerate(sorted_channels[:10], 1):
            channel = self.db.query(TelegramChannel).get(channel_id)
            if channel:
                print(f"  {i}. @{channel.username:<25} {count} connections")

        print()

    def generate_link_report(self, output_file: str = 'link_analysis_report.json'):
        """
        Generate intelligence report of discovered links
        """
        links = self.db.query(IntelligenceLink).all()

        # Group by relationship type
        by_type = defaultdict(list)
        for link in links:
            by_type[link.relationship_type].append({
                'entity_a': f"{link.entity_a_type}:{link.entity_a_identifier}",
                'entity_b': f"{link.entity_b_type}:{link.entity_b_identifier}",
                'strength': link.link_strength,
                'confidence': link.confidence_score,
                'evidence': link.evidence,
                'discovered_by': link.discovered_by
            })

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_links': len(links),
            'by_relationship_type': {k: len(v) for k, v in by_type.items()},
            'links': dict(by_type)
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Report saved: {output_file}")

        return report


def main():
    """Main entry point"""

    engine = LinkAnalysisEngine()
    engine.discover_all_links()
    engine.generate_link_report()

    engine.db.close()


if __name__ == '__main__':
    main()
