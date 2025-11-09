# Complete API Endpoints Reference

**Version:** 2.0
**Last Updated:** November 9, 2025
**Total Endpoints:** 20+

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

**API Version:** 2.0
**Last Updated:** November 9, 2025
**All Endpoints Tested:** ✅
