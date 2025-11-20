# 🔬 Hypothesis Testing Framework
**Local Recruitment vs Russian State Actors**

## 🎯 Research Question

**Zijn de drone incidenten in EU/Benelux uitgevoerd door:**
- **H1**: Lokaal gerekruteerde spotters/operators (EU burgers betaald door GRU)
- **H2**: Russische state actors (GRU officers met tourist/business visa)
- **H3**: Hybride model (Russian handlers + local assets)
- **H4**: False Flag - Andere state actor (China, Iran, North Korea) die Rusland wil framen
- **H5**: Non-state actors - Criminal organizations, hacktivists, of copycats

⚠️ **BELANGRIJK**: We focussen op H1-H3 (Rusland-gerelateerd) maar blijven alert voor H4-H5 indicatoren.

---

## 📊 Hypotheses & Indicatoren

### Hypothesis 1: Local Recruitment (RECRUITED_LOCAL)

**Profiel**:
- EU burger (Nederlands, Belgisch, Duits, etc)
- Financiële motivatie (geld, crypto)
- Beperkte training (consumer drones, basis surveillance)
- Gerekruteerd via online platforms (Telegram, Reddit, VK)

**Indicatoren die H1 ondersteunen**:

| Indicator | Data Source | Hoe te meten | Likelihood H1 |
|-----------|-------------|--------------|---------------|
| **Recruitment posts gevonden** | Telegram, Reddit, VK, forums | Aanwezigheid posts met payment offers | CRITICAL ✅ |
| **Amateur execution** | Incident data | Low-cost drones (DJI), slechte opsec | HIGH |
| **Payment traces** | Blockchain analysis | Small payments (€200-2000) to EU wallets | HIGH |
| **Local knowledge** | Incident locations | Targets require local knowledge (restricted areas) | MEDIUM |
| **Multiple incidents, same region** | Incident clustering | Geographic clustering suggests local asset | MEDIUM |
| **Consumer equipment** | Incident descriptions | DJI drones, GoPro cameras, consumer tech | MEDIUM |
| **Mistakes/arrests** | News reports | Amateur mistakes (caught, drone crashes) | HIGH |
| **Language/communication** | Telegram metadata | Communication in local language (Dutch, German) | MEDIUM |

**Data om te verzamelen**:
1. ✅ Recruitment posts (Telegram, Reddit, VK) - **IN PROGRESS**
2. Blockchain transactions naar EU wallets - **TODO**
3. Incident execution quality analysis - **TODO**
4. Geographic clustering analysis - **TODO**
5. Equipment profiling (consumer vs military) - **TODO**

---

### Hypothesis 2: Russian State Actors (STATE_ACTOR_PROFESSIONAL)

**Profiel**:
- GRU/FSB officer
- Tourist/business visa (Schengen allows 90 days)
- Professional training (military drones, advanced surveillance)
- Exfiltration via Russia (no local ties)

**Indicatoren die H2 ondersteunen**:

| Indicator | Data Source | Hoe te meten | Likelihood H2 |
|-----------|-------------|--------------|---------------|
| **Professional execution** | Incident data | Military-grade drones (Orlan-10), advanced tech | CRITICAL ✅ |
| **No recruitment traces** | SOCMINT | Absence of recruitment posts despite monitoring | HIGH |
| **Russian passport patterns** | Border crossing data | Russian nationals entering EU before incidents | CRITICAL |
| **Systematic targeting** | Incident patterns | Military/strategic targets (not random) | HIGH |
| **No payment traces** | Blockchain | No crypto payments to locals | MEDIUM |
| **Maritime launch** | Flight forensics | Launch from Russian vessels in Baltic/North Sea | HIGH |
| **Zero arrests** | News reports | No local arrests despite incidents | MEDIUM |
| **Russian equipment** | Technical analysis | Russian-made drones, encrypted comms | HIGH |

**Data om te verzamelen**:
1. Border crossing data (Schengen Information System) - **RESTRICTED ACCESS**
2. ✅ Flight forensics (maritime launch analysis) - **IMPLEMENTED**
3. Equipment technical analysis - **TODO**
4. Arrest records analysis - **TODO**
5. Timeline analysis (Russian holidays, diplomatic events) - **TODO**

---

### Hypothesis 3: Hybrid Model (HYBRID)

**Profiel**:
- Russian handler + local spotter
- Handler provides equipment, training, payment
- Spotter provides local access, surveillance
- Payment through intermediaries (handlers)

**Indicatoren die H3 ondersteunen**:

| Indicator | Data Source | Hoe te meten | Likelihood H3 |
|-----------|-------------|--------------|---------------|
| **Sophisticated + local** | Incident data | Advanced equipment + local targeting | HIGH |
| **Recruitment + no arrests** | SOCMINT + news | Recruitment posts found, but no local arrests | MEDIUM |
| **Network patterns** | Social network analysis | Handler → Spotter connections visible | HIGH |
| **Training posts** | Forums | Posts offering training (not just payment) | MEDIUM |
| **Repeated incidents** | Incident timeline | Same region, improving technique over time | MEDIUM |

**Data om te verzamelen**:
1. Network graph analysis (handlers → spotters) - **TODO**
2. ✅ Timeline analysis (learning curve visible?) - **PARTIAL**
3. Training material references - **TODO**

---

## 🔍 Evidence Collection Strategy

### Phase 1: OSINT (Current - Week 1-4)

**Goal**: Find recruitment evidence (supports H1)

**Methods**:
1. ✅ Telegram monitoring (2283 posts analyzed)
2. ⏳ Reddit scraping (r/aviation, r/flightradar24)
3. ⏳ VK/OK.ru monitoring (Russian diaspora)
4. ⏳ Aviation forum monitoring (PPRuNe, FlightRadar24)

**Success Criteria**:
- ✅ **IF found**: Recruitment posts → Supports H1 (local recruitment)
- ❌ **IF NOT found**: Does NOT rule out H1 (recruitment may be in closed groups)
- ❌ **IF NOT found**: Weakly supports H2 (no need to recruit if using own agents)

**Current Status**:
- 2283 Telegram posts: 0 recruitment posts found (all propaganda/news)
- Reddit: Framework ready, needs deployment
- VK: Roadmap created, not yet implemented

**Conclusion so far**:
⚠️ No recruitment evidence found YET, but:
- Sample size still small (only 1 platform monitored)
- May be looking in wrong channels (need VK, Reddit)
- Recruitment may be in private/closed groups

---

### Phase 2: Incident Pattern Analysis (Week 2-5)

**Goal**: Analyze execution quality & patterns (distinguishes H1 vs H2)

**Methods**:
1. Equipment profiling
2. Execution quality scoring
3. Geographic clustering
4. Timeline analysis

**Implementation**:

```python
# Equipment Classification
def classify_equipment(incident):
    """
    Consumer (DJI Mavic, GoPro) → RECRUITED_LOCAL
    Military (Orlan-10, encrypted) → STATE_ACTOR
    """
    if "orlan" in incident.drone_description.lower():
        return "STATE_ACTOR", 0.9
    elif "dji" in incident.drone_description.lower():
        return "RECRUITED_LOCAL", 0.7
    else:
        return "UNKNOWN", 0.3

# Execution Quality
def score_execution_quality(incident):
    """
    Score 0-100:
    - 0-30: Amateur (supports H1)
    - 31-70: Semi-professional (supports H3)
    - 71-100: Professional (supports H2)
    """
    score = 50  # baseline

    # Positive indicators (professional)
    if incident.altitude > 1000:  # meters
        score += 20
    if "encrypted" in incident.description:
        score += 15
    if "maritime" in incident.launch_zone:
        score += 25

    # Negative indicators (amateur)
    if "crashed" in incident.description:
        score -= 20
    if "recovered" in incident.description:
        score -= 15

    return min(100, max(0, score))

# Geographic Clustering
def analyze_geographic_patterns():
    """
    Tight clustering (same city, multiple incidents) → LOCAL asset
    Spread out (random locations) → TRAVELING agents
    """
    # Implement DBSCAN clustering on incident lat/lon
    # High density clusters suggest local asset
    pass
```

**Expected Results**:
- **IF** incidents show amateur execution → Supports H1
- **IF** incidents show professional execution → Supports H2
- **IF** mixed quality over time (improving) → Supports H3

---

### Phase 3: Blockchain Analysis (Week 3-6)

**Goal**: Find payment trails (critical for H1)

**Methods**:
1. Monitor sanctioned Russian wallets (OFAC list)
2. Track transactions to EU-based wallets
3. Identify payment patterns (€200-2000 range = recruitment)

**Data Sources**:
- Blockchain explorers (blockchain.com, blockchair.com)
- OFAC Sanctioned wallets list
- Chainalysis (commercial tool - expensive)

**Expected Results**:
- **IF** small payments (€200-2000) to EU wallets → Supports H1
- **IF** large payments (€50k+) → Supports H2 (state funding)
- **IF** no payments found → Inconclusive (may use cash/other crypto)

**Challenges**:
- Privacy coins (Monero) not traceable
- Mixers/tumblers hide origins
- Need wallet addresses (from recruitment posts)

---

### Phase 4: Border Crossing Analysis (Week 4-8)

**Goal**: Find Russian nationals entering EU before incidents (supports H2)

**Methods**:
1. Request Schengen Information System (SIS) data
2. Analyze Russian visa applications
3. Cross-reference with incident dates

**Data Source**:
- **RESTRICTED** - Requires law enforcement access (AIVD, MIVD, Frontex)
- Cannot be done without official partnership

**Expected Results**:
- **IF** Russian nationals present near incidents → Supports H2
- **IF** no Russians in area → Supports H1

**Reality Check**:
⚠️ This data is ONLY accessible through official channels.
Recommendation: Partner with AIVD/MIVD if project gains traction.

---

## 📈 Scoring Matrix

**How to calculate likelihood for each hypothesis**:

```python
def calculate_hypothesis_likelihood():
    """
    Weighted scoring of evidence for each hypothesis
    Returns: (H1_score, H2_score, H3_score) each 0-100
    """

    weights = {
        'recruitment_posts_found': 30,      # CRITICAL for H1
        'amateur_execution': 20,            # HIGH for H1
        'professional_equipment': 25,       # CRITICAL for H2
        'no_arrests': 15,                   # MEDIUM for H2
        'blockchain_payments': 20,          # HIGH for H1
        'maritime_launch': 25,              # HIGH for H2
        'geographic_clustering': 15,        # MEDIUM for H1
        'russian_nationals_present': 30,    # CRITICAL for H2
    }

    # Evidence scores (0 = no evidence, 1 = strong evidence)
    evidence = {
        'recruitment_posts_found': 0.0,     # NOT YET FOUND
        'amateur_execution': 0.3,           # PARTIAL (need more analysis)
        'professional_equipment': 0.7,      # ORLAN-10 found
        'no_arrests': 1.0,                  # TRUE (no arrests reported)
        'blockchain_payments': 0.0,         # NOT YET ANALYZED
        'maritime_launch': 0.5,             # POSSIBLE (Baltic/North Sea)
        'geographic_clustering': 0.0,       # NOT YET ANALYZED
        'russian_nationals_present': 0.0,   # NO DATA (restricted)
    }

    # Calculate scores
    H1_score = (
        evidence['recruitment_posts_found'] * weights['recruitment_posts_found'] +
        evidence['amateur_execution'] * weights['amateur_execution'] +
        evidence['blockchain_payments'] * weights['blockchain_payments'] +
        evidence['geographic_clustering'] * weights['geographic_clustering']
    )

    H2_score = (
        evidence['professional_equipment'] * weights['professional_equipment'] +
        evidence['no_arrests'] * weights['no_arrests'] +
        evidence['maritime_launch'] * weights['maritime_launch'] +
        evidence['russian_nationals_present'] * weights['russian_nationals_present']
    )

    H3_score = (H1_score + H2_score) / 2  # Hybrid = combination

    return {
        'H1_LOCAL_RECRUITMENT': H1_score,
        'H2_STATE_ACTORS': H2_score,
        'H3_HYBRID': H3_score
    }

# Current scores (based on available data):
scores = calculate_hypothesis_likelihood()
# H1: ~6  (low - no recruitment posts found yet)
# H2: ~33 (medium - professional equipment + no arrests)
# H3: ~19 (low-medium - not enough data)
```

**Current Assessment (November 2025)**:
```
H1 (Local Recruitment):   6/100  ❌ LOW - No recruitment evidence found
H2 (State Actors):       33/100  ⚠️ MEDIUM - Professional equipment, no arrests
H3 (Hybrid):             19/100  ⚠️ LOW-MEDIUM - Insufficient data

Conclusion: Currently H2 (State Actors) is MOST LIKELY based on:
- Professional equipment (Orlan-10)
- Zero arrests despite multiple incidents
- Maritime launch capability

BUT: We haven't exhausted H1 investigation yet!
Need to: Deploy Reddit, VK monitoring before concluding.
```

---

## ✅ Decision Tree: What Evidence Proves What?

```
START: We observe drone incidents in EU
│
├─ FIND recruitment posts? (Telegram/Reddit/VK)
│  │
│  ├─ YES → H1 LIKELY (local recruitment active)
│  │      → Continue: Find payments, arrests?
│  │
│  └─ NO → Inconclusive (may be closed groups)
│         → Check other evidence
│
├─ Equipment analysis
│  │
│  ├─ Consumer (DJI, GoPro) → H1 LIKELY
│  │
│  ├─ Military (Orlan-10) → H2 LIKELY
│  │
│  └─ Mixed → H3 POSSIBLE
│
├─ Arrests made?
│  │
│  ├─ YES, local arrested → H1 CONFIRMED
│  │
│  └─ NO arrests → H2 or H3 (professionals escape)
│
├─ Payment traces? (Blockchain)
│  │
│  ├─ Small (€200-2000) to EU wallets → H1 LIKELY
│  │
│  ├─ Large (€50k+) state funding → H2 LIKELY
│  │
│  └─ None found → H2 (state funded, no crypto)
│
└─ Russian nationals in EU? (Border data)
   │
   ├─ YES, near incidents → H2 CONFIRMED
   │
   └─ NO → H1 or H3 LIKELY
```

---

## 🎯 Immediate Action Plan

### Week 1-2: Recruitment Search (H1 Test)
```bash
1. ✅ Deploy Telegram classifier (DONE - 0 recruitment posts)
2. ⏳ Deploy Reddit scraper
3. ⏳ Deploy VK scraper
4. ⏳ Monitor for 2 weeks

Decision point:
- IF recruitment posts found → H1 supported, continue investigation
- IF no recruitment posts found → H1 weakened, focus on H2 evidence
```

### Week 3-4: Incident Pattern Analysis (H1 vs H2)
```bash
1. Classify all 49 incidents by equipment type
2. Score execution quality (amateur vs professional)
3. Geographic clustering analysis
4. Generate H1 vs H2 likelihood scores

Decision point:
- IF amateur execution → H1 likely
- IF professional execution → H2 likely
- IF mixed → H3 possible
```

### Week 5-6: Blockchain Analysis (H1 Test)
```bash
1. Extract wallet addresses from any recruitment posts found
2. Monitor sanctioned Russian wallets (OFAC list)
3. Track transactions to EU-based wallets
4. Identify payment patterns

Decision point:
- IF payments found → H1 confirmed
- IF no payments → H2 likely (state funded)
```

### Week 7-8: Report & Recommendations
```bash
1. Calculate final H1/H2/H3 likelihood scores
2. Generate evidence report
3. Recommend next steps (law enforcement partnership?)
4. Publish findings (anonymized)
```

---

## 📊 What Would Prove Each Hypothesis?

### H1 (Local Recruitment) PROVEN if:
✅ Recruitment posts found on Telegram/Reddit/VK
✅ Blockchain payments (€200-2000) to EU wallets
✅ Local arrest made
✅ Amateur execution (crashed drones, mistakes)

### H2 (State Actors) PROVEN if:
✅ Russian nationals border crossing data matches incident timeline
✅ Professional equipment (Orlan-10, encrypted comms)
✅ Maritime launch confirmed (Russian vessels in area)
✅ Zero arrests despite multiple incidents
✅ No recruitment posts found (no need to recruit)

### H3 (Hybrid) PROVEN if:
✅ Recruitment posts found + professional execution
✅ Network graph shows handler → spotter connections
✅ Training material shared online
✅ Improving execution quality over time (learning curve)

---

## 🚨 Wat als we NIETS vinden?

**Scenario**: Geen recruitment posts, geen payments, geen arrests.

**Mogelijke verklaringen**:
1. **Private recruitment** - Closed Telegram groups, invite-only
2. **In-person recruitment** - No online trail (handlers meet spotters offline)
3. **State actors** - No recruitment needed (H2 correct)
4. **Cash payments** - No blockchain trail (old-school espionage)

**Wat te doen**:
- Focus op H2 evidence (maritime launch, equipment analysis)
- Partner met AIVD/MIVD voor border crossing data
- Analyze incident patterns (professional execution?)

**Bottom line**:
Absence of evidence ≠ Evidence of absence.
Als we geen recruitment vinden, betekent dat NIET dat H1 onjuist is.
Het betekent dat we dieper moeten graven of dat H2 waarschijnlijker is.

---

## ✅ Success Criteria

**Project succeeds if we can conclude met confidence >70%**:
- H1 is correct (found recruitment evidence) → Build recruitment monitoring platform
- H2 is correct (state actors confirmed) → Pivot to border crossing analysis
- H3 is correct (hybrid model) → Build network analysis platform

**Project fails if**:
- Confidence <50% for all hypotheses → Insufficient data
- Legal/ethical barriers prevent data collection
- No actionable insights for law enforcement

---

---

## 🚩 Additional Hypotheses: False Flags & Non-State Actors

### Hypothesis 4: False Flag Operation (OTHER_STATE_ACTOR)

**Profiel**:
- Chinese/Iranian/North Korean intelligence services
- Motive: Frame Russia, escalate EU-Russia tensions
- Professional execution (state-level resources)
- False trail to Russia (Russian equipment, Russian-language communication)

**Indicatoren die H4 ondersteunen**:

| Indicator | Data Source | Hoe te meten | Likelihood H4 |
|-----------|-------------|--------------|---------------|
| **Too obvious Russian trail** | SOCMINT | Overly obvious Russian indicators (amateur mistake for pros) | MEDIUM |
| **Chinese/Iranian equipment traces** | Technical analysis | Non-Russian components in equipment | HIGH |
| **Geopolitical timing** | News analysis | Incidents coincide with diplomatic events (EU-China summit, etc) | MEDIUM |
| **Misdirection patterns** | Incident analysis | False clues deliberately planted | HIGH |
| **Non-Russian crypto** | Blockchain | Payment patterns to China/Iran, not Russia | HIGH |

**How to detect**:
```python
def check_false_flag_indicators(incident):
    """
    Red flags for false flag:
    - TOO obvious (Orlan-10 with Russian flag sticker)
    - Technical inconsistencies (Russian drone, Chinese radio)
    - Perfect timing for geopolitical gain
    """
    score = 0

    # Check for overly obvious Russian indicators
    if "russian flag" in incident.description.lower():
        score += 20  # Too obvious = suspicious

    # Check technical inconsistencies
    if "orlan" in incident.drone and "chinese radio" in incident.equipment:
        score += 30  # Mismatch suggests false flag

    # Geopolitical timing
    if incident.date in diplomatic_event_dates:
        score += 15

    return score
```

**Why unlikely (but possible)**:
- ❌ China/Iran/NK hebben EIGEN belangen in EU (niet rationeel om te escaleren)
- ❌ False flag operaties zijn HIGH RISK (als ontdekt = diplomatieke catastrofe)
- ❌ Rusland heeft duidelijke motive voor surveillance (Ukraine war logistics)

**But stay alert for**:
- Overly perfect attribution to Russia
- Technical anomalies (equipment mismatch)
- Timing that benefits China/Iran politically

---

### Hypothesis 5: Non-State Actors (CRIMINAL/HACKTIVIST)

**Profiel**:
- Criminal organizations (smuggling, espionage-for-hire)
- Hacktivists (Anonymous, anti-Russia groups)
- Copycats (inspired by media coverage)
- Private intelligence firms (Black Cube, NSO Group types)

**Indicatoren die H5 ondersteunen**:

| Indicator | Data Source | Hoe te meten | Likelihood H5 |
|-----------|-------------|--------------|---------------|
| **For-profit motive** | Incident targets | Commercial targets (not military) | MEDIUM |
| **Hacktivist claims** | Social media | Groups claiming responsibility | HIGH |
| **Amateur + commercial equipment** | Technical analysis | Mix of consumer & commercial drones | MEDIUM |
| **No geopolitical pattern** | Incident analysis | Random targets, no strategic value | HIGH |
| **Copycat behavior** | Timeline | Incidents spike after media coverage | MEDIUM |

**Subcategories**:

#### H5a: Criminal Organizations
**Motive**: Espionage-for-hire, smuggling surveillance, blackmail
**Indicators**:
- Commercial targets (ports, warehouses, corporate HQs)
- Payment in Bitcoin/Monero (not state funding)
- Amateur execution (profit-driven, not professional)
- No geopolitical targeting

#### H5b: Hacktivists (Anti-Russia)
**Motive**: Frame Russia, expose Russia's tactics, provoke EU response
**Indicators**:
- Social media claims ("We did this to show Russian threat")
- Obvious attribution to Russia (deliberately)
- Timeline matches anti-Russia protests/campaigns
- Amateurish execution (activists, not professionals)

#### H5c: Private Intelligence Firms
**Motive**: Client work (corporate espionage, governments hire contractors)
**Indicators**:
- Professional execution (trained operators)
- Commercial-grade equipment (expensive but legal)
- No obvious geopolitical motive
- Targets match corporate interests

**How to detect**:

```python
def check_nonstate_indicators(incident):
    """
    Indicators for non-state actors
    """
    score = 0

    # Commercial targets
    if incident.target_type in ['port', 'warehouse', 'corporate']:
        score += 20

    # Hacktivist claims
    if incident.claimed_by:
        score += 30  # Non-state actors often claim responsibility

    # Amateur + commercial mix
    if "DJI" in incident.drone and "commercial grade" in incident.equipment:
        score += 15

    # No strategic value
    if incident.military_value == "LOW":
        score += 20

    return score
```

**Why unlikely for MOST incidents**:
- ❌ Military/strategic targets = state-level motive
- ❌ Professional Orlan-10 drones = state resources
- ❌ No hacktivist claims (would want publicity)
- ❌ Criminal organizations prefer lower-risk operations

**But possible for SOME incidents**:
- ✅ Consumer drone sightings (DJI Mavic, etc)
- ✅ Commercial/civilian targets
- ✅ Amateur execution (crashes, caught)

---

## 🔍 Multi-Hypothesis Attribution Framework

**When analyzing incidents, consider ALL hypotheses**:

```python
def attribute_incident(incident):
    """
    Calculate likelihood for ALL hypotheses
    Returns: dict with H1-H5 scores
    """
    scores = {
        'H1_LOCAL_RECRUITMENT': 0,
        'H2_RUSSIAN_STATE': 0,
        'H3_HYBRID': 0,
        'H4_FALSE_FLAG': 0,
        'H5_NONSTATE': 0,
    }

    # Equipment analysis
    if "orlan" in incident.drone.lower():
        scores['H2_RUSSIAN_STATE'] += 40
        scores['H4_FALSE_FLAG'] += 10  # Could be planted
    elif "dji" in incident.drone.lower():
        scores['H1_LOCAL_RECRUITMENT'] += 20
        scores['H5_NONSTATE'] += 15

    # Target analysis
    if incident.target_type == 'military':
        scores['H2_RUSSIAN_STATE'] += 30
        scores['H1_LOCAL_RECRUITMENT'] += 10
    elif incident.target_type == 'commercial':
        scores['H5_NONSTATE'] += 25

    # Execution quality
    if incident.execution_quality > 70:
        scores['H2_RUSSIAN_STATE'] += 25
        scores['H4_FALSE_FLAG'] += 15
    else:
        scores['H1_LOCAL_RECRUITMENT'] += 20
        scores['H5_NONSTATE'] += 10

    # Geopolitical timing
    if incident.date_matches_diplomatic_event():
        scores['H4_FALSE_FLAG'] += 20

    # Claims
    if incident.claimed_by:
        scores['H5_NONSTATE'] += 30

    # Hybrid scoring
    scores['H3_HYBRID'] = (scores['H1_LOCAL_RECRUITMENT'] + scores['H2_RUSSIAN_STATE']) / 2

    return scores
```

---

## 🎯 Red Flags for False Flag (H4)

**Immediate investigation if:**

1. **Too Perfect Attribution**
   - Incident scene has Russian flag
   - Russian passport "accidentally" left behind
   - Overly obvious Russian indicators

2. **Technical Inconsistencies**
   - Russian drone + Chinese radio system
   - Professional execution + amateur mistakes
   - Equipment mismatch (state-level + consumer grade)

3. **Geopolitical Timing**
   - Incident during EU-China summit
   - Incident during Iran nuclear negotiations
   - Perfect timing to escalate EU-Russia tensions

4. **Misdirection**
   - Multiple false trails
   - Deliberately planted evidence
   - Evidence TOO easy to find

**Example False Flag Scenario**:
```
Incident: Orlan-10 drone with Russian markings crashes near NATO base
Timeline: Day before EU votes on Ukraine funding
Evidence: Russian passport found at crash site
Technical: Drone has Chinese radio system (inconsistency)
Conclusion: Possible H4 (false flag) - investigate further
```

---

## ✅ Updated Decision Tree

```
START: Drone incident observed
│
├─ Equipment Analysis
│  ├─ Orlan-10 (Russian military) → Check for:
│  │  ├─ Technical inconsistencies → H4 (false flag)
│  │  └─ Consistent Russian tech → H2 (state actor)
│  │
│  ├─ DJI/Consumer → Check for:
│  │  ├─ Recruitment posts found → H1 (local recruitment)
│  │  ├─ Commercial target → H5 (criminal/private firm)
│  │  └─ Military target + amateur → H1 (local recruitment)
│  │
│  └─ Mixed equipment → H3 (hybrid) or H4 (false flag)
│
├─ Target Analysis
│  ├─ Military/Strategic → H2 or H1 (state-directed)
│  ├─ Commercial/Corporate → H5 (non-state)
│  └─ Random/No value → H5 (hacktivist/copycat)
│
├─ Geopolitical Context
│  ├─ Perfect timing for non-Russia state → H4 (false flag)
│  ├─ Russia logistics interest (Ukraine war) → H2 (state)
│  └─ No clear geopolitical motive → H5 (non-state)
│
├─ Claims/Attribution
│  ├─ Hacktivist group claims → H5 (hacktivist)
│  ├─ No claims → H1, H2, or H3 (state/recruitment)
│  └─ Obvious Russian attribution → Check for H4 (too obvious?)
│
└─ Technical Consistency Check
   ├─ Consistent (all Russian or all consumer) → H1, H2, H3
   └─ Inconsistent (mixed systems) → H4 (false flag) or H5 (amateur)
```

---

## 📊 Updated Success Criteria

**Project succeeds if we can:**

1. **Rule OUT false flags (H4)** with >80% confidence
   - No technical inconsistencies found
   - Geopolitical timing not suspicious
   - Attribution consistent with evidence

2. **Rule OUT non-state actors (H5)** with >80% confidence
   - No hacktivist claims
   - Targets have strategic (not commercial) value
   - Professional execution rules out amateurs

3. **Determine H1 vs H2 vs H3** with >70% confidence
   - Recruitment evidence found → H1
   - No recruitment + professional → H2
   - Network connections found → H3

**Key Principle**:
⚠️ **Assume Russia UNLESS evidence points elsewhere**
- Russia has clear motive (Ukraine war logistics)
- Russia has capability (Orlan-10 drones)
- Russia has precedent (hybrid warfare doctrine)

**But stay vigilant**:
✅ Check for H4/H5 indicators on EVERY incident
✅ Document technical inconsistencies
✅ Cross-reference geopolitical events

---

**Created**: 2025-11-16
**Updated**: 2025-11-16 (Added H4 & H5)
**Status**: ACTIVE INVESTIGATION
**Next Review**: After Week 2 (Reddit/VK deployment complete)
