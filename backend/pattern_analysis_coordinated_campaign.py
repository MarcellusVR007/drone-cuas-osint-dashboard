#!/usr/bin/env python3
"""
Coordinated Campaign Pattern Analysis
Analyzes Europa drone incidents for state-actor coordination patterns
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict


class CoordinatedCampaignAnalyzer:
    """
    Analyzes incidents for patterns suggesting coordinated campaigns:
    - Temporal clustering (incidents within days)
    - Geographic clustering (same region)
    - Target similarity (critical infrastructure)
    - Technical similarity (drone types, swarm sizes)
    """

    def __init__(self, db_path: str = 'data/drone_cuas_staging.db'):
        self.db_path = db_path
        self.incidents = []
        self.patterns = {
            'temporal_clusters': [],
            'geographic_clusters': [],
            'target_patterns': [],
            'technical_patterns': [],
            'intelligence_correlation': []
        }

    def load_incidents(self):
        """Load Europa incidents from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, sighting_date, sighting_time, title, description,
                latitude, longitude, source,
                suspected_operator, purpose_assessment,
                operational_class, strategic_assessment,
                estimated_altitude_m
            FROM incidents
            WHERE sighting_date >= '2025-09-01'
            ORDER BY sighting_date DESC
        """)

        rows = cursor.fetchall()
        for row in rows:
            self.incidents.append({
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'title': row[3],
                'description': row[4],
                'latitude': row[5],
                'longitude': row[6],
                'source': row[7],
                'suspected_operator': row[8],
                'purpose': row[9],
                'operational_class': row[10],
                'strategic_assessment': row[11],
                'altitude': row[12]
            })

        conn.close()
        print(f"✓ Loaded {len(self.incidents)} Europa incidents since Sept 1, 2025")

    def analyze_temporal_clustering(self, window_days: int = 7) -> List[Dict]:
        """Find incidents clustered in time"""
        print(f"\n🕐 Analyzing temporal clustering (window: {window_days} days)...")

        clusters = []
        incident_dates = [(i, datetime.fromisoformat(i['date']))
                          for i in self.incidents if i['date']]

        for i, (inc1, date1) in enumerate(incident_dates):
            cluster = [inc1]
            for inc2, date2 in incident_dates[i+1:]:
                if abs((date2 - date1).days) <= window_days:
                    cluster.append(inc2)

            if len(cluster) >= 2:  # At least 2 incidents
                cluster_info = {
                    'incident_count': len(cluster),
                    'date_range': f"{min(c['date'] for c in cluster)} to {max(c['date'] for c in cluster)}",
                    'incidents': cluster,
                    'confidence': self._calculate_temporal_confidence(cluster)
                }
                clusters.append(cluster_info)

        # Deduplicate and sort by size
        unique_clusters = []
        seen = set()
        for c in clusters:
            key = tuple(sorted([i['id'] for i in c['incidents']]))
            if key not in seen:
                unique_clusters.append(c)
                seen.add(key)

        unique_clusters.sort(key=lambda x: x['incident_count'], reverse=True)
        self.patterns['temporal_clusters'] = unique_clusters[:5]  # Top 5

        print(f"   Found {len(unique_clusters)} temporal clusters")
        return unique_clusters[:5]

    def analyze_target_patterns(self) -> List[Dict]:
        """Identify target selection patterns"""
        print(f"\n🎯 Analyzing target patterns...")

        target_types = defaultdict(list)

        for inc in self.incidents:
            # Classify target type from description/title
            text = (inc['title'] + ' ' + inc['description']).lower()

            target_category = 'unknown'
            if any(kw in text for kw in ['chemical', 'dow', 'factory', 'plant']):
                target_category = 'chemical_infrastructure'
            elif any(kw in text for kw in ['port', 'haven', 'shipping']):
                target_category = 'port_infrastructure'
            elif any(kw in text for kw in ['airport', 'luchthaven', 'aviation']):
                target_category = 'aviation_infrastructure'
            elif any(kw in text for kw in ['raf', 'military', 'nato', 'base']):
                target_category = 'military_infrastructure'
            elif any(kw in text for kw in ['nuclear', 'power', 'energy']):
                target_category = 'energy_infrastructure'

            target_types[target_category].append(inc)

        # Create pattern summary
        patterns = []
        for target_type, incidents in target_types.items():
            if len(incidents) >= 2:
                patterns.append({
                    'target_type': target_type,
                    'incident_count': len(incidents),
                    'incidents': incidents,
                    'confidence': self._calculate_target_confidence(incidents)
                })

        patterns.sort(key=lambda x: x['incident_count'], reverse=True)
        self.patterns['target_patterns'] = patterns

        print(f"   Found {len(patterns)} target type patterns")
        return patterns

    def analyze_technical_patterns(self) -> List[Dict]:
        """Analyze technical characteristics (swarm sizes, altitudes)"""
        print(f"\n⚙️ Analyzing technical patterns...")

        patterns = []

        # Swarm operations
        swarm_ops = [i for i in self.incidents
                     if i.get('operational_class') and 'swarm' in i['operational_class'].lower()]

        if swarm_ops:
            patterns.append({
                'pattern_type': 'swarm_operations',
                'incident_count': len(swarm_ops),
                'description': 'Multiple coordinated drones (10+)',
                'incidents': swarm_ops,
                'significance': 'State-actor capability indicator'
            })

        # High-altitude operations (>100m)
        high_altitude = [i for i in self.incidents
                         if i.get('altitude') and i['altitude'] > 100]

        if high_altitude:
            patterns.append({
                'pattern_type': 'high_altitude_operations',
                'incident_count': len(high_altitude),
                'description': 'Operations above 100m altitude',
                'incidents': high_altitude,
                'significance': 'Professional equipment, not hobbyist'
            })

        self.patterns['technical_patterns'] = patterns

        print(f"   Found {len(patterns)} technical patterns")
        return patterns

    def correlate_with_intelligence(self):
        """Correlate incidents with Telegram intelligence"""
        print(f"\n🔗 Correlating with Telegram intelligence...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get Europa-relevant Telegram posts
        cursor.execute("""
            SELECT channel_name, content, post_date
            FROM social_media_posts
            WHERE platform = 'telegram'
              AND (content LIKE '%raf%' OR content LIKE '%airport%'
                   OR content LIKE '%drone%' OR content LIKE '%belgium%'
                   OR content LIKE '%netherlands%' OR content LIKE '%terneuzen%')
              AND post_date >= '2025-09-01'
            ORDER BY post_date DESC
            LIMIT 100
        """)

        posts = cursor.fetchall()
        conn.close()

        # Correlate with incidents
        correlations = []
        for inc in self.incidents:
            inc_date = datetime.fromisoformat(inc['date'])

            for channel, content, post_date in posts:
                try:
                    p_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                except:
                    continue

                # Check if post is within 7 days of incident
                days_diff = (p_date.replace(tzinfo=None) - inc_date).days

                if abs(days_diff) <= 7:
                    # Check content relevance
                    text = content.lower() if content else ''
                    inc_text = (inc['title'] + ' ' + inc['description']).lower()

                    # Look for common keywords
                    keywords = ['drone', 'airport', 'raf', 'military', 'belgium', 'netherlands']
                    common_kw = [kw for kw in keywords if kw in text and kw in inc_text]

                    if common_kw:
                        correlations.append({
                            'incident_id': inc['id'],
                            'incident_title': inc['title'],
                            'incident_date': inc['date'],
                            'telegram_channel': channel,
                            'telegram_post_date': post_date,
                            'days_difference': days_diff,
                            'timing': 'before' if days_diff < 0 else 'after',
                            'common_keywords': common_kw,
                            'post_snippet': content[:200] if content else ''
                        })

        self.patterns['intelligence_correlation'] = correlations

        print(f"   Found {len(correlations)} incident-intelligence correlations")
        return correlations

    def identify_coordinated_campaign(self) -> Dict:
        """
        Synthesize all patterns to assess coordinated campaign likelihood
        """
        print(f"\n🎖️ Assessing coordinated campaign indicators...")

        indicators = {
            'campaign_confidence': 'UNKNOWN',
            'confidence_score': 0,
            'evidence': [],
            'key_incidents': [],
            'recommendation': ''
        }

        score = 0
        evidence = []

        # 1. Temporal clustering
        if self.patterns['temporal_clusters']:
            largest_cluster = self.patterns['temporal_clusters'][0]
            if largest_cluster['incident_count'] >= 3:
                score += 25
                evidence.append(f"Temporal cluster: {largest_cluster['incident_count']} incidents within 7 days")

        # 2. Target pattern consistency
        if self.patterns['target_patterns']:
            critical_infra = [p for p in self.patterns['target_patterns']
                              if 'infrastructure' in p['target_type']]
            if critical_infra:
                score += 20
                evidence.append(f"Critical infrastructure targeting: {len(critical_infra)} patterns")

        # 3. Technical sophistication
        swarm_ops = [p for p in self.patterns['technical_patterns']
                     if p['pattern_type'] == 'swarm_operations']
        if swarm_ops and swarm_ops[0]['incident_count'] >= 2:
            score += 30
            evidence.append(f"Swarm operations detected: {swarm_ops[0]['incident_count']} incidents")

        # 4. Intelligence correlation
        if self.patterns['intelligence_correlation']:
            pre_incident_intel = [c for c in self.patterns['intelligence_correlation']
                                  if c['timing'] == 'before' and abs(c['days_difference']) <= 2]
            if pre_incident_intel:
                score += 25
                evidence.append(f"Pre-incident intelligence: {len(pre_incident_intel)} matches")

        # Calculate confidence
        indicators['confidence_score'] = score
        indicators['evidence'] = evidence

        if score >= 75:
            indicators['campaign_confidence'] = 'HIGH'
            indicators['recommendation'] = 'PRIORITY: Strong evidence of coordinated state-actor campaign'
        elif score >= 50:
            indicators['campaign_confidence'] = 'MEDIUM'
            indicators['recommendation'] = 'INVESTIGATE: Multiple coordination indicators present'
        elif score >= 25:
            indicators['campaign_confidence'] = 'LOW'
            indicators['recommendation'] = 'MONITOR: Some patterns suggest possible coordination'
        else:
            indicators['campaign_confidence'] = 'MINIMAL'
            indicators['recommendation'] = 'Incidents appear independent or copycat activity'

        # Identify key incidents
        # Priority: Swarm ops + critical infrastructure + intelligence correlation
        for inc in self.incidents:
            priority_score = 0

            # Swarm op
            if inc.get('operational_class') and 'swarm' in inc['operational_class'].lower():
                priority_score += 3

            # Critical infrastructure
            text = (inc['title'] + ' ' + inc['description']).lower()
            if any(kw in text for kw in ['chemical', 'military', 'port', 'nuclear', 'raf']):
                priority_score += 2

            # Has intelligence correlation
            correlated = [c for c in self.patterns['intelligence_correlation']
                          if c['incident_id'] == inc['id']]
            if correlated:
                priority_score += 2

            if priority_score >= 4:
                indicators['key_incidents'].append({
                    'id': inc['id'],
                    'title': inc['title'],
                    'date': inc['date'],
                    'priority_score': priority_score
                })

        indicators['key_incidents'].sort(key=lambda x: x['priority_score'], reverse=True)

        return indicators

    def generate_report(self) -> str:
        """Generate comprehensive pattern analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'coordinated_campaign_analysis_{timestamp}.json'

        # Run all analyses
        self.load_incidents()
        self.analyze_temporal_clustering()
        self.analyze_target_patterns()
        self.analyze_technical_patterns()
        self.correlate_with_intelligence()
        campaign_assessment = self.identify_coordinated_campaign()

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analyst_profile': 'MI5/MI6 Coordinated Campaign Assessment',
                'incidents_analyzed': len(self.incidents),
                'timeframe': 'September 1 - November 19, 2025'
            },
            'campaign_assessment': campaign_assessment,
            'patterns': self.patterns,
            'incidents': self.incidents
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.print_report_summary(campaign_assessment)

        return filename

    def print_report_summary(self, assessment: Dict):
        """Print human-readable summary"""
        print("\n" + "="*80)
        print("COORDINATED CAMPAIGN ANALYSIS REPORT")
        print("="*80)

        print(f"\n🎯 CAMPAIGN CONFIDENCE: {assessment['campaign_confidence']}")
        print(f"📊 Confidence Score: {assessment['confidence_score']}/100")

        print(f"\n📋 EVIDENCE:")
        for evidence in assessment['evidence']:
            print(f"   ✓ {evidence}")

        print(f"\n⭐ KEY INCIDENTS ({len(assessment['key_incidents'])}):")
        for inc in assessment['key_incidents'][:5]:
            print(f"   • {inc['date']}: {inc['title']} (score: {inc['priority_score']})")

        print(f"\n💡 RECOMMENDATION:")
        print(f"   {assessment['recommendation']}")

        print(f"\n📊 PATTERN SUMMARY:")
        print(f"   Temporal clusters: {len(self.patterns['temporal_clusters'])}")
        print(f"   Target patterns: {len(self.patterns['target_patterns'])}")
        print(f"   Technical patterns: {len(self.patterns['technical_patterns'])}")
        print(f"   Intelligence correlations: {len(self.patterns['intelligence_correlation'])}")

    def _calculate_temporal_confidence(self, cluster: List[Dict]) -> float:
        """Calculate confidence for temporal cluster"""
        # More incidents + tighter time window = higher confidence
        return min(len(cluster) * 0.2, 1.0)

    def _calculate_target_confidence(self, incidents: List[Dict]) -> float:
        """Calculate confidence for target pattern"""
        # More incidents of same type = higher confidence
        return min(len(incidents) * 0.15, 1.0)


def main():
    analyzer = CoordinatedCampaignAnalyzer()
    report_file = analyzer.generate_report()
    print(f"\n💾 Full report saved: {report_file}")


if __name__ == '__main__':
    main()
