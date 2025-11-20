#!/usr/bin/env python3
"""
Shodan-Incident Correlation DEMO
Shows what the analysis would find with real Shodan data
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict
import random

sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal
from backend.models import Incident

def generate_demo_correlations():
    """
    Generate realistic demo correlations to show the concept
    """
    print("=" * 80)
    print("SHODAN-INCIDENT TEMPORAL CORRELATION DEMO")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("⚠️  NOTE: Using demo data - Real Shodan API requires query credits\n")

    db = SessionLocal()

    # Get all incidents with location data
    incidents = db.query(Incident).filter(
        Incident.latitude.isnot(None),
        Incident.longitude.isnot(None)
    ).limit(10).all()  # Limit to 10 for demo

    print(f"📊 Analyzing {len(incidents)} incidents (demo sample)\\n")

    correlations = []

    for i, incident in enumerate(incidents, 1):
        print(f"\\n{'='*80}")
        print(f"[{i}/{len(incidents)}] INCIDENT ANALYSIS")
        print('='*80)
        print(f"📍 Location: {incident.restricted_area.name if incident.restricted_area else 'Unknown'}")
        print(f"📅 Date: {incident.sighting_date}")
        print(f"🌍 Coordinates: {incident.latitude}, {incident.longitude}")

        # Simulate findings based on location

        # 1. IP Cameras (always find some)
        print(f"\\n🎥 Searching IP cameras within 5km...")
        num_cameras = random.randint(3, 8)
        print(f"   ✓ Found {num_cameras} cameras")

        for j in range(num_cameras):
            # Simulate temporal correlation
            hours_from_incident = random.uniform(0, 200)

            if hours_from_incident <= 168:  # Within 7 days
                time_correlation = "HIGH"
                print(f"   🔥 HIGH CORRELATION: Camera 185.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)} seen {hours_from_incident:.1f}h from incident!")
            else:
                time_correlation = "MEDIUM"

            correlation = {
                'incident_id': incident.id,
                'incident_date': incident.sighting_date.isoformat(),
                'incident_location': f"{incident.latitude}, {incident.longitude}",
                'correlation_type': 'ip_camera',
                'device_ip': f"185.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'device_port': 8080,
                'device_product': random.choice(['Hikvision IP Camera', 'Dahua NVR', 'Axis Camera', 'Generic IP Camera']),
                'device_org': random.choice(['KPN B.V.', 'Ziggo', 'Vodafone NL', 'Private Residence']),
                'distance_km': round(random.uniform(0.5, 5.0), 2),
                'device_timestamp': (incident.sighting_date - timedelta(hours=hours_from_incident)).isoformat(),
                'time_correlation': time_correlation,
                'confidence': 'HIGH' if time_correlation == "HIGH" else 'MEDIUM'
            }
            correlations.append(correlation)

        # 2. C2 Servers (occasionally find critical ones)
        print(f"\\n🎮 Searching drone C2 servers...")

        if random.random() < 0.2:  # 20% chance of finding C2 server
            hours_from_incident = random.uniform(0, 48)

            if hours_from_incident <= 24:
                time_correlation = "CRITICAL"
                print(f"   🚨 CRITICAL: C2 server active {hours_from_incident:.1f}h from incident!")
            else:
                time_correlation = "HIGH"
                print(f"   ⚠️  HIGH: C2 server active {hours_from_incident:.1f}h from incident!")

            correlation = {
                'incident_id': incident.id,
                'incident_date': incident.sighting_date.isoformat(),
                'correlation_type': 'c2_server',
                'device_ip': f"92.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'device_port': 14550,
                'device_product': random.choice(['MAVLink Ground Station', 'ArduPilot GCS', 'PX4 Autopilot']),
                'c2_protocol': 'MAVLink',
                'device_org': random.choice(['KPN B.V.', 'Unknown', 'T-Mobile Netherlands']),
                'distance_km': round(random.uniform(0.1, 10.0), 2),
                'device_timestamp': (incident.sighting_date - timedelta(hours=hours_from_incident)).isoformat(),
                'time_correlation': time_correlation,
                'confidence': 'CRITICAL'
            }
            correlations.append(correlation)
        else:
            print(f"   ⚠️  No C2 servers found")

        # 3. FPV Streams (rarely find)
        print(f"\\n📡 Searching FPV streaming activity...")

        if random.random() < 0.15:  # 15% chance
            hours_from_incident = random.uniform(0, 72)

            if hours_from_incident <= 48:
                print(f"   ⚠️  FPV stream active {hours_from_incident:.1f}h from incident!")

                correlation = {
                    'incident_id': incident.id,
                    'incident_date': incident.sighting_date.isoformat(),
                    'correlation_type': 'fpv_stream',
                    'device_ip': f"188.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    'device_port': random.choice([554, 1935]),
                    'stream_protocol': random.choice(['RTSP', 'RTMP']),
                    'device_timestamp': (incident.sighting_date - timedelta(hours=hours_from_incident)).isoformat(),
                    'time_delta_hours': round(hours_from_incident, 1),
                    'confidence': 'HIGH' if hours_from_incident <= 24 else 'MEDIUM'
                }
                correlations.append(correlation)
        else:
            print(f"   ⚠️  No FPV streams found")

        # 4. Detection Systems (very rare)
        print(f"\\n🛡️  Searching drone detection systems...")

        if random.random() < 0.05:  # 5% chance (near airports)
            print(f"   🚨 CRITICAL: Detection system found!")

            correlation = {
                'incident_id': incident.id,
                'incident_date': incident.sighting_date.isoformat(),
                'correlation_type': 'detection_system',
                'device_ip': f"195.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'system_type': random.choice(['DJI AeroScope', 'DroneShield', 'Dedrone']),
                'device_org': random.choice(['Schiphol Group', 'Royal Netherlands Marechaussee', 'Unknown']),
                'note': 'CRITICAL: This system may have detected the incident!'
            }
            correlations.append(correlation)
        else:
            print(f"   ⚠️  No detection systems found")

    # Generate report
    print(f"\\n{'='*80}")
    print("📊 CORRELATION ANALYSIS REPORT")
    print('='*80 + "\\n")

    # Statistics
    total = len(correlations)
    by_type = {}
    by_confidence = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    for corr in correlations:
        corr_type = corr.get('correlation_type', 'unknown')
        by_type[corr_type] = by_type.get(corr_type, 0) + 1

        confidence = corr.get('confidence', 'LOW')
        if confidence in by_confidence:
            by_confidence[confidence] += 1

    print(f"Total Correlations: {total}")
    print(f"\\nBy Type:")
    for ctype, count in by_type.items():
        print(f"  {ctype}: {count}")

    print(f"\\nBy Confidence:")
    for conf, count in by_confidence.items():
        print(f"  {conf}: {count}")

    # Save report
    report = {
        'generated_at': datetime.now().isoformat(),
        'mode': 'DEMO',
        'note': 'This is demo data showing what real Shodan analysis would find',
        'total_correlations': total,
        'statistics': {
            'by_type': by_type,
            'by_confidence': by_confidence
        },
        'correlations': correlations
    }

    output_file = 'shodan_incident_correlations_DEMO.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\\n✓ Report saved: {output_file}\\n")

    # Print high-value findings
    high_value = [c for c in correlations if c.get('confidence') in ['CRITICAL', 'HIGH']]
    if high_value:
        print(f"\\n🚨 HIGH-VALUE FINDINGS ({len(high_value)}):\\n")
        for finding in high_value[:10]:
            print(f"  [{finding.get('confidence')}] {finding.get('correlation_type')} - {finding.get('device_ip', 'N/A')}")
            if finding.get('time_correlation'):
                print(f"      Time correlation: {finding['time_correlation']}")
            if finding.get('c2_protocol'):
                print(f"      Protocol: {finding['c2_protocol']}")
            print()

    db.close()

    print("=" * 80)
    print("✅ DEMO ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\\nWhat this shows:")
    print(f"  • IP cameras found near {len([c for c in correlations if c['correlation_type'] == 'ip_camera'])} incidents")
    print(f"  • C2 servers correlated with {len([c for c in correlations if c['correlation_type'] == 'c2_server'])} incidents")
    print(f"  • {len([c for c in correlations if c.get('time_correlation') == 'CRITICAL'])} CRITICAL temporal correlations (±24h)")
    print(f"\\nWith real Shodan API credits, this would show:")
    print(f"  ✓ Actual IP addresses of cameras/servers active at incident times")
    print(f"  ✓ Precise timestamps of device activity")
    print(f"  ✓ Geographic correlation with incident locations")
    print(f"  ✓ Potential evidence for attribution\\n")

if __name__ == '__main__':
    generate_demo_correlations()
