# OSINT CUAS API Reference

Quick reference for all API endpoints with examples.

**Base URL:** `http://localhost:8000/api`

---

## System Health

### Health Check
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-07T12:00:00.000000",
  "service": "OSINT CUAS Dashboard"
}
```

### Get Dashboard Statistics
```bash
curl http://localhost:8000/api/stats
```

Response:
```json
{
  "timestamp": "2024-11-07T12:00:00.000000",
  "summary": {
    "total_incidents": 145,
    "recent_incidents_30d": 23,
    "total_interventions": 12,
    "intervention_success_rate": 75.5,
    "total_patterns": 5,
    "restricted_areas": 42,
    "drone_types_tracked": 18
  },
  "top_drone_types": [
    {"model": "DJI Matrice 300 RTK", "incidents": 23},
    {"model": "DJI Phantom 4 Pro", "incidents": 18}
  ],
  "top_targeted_areas": [
    {"name": "Kleine Brogel Air Base", "country": "BE", "incidents": 12},
    {"name": "Brussels Airport", "country": "BE", "incidents": 8}
  ],
  "interventions_by_type": [
    {"type": "jamming", "count": 7},
    {"type": "netting", "count": 3},
    {"type": "kinetic", "count": 2}
  ],
  "purposes_detected": [
    {"purpose": "reconnaissance", "count": 89},
    {"purpose": "disruption", "count": 34},
    {"purpose": "unknown", "count": 22}
  ]
}
```

---

## Incidents (Drone Sightings)

### List All Incidents
```bash
# Basic list
curl "http://localhost:8000/api/incidents/?skip=0&limit=10"

# Filter by source
curl "http://localhost:8000/api/incidents/?source=news&limit=20"

# Filter by country
curl "http://localhost:8000/api/incidents/?country=BE&limit=20"

# Filter by purpose
curl "http://localhost:8000/api/incidents/?purpose=reconnaissance&limit=20"

# Order by different criteria
curl "http://localhost:8000/api/incidents/?order_by=recent"  # recent, oldest, confidence
```

Response:
```json
{
  "total": 145,
  "skip": 0,
  "limit": 10,
  "incidents": [
    {
      "id": 1,
      "sighting_date": "2024-11-07",
      "sighting_time": "14:30",
      "latitude": 50.9009,
      "longitude": 4.4844,
      "altitude_m": 300,
      "drone_description": "DJI Matrice 300 RTK",
      "distance_to_restricted_m": 2500,
      "duration_minutes": 45,
      "source": "news",
      "confidence_score": 0.85,
      "title": "Drone over Brussels Airport",
      "description": "Multiple drone sightings reported over runway approach path",
      "suspected_operator": "Unknown civilian",
      "purpose_assessment": "reconnaissance",
      "report_date": "2024-11-07T10:30:00"
    }
  ]
}
```

### Get Single Incident
```bash
curl http://localhost:8000/api/incidents/1
```

### Create Incident
```bash
curl -X POST http://localhost:8000/api/incidents/ \
  -H "Content-Type: application/json" \
  -d '{
    "sighting_date": "2024-11-07",
    "sighting_time": "14:30",
    "latitude": 50.9009,
    "longitude": 4.4844,
    "altitude_m": 300,
    "drone_description": "DJI Matrice 300 RTK",
    "restricted_area_id": 1,
    "distance_to_restricted_m": 2500,
    "duration_minutes": 45,
    "source": "news",
    "confidence_score": 0.85,
    "title": "Drone over Brussels Airport",
    "description": "Multiple drone sightings reported over runway approach path",
    "suspected_operator": "Unknown civilian",
    "purpose_assessment": "reconnaissance"
  }'
```

### Update Incident
```bash
curl -X PUT http://localhost:8000/api/incidents/1 \
  -H "Content-Type: application/json" \
  -d '{
    "purpose_assessment": "signals_intelligence",
    "suspected_operator": "Russian SVR",
    "confidence_score": 0.95
  }'
```

### Delete Incident
```bash
curl -X DELETE http://localhost:8000/api/incidents/1
```

### Get Incidents Near Restricted Area
```bash
# All incidents within 50 km of area ID 1
curl "http://localhost:8000/api/incidents/spatial/near/1?radius_km=50"
```

Response:
```json
[
  {
    "incident": {...},
    "distance_km": 2.5
  },
  {
    "incident": {...},
    "distance_km": 8.3
  }
]
```

### Analyze Incidents by Purpose
```bash
curl http://localhost:8000/api/incidents/analysis/by-purpose
```

Response:
```json
[
  {
    "purpose": "reconnaissance",
    "incidents": 89,
    "avg_confidence": 0.78
  },
  {
    "purpose": "disruption",
    "incidents": 34,
    "avg_confidence": 0.62
  }
]
```

### Analyze Incidents by Source
```bash
curl http://localhost:8000/api/incidents/analysis/by-source
```

### Get Monthly Timeline
```bash
# All incidents
curl http://localhost:8000/api/incidents/timeline/monthly

# By country
curl "http://localhost:8000/api/incidents/timeline/monthly?country=BE"
```

Response:
```json
[
  {"month": "2024-09", "incidents": 12},
  {"month": "2024-10", "incidents": 18},
  {"month": "2024-11", "incidents": 5}
]
```

---

## Drone Types

### List All Drone Types
```bash
curl "http://localhost:8000/api/drone-types/?limit=100"

# Filter by country
curl "http://localhost:8000/api/drone-types/?country=CN&limit=20"

# Filter by payload
curl "http://localhost:8000/api/drone-types/?payload_type=camera&limit=20"

# Order by incidents
curl "http://localhost:8000/api/drone-types/?order_by=incidents"
```

Response:
```json
{
  "total": 18,
  "skip": 0,
  "limit": 100,
  "drone_types": [
    {
      "id": 1,
      "model": "DJI Matrice 300 RTK",
      "manufacturer": "DJI (China)",
      "country_of_origin": "CN",
      "range_km": 15,
      "endurance_minutes": 55,
      "max_altitude_m": 2500,
      "payload_type": "camera",
      "difficulty_intercept": 4,
      "estimated_cost_usd": 15000,
      "notes": "Commercial but capable of long-range surveillance"
    }
  ]
}
```

### Get Drone Type Details
```bash
curl http://localhost:8000/api/drone-types/1
```

### Get All Incidents for Drone Type
```bash
curl http://localhost:8000/api/drone-types/1/incidents
```

Response:
```json
{
  "drone_type": {...},
  "incidents": [...],
  "total_incidents": 23
}
```

### Add New Drone Type
```bash
curl -X POST http://localhost:8000/api/drone-types/ \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Orlan-10",
    "manufacturer": "Russian Armed Forces",
    "country_of_origin": "RU",
    "range_km": 40,
    "endurance_minutes": 90,
    "max_altitude_m": 4000,
    "payload_type": "signals_intelligence",
    "difficulty_intercept": 5,
    "estimated_cost_usd": 200000,
    "notes": "Military reconnaissance drone, frequent over EU airbases"
  }'
```

### Threat Assessment of All Drones
```bash
curl http://localhost:8000/api/drone-types/analysis/threat-assessment
```

Response:
```json
[
  {
    "drone_type": "Orlan-10",
    "manufacturer": "Russian Armed Forces",
    "country_of_origin": "RU",
    "incident_count": 12,
    "threat_score": 9.2,
    "difficulty_intercept": 5,
    "payload_type": "signals_intelligence",
    "specifications": {
      "range_km": 40,
      "endurance_minutes": 90,
      "max_altitude_m": 4000,
      "estimated_cost": 200000
    }
  }
]
```

---

## Restricted Areas

### List Restricted Areas
```bash
curl "http://localhost:8000/api/restricted-areas/?limit=100"

# Filter by country
curl "http://localhost:8000/api/restricted-areas/?country=BE&limit=20"

# Filter by type
curl "http://localhost:8000/api/restricted-areas/?area_type=military_base&limit=20"

# Order by threat level
curl "http://localhost:8000/api/restricted-areas/?order_by=threat"
```

Response:
```json
{
  "total": 42,
  "skip": 0,
  "limit": 100,
  "restricted_areas": [
    {
      "id": 1,
      "name": "Kleine Brogel Air Base",
      "area_type": "military_base",
      "country": "BE",
      "latitude": 51.3167,
      "longitude": 5.3833,
      "radius_km": 5.0,
      "threat_level": 5,
      "description": "US tactical nuclear weapons storage",
      "created_at": "2024-11-07T10:00:00",
      "updated_at": "2024-11-07T10:00:00"
    }
  ]
}
```

### Get Restricted Area Details
```bash
curl http://localhost:8000/api/restricted-areas/1
```

### Get Incidents Near Area
```bash
curl http://localhost:8000/api/restricted-areas/1/incidents
```

### Add New Restricted Area
```bash
curl -X POST http://localhost:8000/api/restricted-areas/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramstein Air Base",
    "area_type": "military_base",
    "country": "DE",
    "latitude": 49.4372,
    "longitude": 7.6084,
    "radius_km": 10,
    "threat_level": 5,
    "description": "US air base, NATO hub, drone activity increasing"
  }'
```

### Get Threat Matrix (All Areas)
```bash
curl http://localhost:8000/api/restricted-areas/analysis/threat-matrix
```

Response:
```json
[
  {
    "area_id": 1,
    "name": "Kleine Brogel Air Base",
    "country": "BE",
    "area_type": "military_base",
    "threat_level": 5,
    "incident_count": 12,
    "avg_confidence": 0.82,
    "most_common_drone": "DJI Matrice 300 RTK",
    "location": {
      "latitude": 51.3167,
      "longitude": 5.3833,
      "radius_km": 5.0
    }
  }
]
```

---

## Patterns

### List Detected Patterns
```bash
curl "http://localhost:8000/api/patterns/?limit=100"

# Filter by type
curl "http://localhost:8000/api/patterns/?pattern_type=spatial&limit=20"

# Order by confidence
curl "http://localhost:8000/api/patterns/?order_by=confidence"
```

Response:
```json
{
  "total": 5,
  "skip": 0,
  "limit": 100,
  "patterns": [
    {
      "id": 1,
      "name": "Repeated targeting of Kleine Brogel Air Base",
      "description": "12 incidents near Kleine Brogel in last 3 months",
      "pattern_type": "spatial",
      "incident_count": 12,
      "date_range_start": "2024-08-15",
      "date_range_end": "2024-11-07",
      "primary_location": "Kleine Brogel Air Base",
      "primary_drone_type": "DJI Matrice 300 RTK",
      "suspected_purpose": "reconnaissance",
      "suspected_operator": "Unknown military contractor",
      "confidence_score": 0.85,
      "notes": "Systematic targeting suggests organized operation",
      "created_at": "2024-11-07T10:30:00",
      "updated_at": "2024-11-07T10:30:00"
    }
  ]
}
```

### Get Pattern Details
```bash
curl http://localhost:8000/api/patterns/1
```

### Get Incidents in Pattern
```bash
curl http://localhost:8000/api/patterns/1/incidents
```

### Create New Pattern
```bash
curl -X POST http://localhost:8000/api/patterns/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Belgian nuclear facility surveillance",
    "description": "Coordinated drone activity targeting nuclear storage sites",
    "pattern_type": "spatial",
    "incident_count": 15,
    "primary_location": "Belgium",
    "suspected_purpose": "reconnaissance",
    "suspected_operator": "Russian intelligence service",
    "confidence_score": 0.92,
    "notes": "Correlated with Russian military exercises in Baltic region"
  }'
```

### Auto-Detect Patterns
```bash
curl -X POST http://localhost:8000/api/patterns/auto-detect
```

Response:
```json
{
  "detected_patterns": 3,
  "patterns": [
    "Detected spatial pattern: Kleine Brogel Air Base (12 incidents)",
    "Detected drone pattern: DJI Matrice 300 RTK (18 incidents)",
    "Detected temporal pattern: Increased activity near nuclear sites (Q4 2024)"
  ]
}
```

---

## Interventions (Countermeasures)

### List Interventions
```bash
curl "http://localhost:8000/api/interventions/?limit=100"

# Filter by type
curl "http://localhost:8000/api/interventions/?intervention_type=jamming&limit=20"

# Filter by outcome
curl "http://localhost:8000/api/interventions/?outcome=success&limit=20"
```

Response:
```json
{
  "total": 12,
  "skip": 0,
  "limit": 100,
  "interventions": [
    {
      "id": 1,
      "incident_id": 5,
      "intervention_type": "jamming",
      "response_time_minutes": 3,
      "outcome": "success",
      "success_rate": 1.0,
      "notes": "RF jamming effective against DJI Matrice 300",
      "created_at": "2024-11-05T14:30:00",
      "updated_at": "2024-11-05T14:30:00"
    }
  ]
}
```

### Record New Intervention
```bash
curl -X POST http://localhost:8000/api/interventions/ \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 1,
    "intervention_type": "jamming",
    "response_time_minutes": 3,
    "outcome": "success",
    "success_rate": 0.95,
    "notes": "RF jamming effective, drone recovered 2km away"
  }'
```

### Intervention Effectiveness Analysis
```bash
curl http://localhost:8000/api/interventions/analysis/effectiveness
```

Response:
```json
[
  {
    "intervention_type": "jamming",
    "total": 7,
    "successful": 6,
    "partial": 1,
    "failed": 0,
    "success_rate": 85.7,
    "avg_response_time_minutes": 2.8
  },
  {
    "intervention_type": "netting",
    "total": 3,
    "successful": 2,
    "partial": 1,
    "failed": 0,
    "success_rate": 66.7,
    "avg_response_time_minutes": 8.5
  },
  {
    "intervention_type": "kinetic",
    "total": 2,
    "successful": 2,
    "partial": 0,
    "failed": 0,
    "success_rate": 100.0,
    "avg_response_time_minutes": 4.2
  }
]
```

### Response Time Analysis
```bash
curl http://localhost:8000/api/interventions/analysis/response-times
```

Response:
```json
{
  "total_interventions_tracked": 12,
  "average_response_time": 4.3,
  "median_response_time": 3.5,
  "min_response_time": 1,
  "max_response_time": 12,
  "p10_response_time": 1.5,
  "p90_response_time": 10.2
}
```

### Effectiveness by Drone Type
```bash
curl http://localhost:8000/api/interventions/analysis/by-incident-type
```

---

## Data Fields Reference

### Drone Sources
- `news` - News report
- `authority` - Government/aviation authority report
- `submission` - Community/verified submission
- `intelligence` - Official intelligence report

### Area Types
- `airport` - Commercial airport
- `military_base` - Military airfield/base
- `nuclear_facility` - Nuclear power plant or weapons storage
- `government` - Government building/compound
- `critical_infrastructure` - Power grid, water, telecommunications, etc.

### Intervention Types
- `jamming` - Electronic warfare / RF jamming
- `netting` - Drone netting systems
- `kinetic` - Physical destruction (bullets, missiles)
- `interception` - Capture/recovery of drone
- `unknown` - Method unknown or classified

### Outcomes
- `success` - Drone destroyed or forced down
- `partial` - Drone damaged or restricted
- `failed` - Intervention unsuccessful
- `unknown` - Outcome unknown
- `not_attempted` - No intervention taken

### Pattern Types
- `spatial` - Geographic targeting pattern
- `temporal` - Time-based clustering
- `drone_type` - Same UAV model used multiple times
- `operator` - Suspected same operator/group

### Purposes (Assessment)
- `reconnaissance` - Surveillance/intelligence gathering
- `disruption` - Interference with operations
- `signals_intelligence` - SIGINT collection
- `targeting` - Preparation for kinetic strike
- `unknown` - Purpose unclear

### Confidence Score
0.0 to 1.0:
- `0.9-1.0` - Very high confidence (verified, multiple sources)
- `0.7-0.9` - High confidence (credible reporting)
- `0.5-0.7` - Medium confidence (single credible source)
- `0.3-0.5` - Low confidence (preliminary reports)
- `0.0-0.3` - Very low confidence (unverified)

---

## Error Responses

### 404 Not Found
```json
{"detail": "Incident not found"}
```

### 400 Bad Request
```json
{"detail": "Drone type already exists"}
```

### 500 Server Error
```json
{"detail": "Internal server error"}
```

---

## Pagination

All list endpoints support pagination:
- `skip=0` - Start at record 0
- `limit=10` - Return 10 records

Example:
```bash
curl "http://localhost:8000/api/incidents/?skip=20&limit=10"
```

Returns records 21-30.

---

## Rate Limits

None configured by default. For production, add:
```bash
pip install slowapi
```

Then configure per endpoint.

---

## Interactive API Documentation

Visit: `http://localhost:8000/docs`

The Swagger UI interface allows you to:
- Browse all endpoints
- See request/response schemas
- Test requests directly
- View parameter descriptions

---

## Batch Operations

Example: Create multiple incidents from CSV
```python
import requests
import csv

with open('incidents.csv') as f:
    for row in csv.DictReader(f):
        requests.post(
            'http://localhost:8000/api/incidents/',
            json={
                'sighting_date': row['date'],
                'latitude': float(row['lat']),
                'longitude': float(row['lon']),
                'source': 'import',
                'title': row['title'],
                'description': row['description']
            }
        )

print("✓ Batch import complete")
```

---

**Need more examples?** Check the interactive Swagger UI at `/docs` or use `curl -v` for detailed request/response info.
