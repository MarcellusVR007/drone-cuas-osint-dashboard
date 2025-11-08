from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional, List
from backend.database import get_db
from backend.models import Incident, RestrictedArea, DroneType

router = APIRouter()

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
    distance_to_restricted_m: Optional[int]
    duration_minutes: Optional[int]
    source: str
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

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "incidents": incidents
    }

@router.get("/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get incident details"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/")
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Create new incident report"""
    try:
        # Verify drone type exists if provided
        if incident.drone_type_id:
            drone = db.query(DroneType).filter(
                DroneType.id == incident.drone_type_id
            ).first()
            if not drone:
                raise HTTPException(status_code=404, detail="Drone type not found")

        # Verify restricted area exists if provided
        if incident.restricted_area_id:
            area = db.query(RestrictedArea).filter(
                RestrictedArea.id == incident.restricted_area_id
            ).first()
            if not area:
                raise HTTPException(status_code=404, detail="Restricted area not found")

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
