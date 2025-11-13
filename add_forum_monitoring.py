#!/usr/bin/env python3
"""
Aviation Forum Monitoring System
Counter-intelligence to detect GRU-recruited spotters infiltrating aviation forums.
Based on OPSEC instructions found in XakNet Telegram recruitment posts.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def add_forum_monitoring_schema():
    """Add forum monitoring tables"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("👁️ Adding Forum Monitoring Schema...")

    # Monitored forums table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitored_forums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            url VARCHAR(500) NOT NULL,
            platform VARCHAR(100),
            focus_area VARCHAR(255),
            member_count INTEGER,
            mentions_in_opsec_docs BOOLEAN DEFAULT 0,
            threat_level VARCHAR(50),
            last_scraped DATETIME,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created monitored_forums table")

    # Suspicious forum accounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suspicious_forum_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forum_id INTEGER NOT NULL,
            username VARCHAR(255) NOT NULL,
            account_created DATETIME,
            location VARCHAR(255),
            profile_description TEXT,
            post_count INTEGER DEFAULT 0,
            photo_count INTEGER DEFAULT 0,
            suspicious_score FLOAT DEFAULT 0,
            red_flags TEXT,
            first_detected DATETIME,
            last_activity DATETIME,
            telegram_link VARCHAR(255),
            ip_address VARCHAR(50),
            device_info TEXT,
            investigation_status VARCHAR(50) DEFAULT 'monitoring',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(forum_id) REFERENCES monitored_forums(id)
        )
    """)
    print("  ✓ Created suspicious_forum_accounts table")

    # Suspicious posts/photos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suspicious_forum_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            forum_id INTEGER NOT NULL,
            content_type VARCHAR(50),
            post_date DATETIME NOT NULL,
            title VARCHAR(500),
            content TEXT,
            photo_url VARCHAR(500),
            exif_data TEXT,
            location_mentioned VARCHAR(255),
            target_airport_id INTEGER,
            red_flags TEXT,
            risk_score FLOAT DEFAULT 0,
            linked_to_incident_id INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES suspicious_forum_accounts(id),
            FOREIGN KEY(forum_id) REFERENCES monitored_forums(id),
            FOREIGN KEY(target_airport_id) REFERENCES restricted_areas(id),
            FOREIGN KEY(linked_to_incident_id) REFERENCES incidents(id)
        )
    """)
    print("  ✓ Created suspicious_forum_content table")

    # Behavioral patterns (red flags library)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum_red_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category VARCHAR(100) NOT NULL,
            flag_name VARCHAR(255) NOT NULL,
            description TEXT,
            weight FLOAT DEFAULT 1.0,
            detection_pattern TEXT,
            examples TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created forum_red_flags table")

    conn.commit()
    conn.close()
    print("\n✓ Forum monitoring schema created!")

def populate_monitored_forums():
    """Add forums mentioned in GRU OPSEC docs"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n📋 Populating Monitored Forums...")

    forums = [
        # Mentioned in XakNet recruitment post
        {
            "name": "PPRuNe (Professional Pilots Rumour Network)",
            "url": "https://www.pprune.org/",
            "platform": "phpBB",
            "focus_area": "Aviation professionals, military spotting",
            "member_count": 500000,
            "mentions_in_opsec_docs": 1,
            "threat_level": "HIGH",
            "notes": "Explicitly mentioned in XakNet Telegram post as cover story forum. 'Mention aviation forums (PPRuNe, Airliners.net)'. High-value target for recruitment."
        },
        {
            "name": "Airliners.net",
            "url": "https://www.airliners.net/",
            "platform": "Custom",
            "focus_area": "Aviation photography, spotting",
            "member_count": 1200000,
            "mentions_in_opsec_docs": 1,
            "threat_level": "HIGH",
            "notes": "Explicitly mentioned in XakNet Telegram post. Large photo database provides cover for reconnaissance photos. Easy to blend in."
        },
        {
            "name": "SpottersWiki",
            "url": "https://www.spotterswiki.com/",
            "platform": "MediaWiki",
            "focus_area": "Airport spotting locations, security info",
            "member_count": 50000,
            "mentions_in_opsec_docs": 0,
            "threat_level": "MEDIUM",
            "notes": "Contains detailed airport access info, security blind spots, best spotting locations. Useful for reconnaissance planning."
        },
        {
            "name": "Aviation Stack Exchange",
            "url": "https://aviation.stackexchange.com/",
            "platform": "Stack Exchange",
            "focus_area": "Aviation Q&A, technical questions",
            "member_count": 150000,
            "mentions_in_opsec_docs": 0,
            "threat_level": "LOW",
            "notes": "Technical questions could reveal reconnaissance intent (e.g., 'How to identify military cargo aircraft?', 'What do security patrols look for?')."
        },
        {
            "name": "BelgianSpotters Forum",
            "url": "https://www.belgianspotters.be/",
            "platform": "phpBB",
            "focus_area": "Belgian airports, military spotting",
            "member_count": 8000,
            "mentions_in_opsec_docs": 0,
            "threat_level": "HIGH",
            "notes": "Local forum for Brussels/Belgian airports. High concentration of NATO/EU targets. Small community makes infiltration easier to detect."
        },
        {
            "name": "Scramble.nl (Military Aviation)",
            "url": "https://www.scramble.nl/forum/",
            "platform": "phpBB",
            "focus_area": "Military aviation, NATO bases NL",
            "member_count": 25000,
            "mentions_in_opsec_docs": 0,
            "threat_level": "CRITICAL",
            "notes": "Dutch military aviation forum. Focus on Gilze-Rijen, Volkel, De Kooy bases. Members share detailed military movement info. Prime target for GRU recruitment."
        }
    ]

    for forum in forums:
        cursor.execute("""
            INSERT INTO monitored_forums
            (name, url, platform, focus_area, member_count, mentions_in_opsec_docs, threat_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            forum["name"], forum["url"], forum["platform"], forum["focus_area"],
            forum["member_count"], forum["mentions_in_opsec_docs"],
            forum["threat_level"], forum["notes"]
        ))

    conn.commit()
    print(f"  ✓ Added {len(forums)} monitored forums")
    conn.close()

def populate_red_flags():
    """Define behavioral red flags for detection"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🚩 Populating Red Flag Library...")

    red_flags = [
        # Account creation patterns
        {
            "category": "account_creation",
            "flag_name": "New Account Post-Bounty",
            "description": "Account created after Telegram bounty post date",
            "weight": 3.0,
            "detection_pattern": "account_created > bounty_post_date AND account_created < incident_date",
            "examples": "XakNet bounty posted 2025-11-01, account created 2025-11-05, incident 2025-11-08"
        },
        {
            "category": "account_creation",
            "flag_name": "Location Near Target",
            "description": "Profile location within 50km of target airport",
            "weight": 2.5,
            "detection_pattern": "distance(profile_location, target_airport) < 50km",
            "examples": "Profile: 'Amsterdam' → Schiphol target, 'Frankfurt am Main' → Frankfurt Airport"
        },
        {
            "category": "account_creation",
            "flag_name": "Minimal Profile Info",
            "description": "Very sparse profile (no bio, no avatar, minimal posts)",
            "weight": 1.5,
            "detection_pattern": "profile_completeness < 30% AND post_count < 10",
            "examples": "Username only, no location, no intro post, generic avatar"
        },

        # Posting behavior
        {
            "category": "posting_behavior",
            "flag_name": "Enthusiastic But Clueless",
            "description": "Matches OPSEC instruction: 'Act enthusiastic but clueless'",
            "weight": 2.0,
            "detection_pattern": "excessive_exclamation_marks AND basic_questions_ratio > 0.7",
            "examples": "'Wow amazing! How do you identify which plane is which??', 'So cool! What's the best time to spot?'"
        },
        {
            "category": "posting_behavior",
            "flag_name": "Security Infrastructure Focus",
            "description": "Unusual interest in security systems, patrols, cameras",
            "weight": 4.0,
            "detection_pattern": "keywords: ['security', 'patrol', 'camera', 'fence', 'restricted']",
            "examples": "'Are there cameras at the north fence?', 'How often do security patrols come by?'"
        },
        {
            "category": "posting_behavior",
            "flag_name": "Military Cargo Interest",
            "description": "Specific interest in military/cargo flights to Ukraine/Poland",
            "weight": 3.5,
            "detection_pattern": "keywords: ['military', 'cargo', 'Ukraine', 'Poland', 'NATO', 'C-17', 'Antonov']",
            "examples": "'Anyone know the schedule for military cargo flights?', 'What time do the C-17s usually leave?'"
        },
        {
            "category": "posting_behavior",
            "flag_name": "Timing Questions",
            "description": "Questions about schedules, timing, patterns",
            "weight": 2.5,
            "detection_pattern": "keywords: ['schedule', 'timing', 'when', 'how often', 'pattern']",
            "examples": "'What time does the shift change happen?', 'When are the VIP flights usually?'"
        },

        # Photo analysis
        {
            "category": "photo_content",
            "flag_name": "Security Infrastructure in Frame",
            "description": "Photos focusing on security infrastructure rather than planes",
            "weight": 4.5,
            "detection_pattern": "image_analysis: security_objects > aircraft_objects",
            "examples": "Photo of fence/gate with plane in background, camera towers, security vehicles"
        },
        {
            "category": "photo_content",
            "flag_name": "EXIF Location Mismatch",
            "description": "EXIF GPS doesn't match claimed spotting location",
            "weight": 3.0,
            "detection_pattern": "distance(exif_gps, claimed_location) > 5km",
            "examples": "Claims 'Schiphol spotting', EXIF shows coordinates 20km away"
        },
        {
            "category": "photo_content",
            "flag_name": "No EXIF Data",
            "description": "All photos have EXIF stripped (OPSEC instruction compliance)",
            "weight": 2.0,
            "detection_pattern": "exif_data IS NULL FOR ALL photos",
            "examples": "10 photos uploaded, all have EXIF completely removed"
        },
        {
            "category": "photo_content",
            "flag_name": "Unusual Angles",
            "description": "Photos from angles that reveal security blind spots or infrastructure",
            "weight": 3.5,
            "detection_pattern": "manual_review: unusual_perspective = true",
            "examples": "Bird's eye view (drone?), through fence gaps, from suspicious vantage points"
        },

        # Language/writing
        {
            "category": "language",
            "flag_name": "Translation Artifacts",
            "description": "Language patterns suggesting machine translation (Russian→English)",
            "weight": 2.5,
            "detection_pattern": "NLP: translation_probability > 0.7",
            "examples": "'I am very interest in this plane', 'How to make good photograph?'"
        },
        {
            "category": "language",
            "flag_name": "Formal Language",
            "description": "Overly formal/stiff language for casual forum",
            "weight": 1.5,
            "detection_pattern": "formality_score > 0.8 (0-1 scale)",
            "examples": "'I would like to inquire about...', 'Please provide information regarding...'"
        },

        # Temporal patterns
        {
            "category": "temporal",
            "flag_name": "Activity Spike Before Incident",
            "description": "Sudden increase in posting 48-72h before drone incident",
            "weight": 4.0,
            "detection_pattern": "post_frequency(72h_before_incident) > 3x average",
            "examples": "1 post/week normally, 15 posts in 3 days before incident"
        },
        {
            "category": "temporal",
            "flag_name": "Goes Silent Post-Incident",
            "description": "Account goes completely silent after incident",
            "weight": 3.0,
            "detection_pattern": "last_post < incident_date AND days_since_post > 30",
            "examples": "Active until 2025-11-08 incident, then zero posts for 2 months"
        }
    ]

    for flag in red_flags:
        cursor.execute("""
            INSERT INTO forum_red_flags
            (category, flag_name, description, weight, detection_pattern, examples)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            flag["category"], flag["flag_name"], flag["description"],
            flag["weight"], flag["detection_pattern"], flag["examples"]
        ))

    conn.commit()
    print(f"  ✓ Added {len(red_flags)} behavioral red flags")
    conn.close()

def populate_example_suspects():
    """Add example suspicious accounts for demonstration"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🔍 Adding Example Suspicious Accounts...")

    # Get forum IDs
    cursor.execute("SELECT id FROM monitored_forums WHERE name = 'Airliners.net'")
    airliners_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM monitored_forums WHERE name = 'Scramble.nl (Military Aviation)'")
    scramble_id = cursor.fetchone()[0]

    suspects = [
        {
            "forum_id": airliners_id,
            "username": "AvGeek_NL_2025",
            "account_created": "2025-11-03 14:30:00",
            "location": "Amsterdam, Netherlands",
            "profile_description": "New to spotting! Love planes!",
            "post_count": 23,
            "photo_count": 8,
            "suspicious_score": 0.82,
            "red_flags": "New Account Post-Bounty (3.0), Enthusiastic But Clueless (2.0), Security Infrastructure Focus (4.0), Timing Questions (2.5), Activity Spike Before Incident (4.0)",
            "first_detected": "2025-11-05 09:00:00",
            "last_activity": "2025-11-08 18:00:00",
            "telegram_link": None,
            "ip_address": "185.220.101.45 (NL VPN exit node)",
            "device_info": "Windows 10, Chrome 119, NordVPN detected",
            "investigation_status": "high_priority",
            "notes": "Account created 2 days after XakNet airport bounty post. Posted 15 times in 48h before Zuid-Limburg incident, then went silent. Questions focused on Schiphol security patrols. VPN usage suspicious for 'local enthusiast'."
        },
        {
            "forum_id": scramble_id,
            "username": "MilitaryAvFan",
            "account_created": "2025-10-28 11:20:00",
            "location": "Limburg, NL",
            "profile_description": "",
            "post_count": 12,
            "photo_count": 4,
            "suspicious_score": 0.75,
            "red_flags": "Location Near Target (2.5), Minimal Profile Info (1.5), Military Cargo Interest (3.5), EXIF Location Mismatch (3.0), Goes Silent Post-Incident (3.0)",
            "first_detected": "2025-11-01 10:00:00",
            "last_activity": "2025-11-08 16:30:00",
            "telegram_link": None,
            "ip_address": "94.142.241.111 (Ziggo NL, Maastricht region)",
            "device_info": "Android 13, Chrome Mobile",
            "investigation_status": "law_enforcement_referral",
            "notes": "Location matches Zuid-Limburg NATO JFC target. Asked about military cargo schedules at Maastricht Airport. Photo EXIF shows GPS 12km from claimed location. Last post 2h before incident. STRONG SUSPECT - Referred to Dutch AIVD."
        }
    ]

    for suspect in suspects:
        cursor.execute("""
            INSERT INTO suspicious_forum_accounts
            (forum_id, username, account_created, location, profile_description,
             post_count, photo_count, suspicious_score, red_flags, first_detected,
             last_activity, telegram_link, ip_address, device_info, investigation_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suspect["forum_id"], suspect["username"], suspect["account_created"],
            suspect["location"], suspect["profile_description"], suspect["post_count"],
            suspect["photo_count"], suspect["suspicious_score"], suspect["red_flags"],
            suspect["first_detected"], suspect["last_activity"], suspect["telegram_link"],
            suspect["ip_address"], suspect["device_info"], suspect["investigation_status"],
            suspect["notes"]
        ))

    conn.commit()
    print(f"  ✓ Added {len(suspects)} example suspicious accounts")
    conn.close()

if __name__ == "__main__":
    print("👁️ Aviation Forum Monitoring System")
    print("=" * 70)
    print("Counter-intelligence: Detect GRU-recruited spotters")
    print("Based on OPSEC instructions in XakNet Telegram recruitment")
    print("=" * 70)

    add_forum_monitoring_schema()
    populate_monitored_forums()
    populate_red_flags()
    populate_example_suspects()

    print("\n" + "=" * 70)
    print("✓ Complete! Forum monitoring system ready.")
    print("\n📊 What's Monitored:")
    print("  - 6 aviation forums (PPRuNe, Airliners.net, Scramble.nl, etc.)")
    print("  - 15 behavioral red flags (account creation, posting, photos, language)")
    print("  - 2 example suspicious accounts (Zuid-Limburg region)")
    print("\n🔍 Detection Capabilities:")
    print("  - New accounts post-bounty (temporal correlation)")
    print("  - 'Enthusiastic but clueless' behavior (OPSEC compliance)")
    print("  - Security infrastructure focus (reconnaissance intent)")
    print("  - EXIF/location mismatches (OPSEC slip-ups)")
    print("  - Activity spikes before incidents (operational correlation)")
    print("\n🎯 Law Enforcement Value:")
    print("  - IP addresses (VPN detection)")
    print("  - Device fingerprints")
    print("  - Writing style analysis (Russian→English artifacts)")
    print("  - Photo geolocation (EXIF forensics)")
    print("\nReady for frontend forum monitoring dashboard!")
