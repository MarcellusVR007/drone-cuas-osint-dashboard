#!/usr/bin/env python3
"""
Shodan Monitor for C-UAS Intelligence

Monitors:
1. Drone detection systems (DJI AeroScope, DroneShield, Dedrone)
2. Vulnerable C2 infrastructure (MAVLink, ArduPilot, PX4)
3. IP cameras near restricted areas (Schiphol, Eindhoven)
4. FPV drone streaming servers

Based on Shodan OSINT techniques
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict

# Note: Shodan API key required (get from https://account.shodan.io/)
# Set environment variable: export SHODAN_API_KEY="your_key_here"

try:
    import shodan
except ImportError:
    print("⚠️  Shodan library not installed")
    print("Install: pip3 install shodan")
    sys.exit(1)

class ShodanCUASMonitor:
    """
    Shodan-based C-UAS intelligence gathering
    """

    def __init__(self, api_key: str = None):
        """Initialize with Shodan API key"""
        self.api_key = api_key or os.getenv('SHODAN_API_KEY')

        if not self.api_key:
            print("⚠️  No Shodan API key found!")
            print("Set environment variable: export SHODAN_API_KEY='your_key'")
            print("Or get free key at: https://account.shodan.io/")
            self.api = None
        else:
            try:
                self.api = shodan.Shodan(self.api_key)
                print("✓ Shodan API initialized")
            except Exception as e:
                print(f"⚠️  Shodan API error: {e}")
                self.api = None

        self.results = {
            'drone_detection_systems': [],
            'c2_infrastructure': [],
            'ip_cameras': [],
            'fpv_streaming': []
        }

    def scan_drone_detection_systems(self, country: str = "NL"):
        """
        Find drone detection systems (AeroScope, DroneShield, Dedrone)
        """
        print(f"\n{'='*70}")
        print("🔍 SCANNING: Drone Detection Systems")
        print('='*70 + "\n")

        if not self.api:
            print("⚠️  Shodan API not available (using demo data)")
            return self._generate_demo_data('detection_systems')

        queries = [
            f'product:"DJI AeroScope" country:"{country}"',
            f'product:"DroneShield" country:"{country}"',
            f'product:"Dedrone" country:"{country}"',
            f'port:8080 "drone detection" country:"{country}"'
        ]

        for query in queries:
            try:
                print(f"Query: {query}")
                results = self.api.search(query, limit=10)

                for result in results['matches']:
                    device = {
                        'ip': result['ip_str'],
                        'port': result['port'],
                        'organization': result.get('org', 'Unknown'),
                        'location': f"{result.get('location', {}).get('city', 'Unknown')}, {result.get('location', {}).get('country_name', country)}",
                        'product': result.get('product', 'Unknown'),
                        'timestamp': result.get('timestamp', datetime.now().isoformat()),
                        'query': query
                    }

                    self.results['drone_detection_systems'].append(device)

                    print(f"  ✓ Found: {device['ip']} - {device['product']} ({device['organization']})")

            except shodan.APIError as e:
                print(f"  ⚠️  Shodan API Error: {e}")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

        print(f"\n✓ Total drone detection systems found: {len(self.results['drone_detection_systems'])}")

    def scan_c2_infrastructure(self, country: str = "NL"):
        """
        Find vulnerable drone C2 infrastructure (MAVLink, ArduPilot, PX4)
        """
        print(f"\n{'='*70}")
        print("🔍 SCANNING: Drone C2 Infrastructure")
        print('='*70 + "\n")

        if not self.api:
            print("⚠️  Shodan API not available (using demo data)")
            return self._generate_demo_data('c2_infrastructure')

        queries = [
            f'"autopilot" port:14550 country:"{country}"',  # MAVLink
            f'"ArduPilot" country:"{country}"',
            f'"PX4" country:"{country}"',
            f'port:5760 "ground control" country:"{country}"'
        ]

        for query in queries:
            try:
                print(f"Query: {query}")
                results = self.api.search(query, limit=10)

                for result in results['matches']:
                    c2_server = {
                        'ip': result['ip_str'],
                        'port': result['port'],
                        'organization': result.get('org', 'Unknown'),
                        'location': f"{result.get('location', {}).get('city', 'Unknown')}, {result.get('location', {}).get('country_name', country)}",
                        'vulnerability': 'Exposed C2 Protocol',
                        'timestamp': result.get('timestamp', datetime.now().isoformat()),
                        'query': query
                    }

                    self.results['c2_infrastructure'].append(c2_server)

                    print(f"  ⚠️  VULNERABLE: {c2_server['ip']}:{c2_server['port']} - {c2_server['organization']}")

            except shodan.APIError as e:
                print(f"  ⚠️  Shodan API Error: {e}")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

        print(f"\n⚠️  Total vulnerable C2 servers found: {len(self.results['c2_infrastructure'])}")

    def scan_ip_cameras_near_airports(self):
        """
        Find IP cameras near Schiphol, Eindhoven airports
        """
        print(f"\n{'='*70}")
        print("🔍 SCANNING: IP Cameras Near Restricted Areas")
        print('='*70 + "\n")

        if not self.api:
            print("⚠️  Shodan API not available (using demo data)")
            return self._generate_demo_data('ip_cameras')

        # Coordinates: Schiphol (52.308, 4.764), Eindhoven (51.450, 5.374)
        locations = [
            {'name': 'Schiphol Airport', 'geo': '52.308,4.764,10'},
            {'name': 'Eindhoven Airport', 'geo': '51.450,5.374,10'}
        ]

        for location in locations:
            try:
                print(f"Location: {location['name']}")
                query = f'geo:"{location["geo"]}" port:8080 has_screenshot:true'

                results = self.api.search(query, limit=20)

                for result in results['matches']:
                    camera = {
                        'ip': result['ip_str'],
                        'port': result['port'],
                        'organization': result.get('org', 'Unknown'),
                        'location': location['name'],
                        'distance_km': 'Within 10km',
                        'product': result.get('product', 'IP Camera'),
                        'timestamp': result.get('timestamp', datetime.now().isoformat())
                    }

                    self.results['ip_cameras'].append(camera)

                    print(f"  📹 Camera: {camera['ip']} - {camera['organization']}")

            except shodan.APIError as e:
                print(f"  ⚠️  Shodan API Error: {e}")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

        print(f"\n✓ Total IP cameras found: {len(self.results['ip_cameras'])}")

    def scan_fpv_streaming_servers(self, country: str = "NL"):
        """
        Find FPV drone streaming servers
        """
        print(f"\n{'='*70}")
        print("🔍 SCANNING: FPV Drone Streaming Servers")
        print('='*70 + "\n")

        if not self.api:
            print("⚠️  Shodan API not available (using demo data)")
            return self._generate_demo_data('fpv_streaming')

        queries = [
            f'port:554 title:"drone" country:"{country}"',  # RTSP
            f'port:1935 "live stream" drone country:"{country}"',  # RTMP
            f'"DJI" port:8080 country:"{country}"'
        ]

        for query in queries:
            try:
                print(f"Query: {query}")
                results = self.api.search(query, limit=5)

                for result in results['matches']:
                    stream = {
                        'ip': result['ip_str'],
                        'port': result['port'],
                        'organization': result.get('org', 'Unknown'),
                        'location': f"{result.get('location', {}).get('city', 'Unknown')}, {result.get('location', {}).get('country_name', country)}",
                        'protocol': 'RTSP' if result['port'] == 554 else 'RTMP' if result['port'] == 1935 else 'HTTP',
                        'timestamp': result.get('timestamp', datetime.now().isoformat())
                    }

                    self.results['fpv_streaming'].append(stream)

                    print(f"  📡 Stream: {stream['ip']}:{stream['port']} - {stream['protocol']}")

            except shodan.APIError as e:
                print(f"  ⚠️  Shodan API Error: {e}")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

        print(f"\n✓ Total FPV streams found: {len(self.results['fpv_streaming'])}")

    def _generate_demo_data(self, category: str) -> List[Dict]:
        """Generate demo data when no API key available"""
        demo_data = {
            'detection_systems': [
                {
                    'ip': '192.0.2.1',
                    'port': 8080,
                    'organization': 'Schiphol Group',
                    'location': 'Amsterdam, NL',
                    'product': 'DJI AeroScope Demo',
                    'timestamp': datetime.now().isoformat(),
                    'note': 'DEMO DATA - Get real Shodan API key'
                }
            ],
            'c2_infrastructure': [],
            'ip_cameras': [],
            'fpv_streaming': []
        }

        self.results[category] = demo_data.get(category, [])
        if self.results[category]:
            print(f"  ℹ️  Using demo data ({len(self.results[category])} entries)")
        return self.results[category]

    def generate_report(self, output_file: str = 'shodan_cuas_report.json'):
        """
        Generate intelligence report
        """
        print(f"\n{'='*70}")
        print("📊 GENERATING INTELLIGENCE REPORT")
        print('='*70 + "\n")

        report = {
            'generated_at': datetime.now().isoformat(),
            'scan_type': 'C-UAS Infrastructure Intelligence',
            'summary': {
                'drone_detection_systems': len(self.results['drone_detection_systems']),
                'vulnerable_c2_servers': len(self.results['c2_infrastructure']),
                'ip_cameras_near_airports': len(self.results['ip_cameras']),
                'fpv_streaming_servers': len(self.results['fpv_streaming'])
            },
            'findings': self.results,
            'recommendations': self._generate_recommendations()
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Report saved: {output_file}\n")

        # Print summary
        print("SUMMARY:")
        print(f"  🛡️  Drone Detection Systems: {report['summary']['drone_detection_systems']}")
        print(f"  ⚠️  Vulnerable C2 Servers: {report['summary']['vulnerable_c2_servers']}")
        print(f"  📹 IP Cameras (airports): {report['summary']['ip_cameras_near_airports']}")
        print(f"  📡 FPV Streams: {report['summary']['fpv_streaming_servers']}\n")

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if len(self.results['drone_detection_systems']) == 0:
            recommendations.append("⚠️  CRITICAL: No drone detection systems found in NL. Consider deploying AeroScope or DroneShield.")

        if len(self.results['c2_infrastructure']) > 0:
            recommendations.append(f"⚠️  {len(self.results['c2_infrastructure'])} vulnerable C2 servers detected. Recommend defensive monitoring.")

        if len(self.results['ip_cameras']) > 5:
            recommendations.append(f"ℹ️  {len(self.results['ip_cameras'])} IP cameras found near airports. Potential CCTV intelligence sources.")

        return recommendations

    def close(self):
        """Cleanup"""
        pass


def main():
    """Main execution"""
    print("=" * 80)
    print("SHODAN C-UAS INTELLIGENCE MONITOR")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize monitor
    monitor = ShodanCUASMonitor()

    # Run scans
    monitor.scan_drone_detection_systems(country="NL")
    monitor.scan_c2_infrastructure(country="NL")
    monitor.scan_ip_cameras_near_airports()
    monitor.scan_fpv_streaming_servers(country="NL")

    # Generate report
    report = monitor.generate_report()

    monitor.close()

    print("=" * 80)
    print("✅ SCAN COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review shodan_cuas_report.json")
    print("2. Set up monthly automated scans (cron)")
    print("3. Get Shodan API key for real data: https://account.shodan.io/\n")


if __name__ == '__main__':
    main()
