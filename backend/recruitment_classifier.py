"""
Recruitment Post Classifier
Analyzes Telegram posts for GRU recruitment indicators
"""

import sqlite3
import re
from typing import Dict, List, Tuple
from datetime import datetime

class RecruitmentClassifier:
    """
    Classifies social media posts based on recruitment likelihood

    Scoring system:
    - 0-20: Propaganda/News (LOW)
    - 21-40: Suspicious Content (MEDIUM)
    - 41-70: Likely Recruitment (HIGH)
    - 71-100: Confirmed Recruitment (CRITICAL)
    """

    def __init__(self, db_path='data/drone_cuas.db'):
        self.db_path = db_path

        # High-value recruitment indicators
        self.recruitment_patterns = {
            # Direct payment offers
            'payment_offer': [
                r'\$\d{3,}',  # $500, $3000, etc
                r'€\d{3,}',   # €500, €3000, etc
                r'\d{3,}\s*(dollars|euros|USD|EUR)',
                r'(payment|salary|compensation|reward)\s*of\s*[\$€]\d+',
                r'(paid|earn|make)\s*[\$€]\d+',
            ],

            # Recruitment language
            'recruitment_call': [
                r'(looking for|need|seeking|hiring|recruit)\s+(people|persons|individuals|volunteers)',
                r'(join|apply|contact)\s+(us|me|our team)',
                r'send\s+(message|DM|email)',
                r'telegram:\s*@\w+',
                r'interested\?.*contact',
            ],

            # Intelligence gathering requests
            'intelligence_task': [
                r'(take|provide|send)\s+(photo|picture|video|footage)',
                r'(observe|watch|monitor|track|surveillance)',
                r'(report|document|record)\s+(location|coordinates|movements)',
                r'(aircraft|plane|drone|helicopter)\s+(spotting|tracking|observation)',
                r'(military|airport|base|facility)\s+(access|location|security)',
            ],

            # Handler indicators
            'handler_signals': [
                r'confidential|discreet|secret|private',
                r'citizenship\s+in\s+\w+\s+country',
                r'(encrypted|secure)\s+(channel|communication)',
                r'(Ukrainian|Russian)\s+(GRU|intelligence|services)',
                r'handler|operator|contact person',
            ],

            # Crypto/anonymous payment
            'crypto_payment': [
                r'bitcoin|BTC|crypto|monero|XMR',
                r'wallet\s+address',
                r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Bitcoin address pattern
                r'(anonymous|untraceable)\s+payment',
            ],

            # Target indicators
            'target_mention': [
                r'(airport|airbase|military base|naval base|port)',
                r'(NATO|EU|European)\s+(facility|installation|base)',
                r'(Schiphol|Brussels Airport|Charles de Gaulle)',
                r'(critical infrastructure|power plant|refinery)',
            ],
        }

        # Category weights (how much each category contributes to score)
        self.weights = {
            'payment_offer': 25,
            'recruitment_call': 20,
            'intelligence_task': 20,
            'handler_signals': 15,
            'crypto_payment': 10,
            'target_mention': 10,
        }

    def score_post(self, content: str) -> Tuple[int, Dict[str, int]]:
        """
        Score a post based on recruitment indicators

        Returns:
            (total_score, category_matches)
        """
        content_lower = content.lower()
        category_matches = {}
        total_score = 0

        for category, patterns in self.recruitment_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    matches += 1

            if matches > 0:
                # Score = weight * (matches capped at 3) / 3
                category_score = self.weights[category] * min(matches, 3) / 3
                category_matches[category] = matches
                total_score += category_score

        return int(total_score), category_matches

    def classify_risk_level(self, score: int) -> str:
        """Convert score to risk level"""
        if score >= 71:
            return 'CRITICAL'
        elif score >= 41:
            return 'HIGH'
        elif score >= 21:
            return 'MEDIUM'
        else:
            return 'LOW'

    def analyze_all_posts(self) -> List[Dict]:
        """
        Analyze all posts in database

        Returns list of posts with scores, sorted by recruitment likelihood
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                platform,
                channel_name,
                author_name,
                post_date,
                content,
                post_url
            FROM social_media_posts
            ORDER BY id ASC
        """)

        results = []

        for row in cursor.fetchall():
            score, matches = self.score_post(row['content'])
            risk_level = self.classify_risk_level(score)

            results.append({
                'id': row['id'],
                'platform': row['platform'],
                'channel_name': row['channel_name'],
                'author_name': row['author_name'],
                'post_date': row['post_date'],
                'content_preview': row['content'][:200] if row['content'] else '',
                'content_full': row['content'],
                'post_url': row['post_url'],
                'recruitment_score': score,
                'risk_level': risk_level,
                'pattern_matches': matches,
            })

        conn.close()

        # Sort by score descending (highest risk first)
        results.sort(key=lambda x: x['recruitment_score'], reverse=True)

        return results

    def get_high_value_posts(self, min_score: int = 21) -> List[Dict]:
        """Get posts above minimum score threshold"""
        all_posts = self.analyze_all_posts()
        return [p for p in all_posts if p['recruitment_score'] >= min_score]

    def update_database_tags(self):
        """
        Update database with recruitment scores
        Creates new table if needed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create recruitment_analysis table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruitment_analysis (
                post_id INTEGER PRIMARY KEY,
                recruitment_score INTEGER,
                risk_level TEXT,
                pattern_matches TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES social_media_posts(id)
            )
        """)

        # Analyze all posts
        results = self.analyze_all_posts()

        # Insert/update scores
        for post in results:
            cursor.execute("""
                INSERT OR REPLACE INTO recruitment_analysis
                (post_id, recruitment_score, risk_level, pattern_matches, analyzed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                post['id'],
                post['recruitment_score'],
                post['risk_level'],
                str(post['pattern_matches']),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        print(f"✅ Updated recruitment analysis for {len(results)} posts")

    def generate_report(self) -> str:
        """Generate human-readable analysis report"""
        results = self.analyze_all_posts()

        # Statistics
        total = len(results)
        critical = sum(1 for p in results if p['risk_level'] == 'CRITICAL')
        high = sum(1 for p in results if p['risk_level'] == 'HIGH')
        medium = sum(1 for p in results if p['risk_level'] == 'MEDIUM')
        low = sum(1 for p in results if p['risk_level'] == 'LOW')

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║        RECRUITMENT POST ANALYSIS REPORT                      ║
╚══════════════════════════════════════════════════════════════╝

📊 STATISTICS:
   Total Posts Analyzed: {total}

   🔴 CRITICAL (71-100):  {critical:4d} posts ({critical/total*100:.1f}%)
   🟠 HIGH (41-70):       {high:4d} posts ({high/total*100:.1f}%)
   🟡 MEDIUM (21-40):     {medium:4d} posts ({medium/total*100:.1f}%)
   🟢 LOW (0-20):         {low:4d} posts ({low/total*100:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TOP 10 HIGHEST RISK POSTS:

"""

        for i, post in enumerate(results[:10], 1):
            risk_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }[post['risk_level']]

            report += f"""
{i}. {risk_emoji} Post #{post['id']} | Score: {post['recruitment_score']}/100 | {post['risk_level']}
   Channel: {post['channel_name']}
   Date: {post['post_date']}
   Matches: {post['pattern_matches']}
   Preview: {post['content_preview']}...
   URL: {post['post_url'] or 'N/A'}
"""

        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        return report


if __name__ == '__main__':
    print("🔍 Starting Recruitment Post Analysis...\n")

    classifier = RecruitmentClassifier()

    # Generate report
    report = classifier.generate_report()
    print(report)

    # Update database
    print("\n💾 Updating database with recruitment scores...")
    classifier.update_database_tags()

    # Show high-value posts
    high_value = classifier.get_high_value_posts(min_score=41)
    print(f"\n⚠️  Found {len(high_value)} HIGH/CRITICAL risk posts")

    if high_value:
        print("\n🎯 HIGH VALUE TARGETS FOR MANUAL REVIEW:\n")
        for post in high_value:
            print(f"   Post #{post['id']} | Score {post['recruitment_score']} | {post['channel_name']}")
            print(f"   {post['content_preview'][:150]}...")
            print()
