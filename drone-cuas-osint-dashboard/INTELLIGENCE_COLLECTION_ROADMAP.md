# Intelligence Collection Roadmap
## Drone/C-UAS OSINT Dashboard - Enhanced SOCMINT Capabilities

**Document Version:** 1.0
**Date:** 2025-11-18
**Status:** Planning Phase

---

## Executive Summary

Current data collection yields insufficient actionable intelligence (2k Telegram posts, minimal Twitter/X data). This roadmap restructures collection methodology around:
1. **Incident-correlated temporal analysis**
2. **Social graph network mapping**
3. **Multi-source cross-referencing**
4. **Automated attribution indicators**

---

## Phase 1: Telegram Intelligence Enhancement

### 1.1 Social Graph Analysis

**Objective:** Map relationship networks between channels, users, and content flows.

**Database Schema Extensions:**

```sql
-- Telegram social graph tables
CREATE TABLE telegram_channels (
    channel_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    title TEXT,
    description TEXT,
    member_count INTEGER,
    first_discovered TIMESTAMP,
    last_active TIMESTAMP,
    channel_type TEXT, -- public, private, invite_only
    language_primary TEXT,
    risk_score INTEGER DEFAULT 0
);

CREATE TABLE telegram_messages (
    message_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    timestamp TIMESTAMP,
    text_content TEXT,
    forward_from_channel_id INTEGER,
    forward_from_message_id INTEGER,
    media_type TEXT,
    views INTEGER,
    engagement_score REAL,
    FOREIGN KEY (channel_id) REFERENCES telegram_channels(channel_id),
    FOREIGN KEY (forward_from_channel_id) REFERENCES telegram_channels(channel_id)
);

CREATE TABLE telegram_participants (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone_hash TEXT, -- hashed for privacy
    bio TEXT,
    first_seen TIMESTAMP
);

CREATE TABLE channel_participation (
    user_id INTEGER,
    channel_id INTEGER,
    join_date TIMESTAMP,
    last_activity TIMESTAMP,
    activity_level TEXT, -- lurker, occasional, active, admin
    PRIMARY KEY (user_id, channel_id),
    FOREIGN KEY (user_id) REFERENCES telegram_participants(user_id),
    FOREIGN KEY (channel_id) REFERENCES telegram_channels(channel_id)
);

CREATE TABLE message_forwards_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_channel_id INTEGER,
    source_message_id INTEGER,
    destination_channel_id INTEGER,
    destination_message_id INTEGER,
    forward_timestamp TIMESTAMP,
    FOREIGN KEY (source_channel_id) REFERENCES telegram_channels(channel_id),
    FOREIGN KEY (destination_channel_id) REFERENCES telegram_channels(channel_id)
);
```

**Implementation Tasks:**
- [ ] Extend database schema
- [ ] Build Telegram scraper with forward-tracking
- [ ] Create social graph visualization (NetworkX + D3.js)
- [ ] Implement PageRank-style influence scoring for channels

---

### 1.2 Incident-Correlated Temporal Analysis

**Objective:** Detect activity spikes in Telegram channels within ±24h of known drone incidents.

**Algorithm:**

```python
def detect_correlated_activity(incident_timestamp, time_window=24):
    """
    Find Telegram activity anomalies around incident time

    Args:
        incident_timestamp: datetime of drone incident
        time_window: hours before/after to analyze (default 24)

    Returns:
        List of (channel_id, spike_score, messages) tuples
    """
    start_time = incident_timestamp - timedelta(hours=time_window)
    end_time = incident_timestamp + timedelta(hours=time_window)

    # Get baseline activity (30 days prior)
    baseline_start = incident_timestamp - timedelta(days=30)
    baseline_end = incident_timestamp - timedelta(hours=time_window)

    # Calculate z-score for activity spike
    # Flag channels with z > 2.5 (statistical anomaly)
```

**Features:**
- Automated incident ingestion from incidents table
- Hourly message volume tracking per channel
- Statistical anomaly detection (z-score based)
- Keyword co-occurrence analysis during spike windows
- Alert generation for manual review

**Implementation Tasks:**
- [ ] Build temporal correlation engine
- [ ] Create background job for automated analysis
- [ ] Design alert dashboard UI component
- [ ] Implement keyword extraction from spike messages

---

### 1.3 Metadata Mining & Forward Tracking

**Objective:** Extract origin channel information from forwarded messages to discover hidden networks.

**Key Metrics to Track:**
- Forward chain depth (how many hops from origin)
- Forward velocity (time between forwards)
- Channel-to-channel forward frequency matrix
- Common forward patterns (same message to multiple channels = coordination?)

**Implementation:**

```python
class ForwardChainAnalyzer:
    def trace_message_origin(self, message_id):
        """Recursively trace forwards back to origin"""

    def detect_coordinated_forwarding(self, threshold_channels=5, time_window_mins=30):
        """Find messages forwarded to N+ channels within time window"""

    def build_influence_map(self):
        """Create directed graph: channel A → channel B = forward relationship"""
```

**Implementation Tasks:**
- [ ] Implement recursive forward tracing
- [ ] Build coordinated forwarding detector
- [ ] Create influence map visualization
- [ ] Add forward pattern reporting

---

### 1.4 Linguistic Fingerprinting

**Objective:** Detect Russian→Dutch translation artifacts and native Russian speaker patterns.

**Detection Patterns:**

| Category | Indicator | Example |
|----------|-----------|---------|
| **Word Order** | Slavic SOV structures | "De drone boven het vliegveld vloog" (vs natural "De drone vloog boven het vliegveld") |
| **Articles** | Missing/incorrect articles | "Drone werd gezien bij vliegveld" (missing 'de'/'het') |
| **Prepositions** | Direct RU→NL translation | "op het vliegveld" when "bij/nabij" is more natural |
| **Formal/Informal Mix** | Inconsistent register | Mixing 'u' and 'je' unnaturally |
| **Calques** | Literal translations | "maken een foto" (RU: делать фото) vs "een foto nemen" |
| **False Cognates** | Using similar-looking wrong words | "evenement" for "incident" (событие) |

**Machine Learning Approach:**
- Train classifier on known Russian→Dutch translations vs native Dutch
- Features: POS tag sequences, collocation frequencies, formality markers
- Use BERT multilingual embeddings to detect cross-lingual transfer

**Rule-Based Approach (faster, immediate deployment):**
```python
class LinguisticFingerprintDetector:
    def __init__(self):
        self.suspicious_patterns = [
            # Article errors
            r'\b(drone|vliegveld|incident)\s+(werd|is|was)\b',  # missing article

            # Preposition calques
            r'\bna\s+(\d+)\s+(minuten|uren)\b',  # "na 5 minuten" (RU: через)

            # Word order (simplified)
            r'\b\w+\s+(boven|onder|bij)\s+het\s+\w+\s+(vloog|ging|kwam)\b',
        ]

    def score_text(self, text):
        """Returns suspicion score 0-100"""
```

**Implementation Tasks:**
- [ ] Build rule-based detector (MVP)
- [ ] Collect Dutch training corpus (news articles, forums)
- [ ] Collect Russian→Dutch translation corpus (Google Translate samples)
- [ ] Train ML classifier (stretch goal)
- [ ] Add linguistic flags to message analysis

---

## Phase 2: External Source Integration

### 2.1 Aviation Forum Monitoring

**Target Sources:**

| Forum | Focus | Scraping Method |
|-------|-------|-----------------|
| **PPRuNe** (pprune.org) | Professional pilots, ATC discussions | RSS + scraper |
| **AvHerald** (avherald.com) | Incident reports + comments | RSS + scraper |
| **Scramble.nl** | Dutch military aviation spotters | Forum scraper |
| **Airliners.net forums** | General aviation incidents | RSS |

**Data Schema:**

```sql
CREATE TABLE aviation_forum_posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    forum_source TEXT, -- pprune, avherald, etc
    thread_id TEXT,
    thread_title TEXT,
    post_author TEXT,
    post_timestamp TIMESTAMP,
    post_content TEXT,
    referenced_incident_id INTEGER,
    sentiment_score REAL,
    FOREIGN KEY (referenced_incident_id) REFERENCES incidents(id)
);

CREATE TABLE forum_keywords (
    post_id INTEGER,
    keyword TEXT,
    context_snippet TEXT,
    PRIMARY KEY (post_id, keyword),
    FOREIGN KEY (post_id) REFERENCES aviation_forum_posts(post_id)
);
```

**Correlation Logic:**
1. Monitor forums for keywords: "drone", "UAV", "onbemand", airport codes (EHAM, EHEH, etc)
2. NER extraction: dates, locations, aircraft types
3. Fuzzy match to incidents table (location + date ±3 days)
4. Flag for analyst review if forum post precedes official incident report (insider knowledge?)

**Implementation Tasks:**
- [ ] Build PPRuNe scraper
- [ ] Build AvHerald scraper
- [ ] Implement NER pipeline (spaCy Dutch model)
- [ ] Create forum-to-incident correlation algorithm
- [ ] Add forum monitoring dashboard tab

---

### 2.2 Invite-Only Channel Leak Detection

**Objective:** Detect when private Telegram channels leak content to public channels.

**Methodology:**
1. Monitor public channels for messages with "forwarded from private channel" marker
2. Extract private channel metadata (even if you can't access it)
3. Track which public channels receive private channel forwards
4. Identify users who bridge private→public (potential infiltration targets)

**Schema Addition:**

```sql
CREATE TABLE private_channel_leaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    private_channel_id INTEGER, -- may not be accessible
    private_channel_name TEXT,
    public_channel_id INTEGER,
    first_leak_timestamp TIMESTAMP,
    leak_frequency INTEGER DEFAULT 1,
    FOREIGN KEY (public_channel_id) REFERENCES telegram_channels(channel_id)
);
```

**Implementation Tasks:**
- [ ] Detect private channel forwards in scraper
- [ ] Build leak tracking database
- [ ] Create alert system for new private channel discoveries
- [ ] Implement bridging user identification

---

## Phase 3: LinkedIn & Professional Network OSINT

### 3.1 Google Dorking Query System

**Objective:** Gather LinkedIn intelligence without direct platform interaction (avoid tracking).

**Query Templates:**

```python
LINKEDIN_DORK_QUERIES = [
    # Drone hobbyists with Russian connections
    'site:linkedin.com "drone" "Russia" (Netherlands OR Belgium OR Germany)',
    'site:linkedin.com "FPV" "pilot" "Ukraine" Netherlands',
    'site:linkedin.com "UAV" "engineer" "Moscow" -recruiter',

    # Aviation security career switches
    'site:linkedin.com "aviation security" "career change" (2022 OR 2023 OR 2024)',
    'site:linkedin.com "airport security" "consultant" Netherlands',

    # RF/Telecom engineers with gaps
    'site:linkedin.com "RF engineer" "telecommunications" "career break"',
    'site:linkedin.com "signal processing" "freelance" Ukraine',

    # Specific companies of interest
    'site:linkedin.com "Schiphol" "former employee" "security"',
    'site:linkedin.com (DJI OR Autel OR Parrot) Netherlands engineer',
]
```

**Automated Pipeline:**
1. Rotate through queries daily
2. Parse Google SERP results (profile URLs, snippets)
3. Extract: name, title, company, location, keywords
4. Store in database for pattern analysis
5. Flag suspicious combinations (e.g., "aviation security" + "Russia" + "career gap in 2023")

**Schema:**

```sql
CREATE TABLE linkedin_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_url TEXT UNIQUE,
    full_name TEXT,
    headline TEXT,
    current_company TEXT,
    current_title TEXT,
    location TEXT,
    profile_snippet TEXT, -- from Google SERP
    discovered_via_query TEXT,
    discovery_date TIMESTAMP,
    risk_flags TEXT -- JSON array of flags
);

CREATE TABLE persona_matches (
    profile_id INTEGER,
    persona_type TEXT, -- drone_hobbyist, aviation_security, rf_engineer, etc
    confidence_score REAL,
    matching_keywords TEXT, -- JSON array
    PRIMARY KEY (profile_id, persona_type),
    FOREIGN KEY (profile_id) REFERENCES linkedin_profiles(profile_id)
);
```

**Implementation Tasks:**
- [ ] Build Google dorking scraper (with rate limiting)
- [ ] Create SERP parser
- [ ] Implement profile data extraction
- [ ] Build persona matching algorithm
- [ ] Create LinkedIn intel dashboard

---

### 3.2 Target Persona Profiling

**High-Value Personas:**

#### **Persona 1: Drone Hobbyist with Eastern Connections**
- **Keywords:** FPV, racing drone, long-range, custom build, Betaflight
- **Location:** Netherlands, Belgium, Germany (near targets)
- **Connections:** Russia, Ukraine, Belarus LinkedIn connections
- **Red flags:** Aviation photography interest, airport proximity, recent Ukraine/Russia travel

#### **Persona 2: Aviation Security Switcher**
- **Former role:** Airport security, air traffic control, military aviation
- **Timeline:** Career change 2022-2024 (post-Ukraine invasion)
- **Red flags:** Move to "consulting", vague job descriptions, unexplained gaps

#### **Persona 3: RF/Telecom Engineer**
- **Skills:** Signal processing, antenna design, SDR, frequency analysis
- **Red flags:** Freelance work for undisclosed clients, Eastern Europe projects, drone-related repos on GitHub

**Scoring Algorithm:**

```python
def calculate_persona_risk_score(profile):
    score = 0

    # Location proximity to targets
    if profile.location in ['Amsterdam', 'Rotterdam', 'Eindhoven', 'Brussels']:
        score += 20

    # Keywords
    high_risk_keywords = ['drone', 'UAV', 'FPV', 'RF', 'SDR', 'aviation security']
    score += sum(10 for kw in high_risk_keywords if kw in profile.headline.lower())

    # Connections
    if has_russian_connections(profile):
        score += 30

    # Timeline anomalies
    if has_career_gap_2022_2024(profile):
        score += 25

    return min(score, 100)  # Cap at 100
```

**Implementation Tasks:**
- [ ] Define persona templates
- [ ] Build scoring algorithm
- [ ] Create manual review queue for high-scoring profiles
- [ ] Design persona dashboard UI

---

## Phase 4: Integration & Automation

### 4.1 Unified Intelligence Dashboard

**Components:**
- **Temporal Correlation View:** Timeline of incidents + Telegram spikes + forum posts
- **Social Graph Explorer:** Interactive network visualization (channels, users, forwards)
- **Linguistic Anomalies:** Flagged messages with Russian→Dutch indicators
- **LinkedIn Intel:** Persona matches with risk scores
- **Alert Feed:** Real-time notifications for new discoveries

**Implementation Tasks:**
- [ ] Design unified dashboard mockup
- [ ] Build temporal correlation view
- [ ] Integrate social graph visualization
- [ ] Add linguistic analysis panel
- [ ] Create alert management system

---

### 4.2 Automated Collection Jobs

**Cron Schedule:**

```bash
# Telegram scraping (every 2 hours)
0 */2 * * * /path/to/telegram_scraper.py

# Forum monitoring (every 6 hours)
0 */6 * * * /path/to/forum_scraper.py

# LinkedIn dorking (daily at 3 AM)
0 3 * * * /path/to/linkedin_dorker.py

# Incident correlation analysis (daily at 4 AM)
0 4 * * * /path/to/correlation_engine.py

# Weekly social graph update (Sundays at 2 AM)
0 2 * * 0 /path/to/social_graph_builder.py
```

**Implementation Tasks:**
- [ ] Create cron job scripts
- [ ] Implement error handling & logging
- [ ] Add email/Slack notifications for critical alerts
- [ ] Build health monitoring dashboard for scrapers

---

## Implementation Priority Matrix

| Task | Impact | Effort | Priority |
|------|--------|--------|----------|
| Database schema extensions | High | Medium | **P0** |
| Incident correlation engine | High | Medium | **P0** |
| Telegram forward tracking | High | Medium | **P1** |
| Linguistic fingerprinting (rule-based) | Medium | Low | **P1** |
| Forum monitoring (PPRuNe, AvHerald) | High | Medium | **P1** |
| LinkedIn dorking system | Medium | Low | **P2** |
| Social graph visualization | Medium | High | **P2** |
| Persona profiling | Medium | Medium | **P2** |
| ML-based linguistic detection | Low | High | **P3** |

---

## Success Metrics

**Phase 1 (Month 1):**
- [ ] 10+ Telegram channels with social graph data
- [ ] 5+ incident-correlated activity spikes detected
- [ ] 100+ forum posts ingested and correlated

**Phase 2 (Month 2):**
- [ ] 50+ LinkedIn profiles in database
- [ ] 3+ high-risk persona matches flagged
- [ ] Private channel leak detection operational

**Phase 3 (Month 3):**
- [ ] Unified dashboard deployed
- [ ] All automated jobs running stable
- [ ] First actionable intelligence lead generated

---

## Risk Mitigation

### Legal & Ethical Considerations
- **Data retention:** Comply with GDPR (30-day retention for personal data)
- **Scraping:** Respect robots.txt, rate limits
- **Privacy:** Hash personal identifiers, no facial recognition

### Operational Security
- **API keys:** Rotate Telegram API credentials monthly
- **IP rotation:** Use proxy rotation for LinkedIn dorking
- **Logging:** Minimal PII in logs, encryption at rest

---

## Next Steps

1. **Approve roadmap** → Stakeholder review
2. **Database migration** → Implement schema changes
3. **MVP development** → Focus on P0/P1 tasks
4. **Testing phase** → Validate with historical incidents
5. **Production deployment** → Gradual rollout with monitoring

---

**Document Owner:** OSINT Development Team
**Review Cycle:** Bi-weekly
**Last Updated:** 2025-11-18
