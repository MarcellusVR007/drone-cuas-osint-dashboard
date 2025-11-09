# Trusted Sources Framework

## Overview

The OSINT CUAS Dashboard now includes a comprehensive **Trusted Sources Framework** that:

1. ✅ **Validates** all incident source URLs against a curated list of EU-trusted news sources
2. ✅ **Prevents** unreliable sources (non-EU bias, tabloids, sensationalist outlets)
3. ✅ **Checks** if source links are actually working (HTTP status validation)
4. ✅ **Ranks** sources by country and credibility level
5. ✅ **Automates** daily checks for new incidents from trusted EU sources

---

## Source Categories & Credibility Scores

### 1. **Official Military Sources** (Credibility: 0.99)
- NATO official statements
- National defense ministries and armed forces
- Military intelligence agencies
- Examples: Belgian Defense Ministry, NATO AWACS

### 2. **Official Authorities** (Credibility: 0.95)
- Government aviation authorities (EASA, national CAAs)
- Airport authorities
- Civil aviation administration
- Examples: EASA, Dutch Ministry of Defence, Berlin Brandenburg Airport

### 3. **Sensor Networks** (Credibility: 0.95)
- Real-time drone detection systems
- Radar networks, ADS-B feeds
- Professional monitoring platforms
- Examples: Senhive, Flightradar24, ADS-B Exchange

### 4. **Established News Agencies** (Credibility: 0.85)
- Major international wire services
- EU-focused news organizations
- Examples: Reuters, AFP (Agence France-Presse), BBC, dpa

### 5. **Quality Newspapers** (Credibility: 0.80)
- Trusted national/regional publications
- Journalistic standards maintained
- Country-specific lists defined
- Examples: De Standaard (BE), NOS (NL), Tagesschau (DE), Le Monde (FR)

### 6. **Specialized Intelligence** (Credibility: 0.80)
- Aviation intelligence databases
- Military analysis platforms
- Professional OSINT sources
- Examples: Janes Intelligence & Insight, Military Aviation Forums

### 7. **Local Quality News** (Credibility: 0.70)
- Reputable regional/local news outlets
- Community-based journalism
- Examples: Regional broadcast stations, city newspapers

### 8. **Community Submissions** (Credibility: 0.55-0.70)
- Verified community reports
- Professional forums with moderation
- Examples: Military Aviation Forums, verified eyewitness accounts

---

## Trusted Sources by Country

### Belgium 🇧🇪
**Military & Authority:**
- Belgian Ministry of Defence
- Belgian Royal Air Force (Orgaan)
- Federal Civil Aviation Authority
- Port of Antwerp Authority

**Quality Newspapers:**
- De Standaard (credibility: 0.80)
- De Morgen (credibility: 0.78)
- VRT News (Flemish TV) (credibility: 0.82)
- RTBF News (Walloon TV) (credibility: 0.82)

### Netherlands 🇳🇱
**Military & Authority:**
- Dutch Ministry of Defence
- Royal Netherlands Air Force (KLu)
- Schiphol Airport Authority
- Dutch Civil Aviation Authority (ILT)

**Quality Newspapers:**
- NOS News (credibility: 0.85)
- NRC Handelsblad (credibility: 0.83)
- De Volkskrant (credibility: 0.82)
- RTL News (credibility: 0.80)

### Germany 🇩🇪
**Military & Authority:**
- German Ministry of Defence (Bundesverteidigungsministerium)
- Luftwaffe (German Air Force)
- Berlin Brandenburg Airport
- Munich Airport

**Quality Newspapers:**
- Tagesschau (German TV News) (credibility: 0.85)
- Spiegel Online (credibility: 0.83)
- Die Welt (credibility: 0.82)
- Frankfurter Allgemeine (FAZ) (credibility: 0.82)
- Deutsche Presse-Agentur (dpa) (credibility: 0.85)

### France 🇫🇷
**Military & Authority:**
- French Ministry of Defence
- French Air Force
- DGAC Civil Aviation Authority
- Aéroports de Paris

**Quality Newspapers:**
- France 24 News (credibility: 0.84)
- Le Monde (credibility: 0.83)
- Le Figaro (credibility: 0.82)
- Agence France-Presse (AFP) (credibility: 0.85)

### Poland 🇵🇱
**Military & Authority:**
- Polish Ministry of Defence
- Polish Air Force (Siły Powietrzne)
- Polish Civil Aviation Authority (UACL)

**Quality Newspapers:**
- TVN24 News (credibility: 0.80)
- Onet News (credibility: 0.78)
- Polish Press Agency (PAP) (credibility: 0.82)

### Estonia 🇪🇪
**Military & Authority:**
- Estonian Ministry of Defence
- Estonian Air Force
- Estonian Civil Aviation Administration

**Quality Newspapers:**
- ERR News (Estonian TV) (credibility: 0.82)
- Delfi News (credibility: 0.78)

### Lithuania 🇱🇹
**Military & Authority:**
- Lithuanian Ministry of Defence
- Lithuanian Air Force
- Lithuanian Civil Aviation Authority

**Quality Newspapers:**
- LRT News (Lithuanian TV) (credibility: 0.82)
- Delfi.lt News (credibility: 0.78)

### Denmark 🇩🇰
**Military & Authority:**
- Danish Ministry of Defence
- Royal Danish Air Force
- Danish Civil Aviation Authority (Trafikstyrelsen)
- Copenhagen Airport Authority

**Quality Newspapers:**
- DR News (Danish TV) (credibility: 0.85)
- Politiken (credibility: 0.82)

### Spain 🇪🇸
**Military & Authority:**
- Spanish Ministry of Defence
- Spanish Air Force (Ejército del Aire)
- AENA Spanish Airports
- Spanish Civil Aviation Authority (AESA)

**Quality Newspapers:**
- EFE News Agency (credibility: 0.84)
- RTVE.es (Spanish TV) (credibility: 0.83)
- El País (credibility: 0.82)

### Austria 🇦🇹
**Military & Authority:**
- Austrian Ministry of Defence
- Austrian Air Force
- Austrian Civil Aviation Authority (FCCB)
- Vienna International Airport

**Quality Newspapers:**
- ORF News (Austrian TV) (credibility: 0.83)
- Die Presse (credibility: 0.82)

---

## Blocked Sources

The following domains are **NOT allowed** due to bias, sensationalism, or unreliability:

- ❌ `washingtonpost.com` - US bias
- ❌ `nytimes.com` - US bias
- ❌ `cnn.com` - US bias, sensationalist
- ❌ `foxnews.com` - US bias, sensationalist
- ❌ `dailymail.co.uk` - Tabloid, unreliable
- ❌ `breitbart.com` - Extremist content
- ❌ `infowars.com` - Conspiracy theories
- ❌ `twitter.com`, `x.com`, `facebook.com`, `reddit.com` - Unverified social media

---

## API Endpoints

### Get Trusted Sources for a Country
```bash
GET /api/sources/trusted/{country_code}
```

**Example:**
```bash
curl http://localhost:8000/api/sources/trusted/BE
```

**Response:**
```json
{
  "country": "BE",
  "sources": [
    {
      "name": "Belgian Ministry of Defence",
      "url": "https://www.mil.be/",
      "credibility": 0.99
    },
    {
      "name": "De Standaard",
      "url": "https://www.standaard.be/",
      "credibility": 0.80
    }
  ],
  "count": 12
}
```

### Validate a Source URL
```bash
POST /api/sources/validate
Content-Type: application/json

{
  "url": "https://www.standaard.be/article/123",
  "country": "BE"
}
```

**Response:**
```json
{
  "url": "https://www.standaard.be/article/123",
  "valid": true,
  "credibility": 0.80,
  "reason": "Trusted source: De Standaard",
  "blocked": false,
  "link_working": true
}
```

### Check if Link is Working
```bash
GET /api/sources/check-link?url=https://www.reuters.com/world/...
```

**Response:**
```json
{
  "url": "https://www.reuters.com/world/...",
  "working": true,
  "status_code": 200,
  "last_checked": "2025-11-09T15:30:00.123456"
}
```

### Get All Trusted Domains
```bash
GET /api/sources/all-domains
```

**Response:**
```json
{
  "total": 156,
  "domains": [
    "mil.be",
    "standaard.be",
    "demorgen.be",
    "vrt.be",
    "rtbf.be",
    ...
  ]
}
```

### Check if Source is Blocked
```bash
GET /api/sources/blocked?url=https://www.washingtonpost.com/article/...
```

**Response:**
```json
{
  "url": "https://www.washingtonpost.com/article/...",
  "blocked": true,
  "blocked_sources": [...]
}
```

---

## Creating Incidents with Source Validation

When creating a new incident, always include a `source_url`:

```bash
POST /api/incidents/
Content-Type: application/json

{
  "sighting_date": "2025-11-09",
  "latitude": 50.9009,
  "longitude": 4.4844,
  "drone_description": "DJI Matrice 300 RTK",
  "source": "news",
  "source_url": "https://www.standaard.be/article/drone-incident-brussels",
  "title": "Drone over Brussels Airport",
  "description": "Unauthorized drone spotted near runway...",
  "restricted_area_id": 1,
  "confidence_score": 0.85,
  "purpose_assessment": "reconnaissance"
}
```

### Validation Behavior:
1. ✅ **Blocked sources**: Request rejected with 400 error
2. ⚠️ **Unknown sources**: Warning logged, incident created (for research purposes)
3. ✅ **Trusted sources**: Incident created successfully

---

## Incident Detail View with Source Validation

When retrieving incident details, the API now returns source validation information:

```bash
GET /api/incidents/5
```

**Response includes:**
```json
{
  "id": 5,
  "title": "Drone over Brussels Airport",
  "source": "news",
  "source_url": "https://www.standaard.be/article/...",
  "source_validation": {
    "url": "https://www.standaard.be/article/...",
    "working": true,
    "status_code": 200,
    "valid": true,
    "credibility": 0.80,
    "reason": "Trusted source: De Standaard",
    "blocked": false,
    "last_checked": "2025-11-09T15:30:00.123456"
  },
  ...
}
```

---

## Daily Update Mechanism

### How It Works

The dashboard now includes an automated mechanism to check for new incidents:

```bash
python -m backend.daily_update
```

### Features:
1. **Checks trusted news sources** for new drone incident reports
2. **Monitors Senhive API** for real-time detections
3. **Validates** all discovered incidents against trust framework
4. **Adds** new incidents to database automatically
5. **Logs** all activities for audit trail

### Configuration

Set environment variables:
```bash
# How often to check for updates (hours)
export UPDATE_INTERVAL_HOURS=24

# Senhive API key for real-time detections
export SENHIVE_API_KEY=your_api_key_here

# Enable automated checks
export ENABLE_DAILY_UPDATES=true
```

### Logs Example:
```
2025-11-09 15:00:00 - INFO - Checking 8 news sources for new incidents...
2025-11-09 15:00:05 - INFO - ✓ Successfully checked Reuters
2025-11-09 15:00:10 - INFO - ✓ Successfully checked BBC News
2025-11-09 15:00:15 - INFO - Checking Senhive API for new detections...
2025-11-09 15:01:00 - INFO - Daily update check completed in 60.2s
2025-11-09 15:01:00 - INFO - New incidents found: 2
```

---

## Timeline Extended to 60 Days

The dashboard statistics endpoint now supports flexible time windows:

### Default (30 days):
```bash
GET /api/stats
```

### Custom time window (e.g., 60 days):
```bash
GET /api/stats?days=60
```

### Supported ranges:
- Minimum: 7 days
- Maximum: 365 days
- Default: 30 days

**Response:**
```json
{
  "timestamp": "2025-11-09T15:30:00.123456",
  "time_window_days": 60,
  "cutoff_date": "2025-09-10T15:30:00.123456",
  "summary": {
    "total_incidents": 34,
    "recent_incidents_60d": 28,
    "total_interventions": 12,
    "intervention_success_rate": 66.7,
    ...
  }
}
```

---

## Implementation Summary

### Backend Files Modified:
1. **`backend/trusted_sources.py`** - Source credibility framework (NEW)
2. **`backend/routers/sources.py`** - Source validation API (NEW)
3. **`backend/routers/incidents.py`** - Enhanced with source validation
4. **`backend/routers/general.py`** - Extended timeline support (7-365 days)
5. **`backend/daily_update.py`** - Daily incident checker (NEW)
6. **`backend/main.py`** - Integrated sources router

### Key Features:
- ✅ 9 EU countries with 40+ trusted sources
- ✅ Link validation (HTTP status checks)
- ✅ Blocked source detection
- ✅ Source URL validation on incident creation
- ✅ Daily automated update mechanism
- ✅ Extended timeline (60+ days support)
- ✅ Incident detail view with source metadata

---

## Best Practices

1. **Always provide source URLs** when creating incidents
2. **Use trusted EU sources** for better data quality
3. **Check link status** regularly via `/api/sources/check-link`
4. **Report blocked sources** that should be reviewed
5. **Update source rankings** as media landscape changes
6. **Monitor daily updates** for new incident patterns

---

## Future Enhancements

- [ ] Machine learning for source credibility scoring
- [ ] Automatic link replacement when sources move
- [ ] Social media monitoring with manual curation
- [ ] Source sentiment analysis
- [ ] Automated fact-checking integration
- [ ] Multi-language source support
- [ ] EU regulation compliance tracking

---

**Last Updated:** November 9, 2025
**Version:** 2.0
**Status:** Production Ready
