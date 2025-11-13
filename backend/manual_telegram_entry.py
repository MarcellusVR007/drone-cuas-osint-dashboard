#!/usr/bin/env python3
"""
Manual Telegram Post Entry Tool
Quick data entry for posts found through manual Telegram searches
"""

import sys
import sqlite3
from datetime import datetime

def manual_entry():
    """Interactive entry of Telegram posts"""

    print("=" * 80)
    print("MANUAL TELEGRAM POST ENTRY")
    print("=" * 80)
    print("\nEnter Telegram posts you've found manually.")
    print("Press Ctrl+C to exit at any time.\n")

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    posts_added = 0

    try:
        while True:
            print("\n" + "-" * 80)
            print(f"POST #{posts_added + 1}")
            print("-" * 80)

            # Channel/username
            channel = input("\n1. Channel/Username (e.g., @XakNetTeam_Recruitment): ").strip()
            if not channel:
                print("⚠️  Channel is required. Skipping.")
                continue

            # Post date
            while True:
                post_date_str = input("2. Post Date (YYYY-MM-DD or YYYY-MM-DD HH:MM): ").strip()
                try:
                    if len(post_date_str) == 10:
                        post_date = datetime.strptime(post_date_str, "%Y-%m-%d")
                    else:
                        post_date = datetime.strptime(post_date_str, "%Y-%m-%d %H:%M")
                    break
                except ValueError:
                    print("⚠️  Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")

            # Content
            print("\n3. Post Content (paste full text, press Enter twice when done):")
            content_lines = []
            while True:
                line = input()
                if line == "" and content_lines and content_lines[-1] == "":
                    content_lines.pop()  # Remove last empty line
                    break
                content_lines.append(line)
            content = "\n".join(content_lines)

            if not content:
                print("⚠️  Content is required. Skipping.")
                continue

            # Content type
            print("\n4. Content Type:")
            print("   1 = recruitment")
            print("   2 = bounty_offer")
            print("   3 = intelligence_request")
            print("   4 = operational_update")
            content_type_map = {
                "1": "recruitment",
                "2": "bounty_offer",
                "3": "intelligence_request",
                "4": "operational_update"
            }
            content_type_choice = input("   Choice (1-4): ").strip()
            content_type = content_type_map.get(content_type_choice, "unknown")

            # Target location
            target_location = input("\n5. Target Location (e.g., Amsterdam, Copenhagen): ").strip() or "Unknown"

            # Target type
            print("\n6. Target Type:")
            print("   1 = airport")
            print("   2 = military_base")
            print("   3 = nuclear_facility")
            print("   4 = critical_infrastructure")
            print("   5 = unknown")
            target_type_map = {
                "1": "airport",
                "2": "military_base",
                "3": "nuclear_facility",
                "4": "critical_infrastructure",
                "5": "unknown"
            }
            target_type_choice = input("   Choice (1-5): ").strip()
            target_type = target_type_map.get(target_type_choice, "unknown")

            # Payment amount
            payment_str = input("\n7. Payment Amount (e.g., 1500, or leave blank): ").strip()
            payment_amount = float(payment_str) if payment_str else None

            # Payment currency
            if payment_amount:
                print("\n8. Payment Currency:")
                print("   1 = EUR")
                print("   2 = USD")
                print("   3 = BTC")
                currency_map = {"1": "EUR", "2": "USD", "3": "BTC"}
                currency_choice = input("   Choice (1-3): ").strip()
                payment_currency = currency_map.get(currency_choice, "EUR")
            else:
                payment_currency = None

            # Bitcoin wallet
            crypto_wallet = input("\n9. Bitcoin Wallet Address (or leave blank): ").strip() or None

            # Author/handler
            author_name = input("\n10. Author/Handler Username (or leave blank): ").strip() or "Unknown"

            # Credibility score
            print("\n11. Credibility Score:")
            print("    0.9-1.0 = Verified handler, known channel")
            print("    0.7-0.8 = Active channel, multiple posts")
            print("    0.5-0.6 = New channel, unverified")
            print("    0.3-0.4 = Suspicious, possible honeypot")
            credibility_str = input("    Score (0.0-1.0, default 0.75): ").strip()
            credibility_score = float(credibility_str) if credibility_str else 0.75

            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Channel: {channel}")
            print(f"Date: {post_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"Type: {content_type}")
            print(f"Location: {target_location}")
            print(f"Target: {target_type}")
            if payment_amount:
                print(f"Payment: {payment_currency} {payment_amount}")
            if crypto_wallet:
                print(f"Wallet: {crypto_wallet}")
            print(f"Author: {author_name}")
            print(f"Credibility: {credibility_score}")
            print(f"\nContent preview: {content[:200]}{'...' if len(content) > 200 else ''}")

            # Confirm
            confirm = input("\nSave this post? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Skipped.")
                continue

            # Insert into database
            try:
                cursor.execute("""
                    INSERT INTO social_media_posts
                    (platform, channel, post_date, author_name, author_affiliation,
                     content, content_type, target_location, target_type,
                     payment_amount, payment_currency, crypto_wallet_address, credibility_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "Telegram",
                    channel,
                    post_date.isoformat(),
                    author_name,
                    "Unknown (manual entry)",
                    content,
                    content_type,
                    target_location,
                    target_type,
                    payment_amount,
                    payment_currency,
                    crypto_wallet,
                    credibility_score
                ))
                conn.commit()
                posts_added += 1
                print(f"\n✅ Post #{posts_added} saved to database!")

            except Exception as e:
                print(f"\n❌ Error saving post: {e}")

            # Continue?
            another = input("\nAdd another post? (y/n): ").strip().lower()
            if another != 'y':
                break

    except KeyboardInterrupt:
        print("\n\n⚠️  Entry cancelled by user.")

    finally:
        conn.close()
        print("\n" + "=" * 80)
        print(f"✅ COMPLETED: {posts_added} posts added to database")
        print("=" * 80)


def quick_entry():
    """Quick entry with minimal questions (for rapid data collection)"""

    print("=" * 80)
    print("QUICK TELEGRAM POST ENTRY (Minimal Questions)")
    print("=" * 80)

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    posts_added = 0

    try:
        while True:
            print(f"\n--- POST #{posts_added + 1} ---")

            # Essential fields only
            channel = input("Channel: ").strip()
            date_str = input("Date (YYYY-MM-DD): ").strip()
            location = input("Location: ").strip()
            payment = input("Payment (e.g., 1500): ").strip()

            print("Content (paste, then Enter twice):")
            content_lines = []
            empty_count = 0
            while empty_count < 2:
                line = input()
                if line == "":
                    empty_count += 1
                else:
                    empty_count = 0
                content_lines.append(line)
            content = "\n".join(content_lines).strip()

            # Parse date
            try:
                post_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                print("Invalid date, using today")
                post_date = datetime.now()

            # Parse payment
            try:
                payment_amount = float(payment)
                payment_currency = "EUR"
            except:
                payment_amount = None
                payment_currency = None

            # Insert
            cursor.execute("""
                INSERT INTO social_media_posts
                (platform, channel, post_date, author_name, content, content_type,
                 target_location, target_type, payment_amount, payment_currency,
                 credibility_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Telegram", channel, post_date.isoformat(), "Unknown", content,
                "bounty_offer", location, "airport", payment_amount, payment_currency, 0.7
            ))
            conn.commit()
            posts_added += 1
            print(f"✅ Saved!")

            if input("\nAnother? (y/n): ").lower() != 'y':
                break

    except KeyboardInterrupt:
        pass

    finally:
        conn.close()
        print(f"\n✅ Added {posts_added} posts")


if __name__ == "__main__":
    print("\nTelegram Post Entry Tool")
    print("------------------------")
    print("1. Full Entry (detailed)")
    print("2. Quick Entry (fast)")
    print()

    choice = input("Choice (1/2, default=1): ").strip()

    if choice == "2":
        quick_entry()
    else:
        manual_entry()
