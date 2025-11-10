#!/usr/bin/env python3
"""
Batch Import Incidents from Scan Report

Automatically imports high-quality incidents from daily scan reports into the dashboard.
Intelligently matches incidents to restricted areas based on keywords in titles.

Usage:
    python3 batch_import_incidents.py data/scan_report_YYYYMMDD_HHMMSS.json
"""

import requests
import json
import sys
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from difflib import SequenceMatcher

API_BASE = "http://localhost:8000/api"

# Location keywords for matching incidents to restricted areas
LOCATION_KEYWORDS = {
    'Brussels Airport': ['brussels airport', 'zaventem', 'bru airport'],
    'Liège Airport': ['liège', 'liege', 'luik'],
    'Doel Nuclear Power Plant': ['doel', 'kerncentrale doel'],
    'Kleine-Brogel Air Base': ['kleine-brogel', 'kleine brogel'],
    'Florennes Air Base': ['florennes'],
    'Amsterdam Schiphol Airport': ['schiphol', 'amsterdam airport'],
    'Berlin Brandenburg Airport': ['berlin airport', 'ber airport', 'brandenburg'],
    'Stockholm Arlanda Airport': ['stockholm airport', 'arlanda'],
    'Madrid-Barajas Airport': ['madrid airport', 'barajas'],
    'Gilze-Rijen Air Base': ['gilze-rijen', 'gilze rijen'],
    'nuclear power plant': ['nuclear', 'kerncentrale', 'centrale nucléaire', 'atomkraftwerk'],
    'military base': ['military base', 'air base', 'militaire basis', 'luchtmachtbasis']
}

def get_restricted_areas() -> List[Dict]:
    """Fetch all restricted areas from API"""
    response = requests.get(f"{API_BASE}/restricted-areas/")
    response.raise_for_status()
    data = response.json()
    return data.get('restricted_areas', [])

def get_existing_incidents(days_back: int = 60) -> List[Dict]:
    """Fetch recent incidents from API for duplicate detection"""
    try:
        response = requests.get(f"{API_BASE}/incidents/?limit=500")
        response.raise_for_status()
        data = response.json()
        all_incidents = data.get('incidents', [])

        # Filter to recent incidents only (last N days)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent = [
            inc for inc in all_incidents
            if datetime.fromisoformat(inc['sighting_date']) >= cutoff_date
        ]

        return recent
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch existing incidents: {e}")
        return []

def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def is_duplicate(new_incident: Dict, existing_incidents: List[Dict], threshold: float = 0.75) -> bool:
    """
    Check if a new incident is a duplicate of existing incidents.

    Criteria for duplicate:
    - Same exact date (day)
    - Same location (same restricted area or within 10km)

    Rule: Maximum 1 incident per day per location
    """
    new_date = datetime.fromisoformat(new_incident['sighting_date']).date()
    new_lat = new_incident['latitude']
    new_lon = new_incident['longitude']
    new_area_id = new_incident.get('restricted_area_id')

    for existing in existing_incidents:
        # Check if same day
        existing_date = datetime.fromisoformat(existing['sighting_date']).date()

        if new_date != existing_date:
            continue  # Different day, not a duplicate

        # Same day - now check location
        # 1. Same restricted area = duplicate
        if new_area_id and existing.get('restricted_area_id') == new_area_id:
            return True

        # 2. Geographic proximity (within ~10km)
        existing_lat = existing.get('latitude', 0)
        existing_lon = existing.get('longitude', 0)

        # Rough distance check (0.1 degree ≈ 11km at equator)
        lat_diff = abs(new_lat - existing_lat)
        lon_diff = abs(new_lon - existing_lon)

        if lat_diff < 0.1 and lon_diff < 0.1:
            return True

    return False

def match_location(title: str, areas: List[Dict]) -> Optional[Dict]:
    """
    Match incident title to a restricted area using keyword matching.
    Returns the best matching area or None.
    """
    title_lower = title.lower()

    # Try exact name matching first
    for area in areas:
        area_name_lower = area['name'].lower()
        if area_name_lower in title_lower or title_lower in area_name_lower:
            return area

    # Try keyword matching
    for area in areas:
        area_name_lower = area['name'].lower()
        for location, keywords in LOCATION_KEYWORDS.items():
            if location.lower() in area_name_lower:
                for keyword in keywords:
                    if keyword in title_lower:
                        return area

    # Fallback: match by country and type keywords
    for area in areas:
        area_name = area['name'].lower()
        # If title mentions airport and area is an airport
        if 'airport' in title_lower and area['area_type'] == 'airport':
            # Check country match
            country_in_title = extract_country(title)
            if country_in_title and area['country'] == country_in_title:
                return area

        # If title mentions nuclear/power plant
        if any(kw in title_lower for kw in ['nuclear', 'power plant', 'kerncentrale', 'centrale nucléaire']):
            if area['area_type'] == 'nuclear_facility':
                return area

    return None

def extract_country(title: str) -> Optional[str]:
    """Extract country code from title"""
    country_map = {
        'belgium': 'BE', 'belgië': 'BE', 'belgique': 'BE',
        'netherlands': 'NL', 'nederland': 'NL',
        'germany': 'DE', 'deutschland': 'DE', 'duitsland': 'DE',
        'france': 'FR', 'frankrijk': 'FR',
        'spain': 'ES', 'españa': 'ES', 'spanje': 'ES',
        'poland': 'PL', 'polen': 'PL',
        'denmark': 'DK', 'denemarken': 'DK',
        'sweden': 'SE', 'zweden': 'SE',
        'lithuania': 'LT', 'litouwen': 'LT',
        'estonia': 'EE', 'estland': 'EE'
    }

    title_lower = title.lower()
    for country_name, code in country_map.items():
        if country_name in title_lower:
            return code
    return None

def extract_date_from_article(article: Dict) -> str:
    """Extract and format date from article"""
    date_str = article.get('date', '')
    try:
        # Parse ISO format date
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        # Fallback to today
        return datetime.now().strftime('%Y-%m-%d')

def is_reaction_news(title: str, summary: str) -> bool:
    """
    Check if article is about reactions/responses rather than actual incident.
    Returns True if it's reaction news (should be skipped).
    """
    text = (title + ' ' + summary).lower()

    # Keywords that indicate reaction/response articles
    reaction_keywords = [
        'sends counter-drone',
        'sends anti-drone',
        'to protect belgium',
        'ingeschakeld om',  # "militairen ingeschakeld om"
        'dronejagers',
        'rushes to secure',
        'scrambles to address',
        'verantwoord als',  # opinion pieces
        'authorizes military to shoot',
        'investigates new drone',  # investigation news (not the incident)
    ]

    for keyword in reaction_keywords:
        if keyword in text:
            return True

    return False

def assess_purpose(title: str, summary: str) -> str:
    """Assess likely purpose based on title and summary"""
    text = (title + ' ' + summary).lower()

    if any(kw in text for kw in ['espionage', 'spy', 'reconnaissance', 'spionage']):
        return 'reconnaissance'
    elif any(kw in text for kw in ['disrupt', 'halt', 'suspend', 'close']):
        return 'disruption'
    elif any(kw in text for kw in ['attack', 'sabotage', 'threat']):
        return 'sabotage'
    elif 'test' in text or 'exercise' in text:
        return 'testing'
    else:
        return 'unknown'

def assess_suspected_operator(title: str, summary: str) -> str:
    """Assess suspected operator"""
    text = (title + ' ' + summary).lower()

    if any(kw in text for kw in ['russia', 'russian', 'rusland', 'russische']):
        return 'Russia (suspected)'
    elif any(kw in text for kw in ['china', 'chinese']):
        return 'China (suspected)'
    else:
        return 'Unknown'

def create_incident_from_article(article: Dict, area: Dict) -> Dict:
    """Convert article data to incident payload"""
    title = article['title']
    # Clean title - remove source name suffix
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1 and len(parts[-1]) < 30:  # Last part is likely source name
            title = ' - '.join(parts[:-1])

    # Truncate if too long
    if len(title) > 150:
        title = title[:147] + '...'

    summary = article.get('summary', '')[:500]  # Limit summary length

    incident = {
        "sighting_date": extract_date_from_article(article),
        "latitude": area['latitude'],
        "longitude": area['longitude'],
        "restricted_area_id": area['id'],
        "title": title.strip(),
        "description": f"Reported by {article['source']}. {summary}",
        "source": "news",
        "source_url": article['url'],
        "primary_source_name": article['source'],
        "primary_source_credibility": int(article['credibility'] * 10),  # Convert 0-1 to 0-10
        "purpose_assessment": assess_purpose(title, summary),
        "confidence_score": article['credibility'],
        "suspected_operator": assess_suspected_operator(title, summary),
        "identification_method": "intelligence",
        "identification_confidence": article['credibility'],
        "identified_by": article['source']
    }

    return incident

def import_incident(incident_data: Dict) -> bool:
    """Submit incident to API"""
    try:
        response = requests.post(f"{API_BASE}/incidents/", json=incident_data)
        response.raise_for_status()
        result = response.json()
        return True, result['id']
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_import_incidents.py <scan_report.json>")
        sys.exit(1)

    report_file = sys.argv[1]

    print("=" * 80)
    print("  🚁 Batch Import Incidents - OSINT CUAS Dashboard")
    print("=" * 80)
    print(f"\n📄 Reading report: {report_file}")

    # Load scan report
    with open(report_file, 'r') as f:
        report = json.load(f)

    incidents_data = report.get('incidents', [])
    print(f"📊 Found {len(incidents_data)} potential incidents in report")

    # Get restricted areas
    print("\n🗺️  Fetching restricted areas...")
    areas = get_restricted_areas()
    print(f"✓ Loaded {len(areas)} restricted areas")

    # Get existing incidents for duplicate detection
    print("\n🔍 Fetching existing incidents for duplicate detection...")
    existing_incidents = get_existing_incidents(days_back=60)
    print(f"✓ Loaded {len(existing_incidents)} recent incidents")

    # Process incidents
    print("\n🔄 Processing incidents...")
    print("─" * 80)

    successful = 0
    failed = 0
    skipped = 0
    duplicates = 0
    reaction_news = 0

    for idx, article in enumerate(incidents_data, 1):
        title = article['title'][:80]
        summary = article.get('summary', '')

        # Filter reaction news articles
        if is_reaction_news(article['title'], summary):
            print(f"📰 [{idx:2d}] SKIP: Reaction news (not incident) - {title}")
            reaction_news += 1
            continue

        # Match to location
        matched_area = match_location(article['title'], areas)

        if not matched_area:
            print(f"⚠️  [{idx:2d}] SKIP: No location match - {title}")
            skipped += 1
            continue

        # Create incident
        incident = create_incident_from_article(article, matched_area)

        # Check for duplicates
        if is_duplicate(incident, existing_incidents):
            print(f"🔁 [{idx:2d}] SKIP: Duplicate detected - {title}")
            duplicates += 1
            continue

        # Import
        success, result = import_incident(incident)

        if success:
            print(f"✓  [{idx:2d}] Added incident #{result:2d}: {title}")
            successful += 1
        else:
            print(f"✗  [{idx:2d}] Failed: {title}")
            print(f"         Error: {result}")
            failed += 1

    # Summary
    print("─" * 80)
    print("\n" + "=" * 80)
    print("  📊 Import Summary")
    print("=" * 80)
    print(f"✅ Successfully imported: {successful}")
    print(f"🔁 Duplicates skipped:   {duplicates}")
    print(f"📰 Reaction news:        {reaction_news}")
    print(f"⚠️  Skipped (no match):   {skipped}")
    print(f"❌ Failed:               {failed}")
    print(f"📋 Total processed:      {len(incidents_data)}")
    print("=" * 80)

    if successful > 0:
        print(f"\n🔗 View dashboard: http://localhost:8000")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
