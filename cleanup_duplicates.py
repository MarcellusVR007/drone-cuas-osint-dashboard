#!/usr/bin/env python3
"""
Clean up duplicate incidents and reaction news articles from database

This script:
1. Removes duplicate incidents (keeps oldest)
2. Removes "reaction news" articles that aren't actual incidents
"""

import requests
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime

API_BASE = "http://localhost:8000/api"

# Keywords that indicate "reaction news" rather than actual incidents
REACTION_KEYWORDS = [
    'ingeschakeld',  # "militairen ingeschakeld"
    'dronejagers',
    'sends counter-drone',
    'sends anti-drone',
    'to protect belgium',
    'rushes to secure',
    'scrambles to address',
    'verantwoord als ook',  # opinion pieces
    'authorizes military',  # authorization news
    'investigates new',  # investigation news (not the incident itself)
]

def get_all_incidents():
    """Fetch all incidents"""
    response = requests.get(f"{API_BASE}/incidents/?limit=500")
    response.raise_for_status()
    return response.json()['incidents']

def is_reaction_news(title: str, description: str) -> bool:
    """Check if this is a reaction/analysis article rather than an incident"""
    text = (title + ' ' + description).lower()

    for keyword in REACTION_KEYWORDS:
        if keyword in text:
            return True

    return False

def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def find_duplicates(incidents):
    """Find duplicate incidents"""
    duplicates = []
    processed = set()

    for i, inc1 in enumerate(incidents):
        if inc1['id'] in processed:
            continue

        dupes_of_this = [inc1]

        for inc2 in incidents[i+1:]:
            if inc2['id'] in processed:
                continue

            # Check similarity
            title_sim = similarity_ratio(inc1['title'], inc2['title'])

            # Same date and very similar title
            if (inc1['sighting_date'] == inc2['sighting_date'] and
                title_sim > 0.75):
                dupes_of_this.append(inc2)
                processed.add(inc2['id'])

        if len(dupes_of_this) > 1:
            # Keep the first one (oldest ID), mark rest as duplicates
            duplicates.extend([d['id'] for d in dupes_of_this[1:]])

    return duplicates

def delete_incident(incident_id: int) -> bool:
    """Delete an incident by ID"""
    try:
        response = requests.delete(f"{API_BASE}/incidents/{incident_id}")
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ Failed to delete #{incident_id}: {e}")
        return False

def main():
    print("=" * 80)
    print("  🧹 Cleanup: Remove Duplicates & Reaction News")
    print("=" * 80)

    # Fetch all incidents
    print("\n📥 Fetching all incidents...")
    incidents = get_all_incidents()
    print(f"✓ Found {len(incidents)} total incidents")

    # Find reaction news articles
    print("\n🔍 Identifying reaction news articles...")
    reaction_news = []
    for inc in incidents:
        if is_reaction_news(inc['title'], inc.get('description', '')):
            reaction_news.append(inc)

    print(f"✓ Found {len(reaction_news)} reaction news articles")
    if reaction_news:
        print("\nExamples:")
        for rn in reaction_news[:5]:
            print(f"  - [{rn['id']:3d}] {rn['title'][:70]}")

    # Find duplicates
    print("\n🔍 Identifying duplicates...")
    duplicate_ids = find_duplicates(incidents)
    print(f"✓ Found {len(duplicate_ids)} duplicate incidents")

    # Calculate total to delete
    to_delete = set(duplicate_ids + [rn['id'] for rn in reaction_news])
    print(f"\n📊 Total incidents to delete: {len(to_delete)}")
    print(f"   - Duplicates: {len(duplicate_ids)}")
    print(f"   - Reaction news: {len(reaction_news)}")

    # Confirm
    print("\n" + "─" * 80)
    response = input(f"Delete {len(to_delete)} incidents? (yes/no): ")

    if response.lower() != 'yes':
        print("❌ Cancelled")
        return

    # Delete
    print("\n🗑️  Deleting incidents...")
    deleted = 0
    failed = 0

    for inc_id in sorted(to_delete):
        if delete_incident(inc_id):
            print(f"  ✓ Deleted incident #{inc_id}")
            deleted += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 80)
    print("  📊 Cleanup Summary")
    print("=" * 80)
    print(f"✅ Deleted:    {deleted}")
    print(f"❌ Failed:     {failed}")
    print(f"📋 Remaining:  {len(incidents) - deleted}")
    print("=" * 80)

    print("\n🔗 View dashboard: http://localhost:8000")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
