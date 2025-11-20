#!/usr/bin/env python3
"""
Palantir-Style Channel Discovery Engine
Implements graph-based intelligence discovery for Telegram channels

Based on:
- Palantir Gotham ontology-driven analysis
- NSA XKEYSCORE link analysis
- CIA link mapping tradecraft
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import networkx as nx
from typing import List, Dict, Set, Tuple
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import Incident

# Try to import optional dependencies
try:
    from networkx.algorithms import community
    COMMUNITY_AVAILABLE = True
except ImportError:
    COMMUNITY_AVAILABLE = False
    print("⚠️  NetworkX community detection not available. Install: pip install networkx[default]")


class PalantirChannelDiscovery:
    """
    Palantir-style intelligence discovery engine
    """

    def __init__(self, json_file: str):
        self.json_file = json_file
        self.graph = nx.DiGraph()
        self.messages = []
        self.channels = {}
        self.known_threats = ['rybar', 'intelslava']  # Seed channels
        self.discovered_channels = set()

    def load_data(self):
        """Load Telegram messages from JSON"""
        print("=" * 70)
        print("PALANTIR-STYLE CHANNEL DISCOVERY ENGINE")
        print("=" * 70)
        print(f"\n📂 Loading: {self.json_file}")

        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.messages = json.load(f)

        print(f"✓ Loaded {len(self.messages)} messages")

        # Extract unique channels
        for msg in self.messages:
            channel = msg.get('channel')
            if channel and channel not in self.channels:
                self.channels[channel] = {
                    'name': channel,
                    'title': msg.get('channel_title', channel),
                    'message_count': 0,
                    'total_views': 0,
                    'total_forwards': 0,
                    'intel_keywords': 0,
                    'messages': []
                }

            if channel:
                self.channels[channel]['message_count'] += 1
                self.channels[channel]['total_views'] += msg.get('views', 0)
                self.channels[channel]['total_forwards'] += msg.get('forwards', 0)
                if msg.get('intel_keywords'):
                    self.channels[channel]['intel_keywords'] += len(msg['intel_keywords'])
                self.channels[channel]['messages'].append(msg)

        print(f"✓ Found {len(self.channels)} unique channels")

    def build_graph(self):
        """Build network graph from messages (Phase 1: Ontology)"""
        print("\n" + "=" * 70)
        print("PHASE 1: BUILD INTELLIGENCE GRAPH")
        print("=" * 70)

        # Add channel nodes
        for channel_name, data in self.channels.items():
            self.graph.add_node(
                channel_name,
                type='channel',
                title=data['title'],
                messages=data['message_count'],
                views=data['total_views'],
                forwards=data['total_forwards'],
                intel_density=data['intel_keywords'] / max(data['message_count'], 1),
                is_seed=channel_name in self.known_threats
            )

        print(f"✓ Added {len(self.channels)} channel nodes")

        # Add message nodes and edges
        message_nodes = 0
        forward_edges = 0
        mention_edges = 0

        for msg in self.messages:
            msg_id = f"msg_{msg.get('message_id', message_nodes)}"
            channel = msg.get('channel')

            # Add message node
            self.graph.add_node(
                msg_id,
                type='message',
                channel=channel,
                timestamp=msg.get('post_date'),
                content=msg.get('content', '')[:100],  # First 100 chars
                views=msg.get('views', 0),
                forwards=msg.get('forwards', 0)
            )
            message_nodes += 1

            # Add edge: channel -> message
            if channel:
                self.graph.add_edge(channel, msg_id, relation='POSTED')

            # Detect channel mentions in content
            content = msg.get('content', '')
            mentioned_channels = re.findall(r'@(\w+)', content)
            for mentioned in mentioned_channels:
                if mentioned in self.channels:
                    self.graph.add_edge(
                        channel,
                        mentioned,
                        relation='MENTIONED',
                        weight=1
                    )
                    mention_edges += 1

        print(f"✓ Added {message_nodes} message nodes")
        print(f"✓ Added {mention_edges} channel mention edges")
        print(f"✓ Total nodes: {self.graph.number_of_nodes()}")
        print(f"✓ Total edges: {self.graph.number_of_edges()}")

    def expand_from_seeds(self, max_hops: int = 2) -> Set[str]:
        """
        Phase 2: BFS expansion from known threat channels
        Palantir's "Find Linked" feature
        """
        print("\n" + "=" * 70)
        print("PHASE 2: GRAPH EXPANSION (BFS from seed channels)")
        print("=" * 70)

        discovered = set()
        visited = set()
        queue = [(seed, 0) for seed in self.known_threats]

        print(f"\n🌱 Seed channels: {', '.join(self.known_threats)}")
        print(f"🔍 Expanding {max_hops} hops...")

        while queue:
            current, hops = queue.pop(0)

            if current in visited or hops >= max_hops:
                continue

            visited.add(current)

            # Get neighbors (channels this one is connected to)
            neighbors = list(self.graph.neighbors(current))

            for neighbor in neighbors:
                # Only consider channel nodes
                if self.graph.nodes[neighbor].get('type') == 'channel':
                    if neighbor not in self.known_threats and neighbor not in discovered:
                        discovered.add(neighbor)
                        queue.append((neighbor, hops + 1))
                        print(f"  Hop {hops+1}: Discovered {neighbor} (from {current})")

        print(f"\n✓ Discovered {len(discovered)} new channels via graph expansion")
        self.discovered_channels.update(discovered)

        return discovered

    def detect_communities(self) -> List[Set[str]]:
        """
        Phase 3: Community detection
        Palantir's "Find Groups" feature - identify handler networks
        """
        print("\n" + "=" * 70)
        print("PHASE 3: COMMUNITY DETECTION (Handler Networks)")
        print("=" * 70)

        if not COMMUNITY_AVAILABLE:
            print("⚠️  Skipping - NetworkX community module not available")
            return []

        # Build undirected graph of just channels
        channel_graph = nx.Graph()

        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'channel':
                channel_graph.add_node(node, **self.graph.nodes[node])

        # Add edges with weights (mention frequency)
        for u, v, data in self.graph.edges(data=True):
            if (self.graph.nodes[u].get('type') == 'channel' and
                self.graph.nodes[v].get('type') == 'channel'):
                weight = data.get('weight', 1)
                if channel_graph.has_edge(u, v):
                    channel_graph[u][v]['weight'] += weight
                else:
                    channel_graph.add_edge(u, v, weight=weight)

        print(f"📊 Channel graph: {channel_graph.number_of_nodes()} nodes, {channel_graph.number_of_edges()} edges")

        # Louvain community detection
        communities = community.louvain_communities(channel_graph, seed=42)

        print(f"\n✓ Detected {len(communities)} communities\n")

        for i, comm in enumerate(communities, 1):
            channels_in_comm = sorted(list(comm))

            # Check if contains known threats
            has_threat = any(ch in self.known_threats for ch in channels_in_comm)

            print(f"Community {i}: {len(channels_in_comm)} channels {' 🚨 CONTAINS KNOWN THREAT' if has_threat else ''}")
            print(f"  Channels: {', '.join(channels_in_comm[:10])}")

            if has_threat:
                # Flag entire community for monitoring
                for ch in channels_in_comm:
                    if ch not in self.known_threats:
                        self.discovered_channels.add(ch)
                        print(f"    → Flagged {ch} (guilt by association)")

        return communities

    def calculate_network_centrality(self) -> Dict[str, float]:
        """
        Calculate PageRank centrality - identify influential channels
        Palantir's "Influencer Analysis"
        """
        print("\n" + "=" * 70)
        print("PHASE 4: CENTRALITY ANALYSIS (Influence Ranking)")
        print("=" * 70)

        # Build channel-only graph
        channel_graph = nx.DiGraph()

        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'channel':
                channel_graph.add_node(node)

        for u, v, data in self.graph.edges(data=True):
            if (self.graph.nodes.get(u, {}).get('type') == 'channel' and
                self.graph.nodes.get(v, {}).get('type') == 'channel'):
                channel_graph.add_edge(u, v, weight=data.get('weight', 1))

        # Calculate PageRank
        try:
            pagerank = nx.pagerank(channel_graph, weight='weight')
        except:
            # Fallback if graph is not connected
            pagerank = {ch: 1/len(channel_graph) for ch in channel_graph.nodes()}

        # Sort by influence
        sorted_channels = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)

        print(f"\n📈 Top 10 Most Influential Channels:\n")
        for i, (channel, score) in enumerate(sorted_channels[:10], 1):
            is_seed = "🌱" if channel in self.known_threats else "  "
            print(f"{i:2d}. {is_seed} {channel:<30} PageRank: {score:.4f}")

        return pagerank

    def score_channels(self, pagerank: Dict[str, float]) -> List[Tuple[str, float, Dict]]:
        """
        Phase 5: ML-based scoring (Palantir's relevance model)
        Multi-factor scoring algorithm
        """
        print("\n" + "=" * 70)
        print("PHASE 5: MULTI-FACTOR CHANNEL SCORING")
        print("=" * 70)

        db = SessionLocal()
        incidents = db.query(Incident).all()
        db.close()

        scored_channels = []

        for channel_name, channel_data in self.channels.items():
            if channel_name in self.known_threats:
                continue  # Skip seeds

            # Factor 1: Distance to known threats (BFS)
            distance_score = self._calculate_threat_proximity(channel_name)

            # Factor 2: Content quality (intel keywords density)
            intel_density = channel_data['intel_keywords'] / max(channel_data['message_count'], 1)
            content_score = min(intel_density * 50, 100)

            # Factor 3: Network centrality (PageRank)
            centrality = pagerank.get(channel_name, 0)
            network_score = min(centrality * 10000, 100)  # Normalize

            # Factor 4: Temporal correlation to incidents
            temporal_score = self._calculate_temporal_correlation(channel_data, incidents)

            # Factor 5: Engagement metrics (views, forwards)
            avg_views = channel_data['total_views'] / max(channel_data['message_count'], 1)
            engagement_score = min(avg_views / 100, 100)

            # Weighted combination (Palantir's secret sauce)
            final_score = (
                distance_score * 0.35 +    # Proximity to threats (highest weight)
                temporal_score * 0.25 +    # Incident correlation
                content_score * 0.20 +     # Content quality
                network_score * 0.15 +     # Network influence
                engagement_score * 0.05    # Engagement
            )

            metadata = {
                'distance_to_threat': distance_score,
                'content_quality': content_score,
                'network_centrality': network_score,
                'temporal_correlation': temporal_score,
                'engagement': engagement_score,
                'messages': channel_data['message_count'],
                'avg_views': avg_views
            }

            scored_channels.append((channel_name, final_score, metadata))

        # Sort by score
        scored_channels.sort(key=lambda x: x[1], reverse=True)

        print(f"\n🎯 Top 20 Highest Priority Channels:\n")
        print(f"{'Rank':<6}{'Channel':<30}{'Score':<10}{'Reason'}")
        print("-" * 70)

        for i, (channel, score, meta) in enumerate(scored_channels[:20], 1):
            # Determine primary reason
            reasons = []
            if meta['distance_to_threat'] > 50:
                reasons.append("Close to threats")
            if meta['temporal_correlation'] > 50:
                reasons.append("Incident correlation")
            if meta['content_quality'] > 50:
                reasons.append("High intel density")

            reason = ", ".join(reasons) if reasons else "Network position"

            print(f"{i:<6}{channel:<30}{score:>6.1f}    {reason}")

        return scored_channels

    def _calculate_threat_proximity(self, channel: str) -> float:
        """Calculate shortest path distance to known threats"""
        min_distance = float('inf')

        for threat in self.known_threats:
            try:
                distance = nx.shortest_path_length(self.graph, threat, channel)
                min_distance = min(min_distance, distance)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if min_distance == float('inf'):
            return 0

        # Convert distance to score (closer = higher score)
        # 1 hop = 100, 2 hops = 75, 3 hops = 50, 4+ = 25
        return max(0, 100 - (min_distance - 1) * 25)

    def _calculate_temporal_correlation(self, channel_data: Dict, incidents: List) -> float:
        """Calculate correlation with known incidents"""
        if not incidents:
            return 0

        correlation_count = 0

        for incident in incidents:
            incident_time = datetime.combine(incident.sighting_date, datetime.min.time())

            # Count messages within ±48h of incident
            for msg in channel_data['messages']:
                try:
                    msg_time = datetime.fromisoformat(msg['post_date'].replace('Z', '+00:00'))
                    time_diff = abs((msg_time - incident_time).total_seconds() / 3600)

                    if time_diff <= 48:  # Within 48 hours
                        # Check for keywords
                        if msg.get('intel_keywords') or msg.get('location_keywords'):
                            correlation_count += 1
                except:
                    continue

        # Normalize to 0-100
        return min(correlation_count * 10, 100)

    def generate_report(self, scored_channels: List[Tuple[str, float, Dict]]):
        """Generate discovery report"""
        print("\n" + "=" * 70)
        print("INTELLIGENCE DISCOVERY REPORT")
        print("=" * 70)

        report = {
            'generated_at': datetime.now().isoformat(),
            'source_file': self.json_file,
            'seed_channels': self.known_threats,
            'total_channels_analyzed': len(self.channels),
            'total_discovered': len(self.discovered_channels),
            'graph_stats': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges()
            },
            'top_priorities': []
        }

        # Top 30 for review
        for channel, score, meta in scored_channels[:30]:
            report['top_priorities'].append({
                'channel': channel,
                'priority_score': round(score, 2),
                'metadata': {k: round(v, 2) if isinstance(v, float) else v
                           for k, v in meta.items()},
                'recommendation': self._get_recommendation(score)
            })

        # Save report
        report_file = f"channel_discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Discovery Summary:")
        print(f"  Total channels analyzed: {len(self.channels)}")
        print(f"  Channels discovered: {len(self.discovered_channels)}")
        print(f"  High priority (score ≥70): {sum(1 for _, s, _ in scored_channels if s >= 70)}")
        print(f"  Medium priority (score 50-70): {sum(1 for _, s, _ in scored_channels if 50 <= s < 70)}")
        print(f"  Low priority (score <50): {sum(1 for _, s, _ in scored_channels if s < 50)}")

        print(f"\n💾 Full report saved: {report_file}")

        # Generate monitoring recommendations
        print(f"\n🎯 MONITORING RECOMMENDATIONS:")
        print(f"\nTier 1 (Critical - Monitor every 1 hour):")
        tier1 = [ch for ch, score, _ in scored_channels if score >= 80]
        for ch in tier1[:10]:
            print(f"  • {ch}")

        print(f"\nTier 2 (High - Monitor every 2 hours):")
        tier2 = [ch for ch, score, _ in scored_channels if 60 <= score < 80]
        for ch in tier2[:10]:
            print(f"  • {ch}")

        print(f"\nTier 3 (Medium - Monitor every 6 hours):")
        tier3 = [ch for ch, score, _ in scored_channels if 40 <= score < 60]
        for ch in tier3[:10]:
            print(f"  • {ch}")

        return report

    def _get_recommendation(self, score: float) -> str:
        """Get monitoring recommendation based on score"""
        if score >= 80:
            return "TIER 1 - Critical (monitor hourly)"
        elif score >= 60:
            return "TIER 2 - High (monitor every 2h)"
        elif score >= 40:
            return "TIER 3 - Medium (monitor every 6h)"
        else:
            return "LOW PRIORITY - Review weekly"

    def run_full_discovery(self):
        """Execute complete Palantir-style discovery pipeline"""
        # Load data
        self.load_data()

        # Build graph
        self.build_graph()

        # Phase 2: Expand from seeds
        self.expand_from_seeds(max_hops=2)

        # Phase 3: Community detection
        if COMMUNITY_AVAILABLE:
            self.detect_communities()

        # Phase 4: Centrality analysis
        pagerank = self.calculate_network_centrality()

        # Phase 5: Score all channels
        scored_channels = self.score_channels(pagerank)

        # Generate report
        report = self.generate_report(scored_channels)

        print("\n" + "=" * 70)
        print("✅ DISCOVERY COMPLETE")
        print("=" * 70)
        print("\n🚀 Next steps:")
        print("  1. Review top 20 channels manually")
        print("  2. Add Tier 1 channels to monitoring (1h frequency)")
        print("  3. Run discovery again in 7 days to find new channels")

        return report


def main():
    """Main execution"""
    json_file = 'telegram_gru_dutch_20251117_084031.json'

    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        print("Please ensure the Telegram JSON export is in the current directory.")
        return

    # Run discovery
    engine = PalantirChannelDiscovery(json_file)
    engine.run_full_discovery()


if __name__ == "__main__":
    main()
