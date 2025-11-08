from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.models import DroneType, Incident

router = APIRouter()

class DroneTypeCreate(BaseModel):
    model: str
    manufacturer: str
    country_of_origin: str
    range_km: Optional[int] = None
    endurance_minutes: Optional[int] = None
    max_altitude_m: Optional[int] = None
    payload_type: Optional[str] = None
    difficulty_intercept: Optional[int] = 5
    estimated_cost_usd: Optional[int] = None
    notes: Optional[str] = None

class DroneTypeUpdate(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    range_km: Optional[int] = None
    endurance_minutes: Optional[int] = None
    max_altitude_m: Optional[int] = None
    payload_type: Optional[str] = None
    difficulty_intercept: Optional[int] = None
    estimated_cost_usd: Optional[int] = None
    notes: Optional[str] = None

class DroneTypeResponse(BaseModel):
    id: int
    model: str
    manufacturer: str
    country_of_origin: str
    range_km: Optional[int]
    endurance_minutes: Optional[int]
    max_altitude_m: Optional[int]
    payload_type: Optional[str]
    difficulty_intercept: Optional[int]
    estimated_cost_usd: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True

@router.get("/")
async def list_drone_types(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country: Optional[str] = None,
    payload_type: Optional[str] = None,
    order_by: str = "model"
):
    """List all drone types"""
    query = db.query(DroneType)

    if country:
        query = query.filter(DroneType.country_of_origin == country)
    if payload_type:
        query = query.filter(DroneType.payload_type == payload_type)

    if order_by == "model":
        query = query.order_by(DroneType.model)
    elif order_by == "incidents":
        # Join with incidents to count
        query = query.outerjoin(Incident).group_by(DroneType.id).order_by(
            func.count(Incident.id).desc()
        )
    elif order_by == "cost":
        query = query.order_by(DroneType.estimated_cost_usd.desc())
    elif order_by == "difficulty":
        query = query.order_by(DroneType.difficulty_intercept.desc())

    total = query.count()
    drone_types = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "drone_types": drone_types
    }

@router.get("/{drone_type_id}")
async def get_drone_type(drone_type_id: int, db: Session = Depends(get_db)):
    """Get drone type details"""
    drone_type = db.query(DroneType).filter(
        DroneType.id == drone_type_id
    ).first()
    if not drone_type:
        raise HTTPException(status_code=404, detail="Drone type not found")
    return drone_type

@router.get("/{drone_type_id}/incidents")
async def get_drone_incidents(
    drone_type_id: int,
    db: Session = Depends(get_db)
):
    """Get all incidents involving this drone type"""
    drone_type = db.query(DroneType).filter(
        DroneType.id == drone_type_id
    ).first()
    if not drone_type:
        raise HTTPException(status_code=404, detail="Drone type not found")

    incidents = db.query(Incident).filter(
        Incident.drone_type_id == drone_type_id
    ).order_by(Incident.sighting_date.desc()).all()

    return {
        "drone_type": drone_type,
        "incidents": incidents,
        "total_incidents": len(incidents)
    }

@router.post("/")
async def create_drone_type(
    drone_type: DroneTypeCreate,
    db: Session = Depends(get_db)
):
    """Create new drone type"""
    # Check if already exists
    existing = db.query(DroneType).filter(
        DroneType.model == drone_type.model
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Drone type already exists")

    db_drone_type = DroneType(**drone_type.dict())
    db.add(db_drone_type)
    db.commit()
    db.refresh(db_drone_type)
    return db_drone_type

@router.put("/{drone_type_id}")
async def update_drone_type(
    drone_type_id: int,
    drone_type: DroneTypeUpdate,
    db: Session = Depends(get_db)
):
    """Update drone type"""
    db_drone_type = db.query(DroneType).filter(
        DroneType.id == drone_type_id
    ).first()
    if not db_drone_type:
        raise HTTPException(status_code=404, detail="Drone type not found")

    update_data = drone_type.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_drone_type, field, value)

    db.commit()
    db.refresh(db_drone_type)
    return db_drone_type

@router.delete("/{drone_type_id}")
async def delete_drone_type(drone_type_id: int, db: Session = Depends(get_db)):
    """Delete drone type"""
    db_drone_type = db.query(DroneType).filter(
        DroneType.id == drone_type_id
    ).first()
    if not db_drone_type:
        raise HTTPException(status_code=404, detail="Drone type not found")

    db.delete(db_drone_type)
    db.commit()
    return {"deleted": True}

@router.get("/analysis/threat-assessment")
async def threat_assessment(db: Session = Depends(get_db)):
    """Threat assessment of drone types based on incidents and specs"""
    drone_types = db.query(DroneType).all()

    assessments = []
    for drone in drone_types:
        incident_count = db.query(Incident).filter(
            Incident.drone_type_id == drone.id
        ).count()

        # Threat score calculation
        threat_score = (
            (incident_count * 10) +  # Frequency
            ((drone.difficulty_intercept or 5) * 5) +  # Interception difficulty
            ((drone.range_km or 0) / 2) +  # Range capability
            (20 if drone.payload_type == "signals_intelligence" else 5)  # Payload
        ) / 40

        threat_score = min(10, max(0, threat_score))

        assessments.append({
            "drone_type": drone.model,
            "manufacturer": drone.manufacturer,
            "country_of_origin": drone.country_of_origin,
            "incident_count": incident_count,
            "threat_score": round(threat_score, 1),
            "difficulty_intercept": drone.difficulty_intercept,
            "payload_type": drone.payload_type,
            "specifications": {
                "range_km": drone.range_km,
                "endurance_minutes": drone.endurance_minutes,
                "max_altitude_m": drone.max_altitude_m,
                "estimated_cost": drone.estimated_cost_usd
            }
        })

    return sorted(assessments, key=lambda x: x["threat_score"], reverse=True)
