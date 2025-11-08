"""
Data Ingestion Module for Multi-Source Drone Intelligence
Aggregates data from news, radar, SIGINT, drone detection services, and submissions
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.models import DataSource, Incident, RestrictedArea, DroneType

# Available data sources with qualification metrics
CONFIGURED_SOURCES = {
    "senhive": {
        "name": "Senhive (Belgium)",
        "source_type": "drone_detection",
        "url": "https://senhive.com/",
        "api_endpoint": "https://api.senhive.com/incidents",  # Example
        "reliability_score": 0.95,
        "freshness_score": 0.95,
        "coverage_score": 0.9,
        "data_quality_score": 0.92,
        "verification_status": "verified",
        "capabilities": ["drone_detection", "radar", "adsb_analysis", "video_analysis"],
        "coverage_regions": ["Belgium", "Netherlands", "France", "Germany"],
        "drone_types_detected": ["DJI", "Parrot", "Auterion", "fixed_wing", "military"],
        "notes": "Real-time drone detection network across EU, professional monitoring"
    },

    "adsbexchange": {
        "name": "ADS-B Exchange",
        "source_type": "adsb",
        "url": "https://adsbexchange.com/",
        "api_endpoint": "https://api.adsbexchange.com/v2/aircraft",
        "reliability_score": 0.9,
        "freshness_score": 0.99,
        "coverage_score": 0.95,
        "data_quality_score": 0.88,
        "verification_status": "verified",
        "capabilities": ["adsb_tracking", "aircraft_identification", "trajectory_analysis"],
        "coverage_regions": ["Europe", "Global"],
        "drone_types_detected": ["Military drones with ADS-B", "Manned aircraft"],
        "notes": "Global ADS-B receiver network, excellent real-time coverage"
    },

    "janes_ihs": {
        "name": "Janes Intelligence & Insight",
        "source_type": "sigint",
        "url": "https://www.janes.com/",
        "api_endpoint": None,  # Manual data entry or API
        "reliability_score": 0.98,
        "freshness_score": 0.8,
        "coverage_score": 0.85,
        "data_quality_score": 0.95,
        "verification_status": "high_confidence",
        "capabilities": ["sigint", "military_analysis", "threat_assessment", "pattern_analysis"],
        "coverage_regions": ["Europe", "Global"],
        "drone_types_detected": ["Military drones", "Surveillance platforms", "SIGINT collectors"],
        "notes": "Authoritative military intelligence source, high confidence verification"
    },

    "belguim_mil_intel": {
        "name": "Belgium Military Intelligence (Orgaan)",
        "source_type": "authority",
        "url": None,
        "api_endpoint": None,
        "reliability_score": 0.99,
        "freshness_score": 0.75,
        "coverage_score": 0.95,
        "data_quality_score": 0.98,
        "verification_status": "high_confidence",
        "capabilities": ["radar", "sigint", "fighter_interception", "wreckage_analysis"],
        "coverage_regions": ["Belgium", "Benelux", "NATO airspace"],
        "drone_types_detected": ["All types", "Military platforms", "Foreign reconnaissance"],
        "notes": "Official Belgian military intelligence, highest confidence"
    },

    "dutch_mil_intel": {
        "name": "Dutch Ministry of Defence (MIVD)",
        "source_type": "authority",
        "url": None,
        "api_endpoint": None,
        "reliability_score": 0.99,
        "freshness_score": 0.75,
        "coverage_score": 0.95,
        "data_quality_score": 0.98,
        "verification_status": "high_confidence",
        "capabilities": ["radar", "sigint", "air_defense", "threat_analysis"],
        "coverage_regions": ["Netherlands", "Benelux", "North Sea"],
        "drone_types_detected": ["All types", "Military platforms"],
        "notes": "Dutch military intelligence, NATO member"
    },

    "nato_early_warning": {
        "name": "NATO AWACS & Early Warning",
        "source_type": "authority",
        "url": None,
        "api_endpoint": None,
        "reliability_score": 0.99,
        "freshness_score": 0.9,
        "coverage_score": 0.98,
        "data_quality_score": 0.99,
        "verification_status": "high_confidence",
        "capabilities": ["radar", "sigint", "missile_tracking", "real_time_alerts"],
        "coverage_regions": ["Europe", "Atlantic"],
        "drone_types_detected": ["All platforms", "Military reconnaissance"],
        "notes": "NATO AWACS E-3 Sentry and ground radar network"
    },

    "reuters_news": {
        "name": "Reuters News (Drone Incidents)",
        "source_type": "news",
        "url": "https://www.reuters.com/",
        "api_endpoint": None,
        "reliability_score": 0.85,
        "freshness_score": 0.95,
        "coverage_score": 0.8,
        "data_quality_score": 0.82,
        "verification_status": "partial",
        "capabilities": ["news_reporting", "public_reporting", "visual_evidence"],
        "coverage_regions": ["Europe", "Global"],
        "drone_types_detected": ["Commercial", "Public sightings"],
        "notes": "Major news organization, public reporting, occasional visual evidence"
    },

    "bbc_monitoring": {
        "name": "BBC Monitoring (OSINT)",
        "source_type": "news",
        "url": "https://monitoring.bbc.co.uk/",
        "api_endpoint": None,
        "reliability_score": 0.88,
        "freshness_score": 0.9,
        "coverage_score": 0.85,
        "data_quality_score": 0.85,
        "verification_status": "partial",
        "capabilities": ["open_source", "media_monitoring", "incident_reporting"],
        "coverage_regions": ["Europe", "Global"],
        "drone_types_detected": ["Public reports", "Military operations"],
        "notes": "BBC Open Intelligence, professional OSINT analysis"
    },

    "twitter_osint": {
        "name": "Twitter/X OSINT Accounts",
        "source_type": "submission",
        "url": "https://twitter.com/",
        "api_endpoint": "https://api.twitter.com/2/tweets/search",
        "reliability_score": 0.65,
        "freshness_score": 0.99,
        "coverage_score": 0.75,
        "data_quality_score": 0.6,
        "verification_status": "unverified",
        "capabilities": ["real_time_reporting", "visual_evidence", "witness_accounts"],
        "coverage_regions": ["Europe", "Global"],
        "drone_types_detected": ["User observations", "Photos/video"],
        "notes": "Crowdsourced real-time reporting, requires verification"
    },

    "military_aviation_forums": {
        "name": "Military Aviation Forums & Communities",
        "source_type": "submission",
        "url": "https://www.secretprojects.co.uk/",
        "api_endpoint": None,
        "reliability_score": 0.7,
        "freshness_score": 0.85,
        "coverage_score": 0.8,
        "data_quality_score": 0.75,
        "verification_status": "partial",
        "capabilities": ["expert_analysis", "sighting_reports", "identification_help"],
        "coverage_regions": ["Europe", "NATO"],
        "drone_types_detected": ["All types", "Military platforms"],
        "notes": "Expert community analysis, good for aircraft identification"
    },

    "citizen_reports": {
        "name": "Public Citizen Submissions",
        "source_type": "submission",
        "url": None,
        "api_endpoint": None,
        "reliability_score": 0.55,
        "freshness_score": 0.9,
        "coverage_score": 0.7,
        "data_quality_score": 0.5,
        "verification_status": "unverified",
        "capabilities": ["witness_reports", "photo_evidence", "location_data"],
        "coverage_regions": ["Local reports"],
        "drone_types_detected": ["User observations"],
        "notes": "Unverified citizen reports, requires cross-referencing"
    },

    "flight_radar_data": {
        "name": "Flightradar24 Data",
        "source_type": "adsb",
        "url": "https://www.flightradar24.com/",
        "api_endpoint": "https://api.flightradar24.com/v1/",
        "reliability_score": 0.92,
        "freshness_score": 0.99,
        "coverage_score": 0.95,
        "data_quality_score": 0.9,
        "verification_status": "verified",
        "capabilities": ["aircraft_tracking", "trajectory_analysis", "historical_data"],
        "coverage_regions": ["Global"],
        "drone_types_detected": ["ADS-B equipped aircraft"],
        "notes": "Real-time flight tracking, good for manned and some large drones"
    },
}


def get_source_combined_score(source: Dict) -> float:
    """Calculate combined qualification score for a data source"""
    weights = {
        "reliability_score": 0.3,
        "freshness_score": 0.25,
        "coverage_score": 0.2,
        "data_quality_score": 0.25
    }

    score = sum(
        source.get(key, 0) * weight
        for key, weight in weights.items()
    )
    return min(score, 1.0)  # Cap at 1.0


def initialize_data_sources(db: Session):
    """Initialize configured data sources in database"""
    try:
        # Check how many sources already exist
        existing_count = db.query(DataSource).count()
        if existing_count > 0:
            return  # Already initialized

        # Initialize all sources
        for source_key, source_config in CONFIGURED_SOURCES.items():
            source = DataSource(
                name=source_config["name"],
                source_type=source_config["source_type"],
                url=source_config.get("url"),
                api_endpoint=source_config.get("api_endpoint"),
                reliability_score=source_config.get("reliability_score", 0.5),
                freshness_score=source_config.get("freshness_score", 0.5),
                coverage_score=source_config.get("coverage_score", 0.5),
                data_quality_score=source_config.get("data_quality_score", 0.5),
                verification_status=source_config.get("verification_status", "unverified"),
                capabilities=json.dumps(source_config.get("capabilities", [])),
                coverage_regions=json.dumps(source_config.get("coverage_regions", [])),
                drone_types_detected=json.dumps(source_config.get("drone_types_detected", [])),
                notes=source_config.get("notes", ""),
                enabled=True
            )
            db.add(source)

        db.commit()
        print(f"✓ Initialized {len(CONFIGURED_SOURCES)} data sources")
    except Exception as e:
        db.rollback()
        # Silently fail if sources already exist or database is locked
        pass


def get_qualified_sources(db: Session, min_score: float = 0.5) -> List[DataSource]:
    """Get data sources meeting minimum qualification score"""
    all_sources = db.query(DataSource).filter_by(enabled=True).all()

    qualified = []
    for source in all_sources:
        score = get_source_combined_score({
            "reliability_score": source.reliability_score,
            "freshness_score": source.freshness_score,
            "coverage_score": source.coverage_score,
            "data_quality_score": source.data_quality_score,
        })

        if score >= min_score:
            qualified.append(source)

    return sorted(qualified, key=lambda s: (s.verification_status == "high_confidence",
                                            s.reliability_score), reverse=True)


def calculate_incident_source_confidence(source: DataSource) -> float:
    """Calculate confidence boost based on source qualification"""
    verification_multipliers = {
        "high_confidence": 1.0,
        "verified": 0.9,
        "partial": 0.7,
        "unverified": 0.4
    }

    base_score = (
        source.reliability_score * 0.3 +
        source.data_quality_score * 0.4 +
        source.coverage_score * 0.2 +
        source.freshness_score * 0.1
    )

    multiplier = verification_multipliers.get(source.verification_status, 0.5)
    return base_score * multiplier
