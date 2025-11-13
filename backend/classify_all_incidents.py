#!/usr/bin/env python3
"""
Classify all incidents in database using the classification algorithm
"""

import sys
sys.path.insert(0, '/Users/marcel/MarLLM/drone-cuas-osint-dashboard')

from backend.classification import classify_incident
import sqlite3

def classify_all():
    """Classify all incidents"""

    db_path = "data/drone_cuas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all incidents
    cursor.execute("""
        SELECT id, title, drone_description, altitude_m, estimated_altitude_m,
               flight_pattern, time_of_day, sighting_time, duration_minutes,
               description, suspected_operator, lights_observed
        FROM incidents
    """)

    incidents = cursor.fetchall()
    print(f"Found {len(incidents)} incidents to classify")
    print("=" * 80)

    classified = 0
    for row in incidents:
        (inc_id, title, drone_desc, altitude, est_altitude, flight_pattern,
         time_of_day, sighting_time, duration, description, suspected_op, lights) = row

        # Run classification
        classification, confidence, reasoning = classify_incident(
            lights_observed=lights,
            drone_description=drone_desc,
            altitude_m=altitude,
            estimated_altitude_m=est_altitude,
            flight_pattern=flight_pattern,
            time_of_day=time_of_day,
            sighting_time=sighting_time,
            duration_minutes=duration,
            description=description,
            suspected_operator=suspected_op
        )

        # Update incident with classification
        cursor.execute("""
            UPDATE incidents
            SET operational_class = ?,
                classification_confidence = ?,
                classification_reasoning = ?
            WHERE id = ?
        """, (classification, confidence, reasoning, inc_id))

        classified += 1
        print(f"✓ Incident #{inc_id}: {classification} ({confidence*100:.0f}%) - {title[:60]}")

    conn.commit()
    conn.close()

    print("=" * 80)
    print(f"✅ Classified {classified} incidents")
    print("\nRefresh the Patterns view in your dashboard to see results!")

if __name__ == "__main__":
    classify_all()
