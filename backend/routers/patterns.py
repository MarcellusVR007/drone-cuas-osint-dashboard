from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel
from typing import Optional, List, Dict
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

@router.get("/strategic-analysis")
async def get_strategic_analysis(db: Session = Depends(get_db)):
    """Get strategic analysis with operational classification breakdown"""

    # Get operational class distribution
    query = text("""
        SELECT
            operational_class,
            COUNT(*) as count,
            GROUP_CONCAT(DISTINCT drone_description) as drone_types
        FROM incidents
        WHERE operational_class IS NOT NULL
        GROUP BY operational_class
    """)
    result = db.execute(query)
    classification_breakdown = [dict(row._mapping) for row in result]

    # Get all classified incidents with details
    query = text("""
        SELECT
            i.id,
            i.sighting_date,
            i.title,
            i.operational_class,
            i.strategic_assessment,
            i.launch_analysis,
            i.latitude,
            i.longitude,
            i.drone_description,
            i.suspected_operator,
            dt.model as drone_type_model,
            dt.range_km as drone_range,
            ra.name as restricted_area_name
        FROM incidents i
        LEFT JOIN drone_types dt ON i.drone_type_id = dt.id
        LEFT JOIN restricted_areas ra ON i.restricted_area_id = ra.id
        WHERE i.operational_class IS NOT NULL
        ORDER BY i.sighting_date DESC
    """)
    result = db.execute(query)
    classified_incidents = [dict(row._mapping) for row in result]

    # Get state actor incidents (Orlan, military)
    state_actors = [inc for inc in classified_incidents if inc['operational_class'] == 'STATE_ACTOR_PROFESSIONAL']

    # Get recruited local incidents (Telegram bounties)
    recruited_locals = [inc for inc in classified_incidents if inc['operational_class'] == 'RECRUITED_LOCAL']

    return {
        "classification_breakdown": classification_breakdown,
        "state_actor_incidents": state_actors,
        "recruited_local_incidents": recruited_locals,
        "all_classified_incidents": classified_incidents,
        "total_classified": len(classified_incidents)
    }

@router.get("/counter-measures")
async def get_counter_measures(db: Session = Depends(get_db)):
    """Get all available counter-measures"""

    query = text("""
        SELECT * FROM counter_measures
        ORDER BY type, cost_estimate_eur
    """)
    result = db.execute(query)
    counter_measures = [dict(row._mapping) for row in result]

    # Group by type
    by_type = {}
    for cm in counter_measures:
        cm_type = cm['type']
        if cm_type not in by_type:
            by_type[cm_type] = []
        by_type[cm_type].append(cm)

    return {
        "counter_measures": counter_measures,
        "by_type": by_type,
        "total": len(counter_measures)
    }

@router.get("/orlan-analysis")
async def get_orlan_analysis(db: Session = Depends(get_db)):
    """Get detailed analysis of Orlan/military drone incidents with launch predictions"""

    query = text("""
        SELECT
            i.*,
            dt.model as drone_type_model,
            dt.range_km as drone_range,
            dt.max_altitude_m,
            dt.endurance_minutes,
            ra.name as target_name,
            ra.latitude as target_lat,
            ra.longitude as target_lon
        FROM incidents i
        LEFT JOIN drone_types dt ON i.drone_type_id = dt.id
        LEFT JOIN restricted_areas ra ON i.restricted_area_id = ra.id
        WHERE i.operational_class = 'STATE_ACTOR_PROFESSIONAL'
        ORDER BY i.sighting_date DESC
    """)
    result = db.execute(query)
    orlan_incidents = [dict(row._mapping) for row in result]

    # For each Orlan incident, calculate possible launch zones
    for incident in orlan_incidents:
        if incident['drone_range']:
            # Create a circular zone around sighting location
            incident['possible_launch_zone'] = {
                "center_lat": incident['latitude'],
                "center_lon": incident['longitude'],
                "radius_km": incident['drone_range'],
                "analysis": incident['launch_analysis']
            }

    return {
        "orlan_incidents": orlan_incidents,
        "total": len(orlan_incidents),
        "analysis_summary": "Orlan-10 incidents require maritime or cross-border launch analysis. Check AIS vessel tracking and border proximity."
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

    # Pattern 3: Temporal patterns - coordinated campaigns (incidents with "coordinated" in description)
    from sqlalchemy import cast, Date
    coordinated_incidents = db.query(Incident).filter(
        Incident.sighting_date.isnot(None),
        Incident.description.ilike("%coordinated%")
    ).all()

    for incident in coordinated_incidents:
        # Extract date as string
        if hasattr(incident.sighting_date, 'date'):
            sighting_date = incident.sighting_date.date()
            date_str = sighting_date.strftime("%Y-%m-%d")
        else:
            sighting_date = incident.sighting_date
            date_str = str(sighting_date)

        # Check if pattern already exists for this date
        existing = db.query(Pattern).filter(
            Pattern.pattern_type == "temporal",
            Pattern.name.ilike(f"%{date_str}%")
        ).first()

        if not existing:
            # Count total incidents on this date
            incidents_on_date = db.query(Incident).filter(
                cast(Incident.sighting_date, Date) == sighting_date
            ).count()

            incident_count = incidents_on_date if incidents_on_date > 0 else 1

            pattern = Pattern(
                name=f"Coordinated campaign - {date_str}",
                description=f"{incident_count} incident(s) on {date_str} - coordinated campaign detected",
                pattern_type="temporal",
                incident_count=incident_count,
                confidence_score=0.8
            )
            db.add(pattern)
            results.append(f"Detected temporal pattern: Coordinated campaign on {date_str} ({incident_count} incident(s))")

    db.commit()
    return {
        "detected_patterns": len(results),
        "patterns": results
    }

@router.get("/counter-measures/incident/{incident_id}")
async def get_incident_recommendations(incident_id: int, db: Session = Depends(get_db)):
    """Get counter-measure recommendations for specific incident"""

    # Check if incident exists
    incident_check = db.execute(text("SELECT id FROM incidents WHERE id = :id"), {"id": incident_id})
    if not incident_check.fetchone():
        raise HTTPException(status_code=404, detail="Incident not found")

    query = text("""
        SELECT
            ir.*,
            cm.name as cm_name,
            cm.type as cm_type,
            cm.description as cm_description,
            cm.effective_against,
            cm.range_km,
            cm.deployment_time_hours,
            cm.cost_estimate_eur,
            cm.requires_authorization,
            cm.mobile,
            cm.specifications,
            i.title as incident_title,
            i.operational_class,
            i.strategic_assessment
        FROM incident_recommendations ir
        JOIN counter_measures cm ON ir.counter_measure_id = cm.id
        JOIN incidents i ON ir.incident_id = i.id
        WHERE ir.incident_id = :incident_id
        ORDER BY
            CASE ir.priority
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END
    """)
    result = db.execute(query, {"incident_id": incident_id})
    recommendations = [dict(row._mapping) for row in result]

    return {
        "incident_id": incident_id,
        "recommendations": recommendations,
        "total": len(recommendations)
    }
