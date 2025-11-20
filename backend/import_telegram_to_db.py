#!/usr/bin/env python3
"""
Import scraped Telegram data into database
"""

import json
import sqlite3
from datetime import datetime

DB_PATH = "data/drone_cuas.db"
INPUT_FILE = "data/telegram_api_scraped.json"


def import_telegram_posts():
    """Import Telegram posts into database"""

    print("=" * 80)
    print("IMPORTING TELEGRAM DATA INTO DATABASE")
    print("=" * 80)

    # Load scraped data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    posts = data['posts']
    print(f"\n📊 Loaded {len(posts)} posts from {INPUT_FILE}")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing Telegram posts (to avoid duplicates)
    cursor.execute("DELETE FROM social_media_posts WHERE platform = 'Telegram'")
    print(f"   Cleared existing Telegram posts")

    inserted = 0
    skipped = 0

    for post in posts:
        try:
            # Extract data
            channel_name = post.get('channel_title', post['channel'])
            post_date = post['post_date']
            content = post['content']
            post_url = post['post_url']

            # Location and intel keywords
            location_keywords = ', '.join(post.get('location_keywords', []))
            intel_keywords = ', '.join(post.get('intel_keywords', []))

            # Payment info
            payment_info = post.get('payment_info', {})
            payment_amount = None
            payment_currency = None
            crypto_wallet = None

            if payment_info.get('amounts'):
                # Parse first amount
                amount_str = payment_info['amounts'][0]
                if '$' in amount_str:
                    payment_currency = 'USD'
                    payment_amount = float(amount_str.replace('$', '').replace(',', ''))
                elif '€' in amount_str:
                    payment_currency = 'EUR'
                    payment_amount = float(amount_str.replace('€', '').replace(',', ''))

            if payment_info.get('crypto_addresses'):
                crypto_wallet = payment_info['crypto_addresses'][0]

            # Determine target type and location from keywords
            target_type = None
            target_location = None

            if 'nuclear' in intel_keywords.lower():
                target_type = 'nuclear'
            elif 'airport' in intel_keywords.lower() or 'аэропорт' in intel_keywords.lower():
                target_type = 'airport'
            elif 'nato' in intel_keywords.lower() or 'нато' in intel_keywords.lower():
                target_type = 'military'

            # Extract location
            location_kw_list = post.get('location_keywords', [])
            if location_kw_list:
                # Prioritize specific locations
                if 'doel' in [l.lower() for l in location_kw_list]:
                    target_location = 'Doel, Belgium'
                elif 'brunssum' in [l.lower() for l in location_kw_list]:
                    target_location = 'Brunssum, Netherlands'
                elif 'liège' in [l.lower() for l in location_kw_list] or 'liege' in [l.lower() for l in location_kw_list]:
                    target_location = 'Liège, Belgium'
                elif 'maastricht' in [l.lower() for l in location_kw_list]:
                    target_location = 'Maastricht, Netherlands'
                elif 'belgium' in [l.lower() for l in location_kw_list] or 'belgië' in [l.lower() for l in location_kw_list] or 'бельгия' in [l.lower() for l in location_kw_list]:
                    target_location = 'Belgium'
                elif 'netherlands' in [l.lower() for l in location_kw_list] or 'nederland' in [l.lower() for l in location_kw_list]:
                    target_location = 'Netherlands'
                elif 'germany' in [l.lower() for l in location_kw_list] or 'deutschland' in [l.lower() for l in location_kw_list]:
                    target_location = 'Germany'

            # Credibility score based on relevance
            credibility_score = min(post.get('relevance_score', 0) / 20.0, 1.0)

            # Content type
            content_type = 'news_report'  # Most posts are news
            if payment_info.get('has_payment'):
                content_type = 'bounty_offer'
            elif 'recruit' in intel_keywords.lower() or 'рекрут' in intel_keywords.lower():
                content_type = 'recruitment'

            # Insert into database
            cursor.execute("""
                INSERT INTO social_media_posts
                (platform, channel_name, post_url, post_date, content, content_type,
                 target_location, target_type,
                 payment_amount, payment_currency, crypto_wallet_address,
                 credibility_score, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Telegram',
                channel_name,
                post_url,
                post_date,
                content,
                content_type,
                target_location,
                target_type,
                payment_amount,
                payment_currency,
                crypto_wallet,
                credibility_score,
                'unconfirmed'
            ))

            inserted += 1

        except Exception as e:
            print(f"   ✗ Error inserting post: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Successfully inserted {inserted} posts")
    print(f"   Skipped: {skipped}")

    return inserted


if __name__ == "__main__":
    import_telegram_posts()
