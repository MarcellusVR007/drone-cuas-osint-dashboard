"""
Flight Forensics API endpoints
Post-incident flight analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.post_incident_flight_analysis import PostIncidentFlightAnalyzer
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

router = APIRouter()

@router.get("/incident/{incident_id}")
async def get_incident_flight_analysis(incident_id: int):
    """
    Get post-incident flight forensics analysis
    Includes launch zone, maritime correlation, recommendations
    """
    analyzer = PostIncidentFlightAnalyzer()

    try:
        analysis = analyzer.analyze_incident(incident_id)

        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/launch-zone/{incident_id}")
async def get_launch_zone_only(incident_id: int):
    """
    Get just the launch zone calculation (faster)
    """
    analyzer = PostIncidentFlightAnalyzer()

    incident = analyzer.get_incident_details(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    launch_zone = analyzer.calculate_possible_launch_zone(
        incident['latitude'],
        incident['longitude'],
        incident['drone_description']
    )

    return {
        "incident_id": incident_id,
        "launch_zone": launch_zone
    }
