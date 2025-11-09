#!/usr/bin/env python3
"""
Quick script to add a new drone incident to the OSINT CUAS Dashboard

Usage:
    python3 add_new_incident.py

Interactive prompts will guide you through adding an incident.
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

def get_restricted_areas():
    """Fetch available restricted areas"""
    response = requests.get(f"{API_BASE}/restricted-areas/")
    areas = response.json()
    return areas

def display_areas(areas):
    """Display numbered list of restricted areas"""
    print("\n📍 Available Restricted Areas:")
    print("─" * 80)
    for idx, area in enumerate(areas, 1):
        print(f"{idx}. {area['name']} ({area['country']}) - {area['area_type']}")
    print("─" * 80)

def add_incident():
    """Interactive incident creation"""
    print("\n" + "═" * 80)
    print("  🚁 Add New Drone Incident - OSINT CUAS Dashboard")
    print("═" * 80)

    # Get restricted areas
    areas = get_restricted_areas()
    display_areas(areas)

    # Get user input
    print("\n📝 Enter Incident Details:")
    title = input("Title (e.g., 'Drone over Gilze-Rijen'): ").strip()
    description = input("Description: ").strip()

    # Date
    use_today = input("Use today's date? (y/n): ").lower() == 'y'
    if use_today:
        sighting_date = datetime.now().strftime("%Y-%m-%d")
    else:
        sighting_date = input("Date (YYYY-MM-DD): ").strip()

    # Location
    area_choice = int(input(f"Select restricted area (1-{len(areas)}): "))
    selected_area = areas[area_choice - 1]

    # Coordinates (use area coords by default)
    use_area_coords = input("Use area coordinates? (y/n): ").lower() == 'y'
    if use_area_coords:
        latitude = selected_area['latitude']
        longitude = selected_area['longitude']
    else:
        latitude = float(input("Latitude: "))
        longitude = float(input("Longitude: "))

    # Source info
    print("\n📰 Source Information:")
    source_url = input("Source URL (news article): ").strip()
    primary_source_name = input("Source name (e.g., 'DutchNews.nl'): ").strip()
    primary_source_credibility = int(input("Credibility (1-10): "))

    # Purpose
    print("\n🎯 Assessment:")
    print("Purpose options: reconnaissance, sabotage, disruption, testing, unknown")
    purpose = input("Purpose: ").strip()
    confidence_score = float(input("Confidence (0.0-1.0): "))

    # Build payload
    incident_data = {
        "sighting_date": sighting_date,
        "latitude": latitude,
        "longitude": longitude,
        "restricted_area_id": selected_area['id'],
        "title": title,
        "description": description,
        "source": "news",
        "source_url": source_url,
        "primary_source_name": primary_source_name,
        "primary_source_credibility": primary_source_credibility,
        "purpose_assessment": purpose,
        "confidence_score": confidence_score,
        "suspected_operator": "Unknown",
        "identification_method": "intelligence",
        "identification_confidence": confidence_score,
        "identified_by": primary_source_name
    }

    # Confirm
    print("\n" + "─" * 80)
    print("📋 Incident Summary:")
    print(json.dumps(incident_data, indent=2))
    print("─" * 80)

    confirm = input("\n✅ Create this incident? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        return

    # Submit
    try:
        response = requests.post(f"{API_BASE}/incidents/", json=incident_data)
        response.raise_for_status()
        result = response.json()

        print("\n" + "═" * 80)
        print(f"✅ SUCCESS! Incident #{result['id']} created")
        print(f"🔗 View at: http://localhost:8000 (click incident #{result['id']})")
        print("═" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")

if __name__ == "__main__":
    try:
        add_incident()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
