from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.database import get_db
from backend.models import Incident, Intervention, DroneType, RestrictedArea, Pattern

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "OSINT CUAS Dashboard"
    }

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""

    # Total counts
    total_incidents = db.query(Incident).count()
    total_interventions = db.query(Intervention).count()
    total_patterns = db.query(Pattern).count()
    total_restricted_areas = db.query(RestrictedArea).count()
    total_drone_types = db.query(DroneType).count()

    # Recent incidents (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_incidents = db.query(Incident).filter(
        Incident.report_date >= thirty_days_ago
    ).count()

    # Intervention success rate
    successful_interventions = db.query(Intervention).filter(
        Intervention.outcome == "success"
    ).count()
    intervention_success_rate = (
        (successful_interventions / total_interventions * 100)
        if total_interventions > 0 else 0
    )

    # Most common drone types in incidents
    most_common_drones = db.query(
        DroneType.model,
        func.count(Incident.id).label("count")
    ).join(Incident).group_by(DroneType.id).order_by(
        func.count(Incident.id).desc()
    ).limit(5).all()

    # Most targeted restricted areas
    most_targeted_areas = db.query(
        RestrictedArea.name,
        RestrictedArea.country,
        func.count(Incident.id).label("count")
    ).join(Incident).group_by(RestrictedArea.id).order_by(
        func.count(Incident.id).desc()
    ).limit(5).all()

    # Intervention types breakdown
    intervention_breakdown = db.query(
        Intervention.intervention_type,
        func.count(Intervention.id).label("count")
    ).group_by(Intervention.intervention_type).all()

    # Suspected operators/purposes
    purpose_breakdown = db.query(
        Incident.purpose_assessment,
        func.count(Incident.id).label("count")
    ).filter(Incident.purpose_assessment.isnot(None)).group_by(
        Incident.purpose_assessment
    ).all()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_incidents": total_incidents,
            "recent_incidents_30d": recent_incidents,
            "total_interventions": total_interventions,
            "intervention_success_rate": round(intervention_success_rate, 1),
            "total_patterns": total_patterns,
            "restricted_areas": total_restricted_areas,
            "drone_types_tracked": total_drone_types,
        },
        "top_drone_types": [
            {"model": model, "incidents": count}
            for model, count in most_common_drones
        ],
        "top_targeted_areas": [
            {"name": name, "country": country, "incidents": count}
            for name, country, count in most_targeted_areas
        ],
        "interventions_by_type": [
            {"type": itype, "count": count}
            for itype, count in intervention_breakdown
        ],
        "purposes_detected": [
            {"purpose": purpose, "count": count}
            for purpose, count in purpose_breakdown
        ]
    }
