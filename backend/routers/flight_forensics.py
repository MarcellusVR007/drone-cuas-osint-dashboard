"""
Flight Forensics API endpoints
Post-incident flight analysis + Shodan infrastructure scanning
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.post_incident_flight_analysis import PostIncidentFlightAnalyzer
from backend.shodan_launch_zone_scanner import LaunchZoneShodanScanner
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

@router.get("/incident/{incident_id}/infrastructure")
async def get_launch_zone_infrastructure(incident_id: int):
    """
    Scan launch zone for suspect infrastructure using Shodan
    Returns: Devices, CVEs, services, ASN info, timing correlation
    """
    analyzer = PostIncidentFlightAnalyzer()

    # Get incident details
    incident = analyzer.get_incident_details(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Calculate launch zone
    launch_zone = analyzer.calculate_possible_launch_zone(
        incident['latitude'],
        incident['longitude'],
        incident['drone_description']
    )

    # Scan with Shodan
    try:
        scanner = LaunchZoneShodanScanner()

        scan_results = scanner.scan_launch_zone(
            latitude=incident['latitude'],
            longitude=incident['longitude'],
            radius_km=launch_zone.get('radius_km', 10),
            incident_date=f"{incident['sighting_date']}T{incident['sighting_time'] or '00:00'}:00"
        )

        return {
            "incident_id": incident_id,
            "incident": {
                "title": incident['title'],
                "date": incident['sighting_date'],
                "time": incident['sighting_time'],
                "location": {
                    "lat": incident['latitude'],
                    "lon": incident['longitude']
                }
            },
            "launch_zone": launch_zone,
            "infrastructure_scan": scan_results
        }

    except ValueError as e:
        # Shodan API key not configured
        raise HTTPException(status_code=503, detail=f"Shodan API not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/device/{ip}")
async def get_device_details(ip: str):
    """
    Get detailed Shodan information for a specific IP address
    Useful for investigating suspect devices found in launch zone
    """
    try:
        scanner = LaunchZoneShodanScanner()
        details = scanner.get_device_details(ip)

        if 'error' in details:
            raise HTTPException(status_code=404, detail=details['error'])

        return details

    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Shodan API not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
