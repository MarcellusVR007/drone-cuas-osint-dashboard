#!/usr/bin/env python3
"""
Shodan-Incident Temporal Correlation Engine

Analyzes:
1. IP cameras near incident locations at incident times
2. Drone C2 server activity timestamps around incidents
3. FPV streaming activity correlation
4. Drone detection system alerts (if available)

Goal: Find technical infrastructure evidence correlated with incidents
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

try:
    import shodan
except ImportError:
    print("⚠️  Shodan not installed. Install: pip3 install shodan")
    sys.exit(1)

from backend.database import SessionLocal
from backend.models import Incident, TelegramMessage

class ShodanIncidentCorrelator:
    """
    Correlate Shodan infrastructure data with drone incidents
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SHODAN_API_KEY')

        if self.api_key:
            try:
                self.api = shodan.Shodan(self.api_key)
                print("✓ Shodan API initialized")
            except Exception as e:
                print(f"⚠️  Shodan API error: {e}")
                self.api = None
        else:
            print("⚠️  No Shodan API key - using demo mode")
            self.api = None

        self.db = SessionLocal()
        self.correlations = []

    def analyze_all_incidents(self):
        """
        Main analysis: correlate all incidents with Shodan data
        """
        print("=" * 80)
        print("SHODAN-INCIDENT TEMPORAL CORRELATION ANALYSIS")
        print("=" * 80)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get all incidents with location data
        incidents = self.db.query(Incident).filter(
            Incident.latitude.isnot(None),
            Incident.longitude.isnot(None)
        ).all()

        print(f"📊 Analyzing {len(incidents)} incidents with location data\n")

        for i, incident in enumerate(incidents, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(incidents)}] INCIDENT ANALYSIS")
            print('='*80)
            print(f"📍 Location: {incident.restricted_area.name if incident.restricted_area else 'Unknown'}")
            print(f"📅 Date: {incident.sighting_date}")
            print(f"🌍 Coordinates: {incident.latitude}, {incident.longitude}")

            # Analyze this incident
            self.analyze_single_incident(incident)

        # Generate report
        self.generate_correlation_report()

    def analyze_single_incident(self, incident: Incident):
        """
        Deep dive: analyze single incident for Shodan correlations
        """

        # 1. Find IP cameras in area
        self.find_cameras_near_incident(incident)

        # 2. Find drone C2 servers (with timestamps if available)
        self.find_c2_servers_near_incident(incident)

        # 3. Find FPV streaming activity
        self.find_fpv_streams_near_incident(incident)

        # 4. Check for drone detection systems
        self.find_detection_systems_near_incident(incident)

    def find_cameras_near_incident(self, incident: Incident, radius_km: float = 5.0):
        """
        Find IP cameras within radius of incident
        """
        print(f"\n🎥 Searching IP cameras within {radius_km}km...")

        if not self.api:
            print("   ⚠️  No API - using demo data")
            self._add_demo_correlation(incident, 'ip_camera', radius_km)
            return

        # Geospatial query
        lat, lon = incident.latitude, incident.longitude
        query = f'geo:"{lat},{lon},{radius_km}" port:8080 has_screenshot:true'

        try:
            results = self.api.search(query, limit=50)

            print(f"   ✓ Found {len(results['matches'])} cameras")

            for device in results['matches']:
                # Calculate distance
                device_lat = device.get('location', {}).get('latitude')
                device_lon = device.get('location', {}).get('longitude')

                if device_lat and device_lon:
                    distance = self._calculate_distance(
                        incident.latitude, incident.longitude,
                        device_lat, device_lon
                    )
                else:
                    distance = None

                # Check if device has timestamp data
                device_timestamp = device.get('timestamp')
                time_correlation = None

                if device_timestamp:
                    device_dt = datetime.fromisoformat(device_timestamp.replace('Z', '+00:00'))
                    incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())
                    time_delta = abs((device_dt - incident_dt).total_seconds() / 3600)

                    # High correlation if device seen within ±7 days of incident
                    if time_delta <= 168:  # 7 days
                        time_correlation = "HIGH"
                        print(f"   🔥 HIGH CORRELATION: Camera {device['ip_str']} seen {time_delta:.1f}h from incident!")
                    elif time_delta <= 720:  # 30 days
                        time_correlation = "MEDIUM"

                correlation = {
                    'incident_id': incident.id,
                    'incident_date': incident.sighting_date.isoformat(),
                    'incident_location': f"{incident.latitude}, {incident.longitude}",
                    'correlation_type': 'ip_camera',
                    'device_ip': device['ip_str'],
                    'device_port': device.get('port'),
                    'device_product': device.get('product', 'IP Camera'),
                    'device_org': device.get('org', 'Unknown'),
                    'device_location': f"{device.get('location', {}).get('city', 'Unknown')}, {device.get('location', {}).get('country_name', 'Unknown')}",
                    'distance_km': round(distance, 2) if distance else None,
                    'device_timestamp': device_timestamp,
                    'time_correlation': time_correlation,
                    'confidence': self._calculate_confidence('camera', distance, time_correlation)
                }

                self.correlations.append(correlation)

        except shodan.APIError as e:
            print(f"   ⚠️  Shodan API Error: {e}")

    def find_c2_servers_near_incident(self, incident: Incident):
        """
        Find drone C2 servers (MAVLink, ArduPilot, PX4)
        """
        print(f"\n🎮 Searching drone C2 servers...")

        if not self.api:
            print("   ⚠️  No API - using demo data")
            return

        queries = [
            f'"autopilot" port:14550',  # MAVLink
            f'"ArduPilot"',
            f'"PX4"'
        ]

        for query in queries:
            try:
                results = self.api.search(query, limit=20)

                for device in results['matches']:
                    # Check if in Netherlands
                    country = device.get('location', {}).get('country_code')
                    if country != 'NL':
                        continue

                    # Calculate distance to incident
                    device_lat = device.get('location', {}).get('latitude')
                    device_lon = device.get('location', {}).get('longitude')

                    if device_lat and device_lon:
                        distance = self._calculate_distance(
                            incident.latitude, incident.longitude,
                            device_lat, device_lon
                        )
                    else:
                        distance = None

                    # Temporal correlation
                    device_timestamp = device.get('timestamp')
                    time_correlation = None

                    if device_timestamp:
                        device_dt = datetime.fromisoformat(device_timestamp.replace('Z', '+00:00'))
                        incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())
                        time_delta = abs((device_dt - incident_dt).total_seconds() / 3600)

                        # CRITICAL if C2 server active within ±24h of incident!
                        if time_delta <= 24:
                            time_correlation = "CRITICAL"
                            print(f"   🚨 CRITICAL: C2 server {device['ip_str']} active {time_delta:.1f}h from incident!")
                        elif time_delta <= 168:
                            time_correlation = "HIGH"

                    correlation = {
                        'incident_id': incident.id,
                        'incident_date': incident.sighting_date.isoformat(),
                        'correlation_type': 'c2_server',
                        'device_ip': device['ip_str'],
                        'device_port': device.get('port'),
                        'device_product': device.get('product', 'Unknown'),
                        'c2_protocol': 'MAVLink' if device.get('port') == 14550 else 'Unknown',
                        'device_org': device.get('org', 'Unknown'),
                        'distance_km': round(distance, 2) if distance else None,
                        'device_timestamp': device_timestamp,
                        'time_correlation': time_correlation,
                        'confidence': self._calculate_confidence('c2_server', distance, time_correlation)
                    }

                    self.correlations.append(correlation)

            except shodan.APIError as e:
                print(f"   ⚠️  Shodan API Error: {e}")

    def find_fpv_streams_near_incident(self, incident: Incident):
        """
        Find FPV streaming servers
        """
        print(f"\n📡 Searching FPV streaming activity...")

        if not self.api:
            print("   ⚠️  No API - using demo data")
            return

        # Query for streaming protocols
        queries = [
            'port:554 "drone"',  # RTSP
            'port:1935 "live"'   # RTMP
        ]

        for query in queries:
            try:
                results = self.api.search(query, limit=10)

                for device in results['matches']:
                    country = device.get('location', {}).get('country_code')
                    if country != 'NL':
                        continue

                    # Temporal check
                    device_timestamp = device.get('timestamp')
                    if device_timestamp:
                        device_dt = datetime.fromisoformat(device_timestamp.replace('Z', '+00:00'))
                        incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())
                        time_delta = abs((device_dt - incident_dt).total_seconds() / 3600)

                        if time_delta <= 48:  # Within 48h
                            print(f"   ⚠️  FPV stream {device['ip_str']} active near incident time!")

                            correlation = {
                                'incident_id': incident.id,
                                'incident_date': incident.sighting_date.isoformat(),
                                'correlation_type': 'fpv_stream',
                                'device_ip': device['ip_str'],
                                'device_port': device.get('port'),
                                'stream_protocol': 'RTSP' if device.get('port') == 554 else 'RTMP',
                                'device_timestamp': device_timestamp,
                                'time_delta_hours': round(time_delta, 1),
                                'confidence': 'HIGH' if time_delta <= 24 else 'MEDIUM'
                            }

                            self.correlations.append(correlation)

            except shodan.APIError as e:
                print(f"   ⚠️  Shodan API Error: {e}")

    def find_detection_systems_near_incident(self, incident: Incident):
        """
        Find drone detection systems (AeroScope, DroneShield, Dedrone)
        """
        print(f"\n🛡️  Searching drone detection systems...")

        if not self.api:
            print("   ⚠️  No API - using demo data")
            return

        queries = [
            'product:"DJI AeroScope"',
            'product:"DroneShield"',
            'product:"Dedrone"'
        ]

        for query in queries:
            try:
                results = self.api.search(query, limit=5)

                if len(results['matches']) > 0:
                    print(f"   ✓ Found {len(results['matches'])} detection systems")

                for device in results['matches']:
                    # These are CRITICAL findings
                    correlation = {
                        'incident_id': incident.id,
                        'incident_date': incident.sighting_date.isoformat(),
                        'correlation_type': 'detection_system',
                        'device_ip': device['ip_str'],
                        'system_type': device.get('product', 'Unknown'),
                        'device_org': device.get('org', 'Unknown'),
                        'device_location': f"{device.get('location', {}).get('city', 'Unknown')}",
                        'note': 'CRITICAL: This system may have detected the incident!'
                    }

                    self.correlations.append(correlation)
                    print(f"   🚨 CRITICAL: Detection system found - {device.get('product')}")

            except shodan.APIError as e:
                print(f"   ⚠️  Shodan API Error: {e}")

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates (Haversine formula)
        Returns distance in kilometers
        """
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _calculate_confidence(self, device_type: str, distance: float, time_correlation: str) -> str:
        """
        Calculate correlation confidence score
        """
        score = 0

        # Distance scoring
        if distance:
            if distance <= 1:
                score += 40
            elif distance <= 5:
                score += 30
            elif distance <= 10:
                score += 20
            else:
                score += 10

        # Time correlation scoring
        if time_correlation == "CRITICAL":
            score += 50
        elif time_correlation == "HIGH":
            score += 40
        elif time_correlation == "MEDIUM":
            score += 20

        # Device type scoring
        if device_type == 'c2_server':
            score += 10  # C2 servers are high value

        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def _add_demo_correlation(self, incident: Incident, correlation_type: str, radius_km: float):
        """
        Add demo correlation when no API available
        """
        demo = {
            'incident_id': incident.id,
            'incident_date': incident.sighting_date.isoformat(),
            'correlation_type': correlation_type,
            'note': 'DEMO DATA - Requires Shodan API key for real results',
            'expected_results': f'Would search {radius_km}km radius for {correlation_type}'
        }
        self.correlations.append(demo)

    def generate_correlation_report(self):
        """
        Generate comprehensive correlation report
        """
        print(f"\n{'='*80}")
        print("📊 CORRELATION ANALYSIS REPORT")
        print('='*80 + "\n")

        # Statistics
        total = len(self.correlations)
        by_type = {}
        by_confidence = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for corr in self.correlations:
            corr_type = corr.get('correlation_type', 'unknown')
            by_type[corr_type] = by_type.get(corr_type, 0) + 1

            confidence = corr.get('confidence', 'LOW')
            if confidence in by_confidence:
                by_confidence[confidence] += 1

        print(f"Total Correlations: {total}")
        print(f"\nBy Type:")
        for ctype, count in by_type.items():
            print(f"  {ctype}: {count}")

        print(f"\nBy Confidence:")
        for conf, count in by_confidence.items():
            print(f"  {conf}: {count}")

        # Save report
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_correlations': total,
            'statistics': {
                'by_type': by_type,
                'by_confidence': by_confidence
            },
            'correlations': self.correlations
        }

        output_file = 'shodan_incident_correlations.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Report saved: {output_file}\n")

        # Print high-value findings
        high_value = [c for c in self.correlations if c.get('confidence') in ['CRITICAL', 'HIGH']]
        if high_value:
            print(f"\n🚨 HIGH-VALUE FINDINGS ({len(high_value)}):\n")
            for finding in high_value[:10]:
                print(f"  [{finding.get('confidence')}] {finding.get('correlation_type')} - {finding.get('device_ip', 'N/A')}")
                if finding.get('time_correlation'):
                    print(f"      Time correlation: {finding['time_correlation']}")
                print()

    def close(self):
        self.db.close()


def main():
    """Main execution"""
    correlator = ShodanIncidentCorrelator()
    correlator.analyze_all_incidents()
    correlator.close()

    print("=" * 80)
    print("✅ CORRELATION ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nNext: Review shodan_incident_correlations.json for high-value findings\n")


if __name__ == '__main__':
    main()
