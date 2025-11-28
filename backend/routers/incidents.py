from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from typing import Optional, List
from backend.database import get_db
from backend.models import Incident, RestrictedArea, DroneType
from backend.trusted_sources import validate_source_url, is_source_blocked, get_trusted_sources_for_country
import json
import urllib.parse
import re

router = APIRouter()

def detect_country_from_text(text: str) -> Optional[str]:
    """
    Detect country code from text (title or location name).
    Returns country code (e.g., 'NL', 'BE', 'DE') or None.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Country keywords mapping
    country_keywords = {
        'NL': ['netherlands', 'dutch', 'amsterdam', 'rotterdam', 'schiphol', 'volkel', 'holland', 'eindhoven', 'utrecht'],
        'BE': ['belgium', 'belgian', 'brussels', 'zaventem', 'antwerp', 'bruges', 'flanders'],
        'DE': ['germany', 'german', 'berlin', 'munich', 'hamburg', 'frankfurt', 'cologne', 'brunsbüttel'],
        'FR': ['france', 'french', 'paris', 'lyon', 'marseille', 'toulouse', 'nice'],
        'UK': ['united kingdom', 'british', 'london', 'manchester', 'birmingham', 'scotland', 'wales'],
        'EE': ['estonia', 'estonian', 'tallinn', 'reedo'],
        'LV': ['latvia', 'latvian', 'riga'],
        'LT': ['lithuania', 'lithuanian', 'vilnius'],
        'PL': ['poland', 'polish', 'warsaw', 'krakow'],
        'IT': ['italy', 'italian', 'rome', 'milan'],
        'ES': ['spain', 'spanish', 'madrid', 'barcelona'],
    }

    # Check each country's keywords
    for country_code, keywords in country_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return country_code

    return None

def get_display_source(incident: Incident) -> str:
    """
    Determine which source to display, prioritizing Senhive as primary sensor.
    If Senhive is in secondary sources, use it. Otherwise use the main source.
    """
    # Check if Senhive is in secondary sources
    if incident.secondary_sources:
        try:
            sources = json.loads(incident.secondary_sources) if isinstance(incident.secondary_sources, str) else incident.secondary_sources
            if isinstance(sources, list):
                for src in sources:
                    if isinstance(src, dict) and 'name' in src:
                        if 'Senhive' in src['name'] or 'senhive' in src.get('name', '').lower():
                            return 'senhive'
        except:
            pass

    # Check if Senhive is in primary source name
    if incident.primary_source_name and 'Senhive' in incident.primary_source_name:
        return 'senhive'

    # Otherwise return the main source
    return incident.source

class IncidentCreate(BaseModel):
    sighting_date: date
    sighting_time: Optional[str] = None
    latitude: float
    longitude: float
    altitude_m: Optional[int] = None
    drone_type_id: Optional[int] = None
    drone_description: Optional[str] = None
    # Drone characteristics when type unconfirmed
    drone_characteristics: Optional[str] = None  # Observable features: "small white quad copter", "RTK antenna", "fixed wing", etc.
    drone_characteristics_sources: Optional[str] = None  # Where observed from: "witness accounts", "video analysis", "radar", etc.
    restricted_area_id: Optional[int] = None
    distance_to_restricted_m: Optional[int] = None
    duration_minutes: Optional[int] = None
    source: str
    source_url: Optional[str] = None  # Direct link to source/article (will be validated)
    confidence_score: Optional[float] = 0.5
    title: str
    description: str
    details: Optional[str] = None
    suspected_operator: Optional[str] = None
    purpose_assessment: Optional[str] = None
    # Drone identification evidence
    identification_method: Optional[str] = None  # visual, radar, recovered_wreckage, photo, video, adsb, signals, intelligence
    identification_confidence: Optional[float] = 0.5  # How certain is the drone type ID?
    identification_evidence: Optional[str] = None  # Detailed evidence/proof
    identified_by: Optional[str] = None  # Who identified it

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    suspected_operator: Optional[str] = None
    purpose_assessment: Optional[str] = None
    drone_type_id: Optional[int] = None
    drone_characteristics: Optional[str] = None
    drone_characteristics_sources: Optional[str] = None
    identification_method: Optional[str] = None
    identification_confidence: Optional[float] = None
    identification_evidence: Optional[str] = None
    identified_by: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    sighting_date: date
    sighting_time: Optional[str]
    latitude: float
    longitude: float
    altitude_m: Optional[int]
    drone_description: Optional[str]
    drone_characteristics: Optional[str]
    drone_characteristics_sources: Optional[str]
    restricted_area_id: Optional[int]  # For location lookup in frontend
    distance_to_restricted_m: Optional[int]
    duration_minutes: Optional[int]
    source: str
    display_source: str  # Primary source to display (Senhive prioritized)
    confidence_score: float
    title: str
    description: str
    suspected_operator: Optional[str]
    purpose_assessment: Optional[str]
    identification_method: Optional[str]
    identification_confidence: Optional[float]
    identification_evidence: Optional[str]
    identified_by: Optional[str]
    report_date: datetime
    weather_conditions_json: Optional[str]
    weather_favorability_score: Optional[float]
    knmi_station_id: Optional[int]

    class Config:
        from_attributes = True

@router.get("/")
async def list_incidents(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = None,
    country: Optional[str] = None,
    drone_type_id: Optional[int] = None,
    purpose: Optional[str] = None,
    order_by: str = "recent"
):
    """List all incidents with optional filtering"""
    query = db.query(Incident)

    # Filter out duplicates and false positives by default
    query = query.filter(
        or_(
            Incident.operational_class.is_(None),
            Incident.operational_class == 'MERGED_MASTER',
            Incident.operational_class == 'RSS_detected'
        )
    )

    # Apply filters
    if source:
        query = query.filter(Incident.source == source)
    if drone_type_id:
        query = query.filter(Incident.drone_type_id == drone_type_id)
    if purpose:
        query = query.filter(Incident.purpose_assessment == purpose)

    # Country filter (through restricted area)
    if country:
        query = query.join(RestrictedArea).filter(
            RestrictedArea.country == country
        )

    # Order by
    if order_by == "recent":
        query = query.order_by(Incident.sighting_date.desc())
    elif order_by == "oldest":
        query = query.order_by(Incident.sighting_date.asc())
    elif order_by == "confidence":
        query = query.order_by(Incident.confidence_score.desc())

    total = query.count()
    incidents = query.offset(skip).limit(limit).all()

    # Add display_source to each incident
    incident_list = []
    for incident in incidents:
        # Get location name and country from restricted area (with error handling)
        location_name = None
        country = None
        try:
            if incident.restricted_area_id:
                restricted_area = db.query(RestrictedArea).filter(RestrictedArea.id == incident.restricted_area_id).first()
                if restricted_area:
                    location_name = restricted_area.name
                    country = restricted_area.country
        except Exception as e:
            print(f"Error fetching restricted area: {e}")

        # SMART COUNTRY DETECTION: Override country if we can detect it from title or location
        # This fixes cases where restricted_area is mismatched (e.g., Dutch incidents linked to Estonian bases)
        detected_country_from_title = detect_country_from_text(incident.title)
        detected_country_from_location = detect_country_from_text(location_name)

        # Priority: detected from title > detected from location > restricted_area country
        if detected_country_from_title:
            country = detected_country_from_title
        elif detected_country_from_location:
            country = detected_country_from_location
        # Otherwise keep the country from restricted_area (which might be None or wrong)

        # Get drone type name (with error handling)
        drone_type_name = None
        try:
            if incident.drone_type_id:
                drone_type = db.query(DroneType).filter(DroneType.id == incident.drone_type_id).first()
                if drone_type:
                    drone_type_name = drone_type.name
        except Exception as e:
            print(f"Error fetching drone type: {e}")

        incident_dict = {
            "id": incident.id,
            "sighting_date": incident.sighting_date,
            "sighting_time": incident.sighting_time,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "altitude_m": incident.altitude_m,
            "drone_description": incident.drone_description,
            "drone_characteristics": incident.drone_characteristics,
            "drone_characteristics_sources": incident.drone_characteristics_sources,
            "restricted_area_id": incident.restricted_area_id,
            "location_name": location_name,
            "country": country,
            "distance_to_restricted_m": incident.distance_to_restricted_m,
            "duration_minutes": incident.duration_minutes,
            "source": incident.source,
            "display_source": incident.display_source if incident.display_source else get_display_source(incident),
            "confidence_score": incident.confidence_score,
            "title": incident.title,
            "description": incident.description,
            "suspected_operator": incident.suspected_operator,
            "purpose_assessment": incident.purpose_assessment,
            "identification_method": incident.identification_method,
            "identification_confidence": incident.identification_confidence,
            "identification_evidence": incident.identification_evidence,
            "identified_by": incident.identified_by,
            "drone_type_id": incident.drone_type_id,
            "drone_type_name": drone_type_name,
            "report_date": incident.report_date,
            "weather_conditions_json": incident.weather_conditions_json,
            "weather_favorability_score": incident.weather_favorability_score,
            "knmi_station_id": incident.knmi_station_id,
        }
        incident_list.append(incident_dict)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "incidents": incident_list
    }

@router.get("/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get incident details with source validation"""
    import requests

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Prepare response with source validation
    incident_data = {
        "id": incident.id,
        "sighting_date": incident.sighting_date,
        "sighting_time": incident.sighting_time,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "altitude_m": incident.altitude_m,
        "drone_description": incident.drone_description,
        "drone_characteristics": incident.drone_characteristics,
        "drone_characteristics_sources": incident.drone_characteristics_sources,
        "restricted_area_id": incident.restricted_area_id,
        "distance_to_restricted_m": incident.distance_to_restricted_m,
        "duration_minutes": incident.duration_minutes,
        "source": incident.source,
        "source_url": incident.source_url,
        "confidence_score": incident.confidence_score,
        "title": incident.title,
        "description": incident.description,
        "details": incident.details,
        "suspected_operator": incident.suspected_operator,
        "purpose_assessment": incident.purpose_assessment,
        "identification_method": incident.identification_method,
        "identification_confidence": incident.identification_confidence,
        "identification_evidence": incident.identification_evidence,
        "identified_by": incident.identified_by,
        "primary_source_name": incident.primary_source_name,
        "primary_source_credibility": incident.primary_source_credibility,
        "secondary_sources": json.loads(incident.secondary_sources) if incident.secondary_sources else [],
        "display_source": get_display_source(incident),
        "report_date": incident.report_date,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "weather_conditions_json": incident.weather_conditions_json,
        "weather_favorability_score": incident.weather_favorability_score,
        "knmi_station_id": incident.knmi_station_id,
    }

    # Validate source URL if present
    if incident.source_url:
        try:
            # Check if link is working
            response = requests.head(incident.source_url, timeout=5, allow_redirects=True)
            source_validation = {
                "url": incident.source_url,
                "working": response.status_code < 400,
                "status_code": response.status_code,
                "last_checked": datetime.utcnow().isoformat()
            }

            # Validate against trust framework
            country_code = None
            if incident.restricted_area_id:
                area = db.query(RestrictedArea).filter(
                    RestrictedArea.id == incident.restricted_area_id
                ).first()
                if area:
                    country_code = area.country

            trust_validation = validate_source_url(incident.source_url, country_code)
            source_validation.update(trust_validation)

        except requests.exceptions.Timeout:
            source_validation = {
                "url": incident.source_url,
                "working": False,
                "error": "TIMEOUT",
                "status_code": -1,
                "last_checked": datetime.utcnow().isoformat()
            }
        except Exception as e:
            source_validation = {
                "url": incident.source_url,
                "working": False,
                "error": str(e),
                "status_code": -1,
                "last_checked": datetime.utcnow().isoformat()
            }

        incident_data["source_validation"] = source_validation

    return incident_data


@router.get("/{incident_id}/recommended-sources")
async def get_recommended_sources(incident_id: int, db: Session = Depends(get_db)):
    """
    Get trusted local sources for this incident based on its location country.

    For example:
    - Incident at Dutch air base → Recommends De Volkskrant, NRC, NOS (Netherlands)
    - Incident at Belgian airport → Recommends De Standaard, VRT, RTBF (Belgium)

    This helps find news articles about the incident from credible local sources.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get the country from the restricted area
    country_code = None
    location_name = "Unknown Location"

    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            country_code = area.country
            location_name = area.name

    if not country_code:
        raise HTTPException(
            status_code=400,
            detail="Incident location not linked to restricted area. Cannot recommend sources."
        )

    # Get all trusted sources for this country
    all_sources = get_trusted_sources_for_country(country_code)

    # Build search URLs for each source
    search_term = urllib.parse.quote(incident.title)
    recommended = []

    for source in all_sources:
        rec = {
            "name": source['name'],
            "url": source['url'],
            "credibility": source['credibility'],
        }

        # Build Google News search for this incident
        rec["google_news_search"] = f"https://news.google.com/search?q={search_term}"

        recommended.append(rec)

    # Sort by credibility (highest first)
    recommended.sort(key=lambda x: x['credibility'], reverse=True)

    return {
        "incident_id": incident_id,
        "incident_title": incident.title,
        "location_country": country_code,
        "location_name": location_name,
        "recommended_sources": recommended,
        "total_sources": len(recommended),
        "search_tip": f"Use the Google News Search links to find articles about this incident in trusted {country_code} sources"
    }


@router.get("/{incident_id}/search-sources")
async def search_incident_in_sources(incident_id: int, db: Session = Depends(get_db)):
    """
    Get search URLs for finding this incident in trusted local news sources.

    Returns clickable search links for:
    - Google News search
    - Country-specific newspaper searches
    - Government website searches
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get country
    country_code = None
    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            country_code = area.country

    if not country_code:
        raise HTTPException(status_code=400, detail="Location country not determined")

    # Build search URLs
    search_term = urllib.parse.quote(incident.title)
    location_term = urllib.parse.quote(incident.title.split()[0])  # First word usually location

    search_urls = {
        "google_news": f"https://news.google.com/search?q={search_term}",
        "google_search": f"https://www.google.com/search?q={search_term}+drone",
    }

    # Add country-specific searches
    country_searches = {
        'NL': {
            "nos_news": f"https://nos.nl/zoeken/?q={search_term}",
            "volkskrant": f"https://www.volkskrant.nl/search/{search_term}",
            "nrc": f"https://www.nrc.nl/search/{search_term}",
            "ad": f"https://www.ad.nl/search/{search_term}",
        },
        'BE': {
            "vrt": f"https://www.vrt.be/vrtnws/nl/search/?q={search_term}",
            "standaard": f"https://www.standaard.be/search/{search_term}",
            "demorgen": f"https://www.demorgen.be/search/{search_term}",
            "rtbf": f"https://www.rtbf.be/search/?q={search_term}",
        },
        'DE': {
            "tagesschau": f"https://www.tagesschau.de/suche?q={search_term}",
            "spiegel": f"https://www.spiegel.de/suche/?q={search_term}",
            "dpa": f"https://www.dpa.com/search?query={search_term}",
        },
        'FR': {
            "france24": f"https://www.france24.com/fr/search?q={search_term}",
            "lemonde": f"https://www.lemonde.fr/recherche/?keywords={search_term}",
            "afp": f"https://www.afp.com/search?query={search_term}",
        },
        'PL': {
            "tvn24": f"https://www.tvn24.pl/?s={search_term}",
            "onet": f"https://wiadomosci.onet.pl/?q={search_term}",
        },
    }

    # Add country-specific URLs if available
    if country_code in country_searches:
        search_urls.update(country_searches[country_code])

    return {
        "incident_id": incident_id,
        "incident_title": incident.title,
        "country": country_code,
        "search_urls": search_urls,
        "instructions": "Click any URL to search for articles about this incident in trusted local sources"
    }

@router.post("/")
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Create new incident report with source URL validation"""
    try:
        # Verify drone type exists if provided
        if incident.drone_type_id:
            drone = db.query(DroneType).filter(
                DroneType.id == incident.drone_type_id
            ).first()
            if not drone:
                raise HTTPException(status_code=404, detail="Drone type not found")

        # Verify restricted area exists if provided
        country_code = None
        if incident.restricted_area_id:
            area = db.query(RestrictedArea).filter(
                RestrictedArea.id == incident.restricted_area_id
            ).first()
            if not area:
                raise HTTPException(status_code=404, detail="Restricted area not found")
            country_code = area.country

        # Validate source URL if provided
        if incident.source_url:
            # Check if source is blocked
            if is_source_blocked(incident.source_url):
                raise HTTPException(
                    status_code=400,
                    detail=f"Source URL is from a blocked source (non-EU or unreliable). Please use a trusted EU source."
                )

            # Validate against trust framework
            validation = validate_source_url(incident.source_url, country_code)
            if not validation["valid"]:
                # Warn but don't block if source not in framework
                print(f"⚠ Warning: Source URL not in trusted framework: {incident.source_url} - {validation['reason']}")

        db_incident = Incident(**incident.dict())
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        return db_incident
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR in create_incident: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating incident: {str(e)}")

@router.put("/{incident_id}")
async def update_incident(
    incident_id: int,
    incident: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update incident"""
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = incident.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_incident, field, value)

    db_incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.post("/{incident_id}/mark-false-positive")
async def mark_incident_false_positive(incident_id: int, db: Session = Depends(get_db)):
    """Mark incident as false positive (hides it from views)"""
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Mark as false positive
    db_incident.operational_class = "FALSE_POSITIVE"
    db_incident.confidence_score = 0.0
    db_incident.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_incident)

    return {
        "success": True,
        "incident_id": incident_id,
        "operational_class": "FALSE_POSITIVE",
        "message": "Incident marked as false positive and hidden from views"
    }

@router.delete("/{incident_id}")
async def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete incident"""
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(db_incident)
    db.commit()
    return {"deleted": True}

@router.get("/spatial/near/{area_id}")
async def get_incidents_near_area(
    area_id: int,
    radius_km: float = 10,
    db: Session = Depends(get_db)
):
    """Get incidents near a specific restricted area (within radius)"""
    area = db.query(RestrictedArea).filter(RestrictedArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Restricted area not found")

    # Simple distance calculation (for SQLite)
    # In production, use PostGIS for better geospatial queries
    incidents = db.query(Incident).all()
    nearby = []

    for inc in incidents:
        # Haversine formula simplified
        lat1, lon1 = area.latitude, area.longitude
        lat2, lon2 = inc.latitude, inc.longitude

        # Approximate distance in km
        dx = (lon2 - lon1) * 111
        dy = (lat2 - lat1) * 111
        distance_km = (dx**2 + dy**2)**0.5

        if distance_km <= radius_km:
            nearby.append({
                "incident": inc,
                "distance_km": round(distance_km, 2)
            })

    return sorted(nearby, key=lambda x: x["distance_km"])

@router.get("/analysis/by-purpose")
async def get_incidents_by_purpose(db: Session = Depends(get_db)):
    """Analyze incidents by suspected purpose"""
    results = db.query(
        Incident.purpose_assessment,
        func.count(Incident.id).label("count"),
        func.avg(Incident.confidence_score).label("avg_confidence")
    ).filter(Incident.purpose_assessment.isnot(None)).group_by(
        Incident.purpose_assessment
    ).all()

    return [
        {
            "purpose": purpose,
            "incidents": count,
            "avg_confidence": round(avg_conf, 2)
        }
        for purpose, count, avg_conf in results
    ]

@router.get("/analysis/by-source")
async def get_incidents_by_source(db: Session = Depends(get_db)):
    """Analyze incidents by source"""
    results = db.query(
        Incident.source,
        func.count(Incident.id).label("count"),
        func.avg(Incident.confidence_score).label("avg_confidence")
    ).group_by(Incident.source).all()

    return [
        {
            "source": source,
            "incidents": count,
            "avg_confidence": round(avg_conf, 2)
        }
        for source, count, avg_conf in results
    ]

@router.get("/timeline/monthly")
async def get_monthly_timeline(
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get incident timeline by month"""
    query = db.query(Incident)
    if country:
        query = query.join(RestrictedArea).filter(
            RestrictedArea.country == country
        )

    # Group by year-month
    from sqlalchemy import func as sql_func
    results = query.with_entities(
        sql_func.strftime("%Y-%m", Incident.sighting_date).label("month"),
        sql_func.count(Incident.id).label("count")
    ).group_by("month").order_by("month").all()

    return [
        {"month": month, "incidents": count}
        for month, count in results
    ]

@router.get("/intelligence/drone-relationships")
async def get_drone_relationships(db: Session = Depends(get_db)):
    """Get all drone type to incident relationships with identification evidence"""
    incidents = db.query(Incident).filter(
        Incident.drone_type_id.isnot(None)
    ).all()

    relationships = []
    for incident in incidents:
        relationships.append({
            "incident_id": incident.id,
            "incident_title": incident.title,
            "sighting_date": incident.sighting_date,
            "location": incident.restricted_area.name if incident.restricted_area else "Unknown",
            "drone_type_id": incident.drone_type_id,
            "drone_model": incident.drone_type.model if incident.drone_type else "Unknown",
            "identification_method": incident.identification_method,
            "identification_confidence": incident.identification_confidence,
            "identification_evidence": incident.identification_evidence,
            "identified_by": incident.identified_by,
            "source": incident.source,
            "suspected_operator": incident.suspected_operator
        })

    return relationships

@router.get("/intelligence/drone-type/{drone_type_id}/evidence")
async def get_drone_type_evidence(
    drone_type_id: int,
    db: Session = Depends(get_db)
):
    """Get all evidence linking a drone type to incidents"""
    drone = db.query(DroneType).filter(DroneType.id == drone_type_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone type not found")

    incidents = db.query(Incident).filter(
        Incident.drone_type_id == drone_type_id
    ).order_by(Incident.sighting_date.desc()).all()

    evidence_summary = {
        "drone_type": drone.model,
        "total_incidents": len(incidents),
        "identification_methods": {},
        "evidence_by_confidence": {
            "high": [],      # 0.7+
            "medium": [],    # 0.4-0.7
            "low": []        # <0.4
        },
        "identified_by": {}
    }

    for incident in incidents:
        # Count identification methods
        method = incident.identification_method or "unknown"
        evidence_summary["identification_methods"][method] = \
            evidence_summary["identification_methods"].get(method, 0) + 1

        # Group by confidence
        confidence = incident.identification_confidence or 0.5
        confidence_level = "high" if confidence >= 0.7 else "medium" if confidence >= 0.4 else "low"

        evidence_summary["evidence_by_confidence"][confidence_level].append({
            "incident_id": incident.id,
            "title": incident.title,
            "date": incident.sighting_date,
            "location": incident.restricted_area.name if incident.restricted_area else "Unknown",
            "confidence": confidence,
            "method": method,
            "evidence": incident.identification_evidence,
            "source": incident.source
        })

        # Count who identified it
        identified = incident.identified_by or "Unknown"
        evidence_summary["identified_by"][identified] = \
            evidence_summary["identified_by"].get(identified, 0) + 1

    return evidence_summary

@router.get("/intelligence/unconfirmed-characteristics")
async def get_unconfirmed_characteristics(db: Session = Depends(get_db)):
    """Get all incidents with unconfirmed drone types but observed characteristics"""
    incidents = db.query(Incident).filter(
        Incident.drone_characteristics.isnot(None)
    ).order_by(Incident.sighting_date.desc()).all()

    results = []
    for incident in incidents:
        # Get all drone types for potential matching
        drone_types = db.query(DroneType).all()
        potential_matches = []

        # Simple keyword matching on characteristics
        characteristics_lower = (incident.drone_characteristics or "").lower()
        for drone in drone_types:
            model_lower = drone.model.lower()
            payload_lower = (drone.payload_type or "").lower()
            notes_lower = (drone.notes or "").lower()

            # Check if drone details appear in characteristics
            match_score = 0
            if any(keyword in characteristics_lower for keyword in model_lower.split()):
                match_score += 3
            if drone.payload_type and drone.payload_type.lower() in characteristics_lower:
                match_score += 2
            # Check for general drone type keywords
            if "quad" in characteristics_lower and "quadcopter" in notes_lower.lower():
                match_score += 1
            if "fixed wing" in characteristics_lower and "fixed wing" in notes_lower.lower():
                match_score += 1
            if "multi-rotor" in characteristics_lower and "multi" in notes_lower.lower():
                match_score += 1

            if match_score > 0:
                potential_matches.append({
                    "drone_type_id": drone.id,
                    "model": drone.model,
                    "manufacturer": drone.manufacturer,
                    "match_score": match_score,
                    "notes": drone.notes
                })

        # Sort by match score
        potential_matches = sorted(potential_matches, key=lambda x: x["match_score"], reverse=True)

        results.append({
            "incident_id": incident.id,
            "title": incident.title,
            "sighting_date": incident.sighting_date,
            "location": incident.restricted_area.name if incident.restricted_area else "Unknown",
            "characteristics": incident.drone_characteristics,
            "characteristics_sources": incident.drone_characteristics_sources,
            "confirmed_drone_type_id": incident.drone_type_id,
            "potential_matches": potential_matches[:5]  # Top 5 matches
        })

    return results


@router.get("/{incident_id}/tactical-assessment")
async def get_tactical_assessment(incident_id: int, db: Session = Depends(get_db)):
    """
    Generate comprehensive tactical intelligence assessment for an incident
    Includes AI-powered analysis, threat level, attribution, and recommended actions
    """
    from backend.tactical_intel import generate_tactical_assessment, find_related_incidents

    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get restricted area if available
    restricted_area = None
    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            restricted_area = {
                "id": area.id,
                "name": area.name,
                "area_type": area.area_type,
                "country": area.country,
                "latitude": area.latitude,
                "longitude": area.longitude,
                "threat_level": area.threat_level
            }

    # Find related incidents
    related_incidents = find_related_incidents(
        incident_id=incident.id,
        incident_lat=incident.latitude,
        incident_lon=incident.longitude,
        incident_date=datetime.combine(incident.sighting_date, datetime.min.time()),
        restricted_area_id=incident.restricted_area_id,
        db=db
    )

    # Prepare incident data
    incident_data = {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "sighting_date": incident.sighting_date,
        "sighting_time": incident.sighting_time,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "altitude_m": incident.altitude_m,
        "duration_minutes": incident.duration_minutes,
        "drone_description": incident.drone_description,
        "source": incident.source
    }

    # Generate assessment
    assessment = generate_tactical_assessment(
        incident=incident_data,
        restricted_area=restricted_area,
        related_incidents=related_incidents,
        db=db
    )

    return {
        "incident_id": incident_id,
        "assessment": assessment,
        "related_incidents_count": len(related_incidents),
        "restricted_area": restricted_area,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/{incident_id}/related")
async def get_related_incidents(
    incident_id: int,
    radius_km: float = Query(50.0, ge=1.0, le=500.0),
    time_window_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Find incidents related to this one based on location and time proximity
    """
    from backend.tactical_intel import find_related_incidents

    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Find related
    related = find_related_incidents(
        incident_id=incident.id,
        incident_lat=incident.latitude,
        incident_lon=incident.longitude,
        incident_date=datetime.combine(incident.sighting_date, datetime.min.time()),
        restricted_area_id=incident.restricted_area_id,
        db=db,
        radius_km=radius_km,
        time_window_days=time_window_days
    )

    return {
        "incident_id": incident_id,
        "total_related": len(related),
        "search_radius_km": radius_km,
        "time_window_days": time_window_days,
        "related_incidents": related
    }


@router.get("/{incident_id}/sources")
async def get_incident_sources(incident_id: int, db: Session = Depends(get_db)):
    """
    Get all source articles/reports related to this incident
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    sources = []

    # Add primary source
    if incident.source_url:
        sources.append({
            "type": "primary",
            "name": incident.primary_source_name or incident.source,
            "url": incident.source_url,
            "credibility": incident.primary_source_credibility,
            "description": "Primary source for this incident"
        })

    # Add secondary sources
    if incident.secondary_sources:
        try:
            secondary = json.loads(incident.secondary_sources) if isinstance(incident.secondary_sources, str) else incident.secondary_sources
            if isinstance(secondary, list):
                for src in secondary:
                    if isinstance(src, dict):
                        sources.append({
                            "type": "secondary",
                            "name": src.get("name", "Unknown"),
                            "url": src.get("url", ""),
                            "credibility": src.get("credibility", 0.5),
                            "description": src.get("description", "")
                        })
        except Exception as e:
            print(f"Error parsing secondary sources: {e}")

    # Try to find related news articles from news_articles table
    try:
        # Search for articles with similar title or location
        from backend.models import NewsArticle
        news_articles = db.query(NewsArticle).filter(
            or_(
                NewsArticle.title.contains(incident.title[:50]),
                and_(
                    NewsArticle.pub_date >= incident.sighting_date - timedelta(days=2),
                    NewsArticle.pub_date <= incident.sighting_date + timedelta(days=2)
                )
            )
        ).limit(10).all()

        for article in news_articles:
            sources.append({
                "type": "news",
                "name": article.source,
                "url": article.url,
                "title": article.title,
                "published": article.pub_date.isoformat() if article.pub_date else None,
                "summary": article.summary[:200] if article.summary else ""
            })
    except Exception as e:
        print(f"Error fetching news articles: {e}")

    return {
        "incident_id": incident_id,
        "total_sources": len(sources),
        "sources": sources
    }
