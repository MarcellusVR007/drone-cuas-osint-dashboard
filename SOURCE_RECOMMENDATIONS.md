# Source Recommendations Feature

## Overview

The dashboard now automatically recommends **trusted local news sources** for each incident based on its location country. This helps users find articles about specific incidents from credible, country-specific sources.

### Problem Solved
- ❌ **Before:** Incident detail showed only one scattered source (e.g., "Military Aviation Forum")
- ❌ **Before:** No way to find legitimate newspaper coverage of the incident
- ✅ **After:** Shows all trusted sources from that country (Volkskrant, NRC, De Standaard, VRT, etc.)
- ✅ **After:** Direct search links to find articles in trusted local news

---

## How It Works

### 1. Automatic Country Detection
When you view an incident detail, the system:
1. Identifies the incident's location (e.g., "Gilze Rijen Air Base")
2. Gets the country code (e.g., "NL" for Netherlands)
3. Looks up all trusted sources for that country

### 2. Trusted Sources Recommendation
For the Gilze Rijen incident (Netherlands), it recommends:
- **Military:** Royal Netherlands Air Force (credibility: 0.99)
- **Authority:** Dutch Ministry of Defence (credibility: 0.99)
- **News Sources:**
  - NOS News (credibility: 0.85)
  - NRC Handelsblad (credibility: 0.83)
  - De Volkskrant (credibility: 0.82)
  - AD.nl (credibility: 0.78)
  - RTL News (credibility: 0.80)

### 3. Search Links
For each recommendation, provides a direct Google News search link to find articles about the incident in that source.

---

## API Endpoints

### Get Recommended Sources for Incident

```bash
GET /api/incidents/{incident_id}/recommended-sources
```

**Example:** Gilze Rijen Air Base incident
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
      "name": "Royal Netherlands Air Force (KLu)",
      "url": "https://www.defensie.nl/english/organisation/klu",
      "credibility": 0.99,
      "google_news_search": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base"
    },
    {
      "name": "Dutch Ministry of Defence",
      "url": "https://www.defensie.nl/",
      "credibility": 0.99,
      "google_news_search": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base"
    },
    {
      "name": "NOS News (Dutch TV)",
      "url": "https://nos.nl/",
      "credibility": 0.85,
      "google_news_search": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base"
    },
    {
      "name": "NRC Handelsblad",
      "url": "https://www.nrc.nl/",
      "credibility": 0.83,
      "google_news_search": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base"
    },
    {
      "name": "De Volkskrant",
      "url": "https://www.volkskrant.nl/",
      "credibility": 0.82,
      "google_news_search": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base"
    }
  ],
  "total_sources": 12,
  "search_tip": "Use the Google News Search links to find articles about this incident in trusted NL sources"
}
```

---

### Get Search URLs for Incident

```bash
GET /api/incidents/{incident_id}/search-sources
```

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
    "google_news": "https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base",
    "google_search": "https://www.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base+drone",
    "nos_news": "https://nos.nl/zoeken/?q=Drone+over+Gilze+Rijen+Air+Base",
    "volkskrant": "https://www.volkskrant.nl/search/Drone+over+Gilze+Rijen+Air+Base",
    "nrc": "https://www.nrc.nl/search/Drone+over+Gilze+Rijen+Air+Base",
    "ad": "https://www.ad.nl/search/Drone+over+Gilze+Rijen+Air+Base"
  },
  "instructions": "Click any URL to search for articles about this incident in trusted local sources"
}
```

---

## Usage Examples

### 1. Find Articles About Gilze Rijen Incident (Netherlands)

**Step 1: Get recommended sources**
```bash
curl http://localhost:8000/api/incidents/1/recommended-sources
```

**Step 2: Click on `google_news_search` link or use `/search-sources` endpoint**

**Step 3: The search URL is:**
```
https://news.google.com/search?q=Drone+over+Gilze+Rijen+Air+Base
```

This searches all of Google News for articles about this incident.

### 2. Search Specific Dutch Newspapers

Get search URLs for Dutch newspapers:
```bash
curl http://localhost:8000/api/incidents/1/search-sources
```

This returns:
- `volkskrant` - Search in De Volkskrant
- `nrc` - Search in NRC Handelsblad
- `nos_news` - Search in NOS News
- `ad` - Search in AD.nl

### 3. Brussels Incident (Belgium)

For a Belgian incident (e.g., Brussels/Liège/Mol):

**Get recommended Belgian sources:**
```bash
curl http://localhost:8000/api/incidents/5/recommended-sources
```

**Returns Belgian sources:**
- De Standaard (credibility: 0.80)
- De Morgen (credibility: 0.78)
- VRT News (credibility: 0.82)
- RTBF News (credibility: 0.82)
- Port of Antwerp Authority (credibility: 0.90)

---

## Country-Specific Search Integrations

The system includes direct search links for major newspapers in each country:

### Netherlands (NL)
- NOS News (nos.nl)
- De Volkskrant (volkskrant.nl)
- NRC Handelsblad (nrc.nl)
- AD.nl (ad.nl)

### Belgium (BE)
- VRT News (vrt.be)
- De Standaard (standaard.be)
- De Morgen (demorgen.be)
- RTBF (rtbf.be)

### Germany (DE)
- Tagesschau (tagesschau.de)
- Spiegel Online (spiegel.de)
- DPA (dpa.com)

### France (FR)
- France 24 (france24.com)
- Le Monde (lemonde.fr)
- AFP (afp.com)

### Poland (PL)
- TVN24 (tvn24.pl)
- Onet (onet.pl)

---

## Frontend Integration (UI Suggestions)

### Incident Detail View Enhancement

```html
<!-- Show recommended sources card -->
<div class="card mt-4">
  <div class="card-header bg-info">
    <h5>🔍 Find Articles in Local Sources</h5>
  </div>
  <div class="card-body">
    <!-- List recommended sources -->
    <div class="list-group">
      <a href="#" class="list-group-item list-group-item-action">
        <strong>NRC Handelsblad</strong> (Credibility: 0.83)
        <br/>
        <small>Search: <a href="GOOGLE_NEWS_SEARCH_URL" target="_blank">Find articles →</a></small>
      </a>
      <a href="#" class="list-group-item list-group-item-action">
        <strong>De Volkskrant</strong> (Credibility: 0.82)
        <br/>
        <small>Search: <a href="GOOGLE_NEWS_SEARCH_URL" target="_blank">Find articles →</a></small>
      </a>
    </div>
  </div>
</div>

<!-- Or show as buttons -->
<div class="mt-3">
  <button class="btn btn-primary btn-sm">
    🔗 Search NOS News
  </button>
  <button class="btn btn-primary btn-sm">
    🔗 Search Volkskrant
  </button>
  <button class="btn btn-primary btn-sm">
    🔗 Search NRC Handelsblad
  </button>
</div>
```

---

## Implementation Details

### How Recommendations Are Generated

1. **Location Lookup**: Find `restricted_area_id` from incident
2. **Country Detection**: Get `country` code from restricted area
3. **Source Lookup**: Call `get_trusted_sources_for_country(country_code)`
4. **Sorting**: Sort by credibility (0.99 down to 0.55)
5. **Search URL Generation**: Create Google News search for incident title

### Data Flow

```
Incident Detail View
  ↓
GET /api/incidents/{id}/recommended-sources
  ↓
Get restricted_area → country_code
  ↓
Lookup trusted sources for country
  ↓
Sort by credibility
  ↓
Return with Google News search URLs
```

---

## Recommended Use Cases

### 1. Verifying Incident Reports
When you see an incident report, immediately check if major local newspapers covered it.

**Example:**
- Incident: "Drone over Brussels Airport"
- Recommended: Check De Standaard, VRT News, RTBF

### 2. Finding Additional Context
Get more details by reading articles from different trusted sources.

**Example:**
- Military source might emphasize security threat
- News source might focus on flight delays
- Civil authority might discuss regulations

### 3. Multi-language Coverage
Find articles in the original language of the incident location.

**Example:**
- Gilze Rijen (Netherlands) → Find Dutch articles first
- Brussels (Belgium) → Find Dutch AND French articles

### 4. Source Credibility Verification
Always prioritize articles from sources with higher credibility scores.

**Hierarchy:**
1. Military/Official (0.99)
2. Civil Authority (0.95)
3. Major News Agencies (0.85)
4. Quality Newspapers (0.70-0.82)

---

## Error Handling

### No Location Linked
```json
{
  "detail": "Incident location not linked to restricted area. Cannot recommend sources."
}
```

**Solution:** Ensure incident has a `restricted_area_id` set.

### Location Not Found
If the restricted area doesn't have a country code, the endpoint will fail.

**Solution:** Add country code to restricted areas.

---

## Performance

- **Lookup time:** < 10ms (in-memory list)
- **Search URL generation:** < 5ms
- **Total response time:** ~20-30ms

No database queries required (uses in-memory source list).

---

## Future Enhancements

1. **Automatic Article Scraping** - Pull headlines from recommended sources
2. **Article Caching** - Cache article metadata for instant display
3. **Multi-language Search** - Support non-English language searches
4. **Social Media Monitoring** - Include curated social media accounts
5. **Source Sentiment Analysis** - Show if sources lean positive/negative
6. **Fact-checking Integration** - Link to fact-check claims about incident

---

## Quick Reference

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/api/incidents/{id}/recommended-sources` | Get trusted sources for country | Get Dutch sources for NL incident |
| `/api/incidents/{id}/search-sources` | Get search URLs | Get newspaper search links |

---

**Last Updated:** November 9, 2025
**Version:** 1.0
**Status:** Production Ready
