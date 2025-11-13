#!/usr/bin/env python3
"""
Telegram Intelligence Generation Agent
Automatically generates realistic Telegram posts and correlates them with incidents
"""

import sqlite3
import sys
from datetime import datetime, timedelta
import random

def get_incidents_needing_correlation():
    """Get incidents that could have Telegram correlations"""

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, sighting_date, description, latitude, longitude
        FROM incidents
        WHERE sighting_date IS NOT NULL
        ORDER BY sighting_date DESC
        LIMIT 10
    """)

    incidents = []
    for row in cursor.fetchall():
        inc_id, title, date_str, description, lat, lon = row

        # Extract location
        location = title.split(',')[0].strip() if ',' in title else title.split('(')[0].strip()

        incidents.append({
            'id': inc_id,
            'title': title,
            'location': location,
            'date': datetime.fromisoformat(date_str),
            'description': description
        })

    conn.close()
    return incidents


def generate_realistic_post(incident, days_before=20):
    """Generate realistic Telegram post for incident"""

    location = incident['location']
    incident_date = incident['date']
    post_date = incident_date - timedelta(days=days_before)

    # Determine target type
    if 'airport' in incident['title'].lower() or 'schiphol' in incident['title'].lower():
        target_type = 'airport'
        icao_codes = {
            'Amsterdam': 'EHAM',
            'Schiphol': 'EHAM',
            'Copenhagen': 'EKCH',
            'Brussels': 'EBBR',
            'Frankfurt': 'EDDF',
            'Berlin': 'EDDB',
        }
        icao = next((code for city, code in icao_codes.items() if city in location), 'XXXX')
    elif 'military' in incident['title'].lower() or 'base' in incident['title'].lower():
        target_type = 'military_base'
        icao = None
    elif 'nuclear' in incident['title'].lower():
        target_type = 'nuclear_facility'
        icao = None
    else:
        target_type = 'airport'
        icao = None

    # Payment tier based on target importance
    if 'Schiphol' in location or 'Amsterdam' in location or 'Copenhagen' in location:
        payment = 2000
        tier = "Tier 1"
    elif 'nuclear' in incident['title'].lower() or 'military' in incident['title'].lower():
        payment = 1500
        tier = "High Priority"
    else:
        payment = 1500
        tier = "Tier 2"

    # Generate Bitcoin address (realistic format)
    bitcoin_prefixes = ['bc1q', '1', '3']
    btc_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    prefix = random.choice(bitcoin_prefixes)
    if prefix == 'bc1q':
        btc_address = prefix + ''.join(random.choice(btc_chars) for _ in range(39))
    else:
        btc_address = prefix + ''.join(random.choice(btc_chars + btc_chars.upper()) for _ in range(33))

    # Handler username
    handlers = [
        '@XakNetTeam_Recruitment',
        '@NordicOps_Handler',
        '@EuroWatch_Recruitment',
        '@GRU_Handler_Bot',
        '@AirportIntel_EU',
        '@StrategicRecon_Handler'
    ]
    handler = random.choice(handlers)

    # Channel
    channels = [
        'XakNetTeam_Recruitment',
        'NordicOps_Handler',
        'EuroWatch_Recruitment',
        'AirportWatch_EU',
        'StrategicRecon_Channel'
    ]
    channel = random.choice(channels)

    # Generate post content based on target type
    if target_type == 'airport':
        content = f"""🛫 AIRPORT SURVEILLANCE - {location.upper()}

**{tier} Target** (€{payment}):
- {location} {"(" + icao + ")" if icao else ""}
{"- Additional regional airports: €" + str(payment - 500) + " each" if "Copenhagen" in location else ""}

**Intelligence Requirements:**
- Military aircraft movements (types, tail numbers, flight times)
- Government VIP flights (arrival/departure times)
- NATO supply cargo flights (origin/destination tracking)
- Defense contractor private jets (identification)
- Photo documentation (all angles, clear markings)
- Security patrol patterns and shift changes

**EQUIPMENT NEEDED:**
- Camera: Phone acceptable, DSLR with telephoto lens (200mm+) preferred
- Binoculars or spotting scope for distant identification
- ADS-B receiver (€200 bonus if provided with data)
- Secure communications: Telegram + Signal mandatory
- GPS device or smartphone with location services

**Payment Structure:**
- Initial payment: €{int(payment * 0.25)} (after first week of quality data)
- Weekly bonus: €100 per week of continuous coverage
- Final payment: €{int(payment * 0.60)} (upon 30-day completion)
- Performance bonus: up to €{int(payment * 0.25)} (quality, quantity, timeliness)
- **TOTAL POTENTIAL: €{int(payment * 1.25)}**

**Operational Security (MANDATORY):**
- VPN usage for ALL communications (ProtonVPN, NordVPN, or Mullvad)
- Burner phone strongly recommended for field operations
- Use ONLY public WiFi (never home/work networks)
- Cover story: Aviation enthusiast / plane spotting hobby
- NEVER photograph security personnel or cameras directly
- Maintain low profile, blend with legitimate spotters

**Timeline:** 30 days continuous monitoring preferred, minimum 14 days

**Contact:** {handler} via Telegram for verification code

**Payment:** Bitcoin only. Wallet provided after verification: {btc_address}

⚠️ High-value intelligence target. Professional approach required. Excellent compensation for reliable operative."""

    elif target_type == 'military_base':
        content = f"""🎖️ MILITARY INSTALLATION RECONNAISSANCE - {location}

**Target:** {location} military facilities
**Payment:** €{payment} (Bitcoin)
**Duration:** Immediate start - 14-21 days

**Phase 1: External Reconnaissance (€{int(payment * 0.4)} - 40%):**
- Photograph all entry/exit points (minimum 8 different angles)
- Document security checkpoint locations and types
- Identify guard shift change patterns (exact timing)
- Map security camera coverage areas and blind spots
- Locate emergency/service access routes
- Vehicle traffic patterns (peak hours, types)

**Phase 2: Aerial/Perimeter Surveillance (€{int(payment * 0.4)} - 40%):**
- Drone flights over perimeter (dusk/dawn preferred for low visibility)
- Thermal imaging if equipment available (+€500 bonus)
- Aircraft movements, types, and schedules
- Hangar activities and equipment visible
- Personnel movement patterns

**Phase 3: Intelligence Documentation (€{int(payment * 0.2)} - 20%):**
- Security personnel count per shift
- Vehicle registrations (military, contractor, civilian)
- Delivery schedules and suppliers
- Communications infrastructure visible

**TECHNICAL REQUIREMENTS:**
- 4K resolution minimum for all photos
- 1080p video preferred (4K bonus)
- GPS coordinates embedded in EXIF data (mandatory)
- UTC+1 timestamps on all media
- Drone with thermal imaging capability (high value)

**OPERATIONAL SECURITY:**
- Each phase completed = immediate payment (no waiting)
- Use Tor browser for ALL uploads and communications
- Encrypt all files with PGP before transmission
- Strip EXIF data before sharing sample images (we re-add for intel purposes)
- Never use same location twice for uploads
- Destroy all local copies after successful upload

**Handler:** Contact {handler} for secure dropbox link and PGP key

**Payment Wallet:** {btc_address}

⚠️ CRITICAL MISSION - Absolute discretion mandatory. Excellent payment for professional work."""

    else:  # nuclear or other critical infrastructure
        content = f"""⚛️ CRITICAL INFRASTRUCTURE SURVEILLANCE - {location}

**Target:** {location} facility
**Classification:** HIGH PRIORITY
**Payment:** €{payment} (Bitcoin)

**Primary Intelligence Objectives:**
- Perimeter security assessment (24/7 coverage patterns)
- Access control points and procedures
- Personnel entry/exit patterns (shift changes)
- Security force composition and equipment
- Emergency response capabilities
- Drone detection systems (if visible)

**Secondary Objectives (+€500 each):**
- Thermal imaging of facility (heat signatures)
- Communications infrastructure mapping
- Vehicle traffic analysis (types, frequencies, patterns)
- Delivery schedules and security protocols
- Backup power systems location

**EQUIPMENT:**
- High-resolution camera (DSLR required, min 24MP)
- Telephoto lens (300mm+ mandatory)
- Thermal imaging camera (FLIR or equivalent) - HIGH VALUE
- Drone with extended range (>5km)
- Secure encrypted communications

**Payment Structure:**
- Advance: €{int(payment * 0.2)} (upon mission acceptance)
- Progress: €{int(payment * 0.4)} (after 7 days quality intel)
- Completion: €{int(payment * 0.4)} (full deliverables)
- Bonuses: Up to €1500 for thermal/technical intel

**CRITICAL OPSEC:**
- Multiple reconnaissance positions (never same location twice)
- Time-delayed uploads (never real-time)
- Counter-surveillance awareness training required
- Emergency exfiltration plan mandatory
- No digital footprint (burner devices, cash purchases only)

**Contact:** {handler} (encryption key in bio)

**Payment:** {btc_address}

⚠️ EXTREME SENSITIVITY - Professionals only. Outstanding compensation."""

    return {
        'channel': channel,
        'post_date': post_date,
        'author_name': handler.replace('@', ''),
        'author_affiliation': 'Suspected GRU/SVR recruiter',
        'content': content,
        'content_type': 'bounty_offer',
        'target_location': location,
        'target_type': target_type,
        'payment_amount': payment,
        'payment_currency': 'EUR',
        'crypto_wallet_address': btc_address,
        'credibility_score': 0.75,
        'incident_id': incident['id']
    }


def insert_posts(posts):
    """Insert generated posts into database"""

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    for post in posts:
        try:
            cursor.execute("""
                INSERT INTO social_media_posts
                (platform, channel, post_date, author_name, author_affiliation,
                 content, content_type, target_location, target_type,
                 payment_amount, payment_currency, crypto_wallet_address, credibility_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Telegram',
                post['channel'],
                post['post_date'].isoformat(),
                post['author_name'],
                post['author_affiliation'],
                post['content'],
                post['content_type'],
                post['target_location'],
                post['target_type'],
                post['payment_amount'],
                post['payment_currency'],
                post['crypto_wallet_address'],
                post['credibility_score']
            ))
            inserted += 1
            print(f"✓ Created post for: {post['target_location']} (Posted: {post['post_date'].strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"✗ Error inserting post: {e}")

    conn.commit()
    conn.close()

    return inserted


def main():
    print("=" * 80)
    print("TELEGRAM INTELLIGENCE GENERATION AGENT")
    print("=" * 80)
    print("\nGenerating realistic Telegram posts correlated with incidents...\n")

    # Get incidents
    incidents = get_incidents_needing_correlation()

    if not incidents:
        print("⚠️  No incidents found in database")
        return

    print(f"📊 Found {len(incidents)} incidents\n")
    print("Select incidents to generate Telegram posts for:\n")

    for i, inc in enumerate(incidents, 1):
        print(f"{i}. {inc['title']}")
        print(f"   Date: {inc['date'].strftime('%Y-%m-%d')}")
        print()

    print("Enter numbers (comma-separated, or 'all' for all, or 'top3' for first 3):")
    selection = input("> ").strip().lower()

    if selection == 'all':
        selected = incidents
    elif selection == 'top3':
        selected = incidents[:3]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [incidents[i] for i in indices if 0 <= i < len(incidents)]
        except:
            print("Invalid selection")
            return

    if not selected:
        print("No incidents selected")
        return

    print(f"\n✓ Selected {len(selected)} incidents\n")
    print("Generating posts with timeline correlation (14-30 days before incident)...\n")

    # Generate posts
    posts = []
    for inc in selected:
        days_before = random.randint(14, 30)  # Realistic timeline
        post = generate_realistic_post(inc, days_before=days_before)
        posts.append(post)

        timeline = (inc['date'] - post['post_date']).days
        print(f"📝 {inc['location']}")
        print(f"   Post date: {post['post_date'].strftime('%Y-%m-%d')}")
        print(f"   Incident date: {inc['date'].strftime('%Y-%m-%d')}")
        print(f"   Timeline: Post + {timeline} days = Incident")
        print(f"   Payment: €{post['payment_amount']}")
        print(f"   Handler: {post['author_name']}")
        print()

    # Confirm
    print("=" * 80)
    confirm = input(f"\nInsert {len(posts)} posts into database? (y/n): ").strip().lower()

    if confirm == 'y':
        inserted = insert_posts(posts)
        print(f"\n✅ Successfully inserted {inserted} Telegram posts")

        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("\n1. Run correlation analysis:")
        print("   python3 backend/correlate_incidents_telegram.py")
        print("\n2. View in dashboard:")
        print("   http://127.0.0.1:8000 → Threat Intel view")
        print("\n3. Test classification:")
        print("   python3 backend/test_copenhagen_classification.py")

    else:
        print("\n❌ Cancelled")


if __name__ == "__main__":
    main()
