from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.database import get_db
from backend.models import Intervention, Incident

router = APIRouter()

class InterventionCreate(BaseModel):
    incident_id: int
    intervention_type: str  # jamming, netting, kinetic, interception, unknown
    response_time_minutes: Optional[int] = None
    outcome: str  # success, partial, failed, unknown, not_attempted
    success_rate: Optional[float] = None
    notes: Optional[str] = None

class InterventionUpdate(BaseModel):
    intervention_type: Optional[str] = None
    response_time_minutes: Optional[int] = None
    outcome: Optional[str] = None
    success_rate: Optional[float] = None
    notes: Optional[str] = None

@router.get("/")
async def list_interventions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    intervention_type: Optional[str] = None,
    outcome: Optional[str] = None,
    order_by: str = "recent"
):
    """List all interventions"""
    query = db.query(Intervention)

    if intervention_type:
        query = query.filter(Intervention.intervention_type == intervention_type)
    if outcome:
        query = query.filter(Intervention.outcome == outcome)

    if order_by == "recent":
        query = query.order_by(Intervention.created_at.desc())
    elif order_by == "response_time":
        query = query.filter(Intervention.response_time_minutes.isnot(None)).order_by(
            Intervention.response_time_minutes
        )

    total = query.count()
    interventions = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "interventions": interventions
    }

@router.get("/{intervention_id}")
async def get_intervention(intervention_id: int, db: Session = Depends(get_db)):
    """Get intervention details"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention

@router.post("/")
async def create_intervention(
    intervention: InterventionCreate,
    db: Session = Depends(get_db)
):
    """Create new intervention record"""
    # Verify incident exists
    incident = db.query(Incident).filter(
        Incident.id == intervention.incident_id
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    db_intervention = Intervention(**intervention.dict())
    db.add(db_intervention)
    db.commit()
    db.refresh(db_intervention)
    return db_intervention

@router.put("/{intervention_id}")
async def update_intervention(
    intervention_id: int,
    intervention: InterventionUpdate,
    db: Session = Depends(get_db)
):
    """Update intervention"""
    db_intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not db_intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    update_data = intervention.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_intervention, field, value)

    db_intervention.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_intervention)
    return db_intervention

@router.delete("/{intervention_id}")
async def delete_intervention(intervention_id: int, db: Session = Depends(get_db)):
    """Delete intervention record"""
    db_intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not db_intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    db.delete(db_intervention)
    db.commit()
    return {"deleted": True}

@router.get("/analysis/effectiveness")
async def intervention_effectiveness(db: Session = Depends(get_db)):
    """Analyze effectiveness of different intervention types"""

    intervention_types = db.query(Intervention.intervention_type).distinct().all()
    results = []

    for (itype,) in intervention_types:
        total = db.query(Intervention).filter(
            Intervention.intervention_type == itype
        ).count()

        successful = db.query(Intervention).filter(
            Intervention.intervention_type == itype,
            Intervention.outcome == "success"
        ).count()

        partial = db.query(Intervention).filter(
            Intervention.intervention_type == itype,
            Intervention.outcome == "partial"
        ).count()

        failed = db.query(Intervention).filter(
            Intervention.intervention_type == itype,
            Intervention.outcome == "failed"
        ).count()

        avg_response_time = db.query(
            func.avg(Intervention.response_time_minutes)
        ).filter(
            Intervention.intervention_type == itype,
            Intervention.response_time_minutes.isnot(None)
        ).scalar() or 0

        success_rate = (successful / total * 100) if total > 0 else 0

        results.append({
            "intervention_type": itype,
            "total": total,
            "successful": successful,
            "partial": partial,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "avg_response_time_minutes": round(avg_response_time, 1)
        })

    return sorted(results, key=lambda x: x["success_rate"], reverse=True)

@router.get("/analysis/response-times")
async def response_time_analysis(db: Session = Depends(get_db)):
    """Analyze response times for interventions"""

    interventions = db.query(Intervention).filter(
        Intervention.response_time_minutes.isnot(None)
    ).all()

    if not interventions:
        return {"message": "No intervention response time data available"}

    times = [i.response_time_minutes for i in interventions]
    times.sort()

    avg = sum(times) / len(times)
    median = times[len(times) // 2]
    min_time = min(times)
    max_time = max(times)

    # Percentiles
    p10_idx = int(len(times) * 0.1)
    p90_idx = int(len(times) * 0.9)

    return {
        "total_interventions_tracked": len(times),
        "average_response_time": round(avg, 1),
        "median_response_time": median,
        "min_response_time": min_time,
        "max_response_time": max_time,
        "p10_response_time": times[p10_idx],
        "p90_response_time": times[p90_idx]
    }

@router.get("/analysis/by-incident-type")
async def interventions_by_drone_type(db: Session = Depends(get_db)):
    """Analyze intervention effectiveness by drone type"""

    from backend.models import Incident, DroneType

    results = db.query(
        DroneType.model,
        Intervention.intervention_type,
        Intervention.outcome,
        func.count(Intervention.id).label("count")
    ).join(Intervention, Intervention.incident_id == Incident.id).join(
        DroneType, Incident.drone_type_id == DroneType.id
    ).group_by(
        DroneType.model,
        Intervention.intervention_type,
        Intervention.outcome
    ).all()

    # Group results
    effectiveness_matrix = {}
    for model, itype, outcome, count in results:
        key = f"{model} - {itype}"
        if key not in effectiveness_matrix:
            effectiveness_matrix[key] = {
                "drone_model": model,
                "intervention_type": itype,
                "success": 0,
                "partial": 0,
                "failed": 0,
                "unknown": 0
            }
        effectiveness_matrix[key][outcome] = count

    return list(effectiveness_matrix.values())
