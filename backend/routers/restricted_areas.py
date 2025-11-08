from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.models import RestrictedArea, Incident

router = APIRouter()

class RestrictedAreaCreate(BaseModel):
    name: str
    area_type: str  # airport, military_base, nuclear_facility, government
    country: str
    latitude: float
    longitude: float
    radius_km: Optional[float] = 5.0
    threat_level: Optional[int] = 3
    description: Optional[str] = None

class RestrictedAreaUpdate(BaseModel):
    name: Optional[str] = None
    area_type: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    threat_level: Optional[int] = None
    description: Optional[str] = None

@router.get("/")
async def list_restricted_areas(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country: Optional[str] = None,
    area_type: Optional[str] = None,
    order_by: str = "name"
):
    """List all restricted areas"""
    query = db.query(RestrictedArea)

    if country:
        query = query.filter(RestrictedArea.country == country)
    if area_type:
        query = query.filter(RestrictedArea.area_type == area_type)

    if order_by == "name":
        query = query.order_by(RestrictedArea.name)
    elif order_by == "threat":
        query = query.order_by(RestrictedArea.threat_level.desc())
    elif order_by == "incidents":
        query = query.outerjoin(Incident).group_by(RestrictedArea.id).order_by(
            func.count(Incident.id).desc()
        )

    total = query.count()
    areas = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "restricted_areas": areas
    }

@router.get("/{area_id}")
async def get_restricted_area(area_id: int, db: Session = Depends(get_db)):
    """Get restricted area details"""
    area = db.query(RestrictedArea).filter(
        RestrictedArea.id == area_id
    ).first()
    if not area:
        raise HTTPException(status_code=404, detail="Restricted area not found")
    return area

@router.get("/{area_id}/incidents")
async def get_area_incidents(
    area_id: int,
    db: Session = Depends(get_db)
):
    """Get all incidents near this restricted area"""
    area = db.query(RestrictedArea).filter(
        RestrictedArea.id == area_id
    ).first()
    if not area:
        raise HTTPException(status_code=404, detail="Restricted area not found")

    incidents = db.query(Incident).filter(
        Incident.restricted_area_id == area_id
    ).order_by(Incident.sighting_date.desc()).all()

    return {
        "restricted_area": area,
        "incidents": incidents,
        "total_incidents": len(incidents)
    }

@router.post("/")
async def create_restricted_area(
    area: RestrictedAreaCreate,
    db: Session = Depends(get_db)
):
    """Create new restricted area"""
    db_area = RestrictedArea(**area.dict())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

@router.put("/{area_id}")
async def update_restricted_area(
    area_id: int,
    area: RestrictedAreaUpdate,
    db: Session = Depends(get_db)
):
    """Update restricted area"""
    db_area = db.query(RestrictedArea).filter(
        RestrictedArea.id == area_id
    ).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Restricted area not found")

    update_data = area.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_area, field, value)

    db.commit()
    db.refresh(db_area)
    return db_area

@router.delete("/{area_id}")
async def delete_restricted_area(area_id: int, db: Session = Depends(get_db)):
    """Delete restricted area"""
    db_area = db.query(RestrictedArea).filter(
        RestrictedArea.id == area_id
    ).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Restricted area not found")

    db.delete(db_area)
    db.commit()
    return {"deleted": True}

@router.get("/analysis/threat-matrix")
async def threat_matrix(db: Session = Depends(get_db)):
    """Get threat assessment matrix for all areas"""
    areas = db.query(RestrictedArea).all()

    threat_assessments = []
    for area in areas:
        incident_count = db.query(Incident).filter(
            Incident.restricted_area_id == area.id
        ).count()

        avg_confidence = db.query(
            func.avg(Incident.confidence_score)
        ).filter(
            Incident.restricted_area_id == area.id
        ).scalar() or 0

        # Get most common drone type targeting this area
        most_common_drone = db.query(
            Incident.drone_description
        ).filter(
            Incident.restricted_area_id == area.id
        ).group_by(Incident.drone_description).order_by(
            func.count(Incident.id).desc()
        ).first()

        threat_assessments.append({
            "area_id": area.id,
            "name": area.name,
            "country": area.country,
            "area_type": area.area_type,
            "threat_level": area.threat_level,
            "incident_count": incident_count,
            "avg_confidence": round(avg_confidence, 2),
            "most_common_drone": most_common_drone[0] if most_common_drone else None,
            "location": {
                "latitude": area.latitude,
                "longitude": area.longitude,
                "radius_km": area.radius_km
            }
        })

    return sorted(threat_assessments, key=lambda x: x["incident_count"], reverse=True)
