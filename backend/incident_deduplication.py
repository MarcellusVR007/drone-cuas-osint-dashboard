#!/usr/bin/env python3
"""
Incident Deduplication & Quality Control
Identifies and merges duplicate incident reports using multi-factor analysis
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
import anthropic
import json

# Initialize Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using SequenceMatcher
    Returns: 0.0 (completely different) to 1.0 (identical)
    """
    if not text1 or not text2:
        return 0.0

    # Normalize texts
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()

    return SequenceMatcher(None, t1, t2).ratio()


def calculate_geographic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers
    Using simplified Haversine formula
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Earth radius in km

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def calculate_temporal_distance(date1: str, date2: str) -> int:
    """
    Calculate distance between two dates in days
    """
    try:
        d1 = datetime.fromisoformat(date1)
        d2 = datetime.fromisoformat(date2)
        return abs((d2 - d1).days)
    except:
        return 999  # Return large number if dates can't be parsed


def is_duplicate_incident(inc1: Dict, inc2: Dict,
                         time_threshold_days: int = 2,
                         distance_threshold_km: float = 50.0,
                         text_similarity_threshold: float = 0.6) -> Tuple[bool, float, str]:
    """
    Determine if two incidents are duplicates

    Returns: (is_duplicate, confidence_score, reason)
    """

    reasons = []
    confidence_factors = []

    # 1. Temporal proximity check
    time_diff = calculate_temporal_distance(inc1['sighting_date'], inc2['sighting_date'])
    if time_diff > time_threshold_days:
        return (False, 0.0, f"Time difference too large: {time_diff} days")

    temporal_score = 1.0 - (time_diff / time_threshold_days)
    confidence_factors.append(('temporal', temporal_score))
    reasons.append(f"Within {time_diff} days")

    # 2. Geographic proximity check
    if inc1['latitude'] == 0 or inc2['latitude'] == 0:
        # Can't determine location - rely more on text similarity
        geo_score = 0.5  # Neutral
        reasons.append("Location unknown for one or both incidents")
    else:
        distance = calculate_geographic_distance(
            inc1['latitude'], inc1['longitude'],
            inc2['latitude'], inc2['longitude']
        )

        if distance > distance_threshold_km:
            return (False, 0.0, f"Distance too large: {distance:.1f} km")

        geo_score = 1.0 - (distance / distance_threshold_km)
        confidence_factors.append(('geographic', geo_score))
        reasons.append(f"Within {distance:.1f} km")

    # 3. Restricted area match
    if inc1.get('restricted_area_id') and inc2.get('restricted_area_id'):
        if inc1['restricted_area_id'] == inc2['restricted_area_id']:
            confidence_factors.append(('same_location', 1.0))
            reasons.append("Same restricted area")
        else:
            confidence_factors.append(('different_location', 0.0))
            reasons.append("Different restricted areas")

    # 4. Title similarity
    title_similarity = calculate_text_similarity(inc1['title'], inc2['title'])
    confidence_factors.append(('title', title_similarity))

    if title_similarity > 0.8:
        reasons.append(f"Very similar titles ({title_similarity:.2f})")
    elif title_similarity > 0.5:
        reasons.append(f"Similar titles ({title_similarity:.2f})")

    # 5. Description similarity
    desc_similarity = calculate_text_similarity(
        inc1.get('description', ''),
        inc2.get('description', '')
    )
    confidence_factors.append(('description', desc_similarity))

    if desc_similarity > 0.8:
        reasons.append(f"Very similar descriptions ({desc_similarity:.2f})")
    elif desc_similarity > 0.5:
        reasons.append(f"Similar descriptions ({desc_similarity:.2f})")

    # 6. Calculate overall confidence
    # Weight different factors
    weights = {
        'temporal': 0.2,
        'geographic': 0.3,
        'same_location': 0.2,
        'different_location': 0.2,
        'title': 0.15,
        'description': 0.15
    }

    total_confidence = 0.0
    total_weight = 0.0

    for factor_name, score in confidence_factors:
        weight = weights.get(factor_name, 0.1)
        total_confidence += score * weight
        total_weight += weight

    if total_weight > 0:
        confidence = total_confidence / total_weight
    else:
        confidence = 0.0

    # Decision threshold
    is_duplicate = confidence >= 0.65

    reason_str = "; ".join(reasons)

    return (is_duplicate, confidence, reason_str)


def classify_incident_with_ai(incident: Dict) -> Dict:
    """
    Use Claude AI to classify if this is a real incident or false positive

    Returns:
        {
            "is_real_incident": bool,
            "confidence": float,
            "reason": str,
            "category": "REAL_INCIDENT" | "GENERAL_NEWS" | "HISTORICAL_REFERENCE" | "POLICY_DISCUSSION"
        }
    """

    if not client:
        # Fallback to rule-based classification
        return _fallback_classification(incident)

    prompt = f"""Analyze this drone incident report and determine if it's a REAL INCIDENT or a FALSE POSITIVE.

**INCIDENT DATA:**
Title: {incident['title']}
Date: {incident['sighting_date']}
Description: {incident.get('description', 'No description')}
Source: {incident.get('source', 'Unknown')}

**CLASSIFICATION CRITERIA:**

✅ REAL INCIDENT (respond: "REAL_INCIDENT"):
- Specific date AND specific location AND specific action
- Examples: "Drones spotted over RAF Lakenheath on Nov 20"
- Eye-witness accounts or official reports
- Airport closures, military base intrusions, critical infrastructure
- Police/military response mentioned

❌ GENERAL NEWS (respond: "GENERAL_NEWS"):
- Overview articles about drone threat in general
- Statistics about multiple incidents
- Policy discussions without specific incident
- Examples: "Drone incursions continue across NATO"

❌ HISTORICAL REFERENCE (respond: "HISTORICAL_REFERENCE"):
- References to past incidents without new information
- Anniversary articles
- "Remember when..." type content

❌ POLICY DISCUSSION (respond: "POLICY_DISCUSSION"):
- Legislative changes
- New regulations
- Budget discussions
- Training announcements

**YOUR TASK:**
Respond with JSON only:
{{
    "is_real_incident": true/false,
    "confidence": 0.0-1.0,
    "category": "REAL_INCIDENT|GENERAL_NEWS|HISTORICAL_REFERENCE|POLICY_DISCUSSION",
    "reason": "Brief explanation (1 sentence)"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            temperature=0.1,  # Low temperature for classification
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text

        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        return {
            "is_real_incident": result.get("is_real_incident", True),
            "confidence": result.get("confidence", 0.5),
            "reason": result.get("reason", "AI classified"),
            "category": result.get("category", "REAL_INCIDENT")
        }

    except Exception as e:
        print(f"AI classification error: {e}")
        return _fallback_classification(incident)


def _fallback_classification(incident: Dict) -> Dict:
    """Simple rule-based fallback when AI is unavailable"""

    title_lower = incident['title'].lower()
    desc_lower = incident.get('description', '').lower()
    combined = f"{title_lower} {desc_lower}"

    # Red flags for false positives
    false_positive_keywords = [
        'incursions continue', 'threat grows', 'statistics show',
        'policy', 'regulation', 'legislation', 'new law',
        'training exercise', 'drill', 'test flight',
        'anniversary', 'years ago', 'remember when'
    ]

    # Positive indicators for real incidents
    real_incident_keywords = [
        'spotted', 'sighted', 'detected', 'observed',
        'closed', 'shut down', 'grounded', 'diverted',
        'police', 'military', 'arrested', 'investigating',
        'last night', 'yesterday', 'today', 'this morning'
    ]

    false_positive_count = sum(1 for kw in false_positive_keywords if kw in combined)
    real_incident_count = sum(1 for kw in real_incident_keywords if kw in combined)

    if false_positive_count > real_incident_count:
        return {
            "is_real_incident": False,
            "confidence": 0.7,
            "reason": "Appears to be general news or policy discussion",
            "category": "GENERAL_NEWS"
        }
    else:
        return {
            "is_real_incident": True,
            "confidence": 0.6,
            "reason": "Appears to be specific incident report",
            "category": "REAL_INCIDENT"
        }


def find_duplicate_groups(incidents: List[Dict]) -> List[List[int]]:
    """
    Find groups of duplicate incidents

    Returns: List of groups, each group is a list of incident IDs
    """
    duplicate_groups = []
    processed_ids = set()

    for i, inc1 in enumerate(incidents):
        if inc1['id'] in processed_ids:
            continue

        # Start a new group with this incident
        current_group = [inc1['id']]

        # Compare with all subsequent incidents
        for j in range(i + 1, len(incidents)):
            inc2 = incidents[j]

            if inc2['id'] in processed_ids:
                continue

            is_dup, confidence, reason = is_duplicate_incident(inc1, inc2)

            if is_dup:
                print(f"  DUPLICATE FOUND: {inc1['id']} ≈ {inc2['id']} (confidence: {confidence:.2f})")
                print(f"    Reason: {reason}")
                current_group.append(inc2['id'])
                processed_ids.add(inc2['id'])

        # Only add groups with 2+ incidents
        if len(current_group) > 1:
            duplicate_groups.append(current_group)

        processed_ids.add(inc1['id'])

    return duplicate_groups


def merge_duplicate_incidents(db_path: str, incident_ids: List[int]) -> int:
    """
    Merge multiple duplicate incidents into one master record

    Strategy:
    - Keep the earliest incident as master
    - Combine all sources into display_source
    - Keep best quality description (longest)
    - Average confidence scores
    - Mark others as duplicates

    Returns: ID of master incident
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all incidents
    placeholders = ','.join('?' * len(incident_ids))
    cursor.execute(f"""
        SELECT * FROM incidents
        WHERE id IN ({placeholders})
        ORDER BY sighting_date ASC, id ASC
    """, incident_ids)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    incidents = [dict(zip(columns, row)) for row in rows]

    if not incidents:
        return None

    # Master incident (earliest one)
    master = incidents[0]
    master_id = master['id']

    # Collect all sources
    all_sources = set()
    all_urls = set()
    descriptions = []
    confidence_scores = []

    for inc in incidents:
        if inc.get('source'):
            all_sources.add(inc['source'])
        if inc.get('source_url'):
            all_urls.add(inc['source_url'])
        if inc.get('description') and len(inc['description']) > 10:
            descriptions.append(inc['description'])
        if inc.get('confidence_score'):
            confidence_scores.append(inc['confidence_score'])

    # Build merged data
    merged_source = " + ".join(sorted(all_sources)[:5])  # Max 5 sources
    merged_description = max(descriptions, key=len) if descriptions else master.get('description')
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else master.get('confidence_score', 0.5)

    # Update master incident
    cursor.execute("""
        UPDATE incidents SET
            display_source = ?,
            description = ?,
            confidence_score = ?,
            operational_class = 'MERGED_MASTER'
        WHERE id = ?
    """, (merged_source, merged_description, avg_confidence, master_id))

    # Mark duplicates
    duplicate_ids = [inc['id'] for inc in incidents[1:]]
    if duplicate_ids:
        placeholders = ','.join('?' * len(duplicate_ids))
        cursor.execute(f"""
            UPDATE incidents SET
                operational_class = 'DUPLICATE',
                confidence_score = 0.0
            WHERE id IN ({placeholders})
        """, duplicate_ids)

    # Create deduplication record
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_deduplication (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_incident_id INTEGER,
            duplicate_incident_ids TEXT,
            merged_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sources_merged TEXT,
            FOREIGN KEY (master_incident_id) REFERENCES incidents(id)
        )
    """)

    cursor.execute("""
        INSERT INTO incident_deduplication (master_incident_id, duplicate_incident_ids, sources_merged)
        VALUES (?, ?, ?)
    """, (master_id, json.dumps(duplicate_ids), merged_source))

    conn.commit()
    conn.close()

    print(f"  ✅ Merged {len(incident_ids)} incidents into master ID {master_id}")
    print(f"     Sources: {merged_source}")

    return master_id


def run_deduplication(db_path: str = 'data/drone_cuas_staging.db'):
    """Main deduplication workflow"""

    print("=" * 80)
    print("INCIDENT DEDUPLICATION & QUALITY CONTROL")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all incidents (exclude already marked duplicates)
    cursor.execute("""
        SELECT id, sighting_date, sighting_time, latitude, longitude,
               restricted_area_id, title, description, source,
               display_source, confidence_score, operational_class
        FROM incidents
        WHERE operational_class IS NULL OR operational_class != 'DUPLICATE'
        ORDER BY sighting_date DESC
    """)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    incidents = [dict(zip(columns, row)) for row in rows]

    conn.close()

    print(f"\n📊 Analyzing {len(incidents)} incidents...\n")

    # Step 1: Find duplicates
    print("🔍 STEP 1: Finding duplicate incidents...")
    duplicate_groups = find_duplicate_groups(incidents)

    print(f"\n✅ Found {len(duplicate_groups)} duplicate groups\n")

    # Step 2: Merge duplicates
    print("🔗 STEP 2: Merging duplicates...")
    for i, group in enumerate(duplicate_groups, 1):
        print(f"\nGroup {i}: Merging {len(group)} incidents: {group}")
        merge_duplicate_incidents(db_path, group)

    # Step 3: AI Classification
    print(f"\n🤖 STEP 3: AI Classification of incidents...")

    # Re-fetch incidents (excluding duplicates)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sighting_date, title, description, source, confidence_score
        FROM incidents
        WHERE operational_class IS NULL OR operational_class NOT IN ('DUPLICATE', 'FALSE_POSITIVE')
        ORDER BY sighting_date DESC
    """)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    active_incidents = [dict(zip(columns, row)) for row in rows]

    false_positives = []

    for inc in active_incidents:
        classification = classify_incident_with_ai(inc)

        if not classification['is_real_incident']:
            print(f"\n❌ FALSE POSITIVE: ID {inc['id']}")
            print(f"   Title: {inc['title']}")
            print(f"   Reason: {classification['reason']}")
            print(f"   Category: {classification['category']}")

            false_positives.append(inc['id'])

            # Mark as false positive
            cursor.execute("""
                UPDATE incidents SET
                    operational_class = ?,
                    confidence_score = 0.0
                WHERE id = ?
            """, (classification['category'], inc['id']))

    conn.commit()
    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total incidents processed: {len(incidents)}")
    print(f"Duplicate groups found: {len(duplicate_groups)}")
    print(f"Incidents marked as duplicates: {sum(len(g) - 1 for g in duplicate_groups)}")
    print(f"False positives identified: {len(false_positives)}")
    print(f"Real incidents remaining: {len(active_incidents) - len(false_positives)}")
    print("=" * 80)


if __name__ == "__main__":
    run_deduplication()
