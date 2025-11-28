# Incident Detail Page Enrichment Plan
## Quality-First, Sustainable Approach

### Current State Analysis

**What we have:**
- ✅ Database schema supports rich data (corroborating_sources, secondary_sources, details, drone_characteristics_sources)
- ✅ Multiple news source scraping infrastructure
- ✅ Weather data integration
- ✅ Geolocation (lat/lon, restricted area radius)
- ✅ Source validation system
- ⚠️ Text extraction capability (exists but underutilized)

**What's missing:**
- ❌ NLP/LLM-based fact extraction from multiple sources
- ❌ Structured data model for tactical intelligence (drone count, direction, flight time)
- ❌ Source aggregation and conflict resolution
- ❌ Rich visualization on detail page

---

## Phase 1: Data Model Enhancement (Week 1-2)
**Priority: CRITICAL - Foundation for everything else**

### 1.1 Extend Database Schema

```sql
-- New tactical intelligence fields
ALTER TABLE incidents ADD COLUMN tactical_intel_json TEXT;
-- Stores structured data:
{
  "drone_count": {"value": 3, "confidence": 0.8, "sources": ["source1", "source2"]},
  "flight_duration_minutes": {"value": 45, "confidence": 0.9, "sources": ["source1"]},
  "approach_direction": {"value": "NE", "confidence": 0.7, "sources": ["source2"]},
  "departure_direction": {"value": "SW", "confidence": 0.6, "sources": ["source2"]},
  "altitude_estimate_m": {"value": 120, "confidence": 0.5, "sources": ["source3"]},
  "drone_type_visual": {"value": "quadcopter", "confidence": 0.8, "sources": ["source1"]},
  "estimated_pilot_location": {
    "lat": 51.234,
    "lon": 5.678,
    "radius_m": 2000,
    "confidence": 0.6,
    "reasoning": "Based on departure direction SW and estimated range"
  }
}

-- Enhanced source tracking
ALTER TABLE incidents ADD COLUMN source_articles_json TEXT;
-- Stores all collected articles:
[
  {
    "url": "...",
    "source": "telegraaf",
    "title": "...",
    "text": "...",
    "publish_date": "2025-11-24",
    "credibility_score": 0.8,
    "facts_extracted": ["drone_count:3", "direction:NE"]
  },
  ...
]
```

### 1.2 Create Intelligence Extraction Module

**File:** `backend/intelligence_extractor.py`

```python
class TacticalIntelligenceExtractor:
    """
    Extracts tactical intelligence from multiple news sources.
    Uses Claude/GPT to analyze articles and extract structured facts.
    """

    def extract_from_sources(self, articles: List[Article]) -> TacticalIntel:
        """
        Multi-source fact extraction with confidence scoring.

        Process:
        1. For each article, extract candidate facts
        2. Cross-reference facts across sources
        3. Assign confidence based on:
           - Source credibility
           - Number of corroborating sources
           - Consistency of information
        """
        pass

    def estimate_pilot_location(self, incident: Incident, tactical_intel: TacticalIntel):
        """
        Triangulate likely pilot location based on:
        - Departure/approach directions
        - Drone type and estimated range
        - Terrain analysis
        - Restricted area boundaries
        """
        pass
```

**LLM Prompt Template:**
```
Analyze this news article about a drone incident and extract ONLY factual information:

Article: {article_text}

Extract the following if mentioned:
1. Number of drones (exact number)
2. Drone type/description
3. Flight duration (minutes)
4. Altitude (meters)
5. Approach direction (N/NE/E/SE/S/SW/W/NW)
6. Departure direction (N/NE/E/SE/S/SW/W/NW)
7. Eyewitness quotes (exact quotes only)
8. Time of sighting (exact time)
9. Weather conditions
10. Response actions taken

Return JSON with confidence levels (0.0-1.0):
{
  "drone_count": {"value": 3, "confidence": 0.9, "quote": "drie drones gezien"},
  ...
}
```

---

## Phase 2: Source Aggregation Pipeline (Week 2-3)
**Priority: HIGH - Feeds Phase 1**

### 2.1 Enhanced Multi-Source Scraper

**File:** `backend/multi_source_aggregator.py`

```python
class IncidentAggregator:
    """
    Aggregates all articles about a single incident.
    Uses duplicate detection + temporal clustering.
    """

    def find_related_articles(self, incident: Incident, time_window_hours=48):
        """
        1. Search keywords: location + date + "drone"
        2. Fetch from all configured sources (NL newspapers, local news)
        3. Deduplicate (same article republished)
        4. Store in source_articles_json
        """
        pass

    def merge_intelligence(self, articles: List[Article]) -> TacticalIntel:
        """
        Conflict resolution:
        - If 3 sources say "2 drones" and 1 says "3 drones" → confidence weight
        - Prioritize eyewitness quotes over speculation
        - Flag contradictions for manual review
        """
        pass
```

### 2.2 Source Priority Matrix

```python
SOURCE_CREDIBILITY = {
    # Official sources - highest credibility
    "defensie.nl": 0.95,
    "politie.nl": 0.95,

    # Major news - high credibility
    "nos.nl": 0.85,
    "ad.nl": 0.80,
    "telegraaf.nl": 0.75,

    # Local news - medium (but valuable for eyewitness quotes)
    "omroepbrabant.nl": 0.70,
    "rtvutrecht.nl": 0.70,

    # Social media - low (needs verification)
    "twitter": 0.40,
    "reddit": 0.35,
}
```

---

## Phase 3: Rich Detail Page UI (Week 3-4)
**Priority: HIGH - User-facing value**

### 3.1 Component Structure

```
IncidentDetailView.vue
├── Header (title, meta)
├── TacticalIntelligencePanel ⭐ NEW
│   ├── DroneCountBadge
│   ├── FlightTrajectoryMap (shows approach/departure)
│   ├── EstimatedPilotLocation (radius overlay)
│   └── ConfidenceIndicator
├── MultiSourcePanel ⭐ NEW
│   ├── SourceTimeline (all articles chronologically)
│   ├── FactComparisonTable (cross-source verification)
│   └── EyewitnessQuotes (highlighted)
├── WeatherPanel (existing, enhanced)
├── GeospatialPanel
│   ├── InteractiveMap (Leaflet)
│   ├── RestrictedAreaOverlay
│   └── RadiusCircle
└── RelatedIncidentsPanel (existing)
```

### 3.2 Key Visualizations

**A. Flight Trajectory Visualization**
```vue
<FlightTrajectoryMap>
  <!-- Leaflet map showing: -->
  - Incident location (red marker)
  - Approach direction (green arrow)
  - Departure direction (blue arrow)
  - Estimated pilot location (orange circle with radius)
  - Restricted area boundary
</FlightTrajectoryMap>
```

**B. Multi-Source Verification**
```vue
<FactComparisonTable>
  Fact          | Source 1  | Source 2  | Source 3  | Consensus
  ------------- | --------- | --------- | --------- | ---------
  Drone Count   | 3 ✓       | 3 ✓       | 2 ?       | 3 (67%)
  Direction     | NE ✓      | NE ✓      | -         | NE (100%)
  Duration      | 45min ✓   | -         | ~1hr      | 45-60min
</FactComparisonTable>
```

**C. Confidence Indicators**
```vue
<ConfidenceBadge :value="0.85">
  High confidence (3 sources) ✓
</ConfidenceBadge>

<ConfidenceBadge :value="0.45">
  Low confidence (1 source, speculation) ⚠️
</ConfidenceBadge>
```

---

## Phase 4: Automation & Quality Assurance (Week 4-5)
**Priority: MEDIUM - Sustainability**

### 4.1 Automated Enrichment Pipeline

```python
# Cron job: Every 6 hours
async def enrich_recent_incidents():
    """
    1. Find incidents from last 48h
    2. Search for new articles
    3. Run intelligence extraction
    4. Update tactical_intel_json
    5. Flag for manual review if confidence < 0.6
    """
    pass
```

### 4.2 Quality Control Dashboard

**File:** `backend/routers/quality_control.py`

```python
@router.get("/api/quality-control/low-confidence")
async def get_low_confidence_incidents():
    """
    Return incidents with:
    - Conflicting information across sources
    - Low confidence scores
    - Missing critical fields

    For manual analyst review.
    """
    pass
```

### 4.3 Human-in-the-Loop

- Analyst reviews flagged incidents
- Can override extracted facts
- Add manual notes
- Mark facts as "verified" or "disputed"

---

## Phase 5: Advanced Features (Week 5-6)
**Priority: LOW - Nice to have**

### 5.1 Pattern Detection

```python
def detect_pilot_location_patterns(incidents: List[Incident]):
    """
    Cluster estimated pilot locations to find:
    - Recurring launch sites
    - Common approach corridors
    - Potential bases of operation
    """
    pass
```

### 5.2 Predictive Analysis

```python
def predict_next_target(historical_incidents):
    """
    Based on:
    - Temporal patterns
    - Geographic clustering
    - Approach directions

    Suggest likely next targets.
    """
    pass
```

---

## Implementation Priority

### Sprint 1 (Week 1-2): Foundation
1. ✅ Database schema extension
2. ✅ Basic TacticalIntelligenceExtractor with Claude API
3. ✅ Test with 5 sample incidents manually

### Sprint 2 (Week 2-3): Automation
1. ✅ Multi-source aggregator
2. ✅ Automated extraction pipeline
3. ✅ Source credibility weighting

### Sprint 3 (Week 3-4): UI
1. ✅ TacticalIntelligencePanel component
2. ✅ Flight trajectory map
3. ✅ Multi-source verification table

### Sprint 4 (Week 4-5): Quality
1. ✅ Confidence scoring refinement
2. ✅ Quality control dashboard
3. ✅ Manual review workflow

### Sprint 5 (Week 5-6): Advanced
1. ⏸️ Pattern detection
2. ⏸️ Predictive analysis
3. ⏸️ API for external consumers

---

## Success Metrics

**Quality Metrics:**
- ✅ 80%+ of incidents have tactical intel extracted
- ✅ Average confidence score > 0.7
- ✅ < 10% false positives (incorrect facts)
- ✅ Manual review time < 5 min per incident

**Value Metrics:**
- ✅ Pilot location estimation accuracy (validated against known incidents)
- ✅ Pattern detection identifies recurring launch sites
- ✅ Analyst feedback: "saves 30+ minutes per incident"

**Technical Metrics:**
- ✅ Extraction latency < 30 seconds per article
- ✅ API response time < 500ms for detail page
- ✅ 99.9% uptime for extraction pipeline

---

## Cost Estimation

**LLM API Costs (Claude):**
- ~1000 tokens per article analysis
- ~10 articles per incident
- $0.015 per 1K tokens (Claude Haiku)
- **Cost per incident: ~$0.15**
- **100 incidents/month: ~$15/month**

**Infrastructure:**
- Existing server (no additional cost)
- Storage: +100MB per 1000 incidents (negligible)

**Total: ~$20/month for full pipeline**

---

## Risk Mitigation

**Risk: LLM hallucinations**
- ✅ Multi-source cross-validation
- ✅ Confidence scoring
- ✅ Human review for low confidence

**Risk: API rate limits**
- ✅ Queue-based processing
- ✅ Exponential backoff
- ✅ Fallback to rule-based extraction

**Risk: Poor source quality**
- ✅ Source credibility weighting
- ✅ Blacklist low-quality sources
- ✅ Require minimum 2 sources

---

## Next Steps

1. **Approve plan** - Get sign-off on approach
2. **Set up Claude API** - Test extraction with 5 incidents
3. **Database migration** - Add new fields to staging
4. **Build MVP** - TacticalIntelligenceExtractor + simple UI
5. **Evaluate & iterate** - Measure accuracy, adjust prompts

---

## Questions for Discussion

1. **LLM choice:** Claude (better for Dutch) vs GPT-4 (cheaper)?
2. **Manual review:** Who reviews flagged incidents?
3. **Data retention:** How long to keep full article texts?
4. **Privacy:** Any concerns with storing pilot location estimates?
5. **Phase priority:** Start with UI (quick win) or backend (foundation)?

---

**Author:** Claude Code
**Date:** 2025-11-28
**Status:** DRAFT - Awaiting Approval
