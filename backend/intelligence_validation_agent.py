#!/usr/bin/env python3
"""
Intelligence Validation Agent - MI5/MI6 OSINT Analyst Profile
Scores Telegram messages on intelligence value (1-10 scale)
Separates propaganda from actionable intelligence
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))


class IntelligenceValidationAgent:
    """
    Senior MI5/MI6 OSINT Analyst specializing in:
    - Counter-UAS (drone) intelligence
    - Russian/GRU information operations
    - European critical infrastructure threats
    - Attribution analysis
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or 'data/drone_cuas_staging.db'

        # Intelligence scope for this project
        self.scope = {
            'primary_focus': [
                'drone_incidents_europe',
                'airport_security_breaches',
                'military_base_infiltrations',
                'operator_identification',
                'recruitment_patterns'
            ],
            'secondary_focus': [
                'cyber_attacks_infrastructure',
                'gru_information_operations',
                'dutch_locations_targeting',
                'nato_base_intelligence'
            ],
            'out_of_scope': [
                'ukraine_battlefield_tactics',
                'domestic_politics_only',
                'pure_propaganda_no_facts'
            ]
        }

        # Propaganda markers
        self.propaganda_patterns = {
            'attribution_deflection': [
                r'не стоит удивляться',  # "should not be surprised"
                r'можно играть вдвоем',  # "can play together"
                r'рыльце в пушку',       # "not clean themselves"
            ],
            'false_equivalence': [
                r'организовывая диверсии',  # "organizing sabotage"
                r'в ответ',                  # "in response"
            ],
            'threat_signaling': [
                r'серьезную угрозу',     # "serious threat"
                r'не останутся без внимания',  # "will not go unnoticed"
            ],
            'victim_framing': [
                r'британцы бьют тревогу',  # "Britons sound alarm"
                r'русских хакеров',         # "Russian hackers"
            ]
        }

        # High-value entity patterns
        self.entity_patterns = {
            'locations': {
                'raf_bases': r'RAF\s+\w+',
                'airports': r'(airport|аэропорт|luchthaven)\s+\w+',
                'dutch_cities': r'(Amsterdam|Rotterdam|Den Haag|Utrecht|Eindhoven|Groningen|Schiphol)',
                'nato_bases': r'(Ramstein|Lakenheath|Geilenkirchen)',
            },
            'actors': {
                'contractors': r'(Dodd Group|defense contractor|подрядчик)',
                'units': r'(GRU|FSB|Wagner|ГРУ|ФСБ)',
                'individuals': r'@\w+',  # Telegram handles
            },
            'technical': {
                'drones': r'(drone|БПЛА|UAV|FPV|дрон|беспилотник)',
                'crypto': r'(wallet|0x[a-fA-F0-9]{40}|bitcoin|crypto)',
                'infrastructure': r'(nuclear|ядерн|F-35|HIMARS)',
            }
        }

    def score_message(self, content: str, channel: str, date: str) -> Dict[str, Any]:
        """
        Score a single message on intelligence value (1-10)

        Returns:
            {
                'intelligence_score': float,
                'breakdown': {...},
                'assessment': {...},
                'recommendation': str
            }
        """

        # Calculate 5 dimensions
        actionability = self._score_actionability(content, channel)
        specificity = self._score_specificity(content)
        verifiability = self._score_verifiability(content)
        relevance = self._score_relevance(content)
        timeliness = self._score_timeliness(date)

        # Weighted score (1-10 scale)
        intelligence_score = (
            actionability * 0.30 +
            specificity * 0.25 +
            verifiability * 0.20 +
            relevance * 0.15 +
            timeliness * 0.10
        )

        # Extract entities and propaganda markers
        entities = self._extract_entities(content)
        propaganda = self._detect_propaganda(content)

        # Classify content type
        content_type = self._classify_content(content, entities)

        # Attribution confidence
        attribution = self._assess_attribution(content, channel, propaganda)

        # Separate facts from noise
        key_facts = self._extract_key_facts(content, entities)
        noise = self._extract_noise(content, propaganda)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            intelligence_score,
            content_type,
            propaganda
        )

        return {
            'intelligence_score': round(intelligence_score, 2),
            'breakdown': {
                'actionability': actionability,
                'specificity': specificity,
                'verifiability': verifiability,
                'relevance': relevance,
                'timeliness': timeliness
            },
            'assessment': {
                'type': content_type,
                'actors': entities.get('actors', []),
                'targets': entities.get('locations', []),
                'technical_details': entities.get('technical', []),
                'attribution_confidence': attribution['confidence'],
                'attribution_reasoning': attribution['reasoning'],
                'propaganda_markers': propaganda,
                'key_facts': key_facts,
                'discard_noise': noise
            },
            'recommendation': recommendation,
            'metadata': {
                'channel': channel,
                'date': date,
                'analyzed_at': datetime.now().isoformat()
            }
        }

    def _score_actionability(self, content: str, channel: str) -> int:
        """Can we act on this immediately? (1-10)"""
        score = 1

        # Specific locations mentioned
        if re.search(self.entity_patterns['locations']['raf_bases'], content, re.I):
            score += 3
        if re.search(self.entity_patterns['locations']['airports'], content, re.I):
            score += 2
        if re.search(self.entity_patterns['locations']['dutch_cities'], content, re.I):
            score += 2

        # Technical details (drone types, crypto wallets)
        if re.search(self.entity_patterns['technical']['crypto'], content, re.I):
            score += 3  # Crypto = actionable
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', content):
            score += 2  # IP addresses

        # Recruitment/planning language
        if re.search(r'(recruit|набор|volunteer|доброволец)', content, re.I):
            score += 2

        return min(score, 10)

    def _score_specificity(self, content: str) -> int:
        """How specific are the details? (1-10)"""
        score = 1

        # Named entities
        score += len(re.findall(r'RAF\s+\w+', content, re.I))  # RAF bases
        score += len(re.findall(r'\d{1,2}\s+(October|November|September)', content, re.I))  # Dates
        score += len(re.findall(r'\d+\s*km', content, re.I))  # Distances
        score += len(re.findall(r'F-35|MQ-9|Reaper|HIMARS', content, re.I))  # Specific systems

        # Named companies/contractors
        if 'Dodd Group' in content or 'Destinus' in content:
            score += 3

        # Specific numbers (casualties, units, etc)
        numbers = len(re.findall(r'\d+', content))
        score += min(numbers // 3, 2)

        return min(score, 10)

    def _score_verifiability(self, content: str) -> int:
        """Can we verify this? (1-10)"""
        score = 3  # Base score - some verification possible

        # URLs/links
        if re.search(r'https?://', content):
            score += 2

        # References to official sources
        if re.search(r'(ministry|министерство|официальн|MoD)', content, re.I):
            score += 2

        # Specific incident details
        if re.search(r'(darknet|leak|breach|hack)', content, re.I):
            score += 2  # Cyber incidents often verifiable

        # Cross-reference potential (multiple sources)
        if re.search(r'(CNN|BBC|Reuters|TASS|РИА)', content, re.I):
            score += 1

        return min(score, 10)

    def _score_relevance(self, content: str) -> int:
        """Does this match our project scope? (1-10)"""
        score = 1

        # Primary focus keywords
        if re.search(r'(drone|БПЛА|airport|аэропорт)', content, re.I):
            score += 3
        if re.search(r'(RAF|NATO|military base|военная база)', content, re.I):
            score += 2
        if re.search(r'(Nederland|Dutch|Netherlands|Schiphol)', content, re.I):
            score += 3  # Dutch focus = high relevance

        # European context
        if re.search(r'(Europe|EU|Европ)', content, re.I):
            score += 1

        # Operator/recruitment intel
        if re.search(r'(recruit|operator|GRU|FSB)', content, re.I):
            score += 2

        # Penalize if Ukraine battlefield-only
        if re.search(r'(Pokrovsk|Kupyansk|Donetsk|Донецк)', content, re.I):
            score -= 2

        return max(1, min(score, 10))

    def _score_timeliness(self, date_str: str) -> int:
        """How recent is this? (1-10)"""
        try:
            msg_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            age_days = (datetime.now() - msg_date.replace(tzinfo=None)).days

            if age_days <= 7:
                return 10
            elif age_days <= 30:
                return 7
            elif age_days <= 90:
                return 5
            else:
                return 2
        except:
            return 5  # Unknown date = medium score

    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract key entities (locations, actors, technical)"""
        entities = {
            'locations': [],
            'actors': [],
            'technical': []
        }

        # Locations
        for pattern_name, pattern in self.entity_patterns['locations'].items():
            matches = re.findall(pattern, content, re.I)
            entities['locations'].extend([m if isinstance(m, str) else m[0] for m in matches])

        # Actors
        for pattern_name, pattern in self.entity_patterns['actors'].items():
            matches = re.findall(pattern, content, re.I)
            entities['actors'].extend([m if isinstance(m, str) else m[0] for m in matches])

        # Technical
        for pattern_name, pattern in self.entity_patterns['technical'].items():
            matches = re.findall(pattern, content, re.I)
            entities['technical'].extend([m if isinstance(m, str) else m[0] for m in matches])

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _detect_propaganda(self, content: str) -> List[str]:
        """Detect propaganda techniques used"""
        detected = []

        for technique, patterns in self.propaganda_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.I):
                    detected.append(technique)
                    break

        return list(set(detected))

    def _classify_content(self, content: str, entities: Dict) -> str:
        """Classify the type of intelligence content"""

        # Cyber incidents
        if re.search(r'(hack|breach|leak|cyber|darknet)', content, re.I):
            return 'CYBER_INCIDENT'

        # Drone incidents
        if re.search(r'(drone|БПЛА|UAV|FPV)', content, re.I):
            if any('airport' in loc.lower() or 'аэропорт' in loc.lower()
                   for loc in entities['locations']):
                return 'DRONE_AIRPORT_INCIDENT'
            if any('RAF' in loc or 'base' in loc.lower()
                   for loc in entities['locations']):
                return 'DRONE_MILITARY_BASE'
            return 'DRONE_INCIDENT_GENERAL'

        # Recruitment
        if re.search(r'(recruit|набор|volunteer)', content, re.I):
            return 'RECRUITMENT_ACTIVITY'

        # Infrastructure targeting
        if re.search(r'(nuclear|F-35|infrastructure|инфраструктур)', content, re.I):
            return 'INFRASTRUCTURE_TARGETING'

        # Pure propaganda
        if len(self._detect_propaganda(content)) >= 3:
            return 'PROPAGANDA_NARRATIVE'

        return 'GENERAL_OSINT'

    def _assess_attribution(self, content: str, channel: str,
                           propaganda: List[str]) -> Dict[str, str]:
        """Assess attribution confidence"""

        confidence = 'UNKNOWN'
        reasoning = []

        # GRU-linked channels
        if channel.lower() in ['rybar', 'intelslava', 'rusich_army']:
            reasoning.append('GRU-linked channel')
            confidence = 'MEDIUM'

        # Propaganda deflection = lower confidence
        if 'attribution_deflection' in propaganda:
            reasoning.append('Attribution deflection detected')
            if confidence == 'MEDIUM':
                confidence = 'LOW'

        # Official sources mentioned
        if re.search(r'(ministry|MoD|official|министерство)', content, re.I):
            reasoning.append('Official source referenced')
            if confidence in ['UNKNOWN', 'LOW']:
                confidence = 'MEDIUM'

        # Specific technical details
        if re.search(r'(Dodd Group|darknet|IP\s+address)', content, re.I):
            reasoning.append('Verifiable technical details')
            if confidence == 'MEDIUM':
                confidence = 'HIGH'

        return {
            'confidence': confidence,
            'reasoning': '; '.join(reasoning) if reasoning else 'Insufficient information'
        }

    def _extract_key_facts(self, content: str, entities: Dict) -> List[str]:
        """Extract verifiable facts (not propaganda)"""
        facts = []

        # Named entities are facts
        if entities['locations']:
            facts.append(f"Locations: {', '.join(entities['locations'][:5])}")
        if entities['actors']:
            facts.append(f"Actors: {', '.join(entities['actors'][:5])}")
        if entities['technical']:
            facts.append(f"Technical: {', '.join(entities['technical'][:5])}")

        # Specific incidents
        if 'Dodd Group' in content:
            facts.append('Dodd Group contractor breach confirmed')
        if 'RAF Lakenheath' in content:
            facts.append('RAF Lakenheath specifically mentioned')
        if re.search(r'\d+\s+bases', content, re.I):
            match = re.search(r'(\d+)\s+bases', content, re.I)
            facts.append(f'{match.group(1)} bases referenced')

        # Darknet leaks
        if 'darknet' in content.lower() or 'даркнет' in content.lower():
            facts.append('Darknet data leak reported')

        return facts

    def _extract_noise(self, content: str, propaganda: List[str]) -> List[str]:
        """Extract propaganda/noise to discard"""
        noise = []

        # Propaganda techniques are noise
        if 'attribution_deflection' in propaganda:
            noise.append('Attribution deflection - unsubstantiated claims')
        if 'false_equivalence' in propaganda:
            noise.append('False equivalence framing')
        if 'threat_signaling' in propaganda:
            noise.append('Threat signaling - narrative spin')

        # Vague threats
        if re.search(r'серьезн\w+ угроз', content, re.I):
            noise.append('Vague threat language')

        # "They do it too" arguments
        if re.search(r'организовывая диверсии', content, re.I):
            noise.append('Whataboutism - UK sabotage claims')

        return noise

    def _generate_recommendation(self, score: float, content_type: str,
                                 propaganda: List[str]) -> str:
        """Generate action recommendation"""

        if score >= 8:
            return 'PRIORITY - High value intelligence, immediate analysis required'
        elif score >= 6:
            if len(propaganda) >= 2:
                return 'RETAIN - Valuable data but filter propaganda elements'
            return 'RETAIN - Good intelligence value for context'
        elif score >= 4:
            if content_type == 'PROPAGANDA_NARRATIVE':
                return 'LOW_PRIORITY - Mostly propaganda, limited intel value'
            return 'CONTEXT_ONLY - May provide background context'
        else:
            return 'DISCARD - Insufficient intelligence value'

    def validate_database_messages(self, limit: int = None) -> List[Dict]:
        """
        Validate all Telegram messages in database
        Returns list of scored messages
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, channel_name, content, post_date, platform
            FROM social_media_posts
            WHERE platform = 'telegram' AND content IS NOT NULL
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            msg_id, channel, content, date, platform = row

            score_result = self.score_message(content, channel, date)
            score_result['db_id'] = msg_id

            results.append(score_result)

        conn.close()
        return results

    def save_validation_report(self, results: List[Dict], output_file: str = None):
        """Save validation results to JSON report"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'intelligence_validation_report_{timestamp}.json'

        # Calculate statistics
        total = len(results)
        high_value = len([r for r in results if r['intelligence_score'] >= 8])
        medium_value = len([r for r in results if 6 <= r['intelligence_score'] < 8])
        low_value = len([r for r in results if r['intelligence_score'] < 6])

        avg_score = sum(r['intelligence_score'] for r in results) / total if total > 0 else 0

        # Content type distribution
        content_types = {}
        for r in results:
            ctype = r['assessment']['type']
            content_types[ctype] = content_types.get(ctype, 0) + 1

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analyst_profile': 'MI5/MI6 Senior OSINT Analyst - Counter-UAS',
                'total_messages_analyzed': total
            },
            'summary': {
                'average_intelligence_score': round(avg_score, 2),
                'distribution': {
                    'high_value (8-10)': high_value,
                    'medium_value (6-8)': medium_value,
                    'low_value (1-6)': low_value
                },
                'content_types': content_types
            },
            'messages': results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_file, report['summary']


def main():
    """Run validation on database messages"""
    print("=" * 80)
    print("INTELLIGENCE VALIDATION AGENT")
    print("Profile: MI5/MI6 Senior OSINT Analyst - Counter-UAS & GRU Operations")
    print("=" * 80)

    agent = IntelligenceValidationAgent()

    print("\n🔍 Analyzing Telegram messages in database...")
    print("📊 Scoring on 5 dimensions:")
    print("   - Actionability (30%)")
    print("   - Specificity (25%)")
    print("   - Verifiability (20%)")
    print("   - Relevance (15%)")
    print("   - Timeliness (10%)")

    # Validate messages
    results = agent.validate_database_messages(limit=None)

    # Save report
    output_file, summary = agent.save_validation_report(results)

    print(f"\n✅ Validation complete!")
    print(f"\n📄 Report: {output_file}")
    print(f"\n📊 SUMMARY:")
    print(f"   Total messages: {summary['distribution']}")
    print(f"   Average score: {summary['average_intelligence_score']}/10")
    print(f"\n🎯 Content types:")
    for ctype, count in summary['content_types'].items():
        print(f"   {ctype}: {count}")

    # Show top 5 high-value messages
    top_messages = sorted(results, key=lambda x: x['intelligence_score'], reverse=True)[:5]
    print(f"\n⭐ TOP 5 HIGH-VALUE INTELLIGENCE:")
    for i, msg in enumerate(top_messages, 1):
        print(f"\n{i}. Score: {msg['intelligence_score']}/10")
        print(f"   Type: {msg['assessment']['type']}")
        print(f"   Channel: {msg['metadata']['channel']}")
        print(f"   Key facts: {msg['assessment']['key_facts'][:2]}")
        print(f"   Recommendation: {msg['recommendation']}")


if __name__ == '__main__':
    main()
