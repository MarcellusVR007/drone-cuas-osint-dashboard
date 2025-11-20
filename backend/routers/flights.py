"""
Flight Anomaly Detection API
Real-time flight tracking and anomaly detection near critical infrastructure
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.get("/anomalies")
async def get_flight_anomalies(
    hours: int = 24,
    min_risk_score: float = 0.0,
    area_type: str = None,  # airport, military, nuclear
    db: Session = Depends(get_db)
):
    """Get detected flight anomalies near critical infrastructure"""

    # Calculate time threshold
    time_threshold = datetime.now() - timedelta(hours=hours)

    query_str = """
        SELECT
            fa.*,
            ra.name as area_name,
            ra.area_type,
            ra.latitude as area_lat,
            ra.longitude as area_lon
        FROM flight_anomalies fa
        LEFT JOIN restricted_areas ra ON fa.area_name = ra.name
        WHERE fa.detection_time >= :time_threshold
        AND fa.risk_score >= :min_risk_score
    """

    params = {
        "time_threshold": time_threshold.isoformat(),
        "min_risk_score": min_risk_score
    }

    # Add area type filter
    if area_type:
        query_str += " AND ra.area_type = :area_type"
        params["area_type"] = area_type

    query_str += " ORDER BY fa.detection_time DESC, fa.risk_score DESC"

    result = db.execute(text(query_str), params)
    anomalies = []

    for row in result:
        row_dict = dict(row._mapping)

        # Parse JSON fields
        if row_dict.get('anomalies'):
            try:
                row_dict['anomalies'] = json.loads(row_dict['anomalies'])
            except:
                pass

        anomalies.append(row_dict)

    # Calculate statistics
    stats = {
        "total": len(anomalies),
        "by_area_type": {},
        "by_risk_level": {
            "high": sum(1 for a in anomalies if a.get('risk_score', 0) >= 0.7),
            "medium": sum(1 for a in anomalies if 0.4 <= a.get('risk_score', 0) < 0.7),
            "low": sum(1 for a in anomalies if a.get('risk_score', 0) < 0.4)
        },
        "avg_risk_score": sum(a.get('risk_score', 0) for a in anomalies) / len(anomalies) if anomalies else 0
    }

    # Count by area type
    for anomaly in anomalies:
        area_type = anomaly.get('area_type', 'unknown')
        stats['by_area_type'][area_type] = stats['by_area_type'].get(area_type, 0) + 1

    return {
        "anomalies": anomalies,
        "stats": stats,
        "time_range": {
            "from": time_threshold.isoformat(),
            "to": datetime.now().isoformat(),
            "hours": hours
        }
    }


@router.get("/live")
async def get_live_flights(
    area_name: str = None,
    db: Session = Depends(get_db)
):
    """Get current live flights near critical areas (last 5 minutes)"""

    # For now, return recent anomalies
    # In production, this would query OpenSky API in real-time

    time_threshold = datetime.now() - timedelta(minutes=5)

    query_str = """
        SELECT
            fa.*,
            ra.name as area_name,
            ra.area_type
        FROM flight_anomalies fa
        LEFT JOIN restricted_areas ra ON fa.area_name = ra.name
        WHERE fa.detection_time >= :time_threshold
    """

    params = {"time_threshold": time_threshold.isoformat()}

    if area_name:
        query_str += " AND fa.area_name = :area_name"
        params["area_name"] = area_name

    query_str += " ORDER BY fa.detection_time DESC"

    result = db.execute(text(query_str), params)
    flights = []

    for row in result:
        row_dict = dict(row._mapping)

        # Parse JSON
        if row_dict.get('anomalies'):
            try:
                row_dict['anomalies'] = json.loads(row_dict['anomalies'])
            except:
                pass

        flights.append(row_dict)

    return {
        "flights": flights,
        "count": len(flights),
        "last_update": datetime.now().isoformat()
    }


@router.get("/areas")
async def get_monitored_areas(db: Session = Depends(get_db)):
    """Get all critical areas being monitored"""

    query = text("""
        SELECT
            ra.*,
            COUNT(fa.id) as anomaly_count
        FROM restricted_areas ra
        LEFT JOIN flight_anomalies fa ON fa.area_name = ra.name
        GROUP BY ra.id
        ORDER BY anomaly_count DESC
    """)

    result = db.execute(query)
    areas = [dict(row._mapping) for row in result]

    return {
        "areas": areas,
        "total": len(areas)
    }


@router.get("/timeline")
async def get_anomaly_timeline(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get anomaly timeline for visualization"""

    time_threshold = datetime.now() - timedelta(days=days)

    query = text("""
        SELECT
            DATE(fa.detection_time) as date,
            COUNT(*) as count,
            AVG(fa.risk_score) as avg_risk,
            ra.area_type
        FROM flight_anomalies fa
        LEFT JOIN restricted_areas ra ON fa.area_name = ra.name
        WHERE fa.detection_time >= :time_threshold
        GROUP BY DATE(fa.detection_time), ra.area_type
        ORDER BY date DESC
    """)

    result = db.execute(query, {"time_threshold": time_threshold.isoformat()})
    timeline = [dict(row._mapping) for row in result]

    return {
        "timeline": timeline,
        "days": days
    }
