#!/usr/bin/env python3
"""
Maltego Graph Exporter for C-UAS Intelligence

Exports our OSINT data to Maltego format for visual analysis:
1. Telegram command chain (channel → channel relationships)
2. Channel → Incident correlations
3. Social network (users, channels, messages)
4. Temporal patterns

Output: .graphml format (importable in Maltego)
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal
from backend.models import (
    TelegramChannel, TelegramMessage, Incident,
    RestrictedArea, IntelligenceLink
)

class MaltegoExporter:
    """
    Export C-UAS OSINT data to Maltego GraphML format
    """

    def __init__(self):
        self.db = SessionLocal()

    def export_command_chain(self, output_file: str = "maltego_command_chain.graphml"):
        """
        Export Telegram command chain network

        Nodes: Channels
        Edges: Forward relationships, mention relationships, temporal correlations
        """
        print("=" * 80)
        print("MALTEGO EXPORT: COMMAND CHAIN NETWORK")
        print("=" * 80 + "\n")

        # Create GraphML structure
        root = ET.Element("graphml")
        root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")

        # Define node attributes
        for key_id, attr_name, attr_type in [
            ("d0", "label", "string"),
            ("d1", "channel_type", "string"),
            ("d2", "subscriber_count", "int"),
            ("d3", "message_count", "int"),
            ("d4", "threat_level", "string"),
            ("d5", "description", "string"),
        ]:
            key = ET.SubElement(root, "key")
            key.set("id", key_id)
            key.set("for", "node")
            key.set("attr.name", attr_name)
            key.set("attr.type", attr_type)

        # Define edge attributes
        for key_id, attr_name, attr_type in [
            ("d10", "relationship", "string"),
            ("d11", "weight", "int"),
            ("d12", "confidence", "string"),
        ]:
            key = ET.SubElement(root, "key")
            key.set("id", key_id)
            key.set("for", "edge")
            key.set("attr.name", attr_name)
            key.set("attr.type", attr_type)

        graph = ET.SubElement(root, "graph")
        graph.set("id", "G")
        graph.set("edgedefault", "directed")

        # Get all channels
        channels = self.db.query(TelegramChannel).all()

        print(f"📊 Exporting {len(channels)} channels...\n")

        # Add channel nodes
        channel_nodes = {}
        for channel in channels:
            node = ET.SubElement(graph, "node")
            node.set("id", f"channel_{channel.id}")

            # Add attributes
            self._add_data(node, "d0", channel.username or channel.title)
            self._add_data(node, "d1", channel.channel_type or "unknown")
            self._add_data(node, "d2", str(channel.member_count or 0))

            # Count messages
            msg_count = self.db.query(TelegramMessage).filter(
                TelegramMessage.channel_id == channel.id
            ).count()
            self._add_data(node, "d3", str(msg_count))

            # Determine threat level based on channel type
            threat_level = self._assess_threat_level(channel)
            self._add_data(node, "d4", threat_level)

            self._add_data(node, "d5", channel.description or "")

            channel_nodes[channel.id] = node

            print(f"  ✓ {channel.username or channel.title[:30]} ({msg_count} messages, {threat_level})")

        # Build edges based on relationships
        print(f"\n🔗 Building relationships...\n")

        edges_added = 0

        # 1. Forward relationships (if we have forward data)
        forwards = self.db.query(TelegramMessage).filter(
            TelegramMessage.forward_from_channel_id.isnot(None)
        ).all()

        forward_counts = defaultdict(int)
        for msg in forwards:
            key = (msg.channel_id, msg.forward_from_channel_id)
            forward_counts[key] += 1

        for (from_id, to_id), count in forward_counts.items():
            if from_id in channel_nodes and to_id in channel_nodes:
                edge = ET.SubElement(graph, "edge")
                edge.set("id", f"e_{edges_added}")
                edge.set("source", f"channel_{from_id}")
                edge.set("target", f"channel_{to_id}")

                self._add_data(edge, "d10", "forwards")
                self._add_data(edge, "d11", str(count))
                self._add_data(edge, "d12", "HIGH" if count > 10 else "MEDIUM")

                edges_added += 1

        print(f"  ✓ Forward relationships: {len(forward_counts)}")

        # 2. Co-mention relationships (channels mentioned in same messages)
        print(f"  → Analyzing co-mentions...")
        co_mentions = self._find_co_mentions(channels)

        for (ch1_id, ch2_id), count in co_mentions.items():
            if ch1_id in channel_nodes and ch2_id in channel_nodes:
                edge = ET.SubElement(graph, "edge")
                edge.set("id", f"e_{edges_added}")
                edge.set("source", f"channel_{ch1_id}")
                edge.set("target", f"channel_{ch2_id}")

                self._add_data(edge, "d10", "co_mentioned")
                self._add_data(edge, "d11", str(count))
                self._add_data(edge, "d12", "MEDIUM" if count > 5 else "LOW")

                edges_added += 1

        print(f"  ✓ Co-mention relationships: {len(co_mentions)}")

        # 3. Incident correlations (using IntelligenceLink universal table)
        print(f"  → Analyzing incident correlations...")

        # Find links where entity_a is channel and entity_b is incident (or vice versa)
        incident_links = self.db.query(IntelligenceLink).filter(
            ((IntelligenceLink.entity_a_type == 'channel') & (IntelligenceLink.entity_b_type == 'incident')) |
            ((IntelligenceLink.entity_a_type == 'incident') & (IntelligenceLink.entity_b_type == 'channel'))
        ).all()

        incident_node_ids = set()
        for link in incident_links:
            # Determine which is channel and which is incident
            if link.entity_a_type == 'incident':
                incident_id = link.entity_a_id
                channel_id = link.entity_b_id
            else:
                incident_id = link.entity_b_id
                channel_id = link.entity_a_id

            incident = self.db.query(Incident).get(incident_id)
            if not incident:
                continue

            # Add incident node if not exists
            incident_node_id = f"incident_{incident.id}"
            if incident_node_id not in incident_node_ids:
                node = ET.SubElement(graph, "node")
                node.set("id", incident_node_id)

                location_name = incident.restricted_area.name if incident.restricted_area else "Unknown"
                self._add_data(node, "d0", f"Incident: {location_name}")
                self._add_data(node, "d1", "incident")
                self._add_data(node, "d4", "HIGH")
                self._add_data(node, "d5", f"Date: {incident.sighting_date}, Location: {location_name}")

                incident_node_ids.add(incident_node_id)

            # Add edge from channel to incident
            if channel_id in channel_nodes:
                edge = ET.SubElement(graph, "edge")
                edge.set("id", f"e_{edges_added}")
                edge.set("source", f"channel_{channel_id}")
                edge.set("target", incident_node_id)

                self._add_data(edge, "d10", link.relationship_type or "discusses_incident")
                self._add_data(edge, "d11", str(link.strength or 1))
                self._add_data(edge, "d12", link.confidence or "MEDIUM")

                edges_added += 1

        print(f"  ✓ Incident correlations: {len(incident_links)}")
        print(f"\n✓ Total edges: {edges_added}")

        # Write to file
        tree = ET.ElementTree(root)
        xml_str = self._prettify(root)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        print(f"\n✅ Exported to: {output_file}")
        print(f"   Nodes: {len(channels) + len(incident_node_ids)}")
        print(f"   Edges: {edges_added}\n")

        return output_file

    def export_temporal_analysis(self, output_file: str = "maltego_temporal_patterns.graphml"):
        """
        Export temporal patterns: when do channels post about incidents?
        """
        print("=" * 80)
        print("MALTEGO EXPORT: TEMPORAL PATTERNS")
        print("=" * 80 + "\n")

        root = ET.Element("graphml")
        root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")

        # Define attributes
        for key_id, attr_name, attr_type in [
            ("d0", "label", "string"),
            ("d1", "entity_type", "string"),
            ("d2", "timestamp", "string"),
            ("d3", "threat_level", "string"),
        ]:
            key = ET.SubElement(root, "key")
            key.set("id", key_id)
            key.set("for", "node")
            key.set("attr.name", attr_name)
            key.set("attr.type", attr_type)

        for key_id, attr_name in [("d10", "time_delta_hours"), ("d11", "relationship")]:
            key = ET.SubElement(root, "key")
            key.set("id", key_id)
            key.set("for", "edge")
            key.set("attr.name", attr_name)
            key.set("attr.type", "string")

        graph = ET.SubElement(root, "graph")
        graph.set("id", "G")
        graph.set("edgedefault", "directed")

        # Get incidents with linked messages
        incidents = self.db.query(Incident).all()

        edges_added = 0
        nodes_added = 0

        print(f"📊 Analyzing temporal patterns for {len(incidents)} incidents...\n")

        for incident in incidents[:20]:  # Limit for readability
            # Add incident node
            incident_id = f"incident_{incident.id}"
            node = ET.SubElement(graph, "node")
            node.set("id", incident_id)

            location = incident.restricted_area.name if incident.restricted_area else "Unknown"
            self._add_data(node, "d0", f"{location} - {incident.sighting_date}")
            self._add_data(node, "d1", "incident")
            self._add_data(node, "d2", str(incident.sighting_date))
            self._add_data(node, "d3", "HIGH")

            nodes_added += 1

            # Find messages discussing this incident via IntelligenceLink
            links = self.db.query(IntelligenceLink).filter(
                ((IntelligenceLink.entity_a_type == 'incident') & (IntelligenceLink.entity_a_id == incident.id)) |
                ((IntelligenceLink.entity_b_type == 'incident') & (IntelligenceLink.entity_b_id == incident.id))
            ).all()

            for link in links:
                # Get channel ID from link
                if link.entity_a_type == 'channel':
                    channel_id = link.entity_a_id
                elif link.entity_b_type == 'channel':
                    channel_id = link.entity_b_id
                else:
                    continue

                # Find messages from this channel around incident date
                messages = self.db.query(TelegramMessage).filter(
                    TelegramMessage.channel_id == channel_id
                ).order_by(TelegramMessage.timestamp.desc()).limit(100).all()

                for msg in messages:
                    if not msg.timestamp:
                        continue

                    # Calculate time delta
                    time_delta = abs((msg.timestamp.date() - incident.sighting_date).days)

                    if time_delta <= 14:  # Within 2 weeks
                        # Add message node
                        msg_id = f"msg_{msg.id}"
                        node = ET.SubElement(graph, "node")
                        node.set("id", msg_id)

                        channel = self.db.query(TelegramChannel).get(msg.channel_id)
                        channel_name = channel.username if channel else "Unknown"

                        text_preview = (msg.text_content[:50] + "...") if msg.text_content else "No text"
                        self._add_data(node, "d0", f"{channel_name}: {text_preview}")
                        self._add_data(node, "d1", "message")
                        self._add_data(node, "d2", str(msg.timestamp))
                        self._add_data(node, "d3", "MEDIUM")

                        nodes_added += 1

                        # Add edge
                        edge = ET.SubElement(graph, "edge")
                        edge.set("id", f"e_{edges_added}")
                        edge.set("source", msg_id)
                        edge.set("target", incident_id)

                        self._add_data(edge, "d10", f"{time_delta * 24}h")
                        self._add_data(edge, "d11", f"posted_{time_delta}_days_from_incident")

                        edges_added += 1

        # Write to file
        xml_str = self._prettify(root)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        print(f"\n✅ Exported to: {output_file}")
        print(f"   Nodes: {nodes_added}")
        print(f"   Edges: {edges_added}\n")

        return output_file

    def _add_data(self, parent, key, value):
        """Add data element to node/edge"""
        data = ET.SubElement(parent, "data")
        data.set("key", key)
        data.text = str(value)

    def _assess_threat_level(self, channel: TelegramChannel) -> str:
        """Assess threat level based on channel characteristics"""
        if not channel.channel_type:
            return "UNKNOWN"

        high_threat = ["military", "gru", "russian_state", "propaganda"]
        medium_threat = ["news", "independent", "activist"]

        channel_type_lower = channel.channel_type.lower()

        for ht in high_threat:
            if ht in channel_type_lower:
                return "HIGH"

        for mt in medium_threat:
            if mt in channel_type_lower:
                return "MEDIUM"

        return "LOW"

    def _find_co_mentions(self, channels: List[TelegramChannel]) -> Dict[Tuple[int, int], int]:
        """
        Find channels that are mentioned together in messages
        """
        co_mentions = defaultdict(int)

        # Get all messages with text
        messages = self.db.query(TelegramMessage).filter(
            TelegramMessage.text_content.isnot(None)
        ).all()

        channel_usernames = {ch.username.lower(): ch.id for ch in channels if ch.username}

        for msg in messages:
            text_lower = msg.text_content.lower()

            # Find mentioned channels in this message
            mentioned = []
            for username, ch_id in channel_usernames.items():
                if f"@{username}" in text_lower or username in text_lower:
                    mentioned.append(ch_id)

            # Create co-mention pairs
            for i, ch1 in enumerate(mentioned):
                for ch2 in mentioned[i+1:]:
                    key = tuple(sorted([ch1, ch2]))
                    co_mentions[key] += 1

        return dict(co_mentions)

    def _prettify(self, elem):
        """Return pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def close(self):
        self.db.close()


def main():
    """Main execution"""
    print("=" * 80)
    print("MALTEGO GRAPH EXPORTER FOR C-UAS INTELLIGENCE")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    exporter = MaltegoExporter()

    # Export command chain
    file1 = exporter.export_command_chain()

    # Export temporal patterns
    file2 = exporter.export_temporal_analysis()

    exporter.close()

    print("=" * 80)
    print("✅ MALTEGO EXPORT COMPLETE")
    print("=" * 80)
    print("\n📊 Files created:")
    print(f"  1. {file1} - Command chain network")
    print(f"  2. {file2} - Temporal patterns")
    print("\n🔧 Import in Maltego:")
    print("  1. Open Maltego Desktop")
    print("  2. File → Import → Graph from Table...")
    print("  3. Select .graphml file")
    print("  4. Choose layout: Organic/Hierarchical")
    print("\n💡 Analysis tips:")
    print("  • Look for central nodes (high degree)")
    print("  • Identify clusters (coordinated networks)")
    print("  • Trace paths from incident → channels")
    print("  • Filter by threat_level attribute\n")


if __name__ == '__main__':
    main()
