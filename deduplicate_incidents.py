#!/usr/bin/env python3
"""
Remove duplicate incidents from the database.
Keep only one incident per location per day (the one with highest confidence score).
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def deduplicate_incidents():
    """Remove duplicate incidents, keeping the best one per location per day"""
    db_path = Path("data/drone_cuas.db")

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all duplicate groups (same date + location)
    cursor.execute("""
        SELECT
            sighting_date,
            latitude,
            longitude,
            COUNT(*) as duplicates,
            GROUP_CONCAT(id, ',') as incident_ids
        FROM incidents
        GROUP BY sighting_date, latitude, longitude
        HAVING COUNT(*) > 1
        ORDER BY duplicates DESC
    """)

    duplicate_groups = cursor.fetchall()

    if not duplicate_groups:
        print("✓ No duplicates found!")
        return

    print(f"Found {len(duplicate_groups)} duplicate groups")
    total_to_delete = 0

    for group in duplicate_groups:
        sighting_date = group['sighting_date']
        latitude = group['latitude']
        longitude = group['longitude']
        incident_ids = [int(x.strip()) for x in group['incident_ids'].split(',')]

        # Get full details for all incidents in this group
        placeholders = ','.join(['?' for _ in incident_ids])
        cursor.execute(f"""
            SELECT
                id,
                title,
                confidence_score,
                description,
                details,
                source
            FROM incidents
            WHERE id IN ({placeholders})
        """, incident_ids)

        incidents = cursor.fetchall()

        # Sort by confidence score (descending), then by completeness
        def score_incident(inc):
            score = float(inc['confidence_score'] or 0)
            # Bonus for having description and details
            if inc['description']:
                score += 0.1
            if inc['details']:
                score += 0.1
            return score

        sorted_incidents = sorted(incidents, key=score_incident, reverse=True)

        # Keep the best one, delete the rest
        keep_id = sorted_incidents[0]['id']
        delete_ids = [inc['id'] for inc in sorted_incidents[1:]]

        print(f"\n📍 {sighting_date} at ({latitude}, {longitude})")
        print(f"  Keeping: ID {keep_id} - {sorted_incidents[0]['title'][:50]}")
        print(f"  Deleting {len(delete_ids)} duplicates: {delete_ids}")

        # Delete duplicates
        for del_id in delete_ids:
            cursor.execute("DELETE FROM incidents WHERE id = ?", (del_id,))
            total_to_delete += 1

    conn.commit()

    # Get new count
    cursor.execute("SELECT COUNT(*) FROM incidents")
    new_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n✓ Deduplication complete!")
    print(f"  Deleted: {total_to_delete} duplicate incidents")
    print(f"  Remaining: {new_count} unique incidents")

    return total_to_delete

if __name__ == "__main__":
    deleted = deduplicate_incidents()

    if deleted and deleted > 0:
        print("\n⚠️  Remember to run: python3 export_data.py")
        print("   to update the JSON export with cleaned data!")
