from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.database import get_db
from backend.models import Pattern, Incident

router = APIRouter()

class PatternCreate(BaseModel):
    name: str
    description: Optional[str] = None
    pattern_type: str  # temporal, spatial, drone_type, operator
    incident_count: Optional[int] = 1
    primary_location: Optional[str] = None
    primary_drone_type: Optional[str] = None
    suspected_purpose: Optional[str] = None
    suspected_operator: Optional[str] = None
    confidence_score: Optional[float] = 0.5
    notes: Optional[str] = None

class PatternUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pattern_type: Optional[str] = None
    incident_count: Optional[int] = None
    primary_location: Optional[str] = None
    primary_drone_type: Optional[str] = None
    suspected_purpose: Optional[str] = None
    suspected_operator: Optional[str] = None
    confidence_score: Optional[float] = None
    notes: Optional[str] = None

@router.get("/")
async def list_patterns(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    pattern_type: Optional[str] = None,
    order_by: str = "recent"
):
    """List detected patterns"""
    query = db.query(Pattern)

    if pattern_type:
        query = query.filter(Pattern.pattern_type == pattern_type)

    if order_by == "recent":
        query = query.order_by(Pattern.updated_at.desc())
    elif order_by == "confidence":
        query = query.order_by(Pattern.confidence_score.desc())
    elif order_by == "incidents":
        query = query.order_by(Pattern.incident_count.desc())

    total = query.count()
    patterns = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "patterns": patterns
    }

@router.get("/{pattern_id}")
async def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """Get pattern details"""
    pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern

@router.get("/{pattern_id}/incidents")
async def get_pattern_incidents(
    pattern_id: int,
    db: Session = Depends(get_db)
):
    """Get all incidents in this pattern"""
    pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    incidents = db.query(Incident).filter(
        Incident.pattern_id == pattern_id
    ).order_by(Incident.sighting_date.desc()).all()

    return {
        "pattern": pattern,
        "incidents": incidents,
        "total_incidents": len(incidents)
    }

@router.post("/")
async def create_pattern(
    pattern: PatternCreate,
    db: Session = Depends(get_db)
):
    """Create new pattern"""
    db_pattern = Pattern(**pattern.dict())
    db.add(db_pattern)
    db.commit()
    db.refresh(db_pattern)
    return db_pattern

@router.put("/{pattern_id}")
async def update_pattern(
    pattern_id: int,
    pattern: PatternUpdate,
    db: Session = Depends(get_db)
):
    """Update pattern"""
    db_pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    update_data = pattern.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pattern, field, value)

    db_pattern.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_pattern)
    return db_pattern

@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """Delete pattern"""
    db_pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    db.delete(db_pattern)
    db.commit()
    return {"deleted": True}

@router.post("/auto-detect")
async def auto_detect_patterns(db: Session = Depends(get_db)):
    """Automatically detect patterns from incidents"""
    results = []

    # Pattern 1: Same location targeted multiple times
    location_patterns = db.query(
        Incident.restricted_area_id,
        func.count(Incident.id).label("count")
    ).filter(Incident.restricted_area_id.isnot(None)).group_by(
        Incident.restricted_area_id
    ).having(func.count(Incident.id) >= 3).all()

    for area_id, count in location_patterns:
        from backend.models import RestrictedArea
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == area_id
        ).first()

        existing = db.query(Pattern).filter(
            Pattern.pattern_type == "spatial",
            Pattern.primary_location == area.name
        ).first()

        if not existing:
            pattern = Pattern(
                name=f"Repeated targeting of {area.name}",
                description=f"{count} incidents near {area.name}",
                pattern_type="spatial",
                incident_count=count,
                primary_location=area.name,
                suspected_purpose="reconnaissance",
                confidence_score=0.7
            )
            db.add(pattern)
            results.append(f"Detected spatial pattern: {area.name} ({count} incidents)")

    # Pattern 2: Same drone type used multiple times
    drone_patterns = db.query(
        Incident.drone_description,
        func.count(Incident.id).label("count")
    ).filter(Incident.drone_description.isnot(None)).group_by(
        Incident.drone_description
    ).having(func.count(Incident.id) >= 3).all()

    for drone_desc, count in drone_patterns:
        existing = db.query(Pattern).filter(
            Pattern.pattern_type == "drone_type",
            Pattern.primary_drone_type == drone_desc
        ).first()

        if not existing:
            pattern = Pattern(
                name=f"Repeated use of {drone_desc}",
                description=f"{count} incidents using {drone_desc}",
                pattern_type="drone_type",
                incident_count=count,
                primary_drone_type=drone_desc,
                confidence_score=0.6
            )
            db.add(pattern)
            results.append(f"Detected drone pattern: {drone_desc} ({count} incidents)")

    # Pattern 3: Temporal patterns - multiple incidents on same date (coordinated campaigns)
    from sqlalchemy import cast, Date
    temporal_patterns = db.query(
        cast(Incident.sighting_date, Date).label("date"),
        func.count(Incident.id).label("count")
    ).filter(Incident.sighting_date.isnot(None)).group_by(
        cast(Incident.sighting_date, Date)
    ).having(func.count(Incident.id) >= 2).all()

    for sighting_date, count in temporal_patterns:
        # Check if any incident on this date has "coordinated" in description
        coordinated_incidents = db.query(Incident).filter(
            cast(Incident.sighting_date, Date) == sighting_date,
            Incident.description.ilike("%coordinated%")
        ).all()

        if coordinated_incidents:
            date_str = sighting_date.strftime("%Y-%m-%d")
            existing = db.query(Pattern).filter(
                Pattern.pattern_type == "temporal",
                Pattern.name.ilike(f"%{date_str}%")
            ).first()

            if not existing:
                pattern = Pattern(
                    name=f"Coordinated campaign - {date_str}",
                    description=f"{count} incidents on {date_str} - coordinated wave detected",
                    pattern_type="temporal",
                    incident_count=count,
                    confidence_score=0.8
                )
                db.add(pattern)
                results.append(f"Detected temporal pattern: Coordinated campaign on {date_str} ({count} incidents)")

    db.commit()
    return {
        "detected_patterns": len(results),
        "patterns": results
    }
