# Complete API Endpoints Reference

**Version:** 3.0
**Last Updated:** November 13, 2025
**Total Endpoints:** 27+

---

## Base URL
```
http://localhost:8000
```

## Interactive API Documentation
```
http://localhost:8000/docs  (Swagger UI)
```

---

# PATTERN ANALYSIS & COUNTER-MEASURES (7 NEW endpoints)

## 1. Get Strategic Analysis
```http
GET /api/patterns/strategic-analysis
```

**Description:** Get operational classification breakdown (State Actors vs Recruited Locals vs Unknown)

**Example:**
```bash
curl http://localhost:8000/api/patterns/strategic-analysis
```

**Response:**
```json
{
  "classification_breakdown": [
    {
      "operational_class": "STATE_ACTOR",
      "count": 1,
      "drone_types": "Suspected Russian Orlan-10"
    },
    {
      "operational_class": "RECRUITED_LOCAL",
      "count": 1,
      "drone_types": "Consumer DJI-class drone"
    },
    {
      "operational_class": "AUTHORIZED_MILITARY",
      "count": 1,
      "drone_types": "Polish Military Training Drone"
    }
  ],
  "state_actor_incidents": [
    {
      "id": 10,
      "sighting_date": "2024-08-08",
      "title": "Drone sighting at Brunsbüttel Nuclear Power Plant",
      "operational_class": "STATE_ACTOR",
      "strategic_assessment": "Russian military-grade reconnaissance drone (Orlan-10) conducting critical infrastructure surveillance. Range: ~120km. Indicates state-level intelligence operation targeting nuclear facility.",
      "launch_analysis": "Orlan-10 has 120km operational range. Possible launch sites: (1) Baltic Sea vessel within 100km, (2) Land-based site near Polish/Russian border, (3) Belarus territory. Weather conditions and flight duration suggest maritime launch. Recommend correlation with AIS vessel tracking data.",
      "drone_range": 120,
      "restricted_area_name": "Brunsbüttel Nuclear Power Plant"
    }
  ],
  "recruited_local_incidents": [
    {
      "id": 189,
      "sighting_date": "2025-11-08",
      "title": "Multiple drones over South Limburg - NATO JFC Brunssum",
      "operational_class": "RECRUITED_LOCAL",
      "strategic_assessment": "Recruited local operative responding to GRU Telegram bounty (2000 EUR Bitcoin payment). Part of systematic reconnaissance campaign targeting NATO infrastructure. Actor: VWarrior channel. Low-sophistication but high-volume threat vector."
    }
  ],
  "all_classified_incidents": [...],
  "total_classified": 3
}
```

---

## 2. Get Counter-Measures Database
```http
GET /api/patterns/counter-measures
```

**Description:** Get all available C-UAS counter-measures with specifications

**Example:**
```bash
curl http://localhost:8000/api/patterns/counter-measures
```

**Response:**
```json
{
  "counter_measures": [
    {
      "id": 1,
      "name": "DroneDefender 3.0",
      "type": "RF_JAMMER",
      "description": "Handheld directional RF jammer for GNSS and ISM bands",
      "effective_against": "Consumer drones, DJI models, low-end reconnaissance UAVs",
      "range_km": 1.5,
      "deployment_time_hours": 0,
      "cost_estimate_eur": 35000,
      "requires_authorization": true,
      "mobile": true,
      "specifications": "Frequency: 400MHz-6GHz | Weight: 6.8kg | Battery: 2hr continuous | Effective angle: 30° cone"
    },
    {
      "id": 2,
      "name": "AUDS (Anti-UAV Defence System)",
      "type": "RF_JAMMER",
      "description": "Vehicle-mounted RF disruption system with optical tracking",
      "effective_against": "Military UAVs (Orlan-10), tactical reconnaissance drones, consumer drones",
      "range_km": 10,
      "deployment_time_hours": 2,
      "cost_estimate_eur": 850000,
      "requires_authorization": true,
      "mobile": true,
      "specifications": "Radar detection + EO/IR tracking + 2.4/5.8GHz jamming | Vehicle-mounted | Crew: 2 operators"
    }
  ],
  "by_type": {
    "RF_JAMMER": [...],
    "RF_DETECTOR": [...],
    "RADAR": [...],
    "NET_CAPTURE": [...],
    "EW_SUITE": [...],
    "MICROWAVE": [...],
    "INTEGRATED_SYSTEM": [...]
  },
  "total": 10
}
```

**Counter-Measure Types:**
- **RF_JAMMER**: Radio frequency jammers (DroneDefender, AUDS, HP 47, DroneGun)
- **RF_DETECTOR**: Passive RF detection systems (RfPatrol)
- **RADAR**: 3D surveillance radar (AARTOS)
- **NET_CAPTURE**: Physical capture systems (SkyWall)
- **EW_SUITE**: Electronic warfare suites (DroneSentry-X)
- **MICROWAVE**: High-powered microwave (Leonidas HPM)
- **INTEGRATED_SYSTEM**: Multi-layered defense (NINJA Mobile)

---

## 3. Get Counter-Measure Recommendations for Incident
```http
GET /api/patterns/counter-measures/incident/{incident_id}
```

**Parameters:**
- `incident_id` - ID of the incident (path parameter)

**Example:**
```bash
curl http://localhost:8000/api/patterns/counter-measures/incident/10
```

**Response:**
```json
{
  "incident_id": 10,
  "recommendations": [
    {
      "id": 1,
      "priority": "CRITICAL",
      "reasoning": "Military-grade Orlan-10 requires advanced RF disruption. AUDS system effective against military UAVs with 10km range. Deploy at nuclear facility perimeter for critical infrastructure protection.",
      "estimated_effectiveness": 0.85,
      "deployment_location_lat": 53.8917,
      "deployment_location_lon": 9.1280,
      "deployment_notes": "Position on north perimeter of Brunsbüttel facility. Provides coverage of approach vectors from Baltic Sea. Requires 24/7 operator staffing.",
      "cm_name": "AUDS (Anti-UAV Defence System)",
      "cm_type": "RF_JAMMER",
      "cm_description": "Vehicle-mounted RF disruption system with optical tracking",
      "range_km": 10,
      "deployment_time_hours": 2,
      "cost_estimate_eur": 850000,
      "requires_authorization": true,
      "mobile": true,
      "incident_title": "Drone sighting at Brunsbüttel Nuclear Power Plant",
      "operational_class": "STATE_ACTOR"
    },
    {
      "id": 2,
      "priority": "HIGH",
      "reasoning": "AARTOS radar provides early warning for incoming military UAVs. 15km range allows detection before RF countermeasures needed. Essential for layered defense.",
      "estimated_effectiveness": 0.9,
      "cm_name": "AARTOS C-UAS Radar",
      "cm_type": "RADAR",
      "cost_estimate_eur": 1200000
    },
    {
      "id": 3,
      "priority": "MEDIUM",
      "reasoning": "Leonidas HPM as last-resort hard-kill option if RF jamming fails. Effective against hardened military electronics.",
      "estimated_effectiveness": 0.75,
      "cm_name": "Leonidas HPM System",
      "cm_type": "MICROWAVE",
      "cost_estimate_eur": 2500000
    }
  ],
  "total": 3
}
```

---

## 4. Get Orlan/Military Drone Analysis
```http
GET /api/patterns/orlan-analysis
```

**Description:** Get detailed analysis of state-actor incidents with launch range calculations

**Example:**
```bash
curl http://localhost:8000/api/patterns/orlan-analysis
```

**Response:**
```json
{
  "orlan_incidents": [
    {
      "id": 10,
      "sighting_date": "2024-08-08",
      "title": "Drone sighting at Brunsbüttel Nuclear Power Plant",
      "operational_class": "STATE_ACTOR",
      "strategic_assessment": "Russian military-grade reconnaissance drone (Orlan-10) conducting critical infrastructure surveillance...",
      "launch_analysis": "Orlan-10 has 120km operational range. Possible launch sites: (1) Baltic Sea vessel within 100km, (2) Land-based site near Polish/Russian border, (3) Belarus territory. Weather conditions and flight duration suggest maritime launch. Recommend correlation with AIS vessel tracking data.",
      "latitude": 53.891667,
      "longitude": 9.128056,
      "drone_type_model": "Suspected Russian Orlan-10",
      "drone_range": 120,
      "max_altitude_m": 5000,
      "endurance_minutes": 960,
      "target_name": "Brunsbüttel Nuclear Power Plant",
      "target_lat": 53.891667,
      "target_lon": 9.128056,
      "possible_launch_zone": {
        "center_lat": 53.891667,
        "center_lon": 9.128056,
        "radius_km": 120,
        "analysis": "Orlan-10 has 120km operational range. Possible launch sites: (1) Baltic Sea vessel within 100km, (2) Land-based site near Polish/Russian border, (3) Belarus territory..."
      }
    }
  ],
  "total": 1,
  "analysis_summary": "Orlan-10 incidents require maritime or cross-border launch analysis. Check AIS vessel tracking and border proximity."
}
```

---

## 5. List Patterns (Enhanced)
```http
GET /api/patterns/
```

**Parameters:**
- `skip` - Offset (default: 0)
- `limit` - Max results (default: 100, max: 1000)
- `pattern_type` - Filter by type (optional): `temporal`, `spatial`, `drone_type`, `operator`
- `order_by` - Sort by: `recent`, `confidence`, `incidents`

**Example:**
```bash
curl "http://localhost:8000/api/patterns/?pattern_type=spatial&order_by=confidence"
```

**Response:**
```json
{
  "total": 5,
  "skip": 0,
  "limit": 100,
  "patterns": [
    {
      "id": 1,
      "name": "Repeated targeting of Brussels Airport",
      "description": "3 incidents near Brussels Airport",
      "pattern_type": "spatial",
      "incident_count": 3,
      "primary_location": "Brussels Airport",
      "confidence_score": 0.7,
      "created_at": "2025-11-09T10:00:00",
      "updated_at": "2025-11-09T15:30:00"
    }
  ]
}
```

---

## 6. Get Pattern Details with Incidents
```http
GET /api/patterns/{pattern_id}/incidents
```

**Parameters:**
- `pattern_id` - ID of the pattern (path parameter)

**Example:**
```bash
curl http://localhost:8000/api/patterns/1/incidents
```

**Response:**
```json
{
  "pattern": {
    "id": 1,
    "name": "Repeated targeting of Brussels Airport",
    "pattern_type": "spatial",
    "incident_count": 3,
    "confidence_score": 0.7
  },
  "incidents": [
    {
      "id": 5,
      "sighting_date": "2025-11-08",
      "title": "Drone over Brussels Airport runway"
    },
    {
      "id": 12,
      "sighting_date": "2025-10-15",
      "title": "Unauthorized UAV near terminal"
    }
  ],
  "total_incidents": 3
}
```

---

## 7. Auto-Detect Patterns
```http
POST /api/patterns/auto-detect
```

**Description:** Automatically detect patterns from incidents (spatial, temporal, drone type)

**Example:**
```bash
curl -X POST http://localhost:8000/api/patterns/auto-detect
```

**Response:**
```json
{
  "detected_patterns": 3,
  "patterns": [
    "Detected spatial pattern: Brussels Airport (3 incidents)",
    "Detected drone pattern: DJI Phantom 4 (5 incidents)",
    "Detected temporal pattern: Coordinated campaign on 2025-11-08 (2 incidents)"
  ]
}
```

---

# TRUSTED SOURCES FRAMEWORK (7 endpoints)

## 1. Get Trusted Sources for Country
```http
GET /api/sources/trusted/{country}
```

**Parameters:**
- `country` - ISO 2-letter country code (BE, NL, DE, FR, PL, ES, EE, LT, DK, AT)

**Example:**
```bash
curl http://localhost:8000/api/sources/trusted/NL
```

**Response:**
```json
{
  "country": "NL",
  "sources": [
    {
      "name": "Royal Netherlands Air Force (KLu)",
      "url": "https://www.defensie.nl/",
      "credibility": 0.99
    },
    {
      "name": "NOS News",
      "url": "https://nos.nl/",
      "credibility": 0.85
    }
  ],
  "count": 12
}
```

---

## 2. Validate Source URL
```http
POST /api/sources/validate
```

**Request Body:**
```json
{
  "url": "https://www.standaard.be/article/123",
  "country": "BE"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sources/validate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.standaard.be/article", "country": "BE"}'
```

**Response:**
```json
{
  "url": "https://www.standaard.be/article",
  "valid": true,
  "credibility": 0.80,
  "reason": "Trusted source: De Standaard",
  "blocked": false,
  "link_working": true
}
```

---

## 3. Check if Link is Working
```http
GET /api/sources/check-link
```

**Parameters:**
- `url` - Full URL to check (required)

**Example:**
```bash
curl "http://localhost:8000/api/sources/check-link?url=https://www.standaard.be/article"
```

**Response:**
```json
{
  "url": "https://www.standaard.be/article",
  "working": true,
  "status_code": 200,
  "last_checked": "2025-11-09T15:30:00"
}
```

---

## 4. Get All Trusted Domains
```http
GET /api/sources/all-domains
```

**Example:**
```bash
curl http://localhost:8000/api/sources/all-domains
```

**Response:**
```json
{
  "total": 156,
  "domains": [
    "mil.be",
    "standaard.be",
    "demorgen.be",
    "nos.nl",
    "volkskrant.nl",
    ...
  ]
}
```

---

## 5. Check if Source is Blocked
```http
GET /api/sources/blocked
```

**Parameters:**
- `url` - URL to check (required)

**Example:**
```bash
curl "http://localhost:8000/api/sources/blocked?url=https://www.washingtonpost.com/article"
```

**Response:**
```json
{
  "url": "https://www.washingtonpost.com/article",
  "blocked": true,
  "blocked_sources": [
    "washingtonpost.com",
    "nytimes.com",
    "cnn.com",
    ...
  ]
}
```

---

## 6. Get Recommended Sources for Incident
```http
GET /api/incidents/{incident_id}/recommended-sources
```

**Parameters:**
- `incident_id` - ID of the incident (path parameter)

**Example:**
```bash
curl http://localhost:8000/api/incidents/1/recommended-sources
```

**Response:**
```json
{
  "incident_id": 1,
  "incident_title": "Drone over Gilze Rijen Air Base",
  "location_country": "NL",
  "location_name": "Gilze Rijen Air Base",
  "recommended_sources": [
    {
      "name": "Royal Netherlands Air Force",
      "url": "https://www.defensie.nl/",
      "credibility": 0.99,
      "google_news_search": "https://news.google.com/search?q=..."
    }
  ],
  "total_sources": 12,
  "search_tip": "Use Google News Search links..."
}
```

---

## 7. Get Search URLs for Incident
```http
GET /api/incidents/{incident_id}/search-sources
```

**Parameters:**
- `incident_id` - ID of the incident (path parameter)

**Example:**
```bash
curl http://localhost:8000/api/incidents/1/search-sources
```

**Response:**
```json
{
  "incident_id": 1,
  "incident_title": "Drone over Gilze Rijen Air Base",
  "country": "NL",
  "search_urls": {
    "google_news": "https://news.google.com/search?q=...",
    "nos_news": "https://nos.nl/zoeken/?q=...",
    "volkskrant": "https://www.volkskrant.nl/search/...",
    "nrc": "https://www.nrc.nl/search/...",
    "ad": "https://www.ad.nl/search/..."
  },
  "instructions": "Click any URL to search for articles..."
}
```

---

# INTELLIGENCE ANALYSIS (7 endpoints)

## 1. Get Articles for Incident
```http
GET /api/intelligence/articles/{incident_id}
```

**Parameters:**
- `incident_id` - ID of the incident (path parameter)
- `limit` - Maximum articles (optional, default: 10, max: 50)

**Example:**
```bash
curl "http://localhost:8000/api/intelligence/articles/1?limit=15"
```

**Response:**
```json
{
  "incident_id": 1,
  "incident_title": "Drone over Gilze Rijen Air Base",
  "country": "NL",
  "articles_found": 5,
  "articles": [
    {
      "title": "Drone Spotted Over Dutch Military Base",
      "url": "https://nos.nl/article/...",
      "source_name": "NOS News",
      "source_credibility": 0.85,
      "publish_date": "2025-11-09T10:30:00",
      "summary": "A drone was spotted...",
      "language": "nl",
      "sentiment": {
        "score": -0.2,
        "label": "neutral",
        "confidence": 0.75
      },
      "bias": {
        "alarmist": 0.2,
        "sensational": 0.1,
        "politically_motivated": 0.0,
        "overall_bias_score": 0.1
      }
    }
  ],
  "search_date": "2025-11-09T15:30:00"
}
```

---

## 2. Search Articles by Keyword
```http
GET /api/intelligence/articles/search
```

**Parameters:**
- `keyword` - Search term (required, min 3 chars)
- `country` - Country code (optional, default: NL)
- `limit` - Max results (optional, default: 10, max: 50)
- `language` - Language code (optional, default: en)

**Example:**
```bash
curl "http://localhost:8000/api/intelligence/articles/search?keyword=drone&country=NL&limit=10"
```

**Response:**
```json
{
  "keyword": "drone",
  "country": "NL",
  "articles_found": 8,
  "articles": [
    {
      "title": "...",
      "url": "...",
      "source_name": "NOS News",
      "sentiment": {...},
      ...
    }
  ],
  "search_date": "2025-11-09T15:30:00"
}
```

---

## 3. Analyze Sentiment of Text
```http
POST /api/intelligence/analyze-sentiment
```

**Request Body:**
```json
{
  "text": "The drone invasion is a serious threat!",
  "language": "en"
}
```

**Supported Languages:** en, nl, de, fr, es, pl

**Example:**
```bash
curl -X POST http://localhost:8000/api/intelligence/analyze-sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The drone invasion is a serious threat!",
    "language": "en"
  }'
```

**Response:**
```json
{
  "text": "The drone invasion is a serious threat!",
  "language": "en",
  "sentiment": {
    "score": -0.85,
    "label": "negative",
    "confidence": 0.92
  },
  "bias": {
    "alarmist": 0.85,
    "sensational": 0.4,
    "politically_motivated": 0.0,
    "overall_bias_score": 0.45
  },
  "trustworthiness_score": 0.55,
  "analysis_date": "2025-11-09T15:30:00"
}
```

---

## 4. Verify Factual Claim
```http
POST /api/intelligence/verify-claim
```

**Request Body:**
```json
{
  "claim": "The drone can penetrate military defenses"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/intelligence/verify-claim \
  -H "Content-Type: application/json" \
  -d '{"claim": "The drone can penetrate military defenses"}'
```

**Response:**
```json
{
  "claim": "The drone can penetrate military defenses",
  "verification": {
    "claim": "The drone can penetrate military defenses",
    "status": "disputed",
    "source": "Manual Database",
    "explanation": "NATO has specific countermeasures. Some types evade detection.",
    "url": null,
    "date_checked": "2025-11-09T15:30:00",
    "confidence": 0.85
  },
  "is_debunked": false,
  "verification_date": "2025-11-09T15:30:00"
}
```

---

## 5. Assess Incident Credibility
```http
POST /api/intelligence/assess-incident
```

**Request Body:**
```json
{
  "incident_id": 1,
  "custom_description": "Optional custom description to analyze"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/intelligence/assess-incident \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 5,
    "custom_description": "The drone carried advanced surveillance equipment"
  }'
```

**Response:**
```json
{
  "incident_id": 5,
  "incident_title": "Drone over Brussels Airport",
  "credibility_score": 0.62,
  "credibility_assessment": "Partially Credible",
  "sentiment_analysis": {
    "sentiment": {
      "score": -0.35,
      "label": "negative",
      "confidence": 0.8
    },
    "bias": {
      "alarmist": 0.4,
      "sensational": 0.2,
      "politically_motivated": 0.0,
      "overall_bias_score": 0.2
    },
    "trustworthiness_score": 0.8
  },
  "fact_checks": [
    {
      "claim": "advanced surveillance equipment",
      "status": "unverified",
      "explanation": "Cannot determine without inspection"
    }
  ],
  "red_flags": [
    "⚠️ Multiple unverified claims detected"
  ],
  "recommendations": [
    "Gather more sources to verify claims"
  ],
  "analysis_summary": {
    "total_claims_identified": 2,
    "verified_claims": 0,
    "disputed_claims": 0,
    "false_claims": 0
  },
  "analysis_date": "2025-11-09T15:30:00"
}
```

---

## 6. Get Debunked Claims List
```http
GET /api/intelligence/debunked-claims
```

**Example:**
```bash
curl http://localhost:8000/api/intelligence/debunked-claims
```

**Response:**
```json
{
  "total_debunked_claims": 8,
  "debunked_claims": [
    "drones are military grade",
    "drone was armed",
    "drone can penetrate NATO defenses",
    "drone was designed for espionage",
    "drone poses existential threat",
    "drone invasion underway",
    "drone is russian",
    "drone is chinese"
  ],
  "note": "These claims have been verified as false or mostly false",
  "last_updated": "2025-11-09T15:30:00"
}
```

---

## 7. Compare Sources (Sentiment Analysis)
```http
POST /api/intelligence/compare-sources
```

**Request Body:**
```json
{
  "articles": [
    {
      "title": "Drone Threat Over Gilze Rijen",
      "summary": "Authorities confirm drone sighting...",
      "source_name": "NOS News",
      "language": "nl"
    },
    {
      "title": "EXCLUSIVE: Military Base INVADED!",
      "summary": "Shocking report of drone intrusion...",
      "source_name": "Tabloid Weekly",
      "language": "nl"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/intelligence/compare-sources \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Drone Threat",
        "summary": "Official report...",
        "source_name": "NOS News",
        "language": "nl"
      }
    ]
  }'
```

**Response:**
```json
{
  "source_comparison": {
    "NOS News": {
      "avg_sentiment": 0.1,
      "avg_bias": 0.15,
      "avg_trustworthiness": 0.85,
      "article_count": 3
    },
    "Tabloid Weekly": {
      "avg_sentiment": -0.8,
      "avg_bias": 0.75,
      "avg_trustworthiness": 0.25,
      "article_count": 2
    }
  },
  "summary": {
    "most_positive_source": "NOS News",
    "most_biased_source": "Tabloid Weekly",
    "most_trustworthy_source": "NOS News"
  },
  "analysis_date": "2025-11-09T15:30:00"
}
```

---

# GENERAL ENDPOINTS (3 endpoints)

## 1. Health Check
```http
GET /api/health
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T15:30:00",
  "service": "OSINT CUAS Dashboard"
}
```

---

## 2. Get Dashboard Statistics
```http
GET /api/stats
```

**Parameters:**
- `days` - Time window (optional, default: 30, min: 7, max: 365)

**Examples:**
```bash
# Last 30 days (default)
curl http://localhost:8000/api/stats

# Last 60 days
curl "http://localhost:8000/api/stats?days=60"

# Last 90 days
curl "http://localhost:8000/api/stats?days=90"
```

**Response:**
```json
{
  "timestamp": "2025-11-09T15:30:00",
  "time_window_days": 60,
  "cutoff_date": "2025-09-10T15:30:00",
  "summary": {
    "total_incidents": 34,
    "recent_incidents_60d": 28,
    "total_interventions": 12,
    "intervention_success_rate": 66.7,
    "total_patterns": 5,
    "restricted_areas": 100,
    "drone_types_tracked": 25
  },
  "top_drone_types": [
    {"model": "DJI Phantom", "incidents": 5}
  ],
  "top_targeted_areas": [
    {"name": "Brussels Airport", "country": "BE", "incidents": 3}
  ]
}
```

---

## 3. Get Incident Details (Enhanced)
```http
GET /api/incidents/{incident_id}
```

**Parameters:**
- `incident_id` - ID of the incident (path parameter)

**Example:**
```bash
curl http://localhost:8000/api/incidents/1
```

**Response (includes source validation):**
```json
{
  "id": 1,
  "sighting_date": "2025-11-09",
  "title": "Drone over Gilze Rijen Air Base",
  "description": "...",
  "source": "news",
  "source_url": "https://nos.nl/article/...",
  "source_validation": {
    "url": "https://nos.nl/article/...",
    "working": true,
    "status_code": 200,
    "valid": true,
    "credibility": 0.85,
    "reason": "Trusted source: NOS News",
    "blocked": false,
    "last_checked": "2025-11-09T15:30:00"
  },
  "confidence_score": 0.85,
  "location": "Gilze Rijen Air Base",
  "restricted_area_id": 1,
  ...
}
```

---

# INCIDENT MANAGEMENT (Enhanced)

## Create Incident (with source validation)
```http
POST /api/incidents/
```

**Request Body:**
```json
{
  "sighting_date": "2025-11-09",
  "latitude": 51.5,
  "longitude": 5.1,
  "drone_description": "DJI Matrice 300",
  "source": "news",
  "source_url": "https://www.standaard.be/article/...",
  "title": "Drone over Brussels Airport",
  "description": "Unauthorized drone spotted near runway...",
  "restricted_area_id": 1,
  "confidence_score": 0.85,
  "purpose_assessment": "reconnaissance"
}
```

**Validation:**
- ✅ Trusted sources accepted (Standaard, Volkskrant, etc.)
- ❌ Blocked sources rejected (Washington Post, CNN)
- ⚠️ Unknown sources logged with warning
- 🔗 Link status checked automatically

**Response:**
```json
{
  "id": 35,
  "sighting_date": "2025-11-09",
  "title": "Drone over Brussels Airport",
  ...
}
```

---

# STATUS CODES & ERROR HANDLING

## Success Responses
- `200` - OK - Request succeeded
- `201` - Created - Resource created successfully

## Client Error Responses
- `400` - Bad Request - Invalid parameters or blocked source
- `404` - Not Found - Resource doesn't exist
- `422` - Unprocessable Entity - Validation failed

## Server Error Responses
- `500` - Internal Server Error - Server error occurred

## Example Error Response
```json
{
  "detail": "Source URL is from a blocked source (non-EU or unreliable)"
}
```

---

# PAGINATION & FILTERING

## List Incidents
```http
GET /api/incidents/?skip=0&limit=100&source=news&country=BE&order_by=recent
```

**Parameters:**
- `skip` - Offset (default: 0)
- `limit` - Max results (default: 100, max: 1000)
- `source` - Filter by source type
- `country` - Filter by country
- `order_by` - Sort by (recent, oldest, confidence)

---

# RATE LIMITING & PERFORMANCE

### Article Scraping
- **Limit:** 1 request per 5 seconds per country
- **Cache:** 24 hours
- **Response:** 2-5s (first), 50ms (cached)

### Fact-Checking APIs
- **Limit:** 10 requests per minute per service
- **Cache:** 7 days
- **Response:** <10ms (manual DB), 1-3s (APIs)

### General Endpoints
- **Limit:** 100 requests per minute
- **Response:** 20-100ms

---

# AUTHENTICATION

Currently: **No authentication required** (localhost only)

For production deployment:
```python
# Add to backend/main.py:
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/protected")
async def protected_route(credentials: HTTPAuthCredentials = Depends(security)):
    # Validate token
    return {"message": "authenticated"}
```

---

# SOCMINT (SOCIAL MEDIA INTELLIGENCE) ENDPOINTS

See separate documentation for SOCMINT endpoints:
- `/api/socmint/actors` - Get all threat actors
- `/api/socmint/threats/active` - Get unlinked social media posts (proactive threats)
- `/api/socmint/incident/{id}/social-media` - Get social media posts linked to incident
- `/api/socmint/incident/{id}/crypto-transactions` - Get crypto transactions linked to incident
- `/api/socmint/timeline/{id}` - Get full intelligence timeline for incident

---

**API Version:** 3.0
**Last Updated:** November 13, 2025
**All Endpoints Tested:** ✅

## What's New in v3.0

### Pattern Analysis & Counter-Measures
- ✅ Operational classification (State Actor vs Recruited Local vs Unknown)
- ✅ Strategic assessment for incidents
- ✅ Launch analysis for military drones (Orlan-10)
- ✅ 10 C-UAS counter-measures with specifications
- ✅ Tactical recommendations per incident
- ✅ Orlan/military drone analysis with launch range calculations

### Database Enhancements
- New tables: `counter_measures`, `incident_recommendations`
- New columns: `operational_class`, `strategic_assessment`, `launch_analysis`

### Use Cases
1. **Intelligence Analysis**: Distinguish between state operations and recruited locals
2. **Tactical Response**: Get counter-measure recommendations for specific threats
3. **Strategic Planning**: Analyze military drone capabilities and launch zones
4. **Budget Planning**: Compare C-UAS system costs and effectiveness
