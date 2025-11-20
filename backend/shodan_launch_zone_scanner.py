#!/usr/bin/env python3
"""
Shodan Launch Zone Scanner
Infrastructure reconnaissance in calculated drone launch zones
Finds suspect devices: cameras, C2 servers, drone software
"""

import os
import shodan
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

class LaunchZoneShodanScanner:
    """Scan launch zones for suspect infrastructure using Shodan"""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.environ.get('SHODAN_API_KEY')

        if not api_key:
            raise ValueError("SHODAN_API_KEY not found in environment")

        self.api = shodan.Shodan(api_key)

        # Suspicious services/ports for drone operations
        self.suspect_patterns = {
            'drone_software': {
                'keywords': ['mavlink', 'qgroundcontrol', 'mission planner', 'ardupilot', 'px4'],
                'ports': [14550, 14551, 5760, 5761],  # MAVLink telemetry ports
                'risk': 'CRITICAL'
            },
            'cameras': {
                'keywords': ['webcam', 'ipcam', 'camera'],
                'ports': [554, 8554, 8080, 80],  # RTSP, HTTP streams
                'risk': 'HIGH'
            },
            'remote_access': {
                'keywords': ['vnc', 'rdp', 'teamviewer'],
                'ports': [5900, 3389, 5938],
                'risk': 'HIGH'
            },
            'c2_infrastructure': {
                'keywords': ['tor', 'proxy', 'vpn', 'tunnel'],
                'ports': [9050, 1080, 8888, 3128],
                'risk': 'MEDIUM'
            },
            'iot_devices': {
                'keywords': ['raspberry', 'arduino', 'esp8266', 'esp32'],
                'ports': [80, 443, 8080, 22],
                'risk': 'MEDIUM'
            }
        }

    def scan_launch_zone(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10,
        incident_date: Optional[str] = None
    ) -> Dict:
        """
        Scan Shodan for devices in launch zone

        Args:
            latitude: Center of launch zone
            longitude: Center of launch zone
            radius_km: Radius in kilometers
            incident_date: ISO date of incident (for timing analysis)

        Returns:
            Dict with scan results and suspect devices
        """

        results = {
            'scan_area': {
                'center': {'lat': latitude, 'lon': longitude},
                'radius_km': radius_km,
                'area_km2': round(3.14159 * radius_km * radius_km, 2)
            },
            'scan_time': datetime.now().isoformat(),
            'total_devices': 0,
            'suspect_devices': [],
            'summary_by_category': {},
            'high_risk_count': 0
        }

        # Build Shodan query for geographic area
        geo_query = f"geo:{latitude},{longitude},{radius_km}"

        try:
            # Scan for each category
            for category, patterns in self.suspect_patterns.items():
                category_results = []

                # Query by keywords
                for keyword in patterns['keywords']:
                    query = f"{geo_query} {keyword}"
                    try:
                        search_results = self.api.search(query, limit=20)

                        for result in search_results['matches']:
                            device = self._parse_device(result, category, patterns['risk'])

                            # Timing analysis if incident date provided
                            if incident_date:
                                device['timing_analysis'] = self._analyze_timing(
                                    result.get('timestamp'),
                                    incident_date
                                )

                            category_results.append(device)

                    except shodan.APIError as e:
                        print(f"Shodan API error for {keyword}: {e}")
                        continue

                # Query by ports
                for port in patterns['ports']:
                    query = f"{geo_query} port:{port}"
                    try:
                        search_results = self.api.search(query, limit=10)

                        for result in search_results['matches']:
                            device = self._parse_device(result, category, patterns['risk'])

                            if incident_date:
                                device['timing_analysis'] = self._analyze_timing(
                                    result.get('timestamp'),
                                    incident_date
                                )

                            # Check if already found (avoid duplicates)
                            if not any(d['ip'] == device['ip'] for d in category_results):
                                category_results.append(device)

                    except shodan.APIError as e:
                        print(f"Shodan API error for port {port}: {e}")
                        continue

                # Store category results
                if category_results:
                    results['summary_by_category'][category] = {
                        'count': len(category_results),
                        'risk_level': patterns['risk']
                    }
                    results['suspect_devices'].extend(category_results)

            # Sort by risk and suspicion score
            results['suspect_devices'] = sorted(
                results['suspect_devices'],
                key=lambda x: (x['risk_level'] == 'CRITICAL', x.get('suspicion_score', 0)),
                reverse=True
            )

            results['total_devices'] = len(results['suspect_devices'])
            results['high_risk_count'] = len([
                d for d in results['suspect_devices']
                if d['risk_level'] in ['CRITICAL', 'HIGH']
            ])

            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)

        except Exception as e:
            results['error'] = str(e)

        return results

    def _parse_device(self, shodan_result: Dict, category: str, risk: str) -> Dict:
        """Parse Shodan result into device info"""

        device = {
            'ip': shodan_result.get('ip_str'),
            'port': shodan_result.get('port'),
            'category': category,
            'risk_level': risk,
            'organization': shodan_result.get('org', 'Unknown'),
            'isp': shodan_result.get('isp', 'Unknown'),
            'asn': shodan_result.get('asn', 'Unknown'),
            'hostname': shodan_result.get('hostnames', [''])[0] if shodan_result.get('hostnames') else None,
            'product': shodan_result.get('product'),
            'version': shodan_result.get('version'),
            'last_update': shodan_result.get('timestamp'),
            'location': {
                'country': shodan_result.get('location', {}).get('country_name'),
                'city': shodan_result.get('location', {}).get('city'),
                'latitude': shodan_result.get('location', {}).get('latitude'),
                'longitude': shodan_result.get('location', {}).get('longitude')
            },
            'vulns': shodan_result.get('vulns', []),
            'tags': shodan_result.get('tags', []),
            'suspicion_score': 0
        }

        # Calculate suspicion score
        score = 0

        # Critical indicators
        if category == 'drone_software':
            score += 50
        if device['vulns']:
            score += 20
        if 'raspberry' in str(device.get('product', '')).lower():
            score += 15
        if device['port'] in [14550, 14551, 5760]:  # MAVLink
            score += 30

        device['suspicion_score'] = min(score, 100)

        return device

    def _analyze_timing(self, device_timestamp: str, incident_date: str) -> Dict:
        """Analyze timing correlation between device activity and incident"""

        if not device_timestamp:
            return {'status': 'unknown', 'note': 'No timestamp available'}

        try:
            device_time = datetime.fromisoformat(device_timestamp.replace('Z', '+00:00'))
            incident_time = datetime.fromisoformat(incident_date)

            time_diff = (incident_time - device_time).total_seconds() / 3600  # hours

            if abs(time_diff) < 24:
                return {
                    'status': 'CRITICAL',
                    'note': f'Device active {abs(time_diff):.1f}h before incident',
                    'suspicion': 'HIGH - Recent setup detected'
                }
            elif abs(time_diff) < 168:  # 1 week
                return {
                    'status': 'SUSPICIOUS',
                    'note': f'Device active {abs(time_diff)/24:.1f} days before incident',
                    'suspicion': 'MEDIUM - Pre-incident activity'
                }
            else:
                return {
                    'status': 'normal',
                    'note': f'Device seen {abs(time_diff)/24:.1f} days before incident',
                    'suspicion': 'LOW'
                }
        except Exception as e:
            return {'status': 'error', 'note': str(e)}

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate investigation recommendations based on findings"""

        recommendations = []

        if results['high_risk_count'] > 0:
            recommendations.append(
                f"🚨 URGENT: {results['high_risk_count']} high-risk devices found - prioritize investigation"
            )

        # Category-specific recommendations
        categories = results['summary_by_category']

        if 'drone_software' in categories:
            recommendations.append(
                f"🎯 CRITICAL: {categories['drone_software']['count']} devices with drone software detected - "
                "Request ISP customer data via legal channels"
            )

        if 'cameras' in categories:
            recommendations.append(
                f"📹 {categories['cameras']['count']} cameras found - Check for reconnaissance footage of target"
            )

        if 'remote_access' in categories:
            recommendations.append(
                f"🔐 {categories['remote_access']['count']} remote access services - Potential C2 infrastructure"
            )

        if results['total_devices'] == 0:
            recommendations.append(
                "ℹ️ No suspect devices found - Consider: maritime launch, mobile setup, or outside scan radius"
            )

        # General recommendations
        recommendations.extend([
            "📊 Cross-reference IPs with other incidents for pattern matching",
            "🌐 Query ASN ownership for infrastructure attribution",
            "⏱️ Monitor devices for continued activity post-incident"
        ])

        return recommendations

    def get_device_details(self, ip: str) -> Dict:
        """Get detailed Shodan data for specific IP"""
        try:
            host = self.api.host(ip)
            return {
                'ip': ip,
                'organization': host.get('org'),
                'operating_system': host.get('os'),
                'ports': host.get('ports', []),
                'vulnerabilities': host.get('vulns', []),
                'last_update': host.get('last_update'),
                'tags': host.get('tags', []),
                'location': host.get('location'),
                'asn': host.get('asn'),
                'isp': host.get('isp'),
                'data': host.get('data', [])
            }
        except shodan.APIError as e:
            return {'error': str(e)}


if __name__ == "__main__":
    # Test scan
    scanner = LaunchZoneShodanScanner()

    # Terneuzen incident coordinates
    results = scanner.scan_launch_zone(
        latitude=51.3358,
        longitude=3.8258,
        radius_km=10,
        incident_date="2025-11-18T20:00:00"
    )

    print(json.dumps(results, indent=2))
