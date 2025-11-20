#!/usr/bin/env python3
"""
Phone Number Intelligence Pipeline

Extracts phone numbers from Telegram messages and enriches with:
1. Truecaller lookup (name, location, carrier)
2. Geographic analysis (country, region)
3. Telegram account linking
4. Attribution scoring

Output: Operator attribution database
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal
from backend.models import TelegramChannel, TelegramMessage, IntelligenceLink

class PhoneNumberExtractor:
    """
    Extract and analyze phone numbers from OSINT data
    """

    def __init__(self):
        self.db = SessionLocal()
        self.phone_numbers = []

        # International phone number patterns
        self.patterns = [
            # Format: +31 6 12345678 (Netherlands)
            r'\+31[\s\-]?6[\s\-]?\d{8}',
            # Format: +31612345678
            r'\+316\d{8}',
            # Format: 06-12345678 / 06 12345678
            r'0[\s\-]?6[\s\-]?\d{8}',

            # Russian numbers
            # Format: +7 xxx xxx-xx-xx
            r'\+7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            # Format: +7xxxxxxxxxx
            r'\+7\d{10}',
            # Format: 8 xxx xxx-xx-xx
            r'8[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',

            # Ukrainian numbers
            # Format: +380 xx xxx xx xx
            r'\+380[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',

            # Belgian numbers
            # Format: +32 4xx xx xx xx
            r'\+32[\s\-]?4\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}',

            # German numbers
            # Format: +49 1xx xxxxxxx
            r'\+49[\s\-]?1\d{2}[\s\-]?\d{7}',

            # French numbers
            # Format: +33 6/7 xx xx xx xx
            r'\+33[\s\-]?[67][\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}',

            # Generic international format
            # Format: +xx xxxx...
            r'\+\d{1,4}[\s\-]?\d{6,14}',
        ]

    def extract_from_messages(self):
        """
        Scan all Telegram messages for phone numbers
        """
        print("=" * 80)
        print("PHONE NUMBER EXTRACTION FROM TELEGRAM MESSAGES")
        print("=" * 80 + "\n")

        messages = self.db.query(TelegramMessage).filter(
            TelegramMessage.text_content.isnot(None)
        ).all()

        print(f"📊 Scanning {len(messages)} messages...\n")

        found_numbers = defaultdict(list)  # phone -> list of (message_id, channel_id, context)

        for msg in messages:
            if not msg.text_content:
                continue

            # Extract phone numbers
            for pattern in self.patterns:
                matches = re.findall(pattern, msg.text_content, re.IGNORECASE)

                for match in matches:
                    # Normalize phone number (remove spaces, dashes)
                    normalized = self._normalize_phone(match)

                    # Get context (50 chars before and after)
                    context = self._extract_context(msg.text_content, match, 50)

                    # Filter false positives (Twitter IDs, etc.)
                    if not self._is_valid_phone(normalized, context):
                        continue

                    found_numbers[normalized].append({
                        'message_id': msg.id,
                        'channel_id': msg.channel_id,
                        'timestamp': msg.timestamp,
                        'context': context,
                        'raw_match': match
                    })

        print(f"✓ Found {len(found_numbers)} unique phone numbers\n")

        # Analyze findings
        self._analyze_findings(found_numbers)

        return found_numbers

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number format
        """
        # Remove spaces, dashes, parentheses
        normalized = re.sub(r'[\s\-\(\)]', '', phone)

        # Convert leading 0 to country code for NL
        if normalized.startswith('06'):
            normalized = '+316' + normalized[2:]

        # Convert leading 8 to +7 for RU
        if normalized.startswith('8') and len(normalized) == 11:
            normalized = '+7' + normalized[1:]

        return normalized

    def _is_valid_phone(self, phone: str, context: str) -> bool:
        """
        Filter out false positives (Twitter IDs, URLs, bank cards, etc.)
        """
        # 1. Check if it's in a URL context
        if 'status/' in context or 'twitter.com' in context.lower() or 'x.com' in context.lower():
            return False

        # 2. Twitter status IDs are typically 18-19 digits starting with 1
        if phone.startswith('+71') and len(phone) > 15:
            return False

        # 3. Check for other URL patterns
        if 'http' in context.lower() and phone in context:
            return False

        # 4. Bank card numbers (16 digits, often contains phone-like patterns)
        # Cards start with 2202, 4xxx, 5xxx, 6xxx typically
        context_lower = context.lower()

        # Extract phone digits for pattern matching
        import re
        phone_digits = phone.replace('+', '').replace(' ', '').replace('-', '')

        # If number appears embedded in 16-digit card pattern
        # Card patterns: 2202XXXXXXXXXXXX, 4XXXXXXXXXXXXXXX, etc.
        card_pattern = re.search(r'\b(2202|4\d{3}|5\d{3}|6\d{3})\d{12}\b', context)
        if card_pattern and phone_digits in card_pattern.group(0):
            return False

        # If context has BOTH card keywords AND number pattern looks like part of card
        card_keywords = ['карт', 'card', 'сбер', 'sber']
        has_card_keyword = any(keyword in context_lower for keyword in card_keywords)

        # Check if number starts with typical card BIN patterns
        if has_card_keyword and (phone_digits.startswith('2202') or phone_digits.startswith('620') or phone_digits.startswith('220')):
            return False

        # Fundraising contexts usually have card numbers, not phones
        # BUT some also have real phone numbers (like +79300311880 for Sberbank)
        # Only filter if it ALSO looks like a card number pattern
        fundraising_keywords = ['фонд', 'сбор', 'для фронта', 'donation', 'представител']
        has_fundraising = any(keyword in context_lower for keyword in fundraising_keywords)

        # Numbers starting with +31 or +7220 in fundraising context = likely card fragments
        if has_fundraising and (phone.startswith('+31') or phone.startswith('+7220') or phone.startswith('+710')):
            return False

        # 5. Bank account numbers (starting with specific patterns)
        # Russian bank accounts: "Р/с 40703810530000007491"
        if 'р/с' in context_lower or 'счет' in context_lower or 'account' in context_lower:
            return False

        # 6. Numbers that look like part of longer financial sequences
        # If phone number appears embedded in long digit sequence, likely not a phone
        import re
        # Find all digit sequences around this number
        phone_digits = phone.replace('+', '').replace(' ', '').replace('-', '')

        # Check for 14-16 digit sequences (card numbers)
        digit_sequences = re.findall(r'\d{14,19}', context)
        for seq in digit_sequences:
            # If any part of our phone number is embedded in a long sequence, it's a card
            # Example: phone +31694285028 → digits 31694285028
            #          card 2202206942850285 contains "694285028"
            if phone_digits[2:] in seq or phone_digits[1:] in seq or phone_digits in seq:
                return False

        # 7. Specific false positive patterns
        # +31694285028 is part of 2202206942850285
        # +31620919917 is part of 2202206209199178
        if phone.startswith('+316') and len(phone) == 12:
            # Check if preceded by more digits (card number pattern)
            if re.search(r'\d{4,}' + phone_digits, context):
                return False

        # 8. Numbers starting with unusual patterns
        # +71053000000 (too many zeros, looks like account number)
        if phone.count('0') > 5:
            return False

        # 9. Check for BIK, КПП, INN patterns (Russian business identifiers)
        if 'бик' in context_lower or 'кпп' in context_lower or 'инн' in context_lower:
            return False

        return True

    def _extract_context(self, text: str, match: str, chars: int = 50) -> str:
        """
        Extract context around phone number in text
        """
        try:
            pos = text.find(match)
            if pos == -1:
                return ""

            start = max(0, pos - chars)
            end = min(len(text), pos + len(match) + chars)

            context = text[start:end]

            # Add ellipsis
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            return context
        except:
            return ""

    def _analyze_findings(self, found_numbers: Dict):
        """
        Analyze extracted phone numbers
        """
        print("=" * 80)
        print("📊 PHONE NUMBER ANALYSIS")
        print("=" * 80 + "\n")

        # Group by country code
        by_country = defaultdict(int)
        for phone in found_numbers.keys():
            country_code = self._detect_country(phone)
            by_country[country_code] += 1

        print("By Country:")
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count}")

        print(f"\nMost mentioned numbers:\n")

        # Sort by frequency
        sorted_numbers = sorted(found_numbers.items(), key=lambda x: len(x[1]), reverse=True)

        for phone, occurrences in sorted_numbers[:20]:
            country = self._detect_country(phone)
            channels = set(occ['channel_id'] for occ in occurrences)

            print(f"  {phone} ({country})")
            print(f"    Occurrences: {len(occurrences)}")
            print(f"    Channels: {len(channels)}")

            # Show first context
            if occurrences:
                print(f"    Context: {occurrences[0]['context'][:100]}")
            print()

        # Save results
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_unique_numbers': len(found_numbers),
            'by_country': dict(by_country),
            'phone_numbers': {}
        }

        for phone, occurrences in found_numbers.items():
            report['phone_numbers'][phone] = {
                'country': self._detect_country(phone),
                'occurrence_count': len(occurrences),
                'first_seen': str(min(occ['timestamp'] for occ in occurrences if occ['timestamp'])),
                'last_seen': str(max(occ['timestamp'] for occ in occurrences if occ['timestamp'])),
                'channels': list(set(occ['channel_id'] for occ in occurrences)),
                'contexts': [occ['context'] for occ in occurrences[:5]]  # First 5 contexts
            }

        output_file = 'phone_numbers_extracted.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Report saved: {output_file}\n")

    def _detect_country(self, phone: str) -> str:
        """
        Detect country from phone number
        """
        if phone.startswith('+31'):
            return 'Netherlands'
        elif phone.startswith('+7'):
            return 'Russia'
        elif phone.startswith('+380'):
            return 'Ukraine'
        elif phone.startswith('+32'):
            return 'Belgium'
        elif phone.startswith('+49'):
            return 'Germany'
        elif phone.startswith('+33'):
            return 'France'
        elif phone.startswith('+1'):
            return 'USA/Canada'
        elif phone.startswith('+44'):
            return 'UK'
        else:
            return 'Other'

    def lookup_truecaller(self, phone: str) -> Optional[Dict]:
        """
        Lookup phone number via Truecaller API

        Note: Requires Truecaller API key (commercial or free tier)
        Free tier: 250 lookups/month
        """
        # TODO: Implement Truecaller API integration
        # For now, return placeholder

        print(f"  ⚠️  Truecaller lookup not yet implemented")
        print(f"     To enable: Get API key from truecaller.com")
        print(f"     Free tier: 250 lookups/month")

        return {
            'name': 'Unknown',
            'carrier': 'Unknown',
            'location': self._detect_country(phone),
            'note': 'Truecaller API integration needed'
        }

    def create_intelligence_links(self, found_numbers: Dict):
        """
        Create IntelligenceLink entries for phone numbers
        """
        print("\n" + "=" * 80)
        print("🔗 CREATING INTELLIGENCE LINKS")
        print("=" * 80 + "\n")

        links_created = 0

        for phone, occurrences in found_numbers.items():
            for occ in occurrences:
                # Create link: message → phone number
                link = IntelligenceLink(
                    entity_a_type='message',
                    entity_a_id=occ['message_id'],
                    entity_a_identifier=f"Message {occ['message_id']}",
                    entity_b_type='phone',
                    entity_b_id=0,  # Phone numbers don't have DB IDs yet
                    entity_b_identifier=phone,
                    relationship_type='contains_phone',
                    link_strength=1.0,
                    confidence_score=0.8,  # High confidence - direct extraction
                    evidence=json.dumps({
                        'context': occ['context'],
                        'country': self._detect_country(phone)
                    })
                )

                self.db.add(link)
                links_created += 1

        self.db.commit()

        print(f"✓ Created {links_created} intelligence links\n")

    def close(self):
        self.db.close()


def main():
    """Main execution"""
    print("=" * 80)
    print("PHONE NUMBER INTELLIGENCE PIPELINE")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    extractor = PhoneNumberExtractor()

    # Extract phone numbers
    found_numbers = extractor.extract_from_messages()

    # Create intelligence links
    if found_numbers:
        extractor.create_intelligence_links(found_numbers)

    extractor.close()

    print("=" * 80)
    print("✅ PHONE NUMBER EXTRACTION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review phone_numbers_extracted.json")
    print("2. Get Truecaller API key (optional, 250 lookups/month free)")
    print("3. Manually investigate high-frequency numbers")
    print("4. Cross-reference with Telegram usernames\n")


if __name__ == '__main__':
    main()
