#!/usr/bin/env python3
"""
Phone Number Intelligence Visualization

Creates interactive HTML page showing:
1. Phone numbers found in Telegram messages
2. Links to drone incidents
3. Geographic distribution
4. Temporal patterns
5. Network graphs
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal
from backend.models import (
    TelegramChannel, TelegramMessage, Incident,
    RestrictedArea, IntelligenceLink
)

class PhoneIntelligenceVisualizer:
    """
    Create visual intelligence briefing
    """

    def __init__(self):
        self.db = SessionLocal()

    def generate_html_report(self, output_file: str = "phone_intelligence_report.html"):
        """
        Generate interactive HTML intelligence report
        """
        print("=" * 80)
        print("GENERATING PHONE INTELLIGENCE VISUALIZATION")
        print("=" * 80 + "\n")

        # Load phone data
        with open('phone_numbers_extracted.json', 'r', encoding='utf-8') as f:
            phone_data = json.load(f)

        # Get incidents
        incidents = self.db.query(Incident).all()

        # Build HTML
        html = self._build_html(phone_data, incidents)

        # Write file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Report generated: {output_file}\n")
        print(f"   Open in browser to view visualization\n")

        return output_file

    def _build_html(self, phone_data: Dict, incidents: List) -> str:
        """
        Build HTML page
        """
        # Get detailed phone analysis
        phone_details = self._analyze_phones(phone_data)

        # Get incident correlations
        incident_correlations = self._find_incident_correlations(phone_data, incidents)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phone Number Intelligence - Drone C-UAS OSINT</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            color: #e0e0e0;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #1a1f3a 0%, #2d1b3d 100%);
            padding: 40px 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}

        h1 {{
            color: #00d9ff;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
        }}

        .subtitle {{
            color: #888;
            font-size: 1.1em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: #1a1f3a;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #00d9ff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .stat-value {{
            font-size: 2.5em;
            color: #00d9ff;
            font-weight: bold;
        }}

        .stat-label {{
            color: #888;
            text-transform: uppercase;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .section {{
            background: #1a1f3a;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .section-title {{
            color: #00d9ff;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 2px solid #2d1b3d;
            padding-bottom: 10px;
        }}

        .phone-card {{
            background: #0f1425;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #ff6b6b;
        }}

        .phone-card.high-value {{
            border-left-color: #ff4757;
            background: linear-gradient(135deg, #1a0f1f 0%, #0f1425 100%);
        }}

        .phone-card.wagner {{
            border-left-color: #ff0000;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
        }}

        .phone-number {{
            font-size: 1.5em;
            color: #00d9ff;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}

        .phone-meta {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
            flex-wrap: wrap;
        }}

        .meta-badge {{
            background: #2d1b3d;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }}

        .meta-badge.critical {{
            background: #ff4757;
            color: #fff;
        }}

        .context {{
            background: #0a0e1a;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 3px solid #555;
            max-height: 150px;
            overflow-y: auto;
        }}

        .incident-link {{
            background: #2d1b3d;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}

        .incident-link strong {{
            color: #ffa502;
        }}

        .chart-container {{
            background: #0f1425;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}

        .bar {{
            background: linear-gradient(90deg, #00d9ff 0%, #0066ff 100%);
            height: 30px;
            border-radius: 5px;
            margin-bottom: 10px;
            position: relative;
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: #fff;
            font-weight: bold;
        }}

        .bar-label {{
            position: absolute;
            right: 10px;
        }}

        .network-viz {{
            background: #0a0e1a;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
        }}

        .node {{
            display: inline-block;
            background: #2d1b3d;
            padding: 10px 20px;
            border-radius: 20px;
            margin: 5px;
            border: 2px solid #00d9ff;
        }}

        .node.wagner {{
            border-color: #ff0000;
            background: #3d1b1b;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2d1b3d;
        }}

        th {{
            background: #2d1b3d;
            color: #00d9ff;
            font-weight: bold;
        }}

        tr:hover {{
            background: #0f1425;
        }}

        .tag {{
            display: inline-block;
            background: #ffa502;
            color: #000;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
        }}

        .tag.wagner {{
            background: #ff0000;
            color: #fff;
        }}

        .tag.financial {{
            background: #2ed573;
        }}

        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            margin-top: 50px;
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📞 PHONE NUMBER INTELLIGENCE BRIEFING</h1>
            <div class="subtitle">Drone C-UAS OSINT Analysis • Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>

        <!-- Key Metrics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{phone_data['total_unique_numbers']}</div>
                <div class="stat-label">Unique Phone Numbers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(phone_data['by_country'].values())}</div>
                <div class="stat-label">Total Occurrences</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([p for p, d in phone_data['phone_numbers'].items() if d['occurrence_count'] >= 10])}</div>
                <div class="stat-label">High-Frequency Numbers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(incidents)}</div>
                <div class="stat-label">Drone Incidents in DB</div>
            </div>
        </div>

        <!-- Geographic Distribution -->
        <div class="section">
            <h2 class="section-title">🌍 Geographic Distribution</h2>
            <div class="chart-container">
                {self._generate_country_chart(phone_data['by_country'])}
            </div>
        </div>

        <!-- Critical Findings -->
        {self._generate_critical_findings(phone_details)}

        <!-- All Phone Numbers -->
        {self._generate_phone_table(phone_details)}

        <!-- Incident Correlations -->
        {self._generate_incident_section(incident_correlations, incidents)}

        <!-- Maltego Integration -->
        <div class="section">
            <h2 class="section-title">🕸️ Maltego Graph Visualization</h2>
            <p style="margin-bottom: 20px;">
                The command chain and phone number networks have been exported to Maltego format:
            </p>
            <div class="network-viz">
                <div style="margin-bottom: 20px;">
                    <strong>📊 Files Generated:</strong><br><br>
                    <code style="background: #0a0e1a; padding: 10px; border-radius: 5px; display: inline-block;">
                        maltego_command_chain.graphml (15KB)<br>
                        maltego_temporal_patterns.graphml (4.9KB)<br>
                        phone_numbers_extracted.json
                    </code>
                </div>
                <p style="margin-top: 20px; color: #888;">
                    → Open these files in Maltego Desktop for interactive network analysis
                </p>
            </div>
        </div>

        <footer>
            <p>🔒 CLASSIFICATION: INTERNAL OSINT ANALYSIS</p>
            <p>Generated by Drone C-UAS Intelligence System</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Data Source: {len(self.db.query(TelegramMessage).all())} Telegram messages • {len(self.db.query(TelegramChannel).all())} channels monitored
            </p>
        </footer>
    </div>
</body>
</html>
"""
        return html

    def _analyze_phones(self, phone_data: Dict) -> List[Dict]:
        """
        Analyze phones for intelligence value
        """
        phones = []

        for number, data in phone_data['phone_numbers'].items():
            # Determine intelligence value
            value_score = 0
            tags = []

            # High frequency = high value
            if data['occurrence_count'] >= 15:
                value_score += 50
                tags.append('HIGH-FREQUENCY')

            if data['occurrence_count'] >= 10:
                value_score += 30

            # Wagner/Rubicon keywords in context
            for context in data['contexts']:
                if 'Рубикон' in context or 'рубикон' in context:
                    value_score += 100
                    tags.append('WAGNER')
                if 'военн' in context or 'контракт' in context:
                    value_score += 50
                    tags.append('MILITARY')
                if 'СБЕР' in context or 'Сбер' in context or 'карта' in context:
                    value_score += 30
                    tags.append('FINANCIAL')

            # Country-based scoring
            if data['country'] == 'Netherlands':
                value_score += 20
                tags.append('NL-BASED')

            phones.append({
                'number': number,
                'data': data,
                'value_score': value_score,
                'tags': tags,
                'priority': 'CRITICAL' if value_score >= 100 else 'HIGH' if value_score >= 50 else 'MEDIUM'
            })

        # Sort by value score
        phones.sort(key=lambda x: x['value_score'], reverse=True)

        return phones

    def _find_incident_correlations(self, phone_data: Dict, incidents: List) -> List[Dict]:
        """
        Find temporal correlations between phone mentions and incidents
        """
        correlations = []

        for incident in incidents:
            for number, data in phone_data['phone_numbers'].items():
                # Check if phone was mentioned around incident date
                first_seen = datetime.fromisoformat(data['first_seen'])
                last_seen = datetime.fromisoformat(data['last_seen'])

                incident_date = datetime.combine(incident.sighting_date, datetime.min.time())

                # Within 30 days?
                if abs((first_seen - incident_date).days) <= 30 or abs((last_seen - incident_date).days) <= 30:
                    correlations.append({
                        'phone': number,
                        'incident': incident,
                        'time_delta': min(abs((first_seen - incident_date).days), abs((last_seen - incident_date).days)),
                        'confidence': 'HIGH' if abs((first_seen - incident_date).days) <= 7 else 'MEDIUM'
                    })

        return correlations

    def _generate_country_chart(self, by_country: Dict) -> str:
        """
        Generate HTML bar chart for country distribution
        """
        max_count = max(by_country.values()) if by_country else 1

        html = ""
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True):
            width = (count / max_count) * 100
            html += f"""
                <div class="bar" style="width: {width}%;">
                    {country}
                    <span class="bar-label">{count} numbers</span>
                </div>
            """

        return html

    def _generate_critical_findings(self, phones: List[Dict]) -> str:
        """
        Generate critical findings section
        """
        critical = [p for p in phones if p['priority'] == 'CRITICAL']

        if not critical:
            return ""

        html = """
        <div class="section">
            <h2 class="section-title">🚨 CRITICAL FINDINGS</h2>
        """

        for phone in critical:
            tags_html = ''.join([f'<span class="tag wagner" if "WAGNER" in tag else "tag">{tag}</span>' for tag in phone['tags']])

            contexts_html = '<br><br>'.join([
                f'<div class="context">{ctx[:300]}...</div>'
                for ctx in phone['data']['contexts'][:3]
            ])

            html += f"""
            <div class="phone-card wagner">
                <div class="phone-number">{phone['number']}</div>
                <div class="phone-meta">
                    {tags_html}
                    <span class="meta-badge">{phone['data']['country']}</span>
                    <span class="meta-badge critical">{phone['data']['occurrence_count']} occurrences</span>
                    <span class="meta-badge">{len(phone['data']['channels'])} channels</span>
                </div>
                <div style="margin-top: 15px;">
                    <strong>Intelligence Assessment:</strong><br>
                    {'WAGNER/RUBICON RECRUITMENT CENTER' if 'WAGNER' in phone['tags'] else 'High-value military contact'}
                </div>
                {contexts_html}
            </div>
            """

        html += "</div>"
        return html

    def _generate_phone_table(self, phones: List[Dict]) -> str:
        """
        Generate table of all phones
        """
        html = """
        <div class="section">
            <h2 class="section-title">📊 All Phone Numbers (Sorted by Value)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Phone Number</th>
                        <th>Country</th>
                        <th>Occurrences</th>
                        <th>Channels</th>
                        <th>Priority</th>
                        <th>Tags</th>
                    </tr>
                </thead>
                <tbody>
        """

        for phone in phones:
            tags_html = ''.join([f'<span class="tag {"wagner" if tag == "WAGNER" else "financial" if tag == "FINANCIAL" else ""}">{tag}</span>' for tag in phone['tags']])

            html += f"""
                <tr>
                    <td><code>{phone['number']}</code></td>
                    <td>{phone['data']['country']}</td>
                    <td>{phone['data']['occurrence_count']}</td>
                    <td>{len(phone['data']['channels'])}</td>
                    <td><strong>{phone['priority']}</strong></td>
                    <td>{tags_html}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _generate_incident_section(self, correlations: List[Dict], incidents: List) -> str:
        """
        Generate incident correlation section
        """
        html = f"""
        <div class="section">
            <h2 class="section-title">🎯 Phone Number ↔ Drone Incident Correlations</h2>
            <p style="margin-bottom: 20px;">
                Temporal analysis of phone number mentions relative to drone incidents.
                Shows numbers that appeared in Telegram messages within 30 days of incidents.
            </p>
        """

        if not correlations:
            html += """
            <div style="padding: 20px; text-align: center; color: #888;">
                No direct temporal correlations found within 30-day window.
                This suggests phone numbers are for general recruitment/operations, not incident-specific.
            </div>
            """
        else:
            for corr in correlations[:10]:
                incident = corr['incident']
                location = incident.restricted_area.name if incident.restricted_area else "Unknown Location"

                html += f"""
                <div class="incident-link">
                    <strong>Phone:</strong> <code>{corr['phone']}</code><br>
                    <strong>Incident:</strong> {location} ({incident.sighting_date})<br>
                    <strong>Time Delta:</strong> {corr['time_delta']} days<br>
                    <strong>Confidence:</strong> {corr['confidence']}
                </div>
                """

        # Add incident list
        html += f"""
            <h3 style="margin-top: 30px; color: #00d9ff;">All Drone Incidents in Database ({len(incidents)})</h3>
            <table style="margin-top: 15px;">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Location</th>
                        <th>Coordinates</th>
                    </tr>
                </thead>
                <tbody>
        """

        for incident in incidents[:20]:
            location = incident.restricted_area.name if incident.restricted_area else "Unknown"
            coords = f"{incident.latitude}, {incident.longitude}" if incident.latitude else "N/A"

            html += f"""
                <tr>
                    <td>{incident.sighting_date}</td>
                    <td>{location}</td>
                    <td><code>{coords}</code></td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

    def close(self):
        self.db.close()


def main():
    """Main execution"""
    print("=" * 80)
    print("PHONE INTELLIGENCE VISUALIZATION GENERATOR")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    visualizer = PhoneIntelligenceVisualizer()
    output_file = visualizer.generate_html_report()
    visualizer.close()

    print("=" * 80)
    print("✅ VISUALIZATION COMPLETE")
    print("=" * 80)
    print(f"\n🌐 Open in browser:")
    print(f"   file://{os.path.abspath(output_file)}\n")
    print("Or run:")
    print(f"   open {output_file}\n")


if __name__ == '__main__':
    main()
