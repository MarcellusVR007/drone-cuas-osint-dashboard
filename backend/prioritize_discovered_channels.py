#!/usr/bin/env python3
"""
Channel Prioritization Engine
Analyzes discovered channels and creates intelligence-driven monitoring priorities

Scoring Factors:
1. Proximity to known threats (graph distance)
2. Channel type (Russian military vs Dutch political vs other)
3. Creation date (older = more established)
4. Relationship strength (forwards, mentions)
5. Language/region relevance
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))


class ChannelPrioritizer:
    """
    Intelligence-driven channel prioritization
    """

    def __init__(self, discovery_file: str):
        self.discovery_file = discovery_file
        self.channels = {}
        self.priorities = []

        # Known threat categories
        self.russian_military_indicators = [
            'rybar', 'dva_majors', 'voin_dv', 'rusich', 'caucas', 'evropa',
            'afrika', 'pacific', 'mena', 'latam', 'stan', 'belarusian_silovik',
            'patrick', 'soloviev', 'medvedev', 'geopolitics'
        ]

        self.dutch_political_indicators = [
            'fvd', 'vos', 'haga', 'deanderekrant', 'weltschmerz'
        ]

    def load_discoveries(self):
        """Load discovered channels"""
        print("=" * 70)
        print("CHANNEL PRIORITIZATION ENGINE")
        print("=" * 70)
        print(f"\n📂 Loading: {self.discovery_file}\n")

        with open(self.discovery_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.channels = data['channels']
        print(f"✓ Loaded {len(self.channels)} discovered channels\n")

    def categorize_channel(self, username: str, title: str) -> Dict:
        """
        Categorize channel by indicators
        """
        username_lower = username.lower()
        title_lower = title.lower()

        # Check categories
        is_russian_military = any(ind in username_lower or ind in title_lower
                                   for ind in self.russian_military_indicators)
        is_dutch_political = any(ind in username_lower or ind in title_lower
                                  for ind in self.dutch_political_indicators)

        # Determine primary category
        if is_russian_military:
            category = "russian_military"
            risk_multiplier = 1.0  # Highest risk
        elif is_dutch_political:
            category = "dutch_political"
            risk_multiplier = 0.8  # High risk (potential recruitment targets)
        else:
            category = "other"
            risk_multiplier = 0.5  # Medium risk

        return {
            'category': category,
            'risk_multiplier': risk_multiplier,
            'is_russian_military': is_russian_military,
            'is_dutch_political': is_dutch_political
        }

    def calculate_channel_score(self, username: str, metadata: Dict) -> Dict:
        """
        Calculate multi-factor intelligence score for channel

        Score components:
        - Category risk (0-40 points)
        - Proximity to seed channels (0-30 points)
        - Channel age/establishment (0-15 points)
        - Verification status (0-10 points)
        - Language relevance (0-5 points)
        """

        # Factor 1: Category risk (0-40)
        category_info = self.categorize_channel(username, metadata.get('title', ''))
        category_score = category_info['risk_multiplier'] * 40

        # Factor 2: Proximity (0-30)
        # All discovered channels are 1 hop from seeds (direct mention/forward)
        proximity_score = 30  # Direct connection

        # Factor 3: Channel age (0-15)
        age_score = 0
        created = metadata.get('created')
        if created:
            try:
                created_date = datetime.fromisoformat(created.replace('+00:00', ''))
                age_years = (datetime.now() - created_date).days / 365
                # Older channels get higher scores (more established)
                age_score = min(age_years * 3, 15)
            except:
                pass

        # Factor 4: Verification (0-10)
        verification_score = 10 if metadata.get('verified') else 0

        # Factor 5: Language relevance (0-5)
        language_score = 0
        username_lower = username.lower()
        if any(word in username_lower for word in ['dutch', 'nederland', 'nl']):
            language_score = 5
        elif category_info['is_dutch_political']:
            language_score = 4

        # Calculate total
        total_score = (
            category_score +
            proximity_score +
            age_score +
            verification_score +
            language_score
        )

        return {
            'username': username,
            'total_score': total_score,
            'category': category_info['category'],
            'components': {
                'category_risk': category_score,
                'proximity': proximity_score,
                'age': age_score,
                'verification': verification_score,
                'language': language_score
            },
            'metadata': metadata,
            'recommendation': self.get_recommendation(total_score, category_info['category'])
        }

    def get_recommendation(self, score: float, category: str) -> str:
        """
        Generate monitoring recommendation
        """
        if score >= 75:
            return "TIER 1 - Monitor every 1 hour (critical intelligence value)"
        elif score >= 60:
            return "TIER 2 - Monitor every 2-4 hours (high intelligence value)"
        elif score >= 45:
            return "TIER 3 - Monitor every 12 hours (medium intelligence value)"
        else:
            return "TIER 4 - Weekly review (low priority)"

    def analyze_all_channels(self):
        """
        Analyze and score all discovered channels
        """
        print("=" * 70)
        print("CHANNEL ANALYSIS")
        print("=" * 70 + "\n")

        self.priorities = []

        for username, metadata in self.channels.items():
            score_data = self.calculate_channel_score(username, metadata)
            self.priorities.append(score_data)

        # Sort by score
        self.priorities.sort(key=lambda x: x['total_score'], reverse=True)

        print(f"✓ Analyzed {len(self.priorities)} channels\n")

    def print_analysis(self):
        """
        Print prioritized channel list
        """
        print("=" * 70)
        print("PRIORITIZED CHANNEL RECOMMENDATIONS")
        print("=" * 70 + "\n")

        # Group by tier
        tiers = defaultdict(list)
        for channel in self.priorities:
            if channel['total_score'] >= 75:
                tiers['TIER 1'].append(channel)
            elif channel['total_score'] >= 60:
                tiers['TIER 2'].append(channel)
            elif channel['total_score'] >= 45:
                tiers['TIER 3'].append(channel)
            else:
                tiers['TIER 4'].append(channel)

        # Print each tier
        for tier in ['TIER 1', 'TIER 2', 'TIER 3', 'TIER 4']:
            channels = tiers.get(tier, [])
            if not channels:
                continue

            print(f"\n{'='*70}")
            print(f"{tier} - {len(channels)} channels")
            print('='*70)

            for i, ch in enumerate(channels, 1):
                verified = "✅" if ch['metadata'].get('verified') else ""
                restricted = "⚠️" if ch['metadata'].get('restricted') else ""

                print(f"\n{i}. @{ch['username']:<25} Score: {ch['total_score']:.1f}/100 {verified} {restricted}")
                print(f"   {ch['metadata'].get('title', 'N/A')}")
                print(f"   Category: {ch['category'].upper()}")
                print(f"   {ch['recommendation']}")
                print(f"   Score breakdown: Category={ch['components']['category_risk']:.0f}, "
                      f"Proximity={ch['components']['proximity']:.0f}, "
                      f"Age={ch['components']['age']:.0f}")

    def save_report(self, output_file: str = 'channel_priorities_20251119.json'):
        """
        Save prioritization report
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_channels_analyzed': len(self.priorities),
            'tier_distribution': {
                'tier_1': len([c for c in self.priorities if c['total_score'] >= 75]),
                'tier_2': len([c for c in self.priorities if 60 <= c['total_score'] < 75]),
                'tier_3': len([c for c in self.priorities if 45 <= c['total_score'] < 60]),
                'tier_4': len([c for c in self.priorities if c['total_score'] < 45])
            },
            'channels': self.priorities
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print("REPORT SAVED")
        print('='*70)
        print(f"\n💾 {output_file}")

        # Print tier summary
        print(f"\n📊 TIER DISTRIBUTION:")
        print(f"   Tier 1 (Critical):  {report['tier_distribution']['tier_1']} channels")
        print(f"   Tier 2 (High):      {report['tier_distribution']['tier_2']} channels")
        print(f"   Tier 3 (Medium):    {report['tier_distribution']['tier_3']} channels")
        print(f"   Tier 4 (Low):       {report['tier_distribution']['tier_4']} channels")

    def generate_monitoring_commands(self):
        """
        Generate bash commands to add channels to monitoring
        """
        print(f"\n{'='*70}")
        print("NEXT STEPS - ADD TO MONITORING")
        print('='*70 + "\n")

        tier1 = [c for c in self.priorities if c['total_score'] >= 75]
        tier2 = [c for c in self.priorities if 60 <= c['total_score'] < 75]

        if tier1:
            print("🎯 TIER 1 Channels (Add immediately):\n")
            channels_list = ','.join([c['username'] for c in tier1])
            print(f"python3 backend/scrape_telegram_api.py --channels {channels_list} --limit 200\n")

        if tier2:
            print("🎯 TIER 2 Channels (Add next):\n")
            channels_list = ','.join([c['username'] for c in tier2])
            print(f"python3 backend/scrape_telegram_api.py --channels {channels_list} --limit 100\n")


def main():
    """Main entry point"""

    prioritizer = ChannelPrioritizer('discovered_channels_20251119.json')
    prioritizer.load_discoveries()
    prioritizer.analyze_all_channels()
    prioritizer.print_analysis()
    prioritizer.save_report()
    prioritizer.generate_monitoring_commands()

    print(f"\n{'='*70}")
    print("✅ PRIORITIZATION COMPLETE")
    print('='*70 + "\n")


if __name__ == '__main__':
    main()
