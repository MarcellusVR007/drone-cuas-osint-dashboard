#!/usr/bin/env python3
"""
Telegram-Incident Correlation Analysis
Finds which incidents correlate with which Telegram posts
"""

import sys
import sqlite3
from datetime import datetime, timedelta

def correlate_all():
    """Correlate all incidents with all Telegram posts"""

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("TELEGRAM POST ↔ INCIDENT CORRELATION ANALYSIS")
    print("=" * 80)

    # Fetch all incidents
    cursor.execute("""
        SELECT id, title, sighting_date, latitude, longitude
        FROM incidents
        WHERE sighting_date IS NOT NULL
        ORDER BY sighting_date
    """)
    incidents = cursor.fetchall()

    # Fetch all Telegram posts
    cursor.execute("""
        SELECT id, channel_name, post_date, target_location, content,
               payment_amount, payment_currency, crypto_wallet_address
        FROM social_media_posts
        WHERE platform = 'Telegram'
        ORDER BY post_date
    """)
    posts = cursor.fetchall()

    print(f"\n📊 Dataset:")
    print(f"   - Incidents: {len(incidents)}")
    print(f"   - Telegram posts: {len(posts)}")

    if len(posts) == 0:
        print("\n⚠️  No Telegram posts in database. Add posts first:")
        print("   python3 backend/manual_telegram_entry.py")
        conn.close()
        return

    print("\n" + "=" * 80)
    print("CORRELATIONS FOUND")
    print("=" * 80)

    correlations = []

    for incident in incidents:
        inc_id, inc_title, inc_date_str, inc_lat, inc_lon = incident

        try:
            inc_date = datetime.fromisoformat(inc_date_str)
        except:
            continue

        # Extract location from title
        inc_location = inc_title.split(",")[0].strip() if "," in inc_title else inc_title

        for post in posts:
            post_id, channel, post_date_str, target_location, content, payment_amount, payment_currency, wallet = post

            try:
                post_date = datetime.fromisoformat(post_date_str)
                # Make timezone naive for comparison
                if post_date.tzinfo is not None:
                    post_date = post_date.replace(tzinfo=None)
            except:
                continue

            # Calculate time delta
            days_diff = (inc_date - post_date).days

            # Must be after post, within 60 days
            if not (0 <= days_diff <= 60):
                continue

            # Check location match
            location_match = False
            if target_location:
                target_lower = target_location.lower()
                inc_lower = inc_location.lower()

                # Direct match
                if target_lower in inc_lower or inc_lower in target_lower:
                    location_match = True

                # Common variations
                location_aliases = {
                    "amsterdam": ["schiphol", "eham"],
                    "copenhagen": ["kastrup", "ekch", "copenhagen"],
                    "brussels": ["zaventem", "ebbr", "charleroi"],
                    "frankfurt": ["eddf", "frankfurt"],
                    "berlin": ["eddb", "tegel", "eddt"],
                }

                for city, aliases in location_aliases.items():
                    if city in target_lower or any(alias in target_lower for alias in aliases):
                        if city in inc_lower or any(alias in inc_lower for alias in aliases):
                            location_match = True
                            break

            if location_match:
                strength = "HIGH" if days_diff <= 30 else "MEDIUM"
                correlations.append({
                    "incident_id": inc_id,
                    "incident_title": inc_title,
                    "incident_date": inc_date,
                    "post_id": post_id,
                    "post_channel": channel,
                    "post_date": post_date,
                    "days_diff": days_diff,
                    "payment_amount": payment_amount,
                    "payment_currency": payment_currency,
                    "wallet": wallet,
                    "strength": strength,
                })

    if len(correlations) == 0:
        print("\n⚠️  No correlations found.")
        print("\nPossible reasons:")
        print("1. Telegram posts target different locations than incidents")
        print("2. Posts are too old (>60 days before incidents)")
        print("3. Location names don't match (check spelling)")
        print("\nTry adding more Telegram posts targeting:")
        for inc in incidents[:5]:
            print(f"   - {inc[1].split(',')[0]}")
    else:
        print(f"\n✅ Found {len(correlations)} correlations:\n")

        for i, corr in enumerate(correlations, 1):
            print(f"{i}. INCIDENT #{corr['incident_id']}: {corr['incident_title'][:60]}")
            print(f"   Date: {corr['incident_date'].strftime('%Y-%m-%d')}")
            print(f"   ↔")
            print(f"   TELEGRAM POST #{corr['post_id']} from {corr['post_channel']}")
            print(f"   Date: {corr['post_date'].strftime('%Y-%m-%d')}")
            print(f"   Payment: {corr['payment_currency']} {corr['payment_amount']}" if corr['payment_amount'] else "   Payment: Not specified")
            if corr['wallet']:
                print(f"   Wallet: {corr['wallet'][:20]}...")
            print(f"   Timeline: Post → Incident = {corr['days_diff']} days")
            print(f"   Strength: {corr['strength']}")
            print()

        # Summary statistics
        print("=" * 80)
        print("STATISTICS")
        print("=" * 80)
        print(f"Total correlations: {len(correlations)}")
        print(f"HIGH strength: {sum(1 for c in correlations if c['strength'] == 'HIGH')}")
        print(f"MEDIUM strength: {sum(1 for c in correlations if c['strength'] == 'MEDIUM')}")

        avg_days = sum(c['days_diff'] for c in correlations) / len(correlations)
        print(f"\nAverage timeline: Post + {avg_days:.1f} days = Incident")

        payment_amounts = [c['payment_amount'] for c in correlations if c['payment_amount']]
        if payment_amounts:
            print(f"Average bounty: {sum(payment_amounts) / len(payment_amounts):.0f} EUR")

        unique_wallets = set(c['wallet'] for c in correlations if c['wallet'])
        if unique_wallets:
            print(f"\nUnique Bitcoin wallets: {len(unique_wallets)}")
            for wallet in unique_wallets:
                incidents_per_wallet = sum(1 for c in correlations if c['wallet'] == wallet)
                print(f"   - {wallet}: {incidents_per_wallet} incident(s)")

    conn.close()


def show_unmatched_posts():
    """Show Telegram posts that don't match any incidents (predictive value)"""

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("UNMATCHED TELEGRAM POSTS (Predictive Intelligence)")
    print("=" * 80)
    print("\nThese posts don't correlate with known incidents yet.")
    print("They may predict FUTURE incidents.\n")

    cursor.execute("""
        SELECT id, channel_name, post_date, target_location, content,
               payment_amount, payment_currency
        FROM social_media_posts
        WHERE platform = 'Telegram'
        ORDER BY post_date DESC
    """)
    posts = cursor.fetchall()

    cursor.execute("""
        SELECT title, sighting_date
        FROM incidents
        WHERE sighting_date IS NOT NULL
    """)
    incidents = cursor.fetchall()

    for post in posts:
        post_id, channel, post_date_str, target_location, content, payment_amount, payment_currency = post

        matched = False
        for inc_title, inc_date_str in incidents:
            if target_location and target_location.lower() in inc_title.lower():
                matched = True
                break

        if not matched:
            post_date = datetime.fromisoformat(post_date_str)
            # Make timezone naive for comparison
            if post_date.tzinfo is not None:
                post_date = post_date.replace(tzinfo=None)
            days_since = (datetime.now() - post_date).days

            print(f"POST #{post_id} - {channel}")
            print(f"Date: {post_date.strftime('%Y-%m-%d')} ({days_since} days ago)")
            print(f"Target: {target_location}")
            if payment_amount:
                print(f"Payment: {payment_currency} {payment_amount}")

            # Prediction
            if days_since <= 60:
                expected_start = post_date + timedelta(days=14)
                expected_end = post_date + timedelta(days=30)
                print(f"⚠️  PREDICTION: Incident expected {expected_start.strftime('%Y-%m-%d')} to {expected_end.strftime('%Y-%m-%d')}")

                if datetime.now() > expected_end:
                    print(f"   → Window passed. Either:")
                    print(f"      a) Incident occurred but not yet in database")
                    print(f"      b) Operation cancelled/disrupted")
                    print(f"      c) False positive post")
                else:
                    print(f"   → Still within prediction window!")
                    print(f"   → RECOMMENDED: Enhanced monitoring of {target_location}")

            print()

    conn.close()


if __name__ == "__main__":
    correlate_all()
    show_unmatched_posts()
