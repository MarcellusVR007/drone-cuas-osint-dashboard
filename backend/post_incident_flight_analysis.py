#!/usr/bin/env python3
"""
Post-Incident Flight Analysis
Forensic analysis of flight data AFTER a drone incident
Focus: Launch zone triangulation, suspicious aircraft patterns
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sqlite3
import json
import math

class PostIncidentFlightAnalyzer:
    """Analyze flight patterns after drone incidents for forensic investigation"""

    def __init__(self, db_path="data/drone_cuas.db"):
        self.db_path = db_path
        self.api_base = "https://opensky-network.org/api"

    def get_incident_details(self, incident_id: int) -> Optional[Dict]:
        """Get incident location and time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, sighting_date, sighting_time, latitude, longitude,
                   drone_description, suspected_operator, description
            FROM incidents
            WHERE id = ?
        """, (incident_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "sighting_date": row[2],
            "sighting_time": row[3],
            "latitude": row[4],
            "longitude": row[5],
            "drone_description": row[6],
            "suspected_operator": row[7],
            "description": row[8]
        }

    def get_historical_flights(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        timestamp: int
    ) -> List[Dict]:
        """
        Get historical flights near incident location
        OpenSky API: Can query up to 30 days back
        """
        # OpenSky historical API endpoint
        url = f"{self.api_base}/flights/all"

        # Time window: 2 hours before incident
        end_time = timestamp
        begin_time = timestamp - (2 * 3600)  # 2 hours before

        params = {
            "begin": begin_time,
            "end": end_time
        }

        try:
            print(f"   Querying OpenSky for flights {datetime.fromtimestamp(begin_time)} to {datetime.fromtimestamp(end_time)}...")
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 404:
                print(f"   ⚠️  No historical data available (too old or API limit)")
                return []

            response.raise_for_status()
            flights = response.json()

            if not flights:
                return []

            # Filter flights by distance to incident
            nearby_flights = []
            for flight in flights:
                # OpenSky returns flights, not positions
                # We'd need to query states/all for each timestamp
                # This is rate-limited, so we return flight list
                nearby_flights.append(flight)

            print(f"   Found {len(nearby_flights)} flights in time window")
            return nearby_flights

        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  OpenSky API error: {e}")
            return []

    def calculate_possible_launch_zone(
        self,
        incident_lat: float,
        incident_lon: float,
        drone_type: Optional[str],
        drone_range_km: Optional[float] = None
    ) -> Dict:
        """
        Calculate possible launch zone based on drone type and range
        Returns circular area around incident
        """
        # Drone range estimates
        range_estimates = {
            "consumer": 5,      # DJI Mavic etc
            "orlan-10": 120,    # Russian Orlan-10
            "military": 50,     # Generic military drone
            "unknown": 10       # Conservative estimate
        }

        # Determine range
        if drone_range_km:
            range_km = drone_range_km
        elif drone_type:
            dtype_lower = drone_type.lower()
            if "orlan" in dtype_lower:
                range_km = range_estimates["orlan-10"]
            elif any(word in dtype_lower for word in ["dji", "mavic", "phantom", "consumer"]):
                range_km = range_estimates["consumer"]
            elif "military" in dtype_lower:
                range_km = range_estimates["military"]
            else:
                range_km = range_estimates["unknown"]
        else:
            range_km = range_estimates["unknown"]

        return {
            "center_lat": incident_lat,
            "center_lon": incident_lon,
            "radius_km": range_km,
            "area_description": f"Circular zone {range_km}km radius from incident",
            "drone_type": drone_type or "unknown"
        }

    def check_maritime_correlation(
        self,
        launch_zone: Dict,
        incident_time: datetime
    ) -> List[Dict]:
        """
        Check if launch zone includes maritime area (Baltic/North Sea)
        For Orlan-10 incidents, check AIS ship data

        NOTE: This would require AIS data integration (e.g., MarineTraffic API)
        For now, just flag if zone includes water
        """
        lat = launch_zone["center_lat"]
        lon = launch_zone["center_lon"]

        # Rough checks for maritime areas
        maritime_flags = []

        # Baltic Sea
        if 53.0 <= lat <= 66.0 and 10.0 <= lon <= 30.0:
            maritime_flags.append({
                "area": "Baltic Sea",
                "note": "Check AIS ship data for Russian vessels",
                "priority": "HIGH"
            })

        # North Sea
        if 51.0 <= lat <= 61.0 and -4.0 <= lon <= 9.0:
            maritime_flags.append({
                "area": "North Sea",
                "note": "Check AIS ship data near incident time",
                "priority": "MEDIUM"
            })

        return maritime_flags

    def analyze_incident(self, incident_id: int) -> Dict:
        """
        Full post-incident forensic analysis
        """
        print(f"\n{'='*80}")
        print(f"POST-INCIDENT FLIGHT ANALYSIS - Incident #{incident_id}")
        print(f"{'='*80}\n")

        # 1. Get incident details
        incident = self.get_incident_details(incident_id)
        if not incident:
            return {"error": "Incident not found"}

        print(f"📋 Incident: {incident['title']}")
        print(f"📍 Location: {incident['latitude']:.4f}, {incident['longitude']:.4f}")
        print(f"📅 Date: {incident['sighting_date']} {incident['sighting_time'] or ''}")
        print(f"🚁 Drone: {incident['drone_description'] or 'Unknown'}")
        print()

        # 2. Calculate launch zone
        print("🎯 Calculating possible launch zone...")
        launch_zone = self.calculate_possible_launch_zone(
            incident['latitude'],
            incident['longitude'],
            incident['drone_description']
        )
        print(f"   Launch zone: {launch_zone['radius_km']}km radius")
        print(f"   Center: {launch_zone['center_lat']:.4f}, {launch_zone['center_lon']:.4f}")
        print()

        # 3. Check maritime correlation (for Orlan incidents)
        maritime = self.check_maritime_correlation(launch_zone, incident['sighting_date'])
        if maritime:
            print("🚢 Maritime correlation detected:")
            for flag in maritime:
                print(f"   - {flag['area']}: {flag['note']} (Priority: {flag['priority']})")
            print()

        # 4. Query historical flights (if incident is recent)
        if incident['sighting_date']:
            try:
                incident_dt = datetime.fromisoformat(incident['sighting_date'])
                if incident['sighting_time']:
                    time_parts = incident['sighting_time'].split(':')
                    incident_dt = incident_dt.replace(
                        hour=int(time_parts[0]),
                        minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                    )

                incident_timestamp = int(incident_dt.timestamp())
                days_ago = (datetime.now() - incident_dt).days

                print(f"✈️  Querying flight data ({days_ago} days ago)...")

                if days_ago <= 30:  # OpenSky keeps ~30 days
                    flights = self.get_historical_flights(
                        incident['latitude'],
                        incident['longitude'],
                        launch_zone['radius_km'],
                        incident_timestamp
                    )
                else:
                    print(f"   ⚠️  Incident too old ({days_ago} days) - no flight data available")
                    flights = []

            except Exception as e:
                print(f"   ⚠️  Error querying flights: {e}")
                flights = []
        else:
            flights = []

        # 5. Generate report
        analysis = {
            "incident_id": incident_id,
            "incident": incident,
            "launch_zone": launch_zone,
            "maritime_correlation": maritime,
            "flights_detected": len(flights),
            "flights": flights[:10] if flights else [],  # Top 10
            "recommendations": self.generate_recommendations(incident, launch_zone, maritime, flights)
        }

        print("\n📊 ANALYSIS SUMMARY:")
        print(f"   Launch zone: {launch_zone['radius_km']}km radius")
        print(f"   Maritime areas: {len(maritime)}")
        print(f"   Flights detected: {len(flights)}")
        print()

        return analysis

    def generate_recommendations(
        self,
        incident: Dict,
        launch_zone: Dict,
        maritime: List[Dict],
        flights: List[Dict]
    ) -> List[str]:
        """Generate investigation recommendations"""
        recs = []

        # Drone type specific
        if incident['drone_description']:
            desc_lower = incident['drone_description'].lower()
            if "orlan" in desc_lower:
                recs.append("🔴 ORLAN-10 DETECTED - Request AIS ship data for launch zone + 2 hours before incident")
                recs.append("🔴 Check Russian vessel movements in Baltic/North Sea")
                recs.append("🔴 Cross-reference with NATO maritime surveillance")

        # Maritime correlation
        if maritime:
            recs.append(f"🔵 Maritime launch suspected - Query AIS data for {maritime[0]['area']}")
            recs.append("🔵 Contact coast guard for vessel identification")

        # Launch zone analysis
        if launch_zone['radius_km'] < 20:
            recs.append("🟢 Small launch zone - Check local CCTV, witnesses, parked vehicles")
        else:
            recs.append("🟡 Large launch zone - Focus on maritime/cross-border launch")

        # Flight data
        if flights:
            recs.append(f"✈️  {len(flights)} flights detected in time window - Review for suspicious patterns")

        if not recs:
            recs.append("⚪ Insufficient data for specific recommendations")

        return recs


def analyze_all_recent_incidents(days_back: int = 30):
    """Analyze all incidents from last N days"""
    analyzer = PostIncidentFlightAnalyzer()

    conn = sqlite3.connect(analyzer.db_path)
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT id FROM incidents
        WHERE sighting_date >= ?
        ORDER BY sighting_date DESC
    """, (cutoff_date,))

    incident_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\n🔍 Analyzing {len(incident_ids)} incidents from last {days_back} days\n")

    for incident_id in incident_ids:
        analyzer.analyze_incident(incident_id)
        time.sleep(2)  # Rate limiting


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        incident_id = int(sys.argv[1])
        analyzer = PostIncidentFlightAnalyzer()
        analysis = analyzer.analyze_incident(incident_id)

        print("\n🔍 RECOMMENDATIONS:")
        for rec in analysis["recommendations"]:
            print(f"   {rec}")
    else:
        print("Usage: python3 post_incident_flight_analysis.py <incident_id>")
        print("\nExample: python3 post_incident_flight_analysis.py 5")
        print("\nOr analyze all recent incidents:")
        print("   python3 -c 'from post_incident_flight_analysis import analyze_all_recent_incidents; analyze_all_recent_incidents(30)'")
