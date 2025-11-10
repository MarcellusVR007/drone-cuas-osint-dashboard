#!/usr/bin/env python3
"""
Add Belgian airports to restricted areas database
"""
import requests

API_BASE = "http://localhost:8000/api"

airports = [
    {
        "name": "Brussels Airport (Zaventem)",
        "area_type": "airport",
        "latitude": 50.9014,
        "longitude": 4.4844,
        "radius_km": 5.0,
        "country": "BE",
        "threat_level": 5,
        "description": "Belgium - International Airport"
    },
    {
        "name": "Liège Airport",
        "area_type": "airport",
        "latitude": 50.6378,
        "longitude": 5.4490,
        "radius_km": 5.0,
        "country": "BE",
        "threat_level": 4,
        "description": "Belgium - International Airport (Cargo Hub)"
    }
]

for airport in airports:
    try:
        response = requests.post(f"{API_BASE}/restricted-areas/", json=airport)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Added: {airport['name']} (ID: {result['id']})")
    except Exception as e:
        print(f"✗ Failed to add {airport['name']}: {e}")
