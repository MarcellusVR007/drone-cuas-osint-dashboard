from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class RestrictedArea(Base):
    """Military bases, airports, nuclear facilities, and other restricted airspace"""
    __tablename__ = "restricted_areas"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    area_type = Column(String(50), nullable=False)  # airport, military_base, nuclear_facility, government
    country = Column(String(2), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=5.0)  # Airspace radius
    threat_level = Column(Integer, default=3)  # 1-5 scale
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incidents = relationship("Incident", back_populates="restricted_area")

class DroneType(Base):
    """Drone specifications and intelligence"""
    __tablename__ = "drone_types"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False, unique=True, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)
    country_of_origin = Column(String(2), nullable=False)
    range_km = Column(Integer)  # Operational range
    endurance_minutes = Column(Integer)  # Flight time
    max_altitude_m = Column(Integer)
    payload_type = Column(String(100))  # camera, signals_intelligence, unknown
    difficulty_intercept = Column(Integer)  # 1-10 scale, higher = harder
    estimated_cost_usd = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("Incident", back_populates="drone_type")

class Incident(Base):
    """Drone sighting or incursion incident"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    sighting_date = Column(Date, nullable=False, index=True)
    sighting_time = Column(String(5))  # HH:MM format
    report_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Location info
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Integer)

    # Drone info
    drone_type_id = Column(Integer, ForeignKey("drone_types.id"), nullable=True)
    drone_type = relationship("DroneType", back_populates="incidents")
    drone_description = Column(String(255))  # When type not identified

    # Drone characteristics (when type unconfirmed but observations available)
    drone_characteristics = Column(Text)  # Observable features: "small white quad copter", "RTK antenna visible", "fixed wing", etc.
    drone_characteristics_sources = Column(Text)  # Sources of observations: "witness accounts", "video analysis", "radar signature", "photo evidence", etc.

    # Drone Identification Evidence
    identification_method = Column(String(100))  # visual, radar, recovered_wreckage, photo, video, adsb, signals, intelligence
    identification_confidence = Column(Float, default=0.5)  # 0-1, confidence in drone type identification
    identification_evidence = Column(Text)  # Detailed evidence: "Photo analysis, RTK antenna visible", "Military radar signature", "Recovered and analyzed", etc.
    identified_by = Column(String(100))  # Who identified it: "NATO intelligence", "Dutch military", "News analysis", etc.

    # Context
    restricted_area_id = Column(Integer, ForeignKey("restricted_areas.id"), nullable=True)
    restricted_area = relationship("RestrictedArea", back_populates="incidents")
    distance_to_restricted_m = Column(Integer)  # Distance to nearest restricted area

    # Incident details
    duration_minutes = Column(Integer)
    source = Column(String(50), nullable=False, index=True)  # news, authority, submission, intelligence
    source_url = Column(String(500))  # Direct link to the reporting source/article
    corroborating_sources = Column(Text)  # JSON list of additional sources confirming this incident
    confidence_score = Column(Float, default=0.5)  # 0-1, confidence in report accuracy
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    details = Column(Text)

    # Source credibility hierarchy - for OSINT source traceability
    primary_source_name = Column(String(255))  # e.g., "Reuters", "Senhive API", "Military Aviation Forums"
    primary_source_credibility = Column(Integer, default=5)  # 1-10 scale, higher = more credible
    secondary_sources = Column(Text)  # JSON list: [{"name": "Watson", "url": "...", "credibility": 7}, ...]

    # Attribution / Investigation
    suspected_operator = Column(String(100))  # e.g., "Russian SVR", "Unknown civilian"
    purpose_assessment = Column(String(100))  # reconnaissance, disruption, intelligence, unknown
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)

    # Behavioral Indicators (for BOUNTY_AMATEUR vs STATE_ACTOR_PROFESSIONAL classification)
    lights_observed = Column(Boolean, nullable=True)  # True=lights ON (amateur), False=lights OFF (professional), None=unknown
    flight_pattern = Column(String(50), nullable=True)  # "erratic", "systematic", "hover", "perimeter_scan", "unknown"
    time_of_day = Column(String(20), nullable=True)  # "dawn", "day", "dusk", "night", "unknown"
    estimated_altitude_m = Column(Integer, nullable=True)  # Estimated altitude when altitude_m not precise
    flight_behavior_notes = Column(Text, nullable=True)  # Free-text observations: "zigzag pattern", "hovering over entrance", etc.

    # Operational Classification (auto-calculated from indicators)
    operational_class = Column(String(50), nullable=True)  # "BOUNTY_AMATEUR", "STATE_ACTOR_PROFESSIONAL", "UNKNOWN"
    classification_confidence = Column(Float, nullable=True)  # 0-1, confidence in classification
    classification_reasoning = Column(Text, nullable=True)  # Explanation of classification

    # Attribution Chain (linking to Telegram/SOCMINT)
    telegram_post_id = Column(Integer, ForeignKey("social_media_posts.id"), nullable=True)  # Link to recruitment/bounty post
    handler_username = Column(String(100), nullable=True)  # Telegram handler/recruiter username
    payment_wallet_address = Column(String(100), nullable=True)  # Bitcoin wallet from Telegram post
    attribution_chain = Column(Text, nullable=True)  # JSON: full chain from handler to operative

    # Strategic Intelligence (for high-value incidents like Orlan-10)
    strategic_assessment = Column(Text, nullable=True)  # Analysis of strategic implications
    launch_analysis = Column(Text, nullable=True)  # Possible launch locations/methods

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interventions = relationship("Intervention", back_populates="incident", cascade="all, delete-orphan")

class Intervention(Base):
    """Countermeasure/defensive action taken against drone"""
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    incident = relationship("Incident", back_populates="interventions")

    intervention_type = Column(String(50), nullable=False, index=True)  # jamming, netting, kinetic, interception, unknown
    response_time_minutes = Column(Integer)  # Time from detection to action
    outcome = Column(String(50), index=True)  # success, partial, failed, unknown, not_attempted
    success_rate = Column(Float)  # 0-1 scale
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Pattern(Base):
    """Detected patterns linking multiple incidents"""
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    pattern_type = Column(String(50))  # temporal, spatial, drone_type, operator

    # Pattern characteristics
    incident_count = Column(Integer, default=1)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    primary_location = Column(String(255))
    primary_drone_type = Column(String(100))

    # Intelligence
    suspected_purpose = Column(String(100))
    suspected_operator = Column(String(100))
    confidence_score = Column(Float, default=0.5)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incidents = relationship("Incident", backref="pattern")

class DataSource(Base):
    """Track where intelligence comes from"""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50))  # news, authority, api, submission, sigint, radar, adsb, drone_detection
    url = Column(String(500))
    api_endpoint = Column(String(500))
    api_key_required = Column(Boolean, default=False)

    # Source qualification metrics
    reliability_score = Column(Float, default=0.5)  # 0-1, historical accuracy
    freshness_score = Column(Float, default=0.5)  # 0-1, how recent the data is
    coverage_score = Column(Float, default=0.5)   # 0-1, geographical/temporal coverage
    data_quality_score = Column(Float, default=0.5)  # 0-1, detail and accuracy of data
    verification_status = Column(String(50))  # unverified, partial, verified, high_confidence

    enabled = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_frequency_hours = Column(Integer, default=24)  # How often to check this source

    # Source characteristics
    capabilities = Column(Text)  # JSON: ["drone_detection", "sigint", "radar", "video_analysis", "photo_analysis"]
    coverage_regions = Column(Text)  # JSON: ["Belgium", "Netherlands", "Germany", etc]
    drone_types_detected = Column(Text)  # JSON: drone type specialization

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
