"""
Incident Correlation & Social Graph API Router

New intelligence capabilities:
- Temporal incident correlation with Telegram/Forum activity
- Social graph analysis (channel influence mapping)
- Coordinated forwarding detection
- Linguistic fingerprinting (Russian→Dutch patterns)
- Private channel leak tracking

Endpoints:
- GET /api/correlation/analyze - Run correlation analysis
- GET /api/correlation/incident/{id} - Get correlations for specific incident
- GET /api/correlation/alerts - High-confidence correlation alerts
- GET /api/correlation/social-graph - Channel influence map
- GET /api/correlation/coordinated-forwards - Detect coordination
- POST /api/correlation/linguistic-analysis - Analyze text for suspicious patterns
- GET /api/correlation/private-leaks - Private channel leaks
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import (
    Incident, IncidentCorrelation, TelegramChannel, TelegramMessage,
    MessageForward, PrivateChannelLeak
)
from backend.incident_correlation_engine import IncidentCorrelationEngine
from backend.linguistic_fingerprint_detector import LinguisticFingerprintDetector

router = APIRouter()


class CorrelationAnalysisRequest(BaseModel):
    incident_limit: Optional[int] = None
    time_window_hours: Optional[int] = 24


class LinguisticAnalysisRequest(BaseModel):
    text: str


@router.post("/analyze")
async def run_correlation_analysis(
    request: CorrelationAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run temporal correlation analysis on incidents

    Detects:
    - Telegram activity spikes around incidents (±24h)
    - Forum discussions correlated with incidents
    - Statistical anomalies (z-score based)

    Returns summary of detected correlations
    """
    engine = IncidentCorrelationEngine(
        db=db,
        time_window_hours=request.time_window_hours or 24
    )

    results = engine.analyze_all_incidents(limit=request.incident_limit)

    return {
        "status": "complete",
        "analysis_timestamp": datetime.now().isoformat(),
        "results": results,
        "time_window_hours": request.time_window_hours or 24
    }


@router.get("/incident/{incident_id}")
async def get_incident_correlations(
    incident_id: int,
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Get all correlations for a specific incident

    Args:
        incident_id: Incident ID
        min_strength: Minimum correlation strength (0-1)

    Returns correlations sorted by strength
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    correlations = db.query(IncidentCorrelation).filter(
        IncidentCorrelation.incident_id == incident_id,
        IncidentCorrelation.correlation_strength >= min_strength
    ).order_by(IncidentCorrelation.correlation_strength.desc()).all()

    correlation_data = []
    for corr in correlations:
        data = {
            "id": corr.id,
            "correlation_type": corr.correlation_type,
            "correlation_strength": corr.correlation_strength,
            "time_delta_hours": corr.time_delta_hours,
            "description": corr.description,
            "keywords_matched": corr.keywords_matched,
            "auto_detected": corr.auto_detected,
            "created_at": corr.created_at.isoformat()
        }

        # Add source details
        if corr.source_table == "telegram_channels" and corr.source_id:
            channel = db.query(TelegramChannel).filter(
                TelegramChannel.id == corr.source_id
            ).first()
            if channel:
                data["source_channel"] = {
                    "username": channel.username,
                    "title": channel.title,
                    "member_count": channel.member_count
                }

        correlation_data.append(data)

    return {
        "incident_id": incident_id,
        "incident_title": incident.title,
        "incident_date": incident.sighting_date.isoformat(),
        "total_correlations": len(correlation_data),
        "correlations": correlation_data
    }


@router.get("/alerts")
async def get_correlation_alerts(
    min_strength: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get high-confidence correlation alerts

    Args:
        min_strength: Minimum correlation strength (default: 0.7)
        limit: Maximum number of alerts

    Returns recent high-confidence correlations
    """
    correlations = db.query(IncidentCorrelation).filter(
        IncidentCorrelation.correlation_strength >= min_strength
    ).order_by(IncidentCorrelation.created_at.desc()).limit(limit).all()

    alerts = []
    for corr in correlations:
        incident = db.query(Incident).filter(Incident.id == corr.incident_id).first()
        if not incident:
            continue

        alert = {
            "alert_id": corr.id,
            "incident_id": incident.id,
            "incident_title": incident.title,
            "incident_date": incident.sighting_date.isoformat(),
            "correlation_type": corr.correlation_type,
            "correlation_strength": corr.correlation_strength,
            "time_delta_hours": corr.time_delta_hours,
            "description": corr.description,
            "alert_priority": "HIGH" if corr.correlation_strength >= 0.85 else "MEDIUM",
            "detected_at": corr.created_at.isoformat()
        }

        alerts.append(alert)

    return {
        "alert_count": len(alerts),
        "min_strength_threshold": min_strength,
        "alerts": alerts,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/social-graph")
async def get_social_graph(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get channel influence map (social graph)

    Returns:
    - Channel influence scores
    - Forward relationships
    - Network metrics
    """
    channels = db.query(TelegramChannel).limit(limit).all()

    nodes = []
    edges = []

    for channel in channels:
        # Calculate influence metrics
        outgoing_forwards = db.query(MessageForward).filter(
            MessageForward.source_channel_id == channel.id
        ).count()

        incoming_forwards = db.query(MessageForward).filter(
            MessageForward.destination_channel_id == channel.id
        ).count()

        unique_destinations = db.query(MessageForward.destination_channel_id).filter(
            MessageForward.source_channel_id == channel.id
        ).distinct().count()

        influence_score = outgoing_forwards * (unique_destinations or 1)

        nodes.append({
            "id": channel.id,
            "username": channel.username or channel.channel_id,
            "title": channel.title,
            "member_count": channel.member_count or 0,
            "risk_score": channel.risk_score,
            "influence_score": influence_score,
            "outgoing_forwards": outgoing_forwards,
            "incoming_forwards": incoming_forwards,
            "unique_destinations": unique_destinations
        })

    # Get forward relationships (edges)
    forwards = db.query(MessageForward).limit(500).all()

    for forward in forwards:
        edges.append({
            "source": forward.source_channel_id,
            "target": forward.destination_channel_id,
            "velocity_seconds": forward.forward_velocity_seconds,
            "timestamp": forward.forward_timestamp.isoformat()
        })

    # Sort nodes by influence
    nodes.sort(key=lambda x: x["influence_score"], reverse=True)

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/coordinated-forwards")
async def get_coordinated_forwards(
    time_window_minutes: int = Query(30, ge=5, le=360),
    min_channels: int = Query(5, ge=3, le=50),
    db: Session = Depends(get_db)
):
    """
    Detect coordinated forwarding events

    Finds cases where same message is forwarded to N+ channels within time window

    Args:
        time_window_minutes: Time window for detecting coordination (default: 30)
        min_channels: Minimum channels to flag as coordinated (default: 5)

    Returns coordinated forwarding events
    """
    from collections import defaultdict

    # Group forwards by source message
    forwards = db.query(MessageForward).order_by(MessageForward.forward_timestamp).all()

    source_message_forwards = defaultdict(list)
    for forward in forwards:
        source_message_forwards[forward.source_message_id].append(forward)

    coordinated_events = []

    for source_msg_id, forward_list in source_message_forwards.items():
        if len(forward_list) < min_channels:
            continue

        # Sort by timestamp
        forward_list.sort(key=lambda f: f.forward_timestamp)

        # Check if all forwards happened within time window
        first_forward = forward_list[0].forward_timestamp
        last_forward = forward_list[-1].forward_timestamp
        time_diff_minutes = (last_forward - first_forward).total_seconds() / 60

        if time_diff_minutes <= time_window_minutes:
            # Get source message
            source_msg = db.query(TelegramMessage).filter(
                TelegramMessage.id == source_msg_id
            ).first()

            if not source_msg:
                continue

            # Get destination channels
            dest_channels = []
            for fwd in forward_list:
                channel = db.query(TelegramChannel).filter(
                    TelegramChannel.id == fwd.destination_channel_id
                ).first()
                if channel:
                    dest_channels.append({
                        "username": channel.username,
                        "title": channel.title
                    })

            coordinated_events.append({
                "source_message_id": source_msg_id,
                "message_preview": source_msg.text_content[:200] if source_msg.text_content else "",
                "message_timestamp": source_msg.timestamp.isoformat(),
                "destination_count": len(forward_list),
                "destination_channels": dest_channels,
                "time_window_minutes": round(time_diff_minutes, 1),
                "first_forward": first_forward.isoformat(),
                "last_forward": last_forward.isoformat(),
                "coordination_score": min(len(forward_list) / time_window_minutes, 10.0) # Speed score
            })

    # Sort by coordination score
    coordinated_events.sort(key=lambda x: x["coordination_score"], reverse=True)

    return {
        "events_detected": len(coordinated_events),
        "time_window_minutes": time_window_minutes,
        "min_channels_threshold": min_channels,
        "coordinated_events": coordinated_events,
        "detected_at": datetime.now().isoformat()
    }


@router.post("/linguistic-analysis")
async def analyze_linguistic_patterns(
    request: LinguisticAnalysisRequest
):
    """
    Analyze text for Russian→Dutch translation artifacts

    Detects:
    - Missing articles
    - Preposition calques
    - Word order anomalies
    - Literal translations
    - False cognates
    - Formal/informal mixing

    Returns suspicion score (0-100) and detected patterns
    """
    detector = LinguisticFingerprintDetector()

    analysis = detector.analyze_text(request.text)

    return {
        "text": request.text,
        "suspicion_score": analysis["score"],
        "confidence": analysis["confidence"],
        "flag_count": analysis["flag_count"],
        "flags": analysis["flags"],
        "recommendation": "INVESTIGATE" if analysis["score"] >= 50 else "MONITOR" if analysis["score"] >= 30 else "LOW_PRIORITY",
        "analyzed_at": datetime.now().isoformat()
    }


@router.get("/linguistic-analysis/batch")
async def batch_linguistic_analysis(
    limit: int = Query(100, ge=1, le=1000),
    min_score: int = Query(30, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """
    Run batch linguistic analysis on Telegram messages

    Args:
        limit: Number of messages to analyze
        min_score: Minimum suspicion score to return

    Returns suspicious messages with analysis
    """
    detector = LinguisticFingerprintDetector()

    suspicious_messages = detector.analyze_messages_batch(db, limit=limit)

    # Filter by min_score
    filtered = [msg for msg in suspicious_messages if msg["score"] >= min_score]

    return {
        "messages_analyzed": limit,
        "suspicious_count": len(filtered),
        "min_score_threshold": min_score,
        "suspicious_messages": filtered[:50],  # Limit response size
        "analyzed_at": datetime.now().isoformat()
    }


@router.get("/private-leaks")
async def get_private_channel_leaks(
    min_frequency: int = Query(1, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get detected private channel leaks

    Finds private channels that leak content to public channels

    Args:
        min_frequency: Minimum leak frequency to include

    Returns private channel leak events
    """
    leaks = db.query(PrivateChannelLeak).filter(
        PrivateChannelLeak.leak_frequency >= min_frequency
    ).order_by(PrivateChannelLeak.leak_frequency.desc()).all()

    leak_data = []
    for leak in leaks:
        public_channel = db.query(TelegramChannel).filter(
            TelegramChannel.id == leak.public_channel_id
        ).first()

        leak_data.append({
            "private_channel_id": leak.private_channel_id,
            "private_channel_name": leak.private_channel_name,
            "public_channel": {
                "username": public_channel.username if public_channel else "unknown",
                "title": public_channel.title if public_channel else ""
            },
            "leak_frequency": leak.leak_frequency,
            "first_leak": leak.first_leak_timestamp.isoformat(),
            "last_leak": leak.last_leak_timestamp.isoformat() if leak.last_leak_timestamp else None,
            "bridge_user_id": leak.bridge_user_id
        })

    return {
        "leaks_detected": len(leak_data),
        "min_frequency_threshold": min_frequency,
        "leaks": leak_data,
        "detected_at": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_correlation_stats(db: Session = Depends(get_db)):
    """
    Get overall correlation system statistics

    Returns counts and metrics for intelligence collection
    """
    stats = {
        "telegram": {
            "channels": db.query(TelegramChannel).count(),
            "messages": db.query(TelegramMessage).count(),
            "forwards": db.query(MessageForward).count(),
            "private_leaks": db.query(PrivateChannelLeak).count()
        },
        "correlations": {
            "total": db.query(IncidentCorrelation).count(),
            "high_confidence": db.query(IncidentCorrelation).filter(
                IncidentCorrelation.correlation_strength >= 0.7
            ).count(),
            "telegram_spikes": db.query(IncidentCorrelation).filter(
                IncidentCorrelation.correlation_type == "telegram_spike"
            ).count(),
            "forum_discussions": db.query(IncidentCorrelation).filter(
                IncidentCorrelation.correlation_type == "forum_discussion"
            ).count()
        },
        "incidents_with_correlations": db.query(Incident).join(
            IncidentCorrelation,
            Incident.id == IncidentCorrelation.incident_id
        ).distinct().count()
    }

    return {
        "statistics": stats,
        "generated_at": datetime.now().isoformat()
    }
