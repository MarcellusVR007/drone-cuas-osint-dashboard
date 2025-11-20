# Adaptive Intelligence System - Master Plan
**Self-Learning OSINT Collection & Analysis Framework**

**Gebaseerd op:** CIA/NSA/FBI tradecraft + moderne ML/AI technieken

---

## STRATEGISCH OVERZICHT

### Doel
Een **zelf-lerend intelligence systeem** dat:
1. Automatisch waardevolle databronnen ontdekt
2. Slimme relaties legt tussen data points
3. Zijn eigen collection strategie optimaliseert
4. Voorspellende intelligence levert (niet alleen reactief)

### Drie Pijlers
```
┌─────────────────────┐
│   PIJLER 1:         │
│ Multi-Source        │──┐
│ Data Collection     │  │
└─────────────────────┘  │
                         │
┌─────────────────────┐  │    ┌──────────────────────┐
│   PIJLER 2:         │  │    │   INTELLIGENCE       │
│ Intelligent Link    │──┼───►│   OUTPUT             │
│ Analysis            │  │    │  • Predictions       │
└─────────────────────┘  │    │  • Attribution       │
                         │    │  • Alerts            │
┌─────────────────────┐  │    │  • Patterns          │
│   PIJLER 3:         │  │    └──────────────────────┘
│ Adaptive Learning   │──┘
│ & Optimization      │
└─────────────────────┘
```

---

## PIJLER 1: MULTI-SOURCE DATA COLLECTION

### Fase 1.1: Data Source Inventory (Week 1)

**Doel:** Inventariseer ALLE beschikbare bronnen en prioriteer op basis van intelligence value

#### **A. Telegram (Primary SIGINT)**

**Huidige Status:**
- ✅ 486 messages al verzameld
- ✅ Telegram API operational
- ❓ Welke channels worden gemonitord?

**Action Plan:**
```
STAP 1: Analyze Existing Data
├─ Run: python backend/analyze_existing_telegram_data.py
├─ Output: Welke channels zijn high-value?
├─ Output: Welke keywords correleren met incidenten?
└─ Output: Baseline activity patterns

STAP 2: Channel Prioritization (NSA "Collection Requirements" model)
Priority Tier 1 (Critical - Check every 1 hour):
  □ Confirmed GRU/SVR-linked channels
  □ Drone bounty/recruitment channels
  □ Channels with proven incident correlation

Priority Tier 2 (High - Check every 2 hours):
  □ Political extremist (FVD, Baudet inner circle)
  □ Pro-Russia disinformation networks
  □ FPV/drone hobbyist communities (NL/BE/DE)

Priority Tier 3 (Medium - Check every 6 hours):
  □ General aviation news
  □ Military aviation enthusiasts
  □ Flight tracking communities

STAP 3: Collection Parameters
For each message collect:
  ├─ Content: Full text + media (hash + URL)
  ├─ Metadata: views, forwards, reactions, edit history
  ├─ User data: username, bio (hashed voor privacy)
  ├─ Forward chains: Origin channel tracking
  └─ Temporal: Exact timestamp (timezone analysis)

STAP 4: Legal/Ethical Framework
  ├─ Only public channels (no infiltration)
  ├─ GDPR compliance: hash PII, 30-day retention for personal data
  ├─ Audit logging: All collection activities logged
  └─ No active participation/manipulation
```

#### **B. Aviation Forums (Secondary OSINT)**

**Bronnen:**
1. PPRuNe (Professional Pilots Rumour Network) - pprune.org
2. AvHerald - avherald.com
3. Scramble.nl (Dutch military aviation)
4. Airliners.net forums

**Action Plan:**
```
STAP 1: RSS Feed Monitoring
├─ Check every 30 minutes for new posts
├─ Keywords: drone, UAV, unmanned, restricted airspace
└─ Auto-flag posts with ≥3 keywords

STAP 2: Forum Scraping
├─ Daily: Full thread scrape for flagged keywords
├─ Extract: Post content, author metadata, timestamp
└─ Detect: Edit history, deleted posts (archive.org)

STAP 3: Credibility Assessment (FBI Source Rating)
For each post/author:
  A - Completely reliable (verified professionals)
  B - Usually reliable (established members)
  C - Fairly reliable (occasional contributors)
  D - Not usually reliable (new/anonymous)
  E - Unreliable (known trolls)
  F - Cannot be judged

STAP 4: Insider Knowledge Detection
Red flags:
  ├─ Post PRECEDES official incident report
  ├─ Technical details not publicly available
  ├─ Use of insider jargon/terminology
  └─ Author location near incident site
```

#### **C. LinkedIn (HUMINT - Passive)**

**Doel:** Identify potential operatives/handlers via open-source profiling

**ETHISCH/LEGAAL:**
- ❌ NO direct LinkedIn scraping (ToS violation)
- ✅ Google SERP dorking only (public snippets)
- ✅ GDPR Article 6(1)(f) - Legitimate Interest (security)

**Action Plan:**
```
STAP 1: Target Persona Definition
Persona 1: Drone Hobbyist + Russian Ties
  ├─ Keywords: FPV, drone racing, long-range, custom build
  ├─ Location: NL/BE/DE within 100km of incidents
  └─ Red flags: Russia travel, employment gap 2022-2024

Persona 2: Aviation Security Career Switcher
  ├─ Former role: Airport security, ATC, military aviation
  ├─ Timeline: Career change post-Feb 2022
  └─ Red flags: Vague "consulting", unexplained gaps

Persona 3: RF/Telecom Engineer
  ├─ Skills: SDR, antenna design, GPS spoofing
  └─ Red flags: Eastern Europe projects, crypto payments

STAP 2: Google Dork Queries (Daily rotation, use proxies)
site:linkedin.com "FPV pilot" (Netherlands OR Belgium) -recruiter
site:linkedin.com "drone" "Russia" Germany
site:linkedin.com "aviation security" "freelance" 2023
site:linkedin.com "RF engineer" "SDR" Ukraine

STAP 3: Data Storage (Privacy-First)
  ├─ Store: Profile URL + Google snippet ONLY
  ├─ NO: Photos, messages, connections, full profiles
  ├─ Risk score: Based on keyword/signal matches
  └─ Manual review: All high-risk (>70) flagged

STAP 4: Risk Scoring Algorithm
Base score: 0
+ Location proximity to incidents: +20
+ Drone/RF keywords in headline: +15 each
+ Russian connections (travel, language): +30
+ Employment gap 2022-2024: +25
+ Crypto/OpSec behavior: +15
Total > 70 = High risk → Manual analyst review
```

#### **D. Flight Tracking (SIGINT - ADS-B)**

**Bron:** ADS-B Exchange, FlightRadar24 API

**Action Plan:**
```
STAP 1: Incident-Correlated Collection
For each drone incident:
  ├─ Pull 24h flight history (±12h from incident)
  ├─ Radius: 50km from incident location
  └─ Flag: Military scrambles, unusual patterns

STAP 2: Anomaly Detection
  ├─ Sudden altitude changes
  ├─ Loitering patterns (circles, figure-8)
  ├─ Unusual aircraft types for location
  └─ Airspace closures

STAP 3: Real-Time Monitoring (Future Phase)
  ├─ Alert: Military scrambles in NL/BE
  ├─ Alert: Airspace closures at key airports
  └─ Cross-reference with Telegram activity
```

#### **E. Blockchain (FININT)**

**Bron:** Bitcoin/Monero transaction monitoring

**Action Plan:**
```
STAP 1: Wallet Extraction
  ├─ Source: Telegram posts mentioning crypto addresses
  ├─ Extract: BTC, ETH, XMR, USDT addresses
  └─ Validate: Checksum verification

STAP 2: Transaction Monitoring
  ├─ Track: Inflows, outflows, clustering
  ├─ Tool: Blockchain explorers + Chainalysis-style clustering
  └─ Flag: Large transactions (>0.1 BTC) around incident dates

STAP 3: Attribution Chain
  ├─ Link: Wallet → Telegram handler
  ├─ Link: Wallet → Known exchange accounts
  └─ Pattern: Payment timing vs incident timing
```

---

## PIJLER 2: INTELLIGENT LINK ANALYSIS

### Fase 2.1: Link Discovery Engine (Week 2)

**Doel:** Automatisch relaties ontdekken tussen entities (CIA "Link Analysis" tradecraft)

#### **A. Entity-Relationship Database**

**Schema:**
```sql
CREATE TABLE intelligence_entities (
    id INTEGER PRIMARY KEY,
    entity_type TEXT,  -- incident, telegram_message, forum_post, linkedin_profile, wallet, location, person
    entity_id INTEGER,
    entity_data TEXT,  -- JSON blob
    risk_score INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE intelligence_links (
    id INTEGER PRIMARY KEY,
    entity_a_id INTEGER REFERENCES intelligence_entities(id),
    entity_b_id INTEGER REFERENCES intelligence_entities(id),
    link_type TEXT,  -- temporal, spatial, financial, social, linguistic
    confidence_score REAL,  -- 0-1
    evidence TEXT,  -- JSON: supporting evidence
    link_strength REAL,  -- 0-1, how strong is relationship
    auto_detected BOOLEAN,
    analyst_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

#### **B. Automated Link Discovery Algorithms**

**Algorithm 1: Temporal Correlation**
```
For each incident:
  1. Get timestamp T
  2. Query all Telegram messages in window [T-48h, T+24h]
  3. For each message in window:
     a. Calculate time_delta = |message.timestamp - T|
     b. Get channel baseline activity (30-day avg)
     c. Calculate z-score of activity volume
     d. If z-score > 2.5:
        - Create link: (incident ↔ telegram_message)
        - Confidence = min(z-score/10, 1.0)
        - Evidence = {"z_score": z, "baseline": avg, "spike": count}
```

**Algorithm 2: Linguistic Attribution**
```
For each Telegram message:
  1. Run linguistic fingerprint detector
  2. If suspicion_score > 30:
     a. Check temporal proximity to any incident (±48h)
     b. If match found:
        - Create link: (incident ↔ message)
        - Confidence = (linguistic_score/100) * temporal_proximity
        - Evidence = {"patterns": flags, "score": score}
```

**Algorithm 3: Spatial Correlation**
```
For each message with location keywords:
  1. Extract locations (NER: spaCy Dutch model)
  2. Geocode locations → lat/lon
  3. For each incident:
     a. Calculate distance = haversine(msg_location, incident_location)
     b. If distance < 50km AND time_delta < 48h:
        - Create link: (incident ↔ message)
        - Confidence = max(0, 1 - distance/50) * temporal_factor
```

**Algorithm 4: Social Network Analysis**
```
Build social graph:
  Nodes = Telegram channels
  Edges = Forward relationships (with weight = forward_count)

Algorithms:
  1. PageRank: Identify influential channels
  2. Community Detection (Louvain): Find handler clusters
  3. Bridge Node Detection: Key information brokers
  4. Centrality Analysis: Who connects disparate groups?

Application:
  - Channels with high PageRank → Priority Tier 1
  - Bridge nodes → Deep monitoring (possible handlers)
  - Communities → Map handler networks
```

**Algorithm 5: Financial Link Discovery**
```
For each Bitcoin wallet:
  1. Get transaction history
  2. For each transaction:
     a. Check if timestamp near incident (±7 days)
     b. Check if amount > threshold (0.01 BTC)
     c. If match:
        - Create link: (wallet ↔ incident)
        - Confidence = amount_score * temporal_proximity

  3. Wallet clustering:
     a. Identify wallets that transact together
     b. Create social graph of wallets
     c. Link clusters to Telegram handlers
```

#### **C. Graph Traversal & Pattern Mining**

**Query 1: Find Attribution Chain**
```sql
-- Given an incident, find all entities within 3 hops
WITH RECURSIVE entity_graph AS (
    SELECT entity_b_id as entity_id, entity_b_type as entity_type,
           1 as hop, link_type, confidence_score
    FROM intelligence_links
    WHERE entity_a_type = 'incident' AND entity_a_id = ?

    UNION

    SELECT l.entity_b_id, l.entity_b_type,
           eg.hop + 1, l.link_type, l.confidence_score
    FROM intelligence_links l
    JOIN entity_graph eg ON l.entity_a_id = eg.entity_id
    WHERE eg.hop < 3 AND l.confidence_score > 0.5
)
SELECT * FROM entity_graph
ORDER BY hop, confidence_score DESC;
```

**Result Example:**
```
Incident #47 (Gilze-Rijen drone)
  ├─ (hop 1) Telegram message #1234 [confidence: 0.85, temporal]
  │   ├─ (hop 2) Channel "gru_dutch_ops" [confidence: 0.75, social]
  │   │   └─ (hop 3) Bitcoin wallet 1A2B3C... [confidence: 0.65, financial]
  │   └─ (hop 2) Linguistic pattern [confidence: 0.70, linguistic]
  └─ (hop 1) Forum post PPRuNe #9876 [confidence: 0.60, spatial]
```

---

## PIJLER 3: ADAPTIVE LEARNING & OPTIMIZATION

### Fase 3.1: Self-Improving Collection Strategy (Week 3)

**Doel:** Systeem leert welke bronnen/channels waardevol zijn en past strategie aan

#### **A. Channel Value Scoring**

**Utility Function:**
```python
def calculate_channel_utility(channel, time_window_days=30):
    """
    Bereken hoe waardevol een channel is voor intelligence
    """
    # Factor 1: Incident Links (hoogste waarde)
    incidents_linked = count_incident_links(channel, days=time_window_days)
    incident_score = min(incidents_linked * 20, 100)  # Max 100

    # Factor 2: Link Confidence
    avg_confidence = average_link_confidence(channel)
    confidence_score = avg_confidence * 50

    # Factor 3: Linguistic Suspicion
    suspicious_messages = count_suspicious_messages(channel, min_score=30)
    linguistic_score = min(suspicious_messages * 5, 50)

    # Factor 4: Forward Network Value
    influence_score = calculate_pagerank(channel) * 30

    # Factor 5: False Positives (penalty)
    false_positives = count_false_positives(channel)
    penalty = false_positives * -10

    total_utility = (
        incident_score * 0.4 +      # 40% weight
        confidence_score * 0.25 +   # 25% weight
        linguistic_score * 0.15 +   # 15% weight
        influence_score * 0.15 +    # 15% weight
        penalty * 0.05              # 5% penalty
    )

    return max(0, min(100, total_utility))
```

**Automated Adjustments:**
```python
def adjust_collection_priorities(weekly=True):
    """
    Wekelijks: herpriotiseer alle channels op basis van utility
    """
    for channel in all_monitored_channels:
        utility = calculate_channel_utility(channel, days=30)

        if utility > 80:
            # Zeer waardevol
            upgrade_to_tier(channel, tier='critical')
            set_collection_frequency(channel, interval='1h')
            alert_analysts(f"Channel {channel} upgraded to CRITICAL")

        elif utility > 50:
            # Waardevol
            set_tier(channel, tier='high')
            set_collection_frequency(channel, interval='2h')

        elif utility > 20:
            # Matig waardevol
            set_tier(channel, tier='medium')
            set_collection_frequency(channel, interval='6h')

        else:
            # Lage waarde
            if utility < 5 and channel.monitored_days > 60:
                # Drop channel na 60 dagen als geen waarde
                remove_from_collection(channel)
                log_removal(channel, reason="Low utility after 60 days")
```

#### **B. Adaptive Keyword Learning**

**TF-IDF Keyword Extraction:**
```python
def learn_high_value_keywords():
    """
    Leer welke keywords echt correleren met incidenten
    """
    # Get all messages linked to incidents
    incident_linked_messages = get_incident_linked_messages(confidence > 0.6)

    # Calculate TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=100,
        ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
        stop_words=dutch_stopwords
    )

    tfidf_matrix = vectorizer.fit_transform([m.text for m in incident_linked_messages])
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1

    # Top keywords
    top_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)[:50]

    # Add to monitoring if not already present
    for keyword, score in top_keywords:
        if keyword not in current_keywords and score > threshold:
            add_keyword_to_monitoring(keyword, confidence=score)
            log_discovery(f"New keyword discovered: {keyword} (score: {score})")
```

#### **C. Automated Channel Discovery**

**Forward-Chain Discovery (NSA "Chaining"):**
```python
def discover_new_channels_via_forwards():
    """
    Ontdek nieuwe channels door forward chains te volgen
    """
    # Start with high-value channels
    seed_channels = get_channels_with_utility(min_utility=70)

    discovered_channels = []

    for seed in seed_channels:
        # Get all channels this seed forwards to/from
        forward_destinations = get_forward_relationships(seed)

        for dest_channel in forward_destinations:
            if dest_channel in monitored_channels:
                continue  # Already monitoring

            # Assess new channel
            # 1. Check forward frequency (how often does seed → dest happen?)
            forward_freq = count_forwards(source=seed, dest=dest_channel)

            # 2. Sample messages from new channel
            sample_messages = scrape_recent_messages(dest_channel, limit=50)

            # 3. Run linguistic analysis
            suspicious_count = count_suspicious_messages(sample_messages, min_score=30)

            # 4. Check for keywords
            keyword_matches = count_keyword_matches(sample_messages)

            # 5. Calculate discovery score
            discovery_score = (
                (forward_freq / 10) * 0.3 +
                (suspicious_count / 5) * 0.4 +
                (keyword_matches / 20) * 0.3
            )

            if discovery_score > 0.5:
                add_to_collection_queue(
                    channel=dest_channel,
                    priority='high' if discovery_score > 0.7 else 'medium',
                    source=f"forward_chain from {seed}",
                    confidence=discovery_score
                )
                discovered_channels.append(dest_channel)

    return discovered_channels
```

**Content Similarity Discovery:**
```python
def discover_channels_via_content_similarity():
    """
    Vind channels met vergelijkbare content als high-value channels
    """
    # Get high-value channels
    high_value = get_channels_with_utility(min_utility=70)

    # Build content profiles (TF-IDF vectors)
    channel_vectors = {}
    for channel in high_value:
        messages = get_recent_messages(channel, days=30)
        text_corpus = " ".join([m.text for m in messages])
        channel_vectors[channel] = vectorize_text(text_corpus)

    # Sample unknown channels (e.g., from Telegram search)
    candidate_channels = search_telegram_channels(keywords=["drone", "uav", "fpv"])

    for candidate in candidate_channels:
        if candidate in monitored_channels:
            continue

        # Get sample content
        sample = scrape_recent_messages(candidate, limit=30)
        candidate_vector = vectorize_text(" ".join([m.text for m in sample]))

        # Calculate cosine similarity to high-value channels
        max_similarity = 0
        most_similar_channel = None

        for hv_channel, hv_vector in channel_vectors.items():
            similarity = cosine_similarity(candidate_vector, hv_vector)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_channel = hv_channel

        if max_similarity > 0.6:
            add_to_collection_queue(
                channel=candidate,
                priority='medium',
                source=f"content_similarity to {most_similar_channel}",
                confidence=max_similarity
            )
```

---

## IMPLEMENTATIE ROADMAP

### Week 1: Foundation & Baseline
```
DAG 1-2: Data Inventory
  ├─ Analyze existing 486 Telegram messages
  ├─ Identify current channels being monitored
  ├─ Import to database
  └─ Generate baseline report

DAG 3-4: Collection Infrastructure
  ├─ Implement priority-based Telegram scraper
  ├─ Build forum scrapers (PPRuNe, AvHerald)
  ├─ Set up LinkedIn dorking automation
  └─ Configure cron jobs

DAG 5-7: Initial Data Collection
  ├─ Scrape Priority Tier 1 channels (hourly)
  ├─ Scrape Priority Tier 2 channels (2h)
  ├─ Monitor aviation forums (daily)
  └─ Collect 7 days baseline data
```

### Week 2: Link Analysis Engine
```
DAG 8-9: Database Extension
  ├─ Create intelligence_entities table
  ├─ Create intelligence_links table
  └─ Migration scripts

DAG 10-12: Link Discovery Algorithms
  ├─ Implement temporal correlation
  ├─ Implement linguistic attribution
  ├─ Implement spatial correlation
  ├─ Implement social network analysis
  └─ Test on existing data

DAG 13-14: Validation & Tuning
  ├─ Manual review of top 100 links
  ├─ Tune confidence thresholds
  └─ Generate link analysis report
```

### Week 3: Adaptive Learning
```
DAG 15-17: Utility Scoring System
  ├─ Implement channel utility function
  ├─ Build automated priority adjuster
  ├─ Test on current channels
  └─ Deploy weekly adjustment cron

DAG 18-20: Discovery Algorithms
  ├─ Forward-chain discovery
  ├─ Content similarity discovery
  ├─ Keyword evolution system
  └─ Test discovery on sample data

DAG 21: Integration & Testing
  ├─ Full end-to-end test
  ├─ Performance benchmarking
  └─ Deploy to production
```

### Week 4: Intelligence Layer
```
DAG 22-24: Analysis Tools
  ├─ Hypothesis engine (ACH)
  ├─ Timeline generator
  ├─ Attribution chain builder
  └─ Dashboard integration

DAG 25-28: Automated Reporting
  ├─ Daily intelligence summary
  ├─ Weekly pattern analysis
  ├─ Monthly trend report
  └─ Alert system (high-confidence links)
```

---

## SUCCESS METRICS

### Month 1:
- [ ] 20+ Telegram channels monitored
- [ ] 10,000+ messages collected
- [ ] 3+ aviation forums scraped daily
- [ ] 50+ LinkedIn profiles assessed

### Month 2:
- [ ] 100+ high-confidence links discovered
- [ ] 5+ incidents with attribution chains
- [ ] 10+ new channels discovered automatically
- [ ] Channel utility scoring operational

### Month 3:
- [ ] Predictive capability: detect activity spike BEFORE incident
- [ ] Attribution accuracy: 75%+ confidence on 50% of incidents
- [ ] Collection efficiency: 50% increase via adaptive prioritization
- [ ] Full automation: daily intelligence reports

---

## VRAGEN VOOR JOU:

1. **Telegram Channels:** Welke channels zitten in die 486 messages? (kunnen we uit data halen)
2. **Prioriteiten:** Welke van de 3 pijlers wil je als eerste zien draaien?
3. **Resources:** Heb je budget voor tools zoals Chainalysis (blockchain) of premium APIs?
4. **Timeline:** Is 4 weken realistisch of moet het sneller/langzamer?
5. **Manual Review:** Hoeveel tijd heb je voor analyst review van flagged items?

**Wat wil je als eerste aanpakken?**
