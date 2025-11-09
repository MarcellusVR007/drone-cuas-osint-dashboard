#!/usr/bin/env python3
"""
Clean up dead and non-EU links from incidents
"""
from backend.database import SessionLocal
from backend.models import Incident

# Dead link IDs from check_links.py
DEAD_LINK_IDS = [1, 2, 4, 6, 8, 9, 10, 12, 13, 14, 15, 20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32, 34]
NON_EU_IDS = [5]  # Washington Post

def main():
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("CLEANING UP DEAD AND NON-EU LINKS")
        print("="*80 + "\n")

        # Remove non-EU sources (Washington Post)
        for incident_id in NON_EU_IDS:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
            if incident:
                print(f"🗑️  Removing non-EU source (ID {incident_id}): {incident.source_url}")
                incident.source_url = None
                db.add(incident)

        # Set dead links to NULL (keep incidents but no clickable link)
        for incident_id in DEAD_LINK_IDS:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
            if incident:
                print(f"💀 Removing dead link (ID {incident_id}): {incident.source_url[:60]}...")
                incident.source_url = None
                db.add(incident)

        db.commit()

        # Report
        print("\n" + "="*80)
        print(f"✅ Removed {len(NON_EU_IDS)} non-EU sources")
        print(f"💀 Set {len(DEAD_LINK_IDS)} dead links to NULL")
        print(f"📊 Total: {len(NON_EU_IDS) + len(DEAD_LINK_IDS)} links cleaned")
        print("="*80 + "\n")

        # Check remaining valid links
        incidents_with_links = db.query(Incident).filter(
            Incident.source_url != None,
            Incident.source_url != ''
        ).count()

        print(f"✅ Valid links remaining: {incidents_with_links}/34 incidents")
        print(f"📝 Incidents without links: {34 - incidents_with_links}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
