#!/usr/bin/env python3
"""
Linguistic Fingerprint Detector
Detects Russian→Dutch translation artifacts and non-native patterns

Features:
- Rule-based detection (fast, immediate deployment)
- Pattern matching for common translation errors
- Scoring system (0-100)
- Batch analysis of Telegram messages
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import TelegramMessage
from sqlalchemy.orm import Session


class LinguisticFingerprintDetector:
    """Detects Russian→Dutch translation patterns"""

    def __init__(self):
        # Suspicious patterns (regex, description, weight)
        self.patterns = [
            # Article errors (missing definite articles)
            (r'\b(drone|vliegveld|incident|militair|gebied)\s+(werd|is|was|zal)\b',
             "Missing article before noun", 15),

            # Preposition calques from Russian
            (r'\bna\s+\d+\s+(minuten|uren|dagen)\b',
             "Preposition 'na' used like Russian 'через' (through)", 20),

            (r'\bop\s+het\s+(vliegveld|terrein)\b',
             "Preposition 'op' where 'bij/nabij' is more natural", 10),

            # Word order (simplified - verb placement)
            (r'\b\w+\s+(boven|onder|bij|naast)\s+(het|de)\s+\w+\s+(vloog|ging|kwam|reed)\b',
             "Slavic word order (preposition before verb)", 15),

            # Literal translations (calques)
            (r'\bmaken\s+(een\s+)?(foto|video|opname)\b',
             "Calque: 'maken' instead of natural 'nemen' (делать → make)", 12),

            (r'\bevenement\b(?!en)',
             "False cognate: 'evenement' used for 'incident' (событие)", 10),

            # Formal/informal mixing
            (r'\b(u|uw)\b.*\b(je|jou|jouw)\b',
             "Mixing formal 'u' with informal 'je' (unnatural)", 8),

            # Russian-style time expressions
            (r'\bin\s+de\s+(nacht|avond|ochtend)\s+van\s+\d',
             "Time expression pattern common in RU→NL translation", 5),

            # Passive voice overuse (common in Russian formal texts)
            (r'\b(werd|werden)\s+\w+en\b.*\b(werd|werden)\s+\w+en\b',
             "Excessive passive voice (Russian formal style)", 7),

            # Missing possessive pronouns
            (r'\b(verloor|vergat|vond)\s+(tas|telefoon|sleutels|portemonnee)\b',
             "Missing possessive pronoun (RU often omits)", 10),
        ]

        # Suspicious vocabulary (words that sound Dutch but used incorrectly by non-natives)
        self.suspicious_vocab = {
            "actueel": "Used like 'actual' instead of 'huidig/werkelijk'",
            "controle": "Overused (Russian: контроль)",
            "realiseren": "Used like 'realize' instead of 'zich realiseren/beseffen'",
            "problematiek": "Overly formal, common in RU→NL translation",
            "fixeren": "Used like 'to fix' instead of 'repareren/oplossen'",
        }

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text for Russian→Dutch translation artifacts

        Returns:
            Dictionary with suspicion score and detected patterns
        """
        if not text or len(text) < 20:  # Skip very short texts
            return {"score": 0, "flags": [], "confidence": 0.0}

        flags = []
        total_score = 0

        text_lower = text.lower()

        # Check patterns
        for pattern, description, weight in self.patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                flags.append({
                    "type": "pattern",
                    "description": description,
                    "weight": weight,
                    "examples": matches[:3]  # Max 3 examples
                })
                total_score += weight * len(matches)

        # Check suspicious vocabulary
        for word, reason in self.suspicious_vocab.items():
            if re.search(r'\b' + word + r'\b', text_lower):
                flags.append({
                    "type": "vocabulary",
                    "description": f"Suspicious use of '{word}': {reason}",
                    "weight": 8,
                    "examples": [word]
                })
                total_score += 8

        # Additional heuristics
        # 1. Check for unnatural repetition (common in machine translation)
        words = text_lower.split()
        if len(words) > 10:
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only count longer words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Flag if any word appears 3+ times in short text
            for word, count in word_freq.items():
                if count >= 3 and len(words) < 50:
                    flags.append({
                        "type": "repetition",
                        "description": f"Unnatural repetition of '{word}' ({count} times)",
                        "weight": 5,
                        "examples": [word]
                    })
                    total_score += 5

        # 2. Check for missing commas (Russian uses fewer commas)
        sentence_length = len([c for c in text if c == '.'])
        comma_count = len([c for c in text if c == ','])
        if sentence_length > 2 and comma_count == 0:
            flags.append({
                "type": "punctuation",
                "description": "No commas despite multiple sentences (Russian style)",
                "weight": 6,
                "examples": []
            })
            total_score += 6

        # Normalize score to 0-100
        normalized_score = min(total_score, 100)

        # Calculate confidence (more flags = higher confidence)
        confidence = min(len(flags) / 5.0, 1.0)  # 5+ flags = 100% confidence

        return {
            "score": normalized_score,
            "flags": flags,
            "confidence": confidence,
            "flag_count": len(flags)
        }

    def analyze_messages_batch(self, db: Session, limit: int = 1000) -> List[Dict]:
        """
        Analyze batch of messages from database

        Returns:
            List of suspicious messages with analysis
        """
        print(f"🔍 Analyzing {limit} messages for linguistic fingerprints...")

        messages = db.query(TelegramMessage).filter(
            TelegramMessage.text_content.isnot(None)
        ).order_by(TelegramMessage.timestamp.desc()).limit(limit).all()

        suspicious_messages = []

        for msg in messages:
            analysis = self.analyze_text(msg.text_content)

            if analysis["score"] >= 30:  # Threshold for suspicion
                # Update message in database
                msg.linguistic_suspicion_score = analysis["confidence"]
                msg.linguistic_flags = json.dumps([f["description"] for f in analysis["flags"]])

                suspicious_messages.append({
                    "message_id": msg.id,
                    "channel_id": msg.channel_id,
                    "timestamp": msg.timestamp.isoformat(),
                    "text_preview": msg.text_content[:200],
                    "score": analysis["score"],
                    "confidence": analysis["confidence"],
                    "flags": analysis["flags"]
                })

        db.commit()

        # Sort by score
        suspicious_messages.sort(key=lambda x: x["score"], reverse=True)

        print(f"🚩 Found {len(suspicious_messages)} suspicious messages (score ≥30)")

        return suspicious_messages

    def generate_report(self, suspicious_messages: List[Dict], output_file: str = None) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 80)
        report.append("LINGUISTIC FINGERPRINT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Total suspicious messages: {len(suspicious_messages)}")
        report.append("")

        for i, msg in enumerate(suspicious_messages[:20], 1):  # Top 20
            report.append(f"{i}. MESSAGE #{msg['message_id']}")
            report.append(f"   Suspicion Score: {msg['score']}/100 (confidence: {msg['confidence']:.2f})")
            report.append(f"   Timestamp: {msg['timestamp']}")
            report.append(f"   Preview: {msg['text_preview']}")
            report.append(f"   Flags detected:")
            for flag in msg['flags']:
                report.append(f"     • {flag['description']} (weight: {flag.get('weight', 0)})")
                if flag.get('examples'):
                    report.append(f"       Examples: {', '.join(map(str, flag['examples']))}")
            report.append("")
            report.append("-" * 80)
            report.append("")

        report_text = "\n".join(report)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"💾 Report saved to: {output_file}")

        return report_text


def main():
    """CLI interface"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Linguistic Fingerprint Detector")
    parser.add_argument("--test", type=str, help="Test text for analysis")
    parser.add_argument("--batch", action="store_true", help="Analyze batch of messages from DB")
    parser.add_argument("--limit", type=int, default=1000, help="Number of messages to analyze")
    parser.add_argument("--report", action="store_true", help="Generate report")

    args = parser.parse_args()

    detector = LinguisticFingerprintDetector()

    if args.test:
        print(f"Analyzing text: {args.test}\n")
        result = detector.analyze_text(args.test)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.batch:
        db = SessionLocal()
        try:
            suspicious = detector.analyze_messages_batch(db, limit=args.limit)

            if args.report:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"linguistic_analysis_{timestamp}.txt"
                detector.generate_report(suspicious, output_file)
            else:
                # Print top 10
                print("\n🚩 Top 10 Suspicious Messages:")
                for msg in suspicious[:10]:
                    print(f"\n  Score: {msg['score']}/100")
                    print(f"  Preview: {msg['text_preview']}")
                    print(f"  Flags: {len(msg['flags'])}")

        finally:
            db.close()

    else:
        # Demo examples
        print("Demo: Testing linguistic patterns\n")

        test_cases = [
            ("Drone werd gezien boven vliegveld", "Missing articles"),
            ("Na 5 minuten drone verdween in de nacht van 3 november", "Russian time/prep patterns"),
            ("We maken foto van militair gebied op het terrein", "Multiple calques"),
            ("Dit is een normale Nederlandse zin zonder verdachte patronen.", "Clean text"),
        ]

        for text, description in test_cases:
            print(f"Test: {description}")
            print(f"Text: {text}")
            result = detector.analyze_text(text)
            print(f"Score: {result['score']}/100, Flags: {result['flag_count']}\n")


if __name__ == "__main__":
    main()
