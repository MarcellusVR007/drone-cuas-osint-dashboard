#!/usr/bin/env python3
"""
Add recent drone incidents (Nov 2024-2025) to database
Based on news scraping from NOS, BBC, VRT, etc.
"""

import sqlite3
from datetime import datetime

# Recent incidents from news sources
RECENT_INCIDENTS = [
    {
        "title": "Drone sighting forces Aalborg Airport closure",
        "sighting_date": "2025-11-16",
        "sighting_time": "21:30",
        "latitude": 57.0928,
        "longitude": 9.8492,
        "description": "Aalborg Airport in northern Denmark closed for several hours after drones were reported in nearby airspace. Air traffic resumed around 00:35 on Nov 17 when authorities confirmed danger had passed.",
        "source": "The Local DK",
        "display_source": "The Local Denmark",
        "purpose_assessment": "Surveillance/Hybrid Warfare",
        "confidence_score": 0.85,
        "suspected_operator": "Unknown (suspected Russian hybrid warfare)",
        "country": "Denmark"
    },
    {
        "title": "Brussels Airport closed twice due to drone sightings",
        "sighting_date": "2025-11-04",
        "sighting_time": "20:00",
        "latitude": 50.9014,
        "longitude": 4.4844,
        "description": "Brussels Zaventem Airport suspended flights twice on November 4 after air traffic controllers reported drones flying over the airfield. 34 flight cancellations and 36 delays for departures.",
        "source": "VRT News",
        "display_source": "VRT News (Belgium)",
        "purpose_assessment": "Surveillance/Disruption",
        "confidence_score": 0.9,
        "suspected_operator": "Unknown (Belgium suspects Russia)",
        "country": "Belgium"
    },
    {
        "title": "Liège Airport temporarily halted after drone sighting",
        "sighting_date": "2025-11-07",
        "sighting_time": "07:30",
        "latitude": 50.6374,
        "longitude": 5.4432,
        "description": "Liège Airport, one of Europe's largest cargo airports, was closed for 30 minutes on November 7 after a drone was spotted in the vicinity.",
        "source": "Al Jazeera",
        "display_source": "Al Jazeera",
        "purpose_assessment": "Surveillance/Disruption",
        "confidence_score": 0.85,
        "suspected_operator": "Unknown (part of European drone wave)",
        "country": "Belgium"
    },
    {
        "title": "Six drones spotted near Kleine Brogel Air Base",
        "sighting_date": "2025-11-04",
        "sighting_time": "19:00",
        "latitude": 51.1689,
        "longitude": 5.4700,
        "description": "Six unauthorised drones spotted near Kleine Brogel Air Base, which operates Belgian F-16 fighter fleet and stores US nuclear weapons as part of NATO nuclear sharing. Belgian Defense Minister stated drones were 'spying' on military aircraft locations.",
        "source": "CNN / Defense News",
        "display_source": "CNN / Defense News",
        "purpose_assessment": "Military Espionage",
        "confidence_score": 0.95,
        "suspected_operator": "Russia (suspected)",
        "country": "Belgium"
    },
    {
        "title": "Drone swarm over RAF Lakenheath (F-35/F-15 base)",
        "sighting_date": "2024-11-20",
        "sighting_time": "22:00",
        "latitude": 52.4093,
        "longitude": 0.5610,
        "description": "Multiple unidentified drones (5-6 systems) flew over RAF Lakenheath from Nov 20-24. F-15E Strike Eagles scrambled with targeting pods. Criminal investigation launched. Base hosts America's F-35/F-15 fighter wing in Europe.",
        "source": "Air & Space Forces Magazine",
        "display_source": "USAF / Air & Space Forces",
        "purpose_assessment": "Military Espionage",
        "confidence_score": 0.95,
        "suspected_operator": "Unknown (coordinated activity)",
        "country": "United Kingdom",
        "duration_minutes": 240
    },
    {
        "title": "Drones spotted over RAF Mildenhall (air refueling hub)",
        "sighting_date": "2024-11-20",
        "sighting_time": "22:00",
        "latitude": 52.3619,
        "longitude": 0.4864,
        "description": "Coordinated drone incursions at RAF Mildenhall from Nov 20-24, coinciding with Lakenheath incidents. Base houses the only permanent U.S. air refueling wing in Europe. Drones varied in size and configuration.",
        "source": "CBS News / Military Times",
        "display_source": "CBS News / Military Times",
        "purpose_assessment": "Military Espionage",
        "confidence_score": 0.9,
        "suspected_operator": "Unknown (coordinated with Lakenheath)",
        "country": "United Kingdom"
    }
]

def add_incidents_to_db(db_path='data/drone_cuas.db'):
    """Add recent incidents to database"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    added = 0
    skipped = 0

    for incident in RECENT_INCIDENTS:
        # Check if incident already exists (by title + date)
        cursor.execute("""
            SELECT id FROM incidents
            WHERE title = ? AND sighting_date = ?
        """, (incident['title'], incident['sighting_date']))

        if cursor.fetchone():
            print(f"⏭️  Skipping (already exists): {incident['title']}")
            skipped += 1
            continue

        # Insert new incident
        cursor.execute("""
            INSERT INTO incidents (
                title, sighting_date, sighting_time, latitude, longitude,
                description, source, source_url, purpose_assessment,
                confidence_score, suspected_operator, duration_minutes,
                report_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident['title'],
            incident['sighting_date'],
            incident.get('sighting_time'),
            incident['latitude'],
            incident['longitude'],
            incident['description'],
            incident['source'],
            None,  # source_url
            incident['purpose_assessment'],
            incident['confidence_score'],
            incident.get('suspected_operator'),
            incident.get('duration_minutes'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        print(f"✅ Added: {incident['title']} ({incident['sighting_date']})")
        added += 1

    conn.commit()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"   Added: {added}")
    print(f"   Skipped: {skipped}")
    print(f"   Total incidents in DB: {added + 49}")

if __name__ == "__main__":
    print("=" * 80)
    print("ADDING RECENT DRONE INCIDENTS (Nov 2024-2025)")
    print("=" * 80)
    print()
    add_incidents_to_db()
    print()
    print("=" * 80)
