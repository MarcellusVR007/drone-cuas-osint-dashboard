# OSINT CUAS Dashboard
## Counter-UAS Intelligence System

A comprehensive on-premise intelligence dashboard for tracking, analyzing, and understanding hostile drone reconnaissance activities over European restricted airspace.

**Status:** MVP Ready | **Tech Stack:** Python 3.8+ | FastAPI | SQLite | Vue.js 3 | Bootstrap 5

---

## Overview

The OSINT CUAS (Counter-Unmanned Aircraft Systems) Dashboard consolidates intelligence on:

1. **Drone Sightings** - Track unauthorized UAV incursions near airports, military bases, and critical infrastructure
2. **Drone Type Classification** - Identify drone models, manufacturers, and operational characteristics
3. **Restricted Area Targeting** - Understand which locations are targeted and frequency patterns
4. **Intervention Effectiveness** - Measure success rates of countermeasures (jamming, netting, kinetic, interception)
5. **Pattern Detection** - Identify coordinated activity suggesting organized reconnaissance operations
6. **Attribution** - Link incidents to suspected operators and purposes

### Key Intelligence Questions Answered

- **Which locations are being targeted?** - Geographic hotspots showing systematic focus on specific military bases or airports
- **What types of drones are used?** - Identify commercial drones (modified) vs. military reconnaissance UAVs
- **Who is behind this?** - Attribution based on drone types, operational patterns, and timing
- **What is the intent?** - Distinguish between disruption tactics vs. detailed reconnaissance for targeting purposes
- **What works defensively?** - Track which countermeasures succeed against which drone types
- **Are there coordination patterns?** - Detect if incidents link to geopolitical events or coordinated campaigns

---

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation & Launch

```bash
# Navigate to project
cd drone-cuas-osint-dashboard

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
python app.py
```

That's it! The application will:
- ✓ Initialize the SQLite database
- ✓ Seed sample data (EU restricted areas, known drone types)
- ✓ Start the FastAPI backend server on port 8000
- ✓ Auto-open your browser to `http://localhost:8000`

Press `Ctrl+C` to stop the server.

---

## Architecture

### Backend
- **Framework:** FastAPI
- **Database:** SQLite (file-based, in `data/drone_cuas.db`)
- **Server:** Uvicorn (async)
- **Port:** 8000 (localhost only)

### Frontend
- **Framework:** Vue.js 3
- **UI:** Bootstrap 5 + Custom dark theme
- **Mapping:** Leaflet.js (OpenStreetMap)
- **Routing:** Hash-based (#/)
- **No build step required** (uses CDN)

### API Endpoints

**General**
- `GET /health` - Lightweight uptime/keep-alive check
- `GET /api/health` - Health check
- `GET /api/stats` - Dashboard statistics

**Incidents** (Drone sightings)
- `GET /api/incidents/` - List incidents with filters
- `GET /api/incidents/{id}` - Get incident details
- `POST /api/incidents/` - Create incident report
- `PUT /api/incidents/{id}` - Update incident
- `DELETE /api/incidents/{id}` - Delete incident
- `GET /api/incidents/spatial/near/{area_id}` - Incidents near a restricted area
- `GET /api/incidents/analysis/by-purpose` - Analyze by suspected purpose
- `GET /api/incidents/timeline/monthly` - Monthly timeline

**Drone Types**
- `GET /api/drone-types/` - List drone types
- `GET /api/drone-types/{id}` - Get drone type details
- `GET /api/drone-types/{id}/incidents` - All incidents using this drone
- `POST /api/drone-types/` - Create new drone type
- `GET /api/drone-types/analysis/threat-assessment` - Threat scoring

**Restricted Areas** (Airports, military bases, critical infrastructure)
- `GET /api/restricted-areas/` - List all areas
- `GET /api/restricted-areas/{id}` - Get area details
- `GET /api/restricted-areas/{id}/incidents` - All incidents near this area
- `POST /api/restricted-areas/` - Create new area
- `GET /api/restricted-areas/analysis/threat-matrix` - Threat assessment matrix

**Patterns** (Detected correlations and coordinated activity)
- `GET /api/patterns/` - List detected patterns
- `GET /api/patterns/{id}` - Get pattern details
- `POST /api/patterns/` - Create new pattern
- `POST /api/patterns/auto-detect` - Auto-detect patterns from incidents

**Interventions** (Countermeasures & defensive actions)
- `GET /api/interventions/` - List interventions
- `POST /api/interventions/` - Record intervention attempt
- `GET /api/interventions/analysis/effectiveness` - Success rates by type
- `GET /api/interventions/analysis/response-times` - Response time analysis
- `GET /api/interventions/analysis/by-incident-type` - Effectiveness by drone type

---

## Data Models

### Incident
Core drone sighting/incursion report
```
- sighting_date, sighting_time
- location (lat/lon, altitude)
- drone_type or description
- nearest_restricted_area
- duration, source, confidence_score
- title, description, details
- suspected_operator, purpose_assessment
```

### DroneType
UAV specifications and intelligence
```
- model, manufacturer, country_of_origin
- range_km, endurance_minutes, max_altitude_m
- payload_type (camera, signals_intelligence, unknown)
- difficulty_intercept (1-10 scale)
- estimated_cost_usd
```

### RestrictedArea
Military bases, airports, critical infrastructure
```
- name, area_type (airport, military_base, nuclear_facility, government)
- country, location (lat/lon)
- radius_km (airspace coverage)
- threat_level (1-5 scale)
- description
```

### Intervention
Defensive countermeasure or action taken
```
- incident_id
- intervention_type (jamming, netting, kinetic, interception, unknown)
- response_time_minutes
- outcome (success, partial, failed, unknown, not_attempted)
- success_rate (0-1)
```

### Pattern
Detected correlations linking multiple incidents
```
- name, description
- pattern_type (temporal, spatial, drone_type, operator)
- incident_count, date_range
- primary_location, primary_drone_type
- suspected_purpose, suspected_operator, confidence_score
```

---

## Usage

### Dashboard View
- **Summary cards** - Total incidents, 30-day activity, intervention success rate, detected patterns
- **Top targeted locations** - Geographic hotspots
- **Common drone types** - Frequency distribution of UAV models
- **Interactive map** - Visualize restricted areas and incident locations

### Incident Management
- **Browse incidents** - Filter by date, source, purpose, country
- **Add new incident** - Report drone sighting or incursion
- **Spatial queries** - Find incidents near specific restricted area
- **Timeline analysis** - Monthly incident distribution

### Drone Type Intelligence
- **Drone catalog** - Known UAV models with specifications
- **Threat assessment** - Score drones by interception difficulty and proliferation
- **Incident correlation** - See all incidents involving specific drone model

### Restricted Area Protection
- **Geospatial queries** - Find incidents within X km of any restricted area
- **Threat matrix** - Risk assessment of each location
- **Frequency analysis** - Most-targeted locations

### Pattern Detection
- **Spatial patterns** - Same location targeted repeatedly
- **Temporal patterns** - Coordinated activity across time
- **Drone type patterns** - Same UAV model used in multiple incidents
- **Auto-detection** - Automatically identify patterns from incident data

### Intervention Tracking
- **Effectiveness analysis** - Success rate of jamming, netting, kinetic, interception
- **Response time tracking** - How quickly can defenses be deployed?
- **Drone vs. countermeasure matrix** - Which tactics work against which UAVs?

---

## Adding Data

### Manually Add Incident
```bash
curl -X POST "http://localhost:8000/api/incidents/" \
  -H "Content-Type: application/json" \
  -d '{
    "sighting_date": "2024-11-07",
    "latitude": 50.9009,
    "longitude": 4.4844,
    "drone_description": "DJI Matrice 300 RTK",
    "source": "news",
    "confidence_score": 0.85,
    "title": "Drone over Brussels Airport",
    "description": "Multiple drone sightings reported over runway approach path",
    "purpose_assessment": "reconnaissance"
  }'
```

### Add Restricted Area
```bash
curl -X POST "http://localhost:8000/api/restricted-areas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kleine Brogel Air Base",
    "area_type": "military_base",
    "country": "BE",
    "latitude": 51.3167,
    "longitude": 5.3833,
    "threat_level": 5,
    "description": "US tactical nuclear storage facility"
  }'
```

### Record Intervention
```bash
curl -X POST "http://localhost:8000/api/interventions/" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 1,
    "intervention_type": "jamming",
    "response_time_minutes": 3,
    "outcome": "success"
  }'
```

---

## Advanced Features

### Auto-Detect Patterns
```bash
curl -X POST "http://localhost:8000/api/patterns/auto-detect"
```

The system will automatically identify:
- Locations targeted multiple times (spatial patterns)
- Same drone types used repeatedly (drone type patterns)
- Temporal clustering (coordinated activity)

### Threat Assessment
```bash
curl "http://localhost:8000/api/drone-types/analysis/threat-assessment"
```

Returns threat scores considering:
- Frequency of incidents
- Interception difficulty
- Operational range
- Payload type

### Intervention Effectiveness
```bash
curl "http://localhost:8000/api/interventions/analysis/effectiveness"
```

Shows success rates, response times, and outcome distribution by intervention type.

---

## Project Structure

```
drone-cuas-osint-dashboard/
├── app.py                  # Main launcher (run this!)
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore
│
├── backend/
│   ├── main.py           # FastAPI application
│   ├── database.py       # SQLAlchemy setup, migrations
│   ├── models.py         # Database models
│   └── routers/          # API endpoints
│       ├── general.py    # Health & stats
│       ├── incidents.py  # Drone sighting reports
│       ├── drone_types.py # UAV specifications
│       ├── restricted_areas.py # Airports, bases, facilities
│       ├── patterns.py   # Pattern detection & correlation
│       └── interventions.py # Countermeasure tracking
│
├── frontend/
│   ├── index.html        # Main page (served by FastAPI)
│   └── src/
│       ├── app.js        # Vue.js application
│       └── public/       # Static assets
│
└── data/
    └── drone_cuas.db     # SQLite database (auto-created)
```

---

## Development

### Adding New Endpoints

1. Create router in `backend/routers/`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class MyDataCreate(BaseModel):
    name: str
    description: str

@router.post("/")
async def create_my_data(data: MyDataCreate, db: Session = Depends(get_db)):
    db_data = MyModel(**data.dict())
    db.add(db_data)
    db.commit()
    return db_data
```

2. Include in `backend/main.py`:
```python
from backend.routers import my_router
app.include_router(my_router.router, prefix="/api/myfeature", tags=["myfeature"])
```

### Adding Database Models

1. Define in `backend/models.py` (inherits from `Base`)
2. Run the app - tables auto-create on startup

### Frontend Development

Edit `frontend/src/app.js` and `frontend/index.html`. The app uses Vue 3 with:
- `ref()` for reactive values
- `reactive()` for objects
- `computed()` for derived values
- Hash-based routing

---

## Troubleshooting

### Port 8000 already in use
Modify `app.py`:
```python
PORT = 8001  # Change to different port
```

### Browser doesn't auto-open
Manually navigate to `http://127.0.0.1:8000`

### Database errors
Delete `data/drone_cuas.db` - it will recreate on next run

### API not accessible
Verify backend is running: `GET http://127.0.0.1:8000/api/health`
Check browser console for CORS errors (shouldn't have any, frontend served from backend)

---

## Render Deployment Notes

- Deploy via `render.yaml`; the `RENDER` env var enables production settings automatically.
- Render free-tier web services pause after ~15 minutes of inactivity. `app.py` now spawns a keep-alive thread that pings `RENDER_EXTERNAL_URL/health` every 9 minutes so long as that env var (or an override `KEEP_ALIVE_URL`) is present.
- Adjust the interval by setting `KEEP_ALIVE_INTERVAL` (seconds) if you need a different cadence; leave the default if you're on the free plan to avoid unnecessary traffic.
- If you prefer full control, disable the keep-alive by omitting both `RENDER_EXTERNAL_URL` and `KEEP_ALIVE_URL`, or switch to a paid Render plan where the service remains on without pings.
- Continuous monitoring: `render.yaml` also defines a `drone-cuas-watchdog` worker that runs `watchdog_agent.py`. Configure `WATCHDOG_TARGET_URL` (defaults to the deployed `/health` route), `WATCHDOG_INTERVAL_SECONDS`, and optional `WATCHDOG_WEBHOOK_URL` to get alerts after repeated failures. Render logs for that worker show the live heartbeat.

### Watchdog Agent Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `WATCHDOG_TARGET_URL` | required | Full URL to ping (typically `https://<service>.onrender.com/health`). |
| `WATCHDOG_INTERVAL_SECONDS` | `180` | Interval between checks. Increase if you need fewer requests. |
| `WATCHDOG_TIMEOUT_SECONDS` | `10` | Per-request timeout in seconds. |
| `WATCHDOG_FAILURE_THRESHOLD` | `3` | Number of consecutive failures before the webhook fires. |
| `WATCHDOG_WEBHOOK_URL` | unset | Optional webhook to POST alerts (JSON payload). |

---

## Security Notes

- ✓ SQLite file-based (no network exposure)
- ✓ Localhost-only by default (127.0.0.1)
- ✓ No authentication required (add LDAP/AD later)
- ⚠ All data stored locally (audit carefully)
- ⚠ For on-premise deployment only (not cloud)

### For Production Deployment

1. Add authentication (OAuth2, LDAP, AD)
2. Use PostgreSQL instead of SQLite (better for multi-user)
3. Deploy behind reverse proxy (nginx, Apache)
4. Add HTTPS/TLS
5. Restrict CORS to known origins
6. Add rate limiting
7. Implement audit logging
8. Regular database backups

---

## Next Steps

### Phase 2: Intelligence Features
- [ ] Relationship mapping & network visualization
- [ ] Timeline views with geopolitical context
- [ ] Risk rating system
- [ ] Report generation (PDF export)
- [ ] Alert system for new patterns

### Phase 3: Data Integration
- [ ] RSS feed aggregation (news, aviation authorities)
- [ ] API integration with EU aviation authorities (EASA)
- [ ] ADS-B and FLARM data integration
- [ ] Web scraping for incident reports
- [ ] Manual submission forms

### Phase 4: Advanced Analysis
- [ ] Machine learning for pattern detection
- [ ] Predictive hotspot analysis
- [ ] Supply chain tracking (drone procurement routes)
- [ ] Actor network analysis
- [ ] Temporal correlation with geopolitical events

### Phase 5: Operational Support
- [ ] Real-time alert dashboards
- [ ] Intervention recommendations
- [ ] Cost analysis (interceptor vs. reconnaissance value)
- [ ] EU coordination platform
- [ ] NATO intelligence sharing format

---

## Contributing

This is a defensive security project for legitimate EU intelligence coordination.

### Data Sources
- European aviation authorities (EASA, national CAAs)
- News reports and media alerts
- Public APIs (ADS-B, FLARM)
- Verified community submissions
- Official incident reports

### Intelligence Standards
- All data must include source attribution
- Confidence scores required for analysis
- Chain of custody for evidence
- Regular validation of drone type identifications

---

## Support

For issues:
1. Check API docs: `http://localhost:8000/docs` (Swagger UI)
2. Review this README and troubleshooting section
3. Check console output for error messages
4. Verify data directory exists: `mkdir -p data/`

---

## License & Usage

**Defensive Security Only** - This dashboard is designed for:
- ✓ EU intelligence agencies (counter-reconnaissance)
- ✓ NATO coordination
- ✓ Airport/airbase security operations
- ✓ Academic research on counter-UAS
- ✓ Authorized defense contractors

**Not for:**
- Commercial drone surveillance
- Privacy violations
- Unauthorized tracking
- Detection evasion for hostile purposes

---

**Status:** MVP Ready
**Last Updated:** November 2024
**Version:** 1.0.0
**Technology Stack:** Python 3.8+ | FastAPI | SQLite | Vue.js 3 | Bootstrap 5 | Leaflet.js

---

## Quick Reference

| Task | Command |
|------|---------|
| **Start Dashboard** | `python app.py` |
| **View API Docs** | `http://localhost:8000/docs` |
| **View Health** | `curl http://localhost:8000/api/health` |
| **Get Stats** | `curl http://localhost:8000/api/stats` |
| **List Incidents** | `curl http://localhost:8000/api/incidents/` |
| **Auto-detect Patterns** | `curl -X POST http://localhost:8000/api/patterns/auto-detect` |
| **Intervention Analysis** | `curl http://localhost:8000/api/interventions/analysis/effectiveness` |
