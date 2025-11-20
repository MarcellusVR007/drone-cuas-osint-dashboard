#!/usr/bin/env python3
"""
Quick import of Round 2 data - NO AI analysis yet, just raw posts
This gives immediate visibility while AI analysis runs in background
"""

import json
import sqlite3
from datetime import datetime

DB_PATH = "data/drone_cuas.db"
JSON_FILE = "backend/scraped_data/telegram_round2_all_20251113_192547.json"

def import_posts():
    print("=" * 80)
    print("QUICK IMPORT - Round 2 Telegram Posts")
    print("=" * 80)

    # Load JSON
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"\n📊 Loaded {len(posts)} posts from Round 2")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear old posts (keep only incidents)
    cursor.execute("DELETE FROM social_media_posts")
    print(f"🗑️  Cleared old posts")

    # Import new posts
    imported = 0
    for post in posts:
        try:
            cursor.execute("""
                INSERT INTO social_media_posts (
                    platform, channel_name, post_url, post_date,
                    content,
                    payment_amount, payment_currency, crypto_wallet_address,
                    credibility_score, verification_status,
                    target_location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Telegram',
                post['channel_name'],
                post['url'],
                post['date'],
                post['text'],
                post.get('payment_amount'),
                post.get('payment_currency'),
                post.get('crypto_address'),
                post.get('relevance_score', 0) / 10.0,  # Convert to 0-1 scale
                'PENDING_ANALYSIS',
                None  # Will be extracted during AI analysis
            ))
            imported += 1

        except Exception as e:
            print(f"❌ Error importing post: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"✅ Imported {imported} posts")
    print(f"📊 Database now has {imported} posts pending AI analysis")
    print("\n💡 Next steps:")
    print("   1. View posts at: http://127.0.0.1:8000/telegram-intel.html")
    print("   2. Run AI analysis: python3 backend/analyze_telegram_intel.py")

if __name__ == "__main__":
    import_posts()
