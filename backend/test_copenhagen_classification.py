"""
Test Classification: Copenhagen September 22, 2025
Incident ID: 20
"""

import sys
sys.path.insert(0, '/Users/marcel/MarLLM/drone-cuas-osint-dashboard')

from backend.classification import classify_incident, analyze_for_telegram_correlation
import sqlite3

def analyze_copenhagen():
    """Analyze Copenhagen Sept 22 incident"""

    # Fetch incident from database
    conn = sqlite3.connect('data/drone_cuas.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, title, sighting_date, drone_description, description,
            altitude_m, estimated_altitude_m, sighting_time, duration_minutes,
            suspected_operator, lights_observed, flight_pattern, time_of_day
        FROM incidents
        WHERE id = 20
    """)

    incident = cursor.fetchone()

    if not incident:
        print("❌ Incident #20 not found!")
        return

    (id, title, sighting_date, drone_description, description, altitude_m,
     estimated_altitude_m, sighting_time, duration_minutes, suspected_operator,
     lights_observed, flight_pattern, time_of_day) = incident

    print("=" * 80)
    print(f"INCIDENT ANALYSIS: #{id}")
    print("=" * 80)
    print(f"Title: {title}")
    print(f"Date: {sighting_date}")
    print(f"Drone: {drone_description}")
    print(f"\nDescription:\n{description}")
    print("\n" + "=" * 80)

    # Current data
    print("\nCURRENT DATA AVAILABLE:")
    print(f"- Lights observed: {lights_observed}")
    print(f"- Altitude: {altitude_m}m (estimated: {estimated_altitude_m}m)")
    print(f"- Flight pattern: {flight_pattern}")
    print(f"- Time of day: {time_of_day}")
    print(f"- Duration: {duration_minutes} minutes")
    print(f"- Suspected operator: {suspected_operator}")

    # Run classification
    classification, confidence, reasoning = classify_incident(
        lights_observed=lights_observed,
        drone_description=drone_description,
        altitude_m=altitude_m,
        estimated_altitude_m=estimated_altitude_m,
        flight_pattern=flight_pattern,
        time_of_day=time_of_day,
        sighting_time=sighting_time,
        duration_minutes=duration_minutes,
        description=description,
        suspected_operator=suspected_operator
    )

    print("\n" + "=" * 80)
    print("CLASSIFICATION RESULT:")
    print("=" * 80)
    print(f"Classification: {classification}")
    print(f"Confidence: {confidence * 100:.1f}%")
    print(f"\nReasoning:\n{reasoning}")

    # Analysis based on description
    print("\n" + "=" * 80)
    print("MANUAL ANALYSIS FROM DESCRIPTION:")
    print("=" * 80)

    findings = []

    # Check for coordination
    if "coordinated" in description.lower():
        findings.append("✓ COORDINATED OPERATION - Multiple sites simultaneously")
        findings.append("  → Suggests professional command & control")

    # Check for scale
    if "major" in description.lower() or "multiple" in description.lower():
        findings.append("✓ LARGE-SCALE OPERATION - Multiple airports + military bases")
        findings.append("  → Beyond capability of single amateur")

    # Check for drone size
    if "large drones" in description.lower():
        findings.append("✓ LARGE DRONES - Not consumer DJI models")
        findings.append("  → Likely military-grade or custom-built")

    # Check for disruption
    if "disruption" in description.lower() or "ban" in description.lower():
        findings.append("✓ SIGNIFICANT DISRUPTION - National drone ban triggered")
        findings.append("  → Strategic objective achieved")

    # Check target types
    if "military bases" in description.lower():
        findings.append("✓ MILITARY TARGETS - Skrydstrup, Karup, Holstebro bases")
        findings.append("  → Primary intelligence objective")

    for finding in findings:
        print(finding)

    # Hypothetical scenario analysis
    print("\n" + "=" * 80)
    print("SCENARIO ANALYSIS:")
    print("=" * 80)

    print("\n🎯 SCENARIO 1: BOUNTY_AMATEUR (Multiple Recruited Locals)")
    print("   Hypothesis: Telegram bounty post Aug/Sept 2025 → €1500 per airport")
    print("   Evidence needed:")
    print("   - Search Telegram for 'Copenhagen airport surveillance' posts")
    print("   - Check if lights were ON (witnesses would mention)")
    print("   - Verify drone types (DJI consumer models?)")
    print("   - Timeline: Post date + 14-30 days = Sept 22?")

    print("\n🎖️ SCENARIO 2: STATE_ACTOR_PROFESSIONAL (Russian Military)")
    print("   Hypothesis: Coordinated reconnaissance/disruption operation")
    print("   Evidence:")
    print("   ✓ 'Coordinated hybrid operation' (description)")
    print("   ✓ Multiple simultaneous sites (5 airports + 3 military bases)")
    print("   ✓ 'Large drones' (not consumer)")
    print("   ✓ Triggered national drone ban (strategic impact)")
    print("   ✓ Targeted military bases (intelligence objective)")
    print("   Missing:")
    print("   - Lights ON/OFF observation")
    print("   - Exact altitude")
    print("   - Flight patterns")

    print("\n💡 RECOMMENDED NEXT STEPS:")
    print("1. Search Danish news for 'drone lights' or 'drone sightings details'")
    print("2. Search Telegram for Copenhagen/Denmark bounty posts (Aug-Sept 2025)")
    print("3. Contact Danish authorities for technical details")
    print("4. Check ADS-B/radar data if available")
    print("5. Cross-reference with other Nordic incidents (pattern?)")

    conn.close()

if __name__ == "__main__":
    analyze_copenhagen()
