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
    display_source = Column(String(500), nullable=True)  # Merged sources display string for deduplicated incidents
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
    telegram_post = relationship("SocialMediaPost", back_populates="incidents")
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

class SocialMediaPost(Base):
    """Telegram/social media posts for GRU recruitment monitoring"""
    __tablename__ = "social_media_posts"

    id = Column(Integer, primary_key=True)
    channel_name = Column(String(255), nullable=False, index=True)
    post_date = Column(DateTime, nullable=False, index=True)
    content = Column(Text)
    post_url = Column(String(500))
    gru_recruitment_score = Column(Integer, default=0)  # 0-100 score for recruitment indicators
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("Incident", back_populates="telegram_post")

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

# ============================================================
# TELEGRAM SOCIAL GRAPH INTELLIGENCE TABLES
# ============================================================

class TelegramChannel(Base):
    """Telegram channels for social graph analysis"""
    __tablename__ = "telegram_channels"

    id = Column(Integer, primary_key=True)
    channel_id = Column(String(100), unique=True, nullable=False, index=True)  # Telegram channel ID
    username = Column(String(100), unique=True, index=True)
    title = Column(String(255))
    description = Column(Text)
    member_count = Column(Integer)
    first_discovered = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime)
    channel_type = Column(String(20))  # public, private, invite_only
    language_primary = Column(String(10))  # nl, ru, en, etc
    risk_score = Column(Integer, default=0)  # 0-100 automated risk assessment

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("TelegramMessage", back_populates="channel", foreign_keys="TelegramMessage.channel_id")
    forwards_sent = relationship("MessageForward", back_populates="source_channel", foreign_keys="MessageForward.source_channel_id")
    forwards_received = relationship("MessageForward", back_populates="destination_channel", foreign_keys="MessageForward.destination_channel_id")
    participants = relationship("ChannelParticipation", back_populates="channel")

class TelegramMessage(Base):
    """Individual messages from Telegram channels"""
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String(100), nullable=False, index=True)  # Telegram message ID
    channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False, index=True)
    channel = relationship("TelegramChannel", back_populates="messages", foreign_keys=[channel_id])

    timestamp = Column(DateTime, nullable=False, index=True)
    text_content = Column(Text)
    media_type = Column(String(50))  # photo, video, document, etc
    views = Column(Integer)
    engagement_score = Column(Float)  # views + forwards + reactions

    # Forward tracking
    forward_from_channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=True)
    forward_from_channel = relationship("TelegramChannel", foreign_keys=[forward_from_channel_id])
    forward_from_message_id = Column(String(100))

    # Linguistic analysis
    linguistic_suspicion_score = Column(Float)  # 0-1, Russian→Dutch translation detection
    linguistic_flags = Column(Text)  # JSON array of detected patterns

    # Correlation to incidents
    incident_correlation_score = Column(Float)  # 0-1, temporal correlation to known incidents
    related_incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    forwards = relationship("MessageForward", back_populates="source_message", foreign_keys="MessageForward.source_message_id")

class TelegramParticipant(Base):
    """Telegram users tracked across channels"""
    __tablename__ = "telegram_participants"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)  # Telegram user ID
    username = Column(String(100), index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_hash = Column(String(64))  # SHA-256 hash for privacy
    bio = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime)

    # Risk assessment
    risk_score = Column(Integer, default=0)  # 0-100
    risk_factors = Column(Text)  # JSON array of risk indicators

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participations = relationship("ChannelParticipation", back_populates="participant")

class ChannelParticipation(Base):
    """Many-to-many: users in channels"""
    __tablename__ = "channel_participation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("telegram_participants.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False, index=True)

    participant = relationship("TelegramParticipant", back_populates="participations")
    channel = relationship("TelegramChannel", back_populates="participants")

    join_date = Column(DateTime)
    last_activity = Column(DateTime)
    activity_level = Column(String(20))  # lurker, occasional, active, admin
    message_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

class MessageForward(Base):
    """Track message forwarding chains (social graph edges)"""
    __tablename__ = "message_forwards"

    id = Column(Integer, primary_key=True)
    source_channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False, index=True)
    source_message_id = Column(Integer, ForeignKey("telegram_messages.id"), nullable=False)
    destination_channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False, index=True)
    destination_message_id = Column(Integer, ForeignKey("telegram_messages.id"), nullable=False)
    forward_timestamp = Column(DateTime, nullable=False, index=True)

    # Time from original post to forward (in seconds)
    forward_velocity_seconds = Column(Integer)

    source_channel = relationship("TelegramChannel", back_populates="forwards_sent", foreign_keys=[source_channel_id])
    destination_channel = relationship("TelegramChannel", back_populates="forwards_received", foreign_keys=[destination_channel_id])
    source_message = relationship("TelegramMessage", back_populates="forwards", foreign_keys=[source_message_id])

    created_at = Column(DateTime, default=datetime.utcnow)

class PrivateChannelLeak(Base):
    """Track when private channels leak content to public channels"""
    __tablename__ = "private_channel_leaks"

    id = Column(Integer, primary_key=True)
    private_channel_id = Column(String(100), nullable=False, index=True)  # May not be accessible
    private_channel_name = Column(String(255))
    public_channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False, index=True)
    first_leak_timestamp = Column(DateTime, nullable=False)
    leak_frequency = Column(Integer, default=1)
    last_leak_timestamp = Column(DateTime)

    # Bridge user (if identifiable)
    bridge_user_id = Column(Integer, ForeignKey("telegram_participants.id"), nullable=True)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================
# AVIATION FORUM MONITORING TABLES
# ============================================================

class AviationForumPost(Base):
    """Posts from aviation forums (PPRuNe, AvHerald, etc)"""
    __tablename__ = "aviation_forum_posts"

    id = Column(Integer, primary_key=True)
    forum_source = Column(String(50), nullable=False, index=True)  # pprune, avherald, scramble, etc
    thread_id = Column(String(100), index=True)
    thread_title = Column(String(500))
    post_author = Column(String(100))
    post_timestamp = Column(DateTime, nullable=False, index=True)
    post_content = Column(Text)
    post_url = Column(String(500))

    # Analysis
    keywords_detected = Column(Text)  # JSON array of relevant keywords
    sentiment_score = Column(Float)  # -1 to 1 (negative to positive)

    # Incident correlation
    referenced_incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    correlation_confidence = Column(Float)  # 0-1, how confident we are this relates to an incident

    # Insider knowledge detection
    precedes_official_report = Column(Boolean, default=False)  # Post came before official incident report
    insider_knowledge_score = Column(Float)  # 0-1, likelihood this is insider info

    created_at = Column(DateTime, default=datetime.utcnow)

class ForumKeywordMatch(Base):
    """Keyword matches in forum posts (for quick filtering)"""
    __tablename__ = "forum_keyword_matches"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("aviation_forum_posts.id"), nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    context_snippet = Column(Text)  # Surrounding text for context

    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================
# LINKEDIN & PROFESSIONAL NETWORK OSINT TABLES
# ============================================================

class LinkedInProfile(Base):
    """LinkedIn profiles discovered via Google dorking"""
    __tablename__ = "linkedin_profiles"

    id = Column(Integer, primary_key=True)
    profile_url = Column(String(500), unique=True, nullable=False, index=True)
    full_name = Column(String(255), index=True)
    headline = Column(String(500))  # Professional title
    current_company = Column(String(255))
    current_title = Column(String(255))
    location = Column(String(255), index=True)
    profile_snippet = Column(Text)  # From Google SERP

    # Discovery metadata
    discovered_via_query = Column(Text)  # The Google dork query that found this
    discovery_date = Column(DateTime, default=datetime.utcnow)

    # Risk assessment
    risk_score = Column(Integer, default=0)  # 0-100
    risk_flags = Column(Text)  # JSON array: ["aviation_security", "russia_connections", "career_gap_2023"]

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    persona_matches = relationship("PersonaMatch", back_populates="profile")

class PersonaMatch(Base):
    """Maps LinkedIn profiles to target personas"""
    __tablename__ = "persona_matches"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("linkedin_profiles.id"), nullable=False, index=True)
    profile = relationship("LinkedInProfile", back_populates="persona_matches")

    persona_type = Column(String(100), nullable=False, index=True)  # drone_hobbyist, aviation_security, rf_engineer, etc
    confidence_score = Column(Float, nullable=False)  # 0-1
    matching_keywords = Column(Text)  # JSON array of keywords that matched
    matching_signals = Column(Text)  # JSON array of signals (location, connections, timeline anomalies)

    # Manual review
    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)
    actionable = Column(Boolean, nullable=True)  # True = worth investigating, False = false positive

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================
# INCIDENT CORRELATION & TEMPORAL ANALYSIS
# ============================================================

class IncidentCorrelation(Base):
    """Temporal correlations between incidents and OSINT signals"""
    __tablename__ = "incident_correlations"

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # Correlation type and source
    correlation_type = Column(String(50), nullable=False, index=True)  # telegram_spike, forum_discussion, social_media
    source_id = Column(Integer)  # Foreign key to telegram_messages, forum_posts, etc (polymorphic)
    source_table = Column(String(50))  # Which table the source_id refers to

    # Temporal analysis
    time_delta_hours = Column(Integer)  # Hours before/after incident
    correlation_strength = Column(Float, nullable=False)  # 0-1, statistical significance

    # Context
    description = Column(Text)
    keywords_matched = Column(Text)  # JSON array

    # Analysis metadata
    auto_detected = Column(Boolean, default=True)  # True = algorithm, False = manual
    analyst_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================
# UNIVERSAL INTELLIGENCE LINK ANALYSIS (Palantir-style)
# ============================================================

class IntelligenceLink(Base):
    """Universal entity relationship mapping for link analysis
    
    FBI/NSA/Palantir-style link analysis table.
    Maps relationships between ANY entities: incidents, messages, channels,
    locations, wallets, users, etc.
    """
    __tablename__ = "intelligence_links"
    
    id = Column(Integer, primary_key=True)
    
    # Entity A (source)
    entity_a_type = Column(String(50), nullable=False, index=True)  # incident, message, channel, wallet, profile, location
    entity_a_id = Column(Integer, nullable=False, index=True)
    entity_a_identifier = Column(String(255))  # Human-readable identifier
    
    # Entity B (target)
    entity_b_type = Column(String(50), nullable=False, index=True)
    entity_b_id = Column(Integer, nullable=False, index=True)
    entity_b_identifier = Column(String(255))
    
    # Relationship metadata
    relationship_type = Column(String(50), nullable=False, index=True)  # temporal, spatial, financial, social, linguistic, forward_chain
    link_strength = Column(Float, nullable=False)  # 0-1, how strong is this relationship
    confidence_score = Column(Float, nullable=False)  # 0-1, how confident are we
    
    # Evidence and context
    evidence = Column(Text)  # JSON: supporting evidence for this link
    evidence_count = Column(Integer, default=1)  # How many pieces of evidence
    keywords_matched = Column(Text)  # JSON: keywords that triggered this link
    
    # Temporal context
    earliest_evidence_date = Column(DateTime)
    latest_evidence_date = Column(DateTime)
    
    # Analysis metadata
    auto_detected = Column(Boolean, default=True)
    analyst_verified = Column(Boolean, default=False)
    analyst_notes = Column(Text)
    
    # Discovery metadata
    discovered_by = Column(String(100))  # Which algorithm/analyst discovered this
    discovered_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
