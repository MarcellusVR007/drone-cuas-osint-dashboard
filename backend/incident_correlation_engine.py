#!/usr/bin/env python3
"""
Incident Correlation Engine
Detects temporal correlations between drone incidents and OSINT signals

Features:
- Telegram activity spike detection (±24h around incidents)
- Forum discussion correlation
- Statistical anomaly detection (z-score based)
- Automated alert generation
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json
from collections import defaultdict
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import (
    Incident, TelegramMessage, TelegramChannel, AviationForumPost,
    IncidentCorrelation
)
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session


class IncidentCorrelationEngine:
    """Engine for detecting correlations between incidents and OSINT signals"""

    def __init__(self, db: Session = None, time_window_hours: int = 24):
        self.db = db or SessionLocal()
        self.time_window_hours = time_window_hours
        self.z_score_threshold = 2.5  # Statistical significance threshold

    def analyze_all_incidents(self, limit: Optional[int] = None) -> Dict:
        """
        Analyze all incidents for correlations with OSINT signals

        Args:
            limit: Maximum number of incidents to analyze (None = all)

        Returns:
            Dictionary with analysis results
        """
        print("=" * 70)
        print("INCIDENT CORRELATION ANALYSIS")
        print("=" * 70)

        # Get incidents ordered by most recent
        query = self.db.query(Incident).order_by(Incident.sighting_date.desc())
        if limit:
            query = query.limit(limit)

        incidents = query.all()
        print(f"\n📊 Analyzing {len(incidents)} incidents...")

        results = {
            "total_incidents": len(incidents),
            "incidents_with_correlations": 0,
            "telegram_correlations": 0,
            "forum_correlations": 0,
            "high_confidence_correlations": 0,
            "correlations": []
        }

        for incident in incidents:
            print(f"\n🔍 Incident #{incident.id}: {incident.title}")
            print(f"   Date: {incident.sighting_date}, Location: {incident.latitude}, {incident.longitude}")

            # Analyze Telegram activity
            telegram_corr = self.analyze_telegram_correlation(incident)

            # Analyze forum activity
            forum_corr = self.analyze_forum_correlation(incident)

            # Combine results
            incident_correlations = []
            if telegram_corr:
                incident_correlations.extend(telegram_corr)
                results["telegram_correlations"] += len(telegram_corr)

            if forum_corr:
                incident_correlations.extend(forum_corr)
                results["forum_correlations"] += len(forum_corr)

            if incident_correlations:
                results["incidents_with_correlations"] += 1

                # Save correlations to database
                for corr_data in incident_correlations:
                    self.save_correlation(incident.id, corr_data)

                    if corr_data["correlation_strength"] >= 0.7:
                        results["high_confidence_correlations"] += 1

                results["correlations"].append({
                    "incident_id": incident.id,
                    "incident_title": incident.title,
                    "correlations": incident_correlations
                })

        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Total incidents analyzed: {results['total_incidents']}")
        print(f"Incidents with correlations: {results['incidents_with_correlations']}")
        print(f"  - Telegram correlations: {results['telegram_correlations']}")
        print(f"  - Forum correlations: {results['forum_correlations']}")
        print(f"  - High confidence (≥0.7): {results['high_confidence_correlations']}")

        return results

    def analyze_telegram_correlation(self, incident: Incident) -> List[Dict]:
        """
        Detect Telegram activity spikes around incident timestamp

        Returns:
            List of correlation dictionaries
        """
        # Get incident timestamp
        incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())
        if incident.sighting_time:
            try:
                hours, minutes = map(int, incident.sighting_time.split(':'))
                incident_dt = incident_dt.replace(hour=hours, minute=minutes)
            except:
                pass

        # Define time windows
        spike_start = incident_dt - timedelta(hours=self.time_window_hours)
        spike_end = incident_dt + timedelta(hours=self.time_window_hours)

        # Get baseline (30 days prior, excluding spike window)
        baseline_end = incident_dt - timedelta(hours=self.time_window_hours)
        baseline_start = baseline_end - timedelta(days=30)

        correlations = []

        # Get all channels
        channels = self.db.query(TelegramChannel).all()

        for channel in channels:
            # Count messages in spike window
            spike_count = self.db.query(TelegramMessage).filter(
                and_(
                    TelegramMessage.channel_id == channel.id,
                    TelegramMessage.timestamp >= spike_start,
                    TelegramMessage.timestamp <= spike_end
                )
            ).count()

            if spike_count == 0:
                continue

            # Count messages in baseline period
            baseline_messages = self.db.query(TelegramMessage).filter(
                and_(
                    TelegramMessage.channel_id == channel.id,
                    TelegramMessage.timestamp >= baseline_start,
                    TelegramMessage.timestamp < baseline_end
                )
            ).all()

            if len(baseline_messages) < 10:  # Need sufficient baseline data
                continue

            # Calculate daily average in baseline
            baseline_days = (baseline_end - baseline_start).days
            daily_avg = len(baseline_messages) / baseline_days

            # Expected count in spike window
            spike_window_days = (spike_end - spike_start).total_seconds() / (24 * 3600)
            expected_count = daily_avg * spike_window_days

            if expected_count == 0:
                continue

            # Calculate z-score
            # Get daily counts for standard deviation
            daily_counts = defaultdict(int)
            for msg in baseline_messages:
                day = msg.timestamp.date()
                daily_counts[day] += 1

            if len(daily_counts) < 5:  # Need enough days for std dev
                continue

            daily_values = list(daily_counts.values())
            std_dev = statistics.stdev(daily_values) if len(daily_values) > 1 else 1

            z_score = (spike_count - expected_count) / (std_dev + 0.1)  # Add epsilon to avoid div by zero

            # Only flag significant anomalies
            if z_score >= self.z_score_threshold:
                # Calculate correlation strength (normalize z-score to 0-1)
                correlation_strength = min(z_score / 10.0, 1.0)  # z=10 = max strength

                # Get sample messages from spike window
                spike_messages = self.db.query(TelegramMessage).filter(
                    and_(
                        TelegramMessage.channel_id == channel.id,
                        TelegramMessage.timestamp >= spike_start,
                        TelegramMessage.timestamp <= spike_end
                    )
                ).limit(5).all()

                keywords = self._extract_keywords(spike_messages)

                time_delta_hours = int((incident_dt - spike_start).total_seconds() / 3600)

                correlation = {
                    "correlation_type": "telegram_spike",
                    "source_id": channel.id,
                    "source_table": "telegram_channels",
                    "time_delta_hours": time_delta_hours,
                    "correlation_strength": correlation_strength,
                    "description": f"Activity spike detected in {channel.title or channel.username}: "
                                   f"{spike_count} messages (expected: {expected_count:.1f}, z-score: {z_score:.2f})",
                    "keywords_matched": json.dumps(keywords),
                    "metadata": {
                        "channel_username": channel.username,
                        "spike_count": spike_count,
                        "expected_count": expected_count,
                        "z_score": z_score,
                        "baseline_daily_avg": daily_avg
                    }
                }

                correlations.append(correlation)
                print(f"   ⚡ Telegram spike: {channel.username} (z={z_score:.2f}, strength={correlation_strength:.2f})")

        return correlations

    def analyze_forum_correlation(self, incident: Incident) -> List[Dict]:
        """
        Detect forum discussions around incident timestamp

        Returns:
            List of correlation dictionaries
        """
        # Get incident timestamp
        incident_dt = datetime.combine(incident.sighting_date, datetime.min.time())
        if incident.sighting_time:
            try:
                hours, minutes = map(int, incident.sighting_time.split(':'))
                incident_dt = incident_dt.replace(hour=hours, minute=minutes)
            except:
                pass

        # Define search window
        search_start = incident_dt - timedelta(hours=self.time_window_hours)
        search_end = incident_dt + timedelta(hours=self.time_window_hours)

        correlations = []

        # Find forum posts in time window with relevant keywords
        keywords = [
            "drone", "uav", "unmanned", "quadcopter",
            "schiphol", "zaventem", "brussels", "airport",
            "military base", "air force", "restricted airspace"
        ]

        # Get posts in time window
        forum_posts = self.db.query(AviationForumPost).filter(
            and_(
                AviationForumPost.post_timestamp >= search_start,
                AviationForumPost.post_timestamp <= search_end
            )
        ).all()

        for post in forum_posts:
            content_lower = (post.post_content or "").lower()
            thread_title_lower = (post.thread_title or "").lower()

            matched_keywords = []
            for keyword in keywords:
                if keyword in content_lower or keyword in thread_title_lower:
                    matched_keywords.append(keyword)

            if matched_keywords:
                # Calculate correlation strength based on:
                # 1. Number of keywords matched
                # 2. Temporal proximity to incident
                keyword_score = min(len(matched_keywords) / 3.0, 1.0)  # Max 3 keywords = 1.0

                time_diff_hours = abs((post.post_timestamp - incident_dt).total_seconds() / 3600)
                temporal_score = max(0, 1.0 - (time_diff_hours / self.time_window_hours))

                correlation_strength = (keyword_score + temporal_score) / 2.0

                # Check if post precedes official report (potential insider knowledge)
                precedes_report = post.post_timestamp < incident_dt

                time_delta_hours = int((post.post_timestamp - incident_dt).total_seconds() / 3600)

                correlation = {
                    "correlation_type": "forum_discussion",
                    "source_id": post.id,
                    "source_table": "aviation_forum_posts",
                    "time_delta_hours": time_delta_hours,
                    "correlation_strength": correlation_strength,
                    "description": f"Forum post on {post.forum_source}: {post.thread_title[:100]}",
                    "keywords_matched": json.dumps(matched_keywords),
                    "metadata": {
                        "forum_source": post.forum_source,
                        "post_author": post.post_author,
                        "precedes_incident": precedes_report,
                        "post_url": post.post_url
                    }
                }

                correlations.append(correlation)
                print(f"   💬 Forum post: {post.forum_source} ({len(matched_keywords)} keywords, strength={correlation_strength:.2f})")

        return correlations

    def _extract_keywords(self, messages: List[TelegramMessage]) -> List[str]:
        """Extract relevant keywords from messages"""
        keywords = set()
        target_terms = [
            "drone", "uav", "quadcopter", "fpv",
            "schiphol", "airport", "airbase", "vliegveld",
            "military", "air force", "luchtmacht"
        ]

        for msg in messages:
            if not msg.text_content:
                continue

            text_lower = msg.text_content.lower()
            for term in target_terms:
                if term in text_lower:
                    keywords.add(term)

        return list(keywords)

    def save_correlation(self, incident_id: int, correlation_data: Dict):
        """Save correlation to database"""
        try:
            existing = self.db.query(IncidentCorrelation).filter(
                and_(
                    IncidentCorrelation.incident_id == incident_id,
                    IncidentCorrelation.correlation_type == correlation_data["correlation_type"],
                    IncidentCorrelation.source_id == correlation_data.get("source_id"),
                    IncidentCorrelation.source_table == correlation_data.get("source_table")
                )
            ).first()

            if existing:
                # Update existing
                existing.correlation_strength = correlation_data["correlation_strength"]
                existing.description = correlation_data["description"]
                existing.keywords_matched = correlation_data.get("keywords_matched")
                existing.time_delta_hours = correlation_data.get("time_delta_hours")
            else:
                # Create new
                new_corr = IncidentCorrelation(
                    incident_id=incident_id,
                    correlation_type=correlation_data["correlation_type"],
                    source_id=correlation_data.get("source_id"),
                    source_table=correlation_data.get("source_table"),
                    time_delta_hours=correlation_data.get("time_delta_hours"),
                    correlation_strength=correlation_data["correlation_strength"],
                    description=correlation_data["description"],
                    keywords_matched=correlation_data.get("keywords_matched"),
                    auto_detected=True
                )
                self.db.add(new_corr)

            self.db.commit()
        except Exception as e:
            print(f"⚠️  Error saving correlation: {e}")
            self.db.rollback()

    def generate_alert_report(self, min_correlation_strength: float = 0.7) -> str:
        """Generate human-readable alert report for high-confidence correlations"""
        correlations = self.db.query(IncidentCorrelation).filter(
            IncidentCorrelation.correlation_strength >= min_correlation_strength
        ).order_by(IncidentCorrelation.created_at.desc()).limit(20).all()

        if not correlations:
            return "No high-confidence correlations found."

        report = []
        report.append("=" * 70)
        report.append("HIGH-CONFIDENCE INCIDENT CORRELATIONS ALERT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Threshold: correlation_strength ≥ {min_correlation_strength}")
        report.append("")

        for corr in correlations:
            incident = self.db.query(Incident).get(corr.incident_id)
            if not incident:
                continue

            report.append(f"INCIDENT #{incident.id}: {incident.title}")
            report.append(f"Date: {incident.sighting_date}")
            report.append(f"Correlation Type: {corr.correlation_type}")
            report.append(f"Strength: {corr.correlation_strength:.2f}")
            report.append(f"Time Delta: {corr.time_delta_hours}h")
            report.append(f"Description: {corr.description}")

            if corr.keywords_matched:
                keywords = json.loads(corr.keywords_matched)
                report.append(f"Keywords: {', '.join(keywords)}")

            report.append("")
            report.append("-" * 70)
            report.append("")

        return "\n".join(report)

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Incident Correlation Engine")
    parser.add_argument("--limit", type=int, help="Limit number of incidents to analyze")
    parser.add_argument("--time-window", type=int, default=24, help="Time window in hours (default: 24)")
    parser.add_argument("--alert", action="store_true", help="Generate alert report")
    parser.add_argument("--min-strength", type=float, default=0.7, help="Minimum correlation strength for alerts")

    args = parser.parse_args()

    engine = IncidentCorrelationEngine(time_window_hours=args.time_window)

    if args.alert:
        print(engine.generate_alert_report(min_correlation_strength=args.min_strength))
    else:
        results = engine.analyze_all_incidents(limit=args.limit)

        # Save results to JSON
        output_file = f"correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
