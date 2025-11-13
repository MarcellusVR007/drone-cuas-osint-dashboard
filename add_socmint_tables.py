#!/usr/bin/env python3
"""
Add Social Media Intelligence (SOCMINT) tables to track:
- Telegram posts with crypto bounties
- Threat actors
- Crypto transactions
- Links to incidents
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def create_socmint_tables():
    """Create social media intelligence tables"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 1. Actors table - threat actors, handlers, operatives
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            alias TEXT,
            actor_type TEXT,  -- handler, operative, financier, coordinator
            affiliation TEXT,  -- GRU, SVR, Hacktivist, Unknown
            telegram_handle TEXT,
            telegram_user_id TEXT,
            nationality TEXT,
            confidence_score REAL DEFAULT 0.5,
            status TEXT,  -- active, arrested, suspected, confirmed
            first_observed DATE,
            last_activity DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Social Media Posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_media_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,  -- Telegram, Twitter, VK, etc
            channel_name TEXT,
            channel_id TEXT,
            post_id TEXT,
            post_url TEXT,
            author_id INTEGER,  -- FK to actors
            post_date TIMESTAMP,
            content TEXT,
            content_type TEXT,  -- bounty_offer, recruitment, claim_responsibility, coordination

            -- Bounty details
            payment_amount REAL,
            payment_currency TEXT,  -- BTC, ETH, USD
            crypto_wallet_address TEXT,
            target_type TEXT,  -- infrastructure, military, airport, nuclear
            target_location TEXT,

            -- Evidence & attribution
            screenshot_url TEXT,
            archived_url TEXT,
            credibility_score REAL DEFAULT 0.5,
            verification_status TEXT,  -- verified, suspected, unconfirmed

            -- Link to incidents
            linked_incident_id INTEGER,  -- FK to incidents
            correlation_confidence REAL,
            correlation_notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES actors(id),
            FOREIGN KEY (linked_incident_id) REFERENCES incidents(id)
        )
    """)

    # 3. Crypto Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blockchain TEXT,  -- Bitcoin, Ethereum, Monero
            transaction_hash TEXT UNIQUE,
            from_address TEXT,
            to_address TEXT,
            amount REAL,
            currency TEXT,  -- BTC, ETH, etc
            usd_value REAL,
            transaction_date TIMESTAMP,

            -- Attribution
            sender_actor_id INTEGER,  -- FK to actors
            recipient_actor_id INTEGER,  -- FK to actors
            purpose TEXT,  -- payment_for_incident, donation, funding

            -- Links
            linked_post_id INTEGER,  -- FK to social_media_posts
            linked_incident_id INTEGER,  -- FK to incidents

            -- On-chain analysis
            block_number INTEGER,
            confirmation_count INTEGER,
            source_url TEXT,  -- blockchain explorer link

            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_actor_id) REFERENCES actors(id),
            FOREIGN KEY (recipient_actor_id) REFERENCES actors(id),
            FOREIGN KEY (linked_post_id) REFERENCES social_media_posts(id),
            FOREIGN KEY (linked_incident_id) REFERENCES incidents(id)
        )
    """)

    # 4. Actor Relationships table (network connections)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actor_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor1_id INTEGER NOT NULL,
            actor2_id INTEGER NOT NULL,
            relationship_type TEXT,  -- handler, coordinator, collaborator, recruiter
            confidence_score REAL DEFAULT 0.5,
            first_observed DATE,
            last_activity DATE,
            evidence TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (actor1_id) REFERENCES actors(id),
            FOREIGN KEY (actor2_id) REFERENCES actors(id)
        )
    """)

    conn.commit()
    conn.close()

    print("✓ Created SOCMINT tables:")
    print("  - actors")
    print("  - social_media_posts")
    print("  - crypto_transactions")
    print("  - actor_relationships")

def add_sample_data():
    """Add sample OSINT data based on research"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Sample actors based on OSINT research
    actors = [
        ("VWarrior", "V_Warrior", "handler", "GRU", "@VWarrior_GRU", None, "RU", 0.85, "active",
         "2024-01-01", "2025-11-01", "GRU handler using Telegram for recruitment. Linked to arson/sabotage operations across Europe. Cryptocurrency payments."),

        ("XakNet Team Moderator", "XakNet_Admin", "coordinator", "GRU APT28", "@XakNetTeam", None, "RU", 0.9, "active",
         "2022-03-01", "2025-11-01", "Telegram channel moderator coordinating with GRU APT28. Crypto donations, DDoS operations."),

        ("CyberArmy Coordinator", "CAR_Reborn", "coordinator", "GRU-linked Hacktivist", "@CyberArmyofRussia_Reborn", None, "RU", 0.8, "active",
         "2022-02-24", "2025-10-15", "Hacktivist group coordinator. Telegram channel for claims and crypto fundraising."),

        ("Unknown Operative - Brunssum", "Brunssum_Op", "operative", "Unknown", None, None, "Unknown", 0.3, "suspected",
         "2025-11-08", "2025-11-08", "Suspected operative behind Zuid-Limburg NATO JFC drone reconnaissance."),
    ]

    for actor in actors:
        try:
            cursor.execute("""
                INSERT INTO actors (name, alias, actor_type, affiliation, telegram_handle,
                                   telegram_user_id, nationality, confidence_score, status,
                                   first_observed, last_activity, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, actor)
        except sqlite3.IntegrityError:
            pass  # Skip duplicates

    # Sample social media posts
    posts = [
        ("Telegram", "XakNet Team", "t.me/XakNetTeam", "post_12345", "https://t.me/XakNetTeam/12345",
         2,  # XakNet moderator
         "2025-10-15 10:30:00",
         "募集: 空港监视. €1500 BTC支付. 联系 @handler_bot",
         "recruitment",
         1500.0, "EUR", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "airport", "Western Europe",
         None, None, 0.7, "suspected", None, None, None),

        ("Telegram", "Pro-Russian Recruitment", "t.me/work_offers", "post_67890", "https://t.me/work_offers/67890",
         1,  # VWarrior
         "2024-08-10 14:20:00",
         "Срочная работа! Наблюдение за военной базой. Оплата $1000 в криптовалюте после выполнения. Контакт через бот.",
         "bounty_offer",
         1000.0, "USD", "bc1q...example", "military_base", "Germany",
         None, None, 0.8, "verified", None, None, "Linked to Brunsbüttel reconnaissance campaign"),

        ("Telegram", "VWarrior Direct", None, "dm_12345", None,
         1,  # VWarrior
         "2025-11-07 18:00:00",
         "Target: NATO command center South Limburg. Payment: 2000 EUR BTC. Deliver reconnaissance photos.",
         "bounty_offer",
         2000.0, "EUR", "bc1q...limburg", "military_base", "Zuid-Limburg, NL",
         None, None, 0.6, "suspected", 49, 0.6, "Temporal correlation with Nov 8 Zuid-Limburg incident (24h before)"),
    ]

    for post in posts:
        try:
            cursor.execute("""
                INSERT INTO social_media_posts
                (platform, channel_name, channel_id, post_id, post_url, author_id, post_date,
                 content, content_type, payment_amount, payment_currency, crypto_wallet_address,
                 target_type, target_location, screenshot_url, archived_url, credibility_score,
                 verification_status, linked_incident_id, correlation_confidence, correlation_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, post)
        except sqlite3.IntegrityError:
            pass

    # Sample crypto transaction
    transactions = [
        ("Bitcoin", "abc123def456...", "bc1q_sender_example", "bc1q...limburg",
         0.0456, "BTC", 2100.0, "2025-11-07 20:30:00",
         1, None, "payment_for_incident", 3, 49, 812345, 6, "https://blockchain.info/tx/abc123",
         "Suspicious BTC transfer 18h before Zuid-Limburg incident. Amount matches bounty offer."),
    ]

    for tx in transactions:
        try:
            cursor.execute("""
                INSERT INTO crypto_transactions
                (blockchain, transaction_hash, from_address, to_address, amount, currency,
                 usd_value, transaction_date, sender_actor_id, recipient_actor_id, purpose,
                 linked_post_id, linked_incident_id, block_number, confirmation_count,
                 source_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tx)
        except sqlite3.IntegrityError:
            pass

    # Actor relationships
    relationships = [
        (2, 3, "collaborator", 0.9, "2022-03-01", "2025-10-15",
         "Both Telegram channels coordinate operations. GRU APT28 tools found on victims whose data leaked on both channels within 24h.",
         "XakNet Team and CyberArmy coordination confirmed by Google Threat Intelligence"),
    ]

    for rel in relationships:
        try:
            cursor.execute("""
                INSERT INTO actor_relationships
                (actor1_id, actor2_id, relationship_type, confidence_score, first_observed,
                 last_observed, evidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rel)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

    print("\n✓ Added sample SOCMINT data:")
    print("  - 4 threat actors")
    print("  - 3 Telegram posts (bounty offers)")
    print("  - 1 crypto transaction")
    print("  - 1 actor relationship")

if __name__ == "__main__":
    print("🔍 Adding Social Media Intelligence (SOCMINT) Layer")
    print("=" * 60)
    print("\n1. Creating database tables...")
    create_socmint_tables()

    print("\n2. Adding sample OSINT data...")
    add_sample_data()

    print("\n✓ SOCMINT layer complete!")
    print("\nThis enables 'connecting the dots':")
    print("  📱 Telegram posts → 💰 Bitcoin payments → 🚁 Drone incidents")
