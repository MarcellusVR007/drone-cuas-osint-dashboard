"""
Data Sources Management Router
Manage and qualify intelligence sources
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from backend.database import get_db
from backend.models import DataSource
from backend.data_ingestion import (
    get_source_combined_score,
    calculate_incident_source_confidence,
    get_qualified_sources
)

router = APIRouter()


class DataSourceResponse:
    pass


@router.get("/")
async def list_data_sources(
    db: Session = Depends(get_db),
    enabled_only: bool = True,
    min_score: float = 0.0
):
    """List configured data sources with qualification scores"""
    query = db.query(DataSource)

    if enabled_only:
        query = query.filter_by(enabled=True)

    sources = query.all()

    results = []
    for source in sources:
        combined_score = get_source_combined_score({
            "reliability_score": source.reliability_score,
            "freshness_score": source.freshness_score,
            "coverage_score": source.coverage_score,
            "data_quality_score": source.data_quality_score,
        })

        if combined_score >= min_score:
            results.append({
                "id": source.id,
                "name": source.name,
                "source_type": source.source_type,
                "url": source.url,
                "reliability_score": source.reliability_score,
                "freshness_score": source.freshness_score,
                "coverage_score": source.coverage_score,
                "data_quality_score": source.data_quality_score,
                "combined_score": round(combined_score, 3),
                "verification_status": source.verification_status,
                "capabilities": json.loads(source.capabilities or "[]"),
                "coverage_regions": json.loads(source.coverage_regions or "[]"),
                "enabled": source.enabled,
                "last_sync": source.last_sync,
            })

    return {
        "total": len(results),
        "sources": sorted(results, key=lambda x: x["combined_score"], reverse=True)
    }


@router.get("/qualified")
async def get_qualified(
    db: Session = Depends(get_db),
    min_score: float = 0.7
):
    """Get only high-quality data sources"""
    qualified = get_qualified_sources(db, min_score=min_score)

    results = []
    for source in qualified:
        combined_score = get_source_combined_score({
            "reliability_score": source.reliability_score,
            "freshness_score": source.freshness_score,
            "coverage_score": source.coverage_score,
            "data_quality_score": source.data_quality_score,
        })

        results.append({
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "verification_status": source.verification_status,
            "combined_score": round(combined_score, 3),
            "capabilities": json.loads(source.capabilities or "[]"),
        })

    return {
        "threshold": min_score,
        "qualified_count": len(results),
        "sources": results
    }


@router.get("/by-type/{source_type}")
async def get_by_type(
    source_type: str,
    db: Session = Depends(get_db)
):
    """Get all sources of a specific type"""
    sources = db.query(DataSource).filter_by(
        source_type=source_type,
        enabled=True
    ).all()

    results = []
    for source in sources:
        combined_score = get_source_combined_score({
            "reliability_score": source.reliability_score,
            "freshness_score": source.freshness_score,
            "coverage_score": source.coverage_score,
            "data_quality_score": source.data_quality_score,
        })

        results.append({
            "id": source.id,
            "name": source.name,
            "verification_status": source.verification_status,
            "combined_score": round(combined_score, 3),
        })

    return {
        "source_type": source_type,
        "count": len(results),
        "sources": results
    }


@router.get("/by-verification/{status}")
async def get_by_verification(
    status: str,  # high_confidence, verified, partial, unverified
    db: Session = Depends(get_db)
):
    """Get sources by verification status"""
    sources = db.query(DataSource).filter_by(
        verification_status=status,
        enabled=True
    ).all()

    results = []
    for source in sources:
        combined_score = get_source_combined_score({
            "reliability_score": source.reliability_score,
            "freshness_score": source.freshness_score,
            "coverage_score": source.coverage_score,
            "data_quality_score": source.data_quality_score,
        })

        results.append({
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "combined_score": round(combined_score, 3),
        })

    return {
        "verification_status": status,
        "count": len(results),
        "sources": results
    }


@router.get("/statistics")
async def source_statistics(db: Session = Depends(get_db)):
    """Get statistics about configured data sources"""
    all_sources = db.query(DataSource).all()

    by_type = {}
    by_verification = {}
    avg_scores = {
        "reliability": 0,
        "freshness": 0,
        "coverage": 0,
        "data_quality": 0,
    }

    for source in all_sources:
        # Count by type
        if source.source_type not in by_type:
            by_type[source.source_type] = 0
        by_type[source.source_type] += 1

        # Count by verification
        if source.verification_status not in by_verification:
            by_verification[source.verification_status] = 0
        by_verification[source.verification_status] += 1

        # Accumulate scores
        avg_scores["reliability"] += source.reliability_score
        avg_scores["freshness"] += source.freshness_score
        avg_scores["coverage"] += source.coverage_score
        avg_scores["data_quality"] += source.data_quality_score

    # Calculate averages
    count = len(all_sources)
    if count > 0:
        for key in avg_scores:
            avg_scores[key] = round(avg_scores[key] / count, 3)

    return {
        "total_sources": count,
        "enabled_sources": len([s for s in all_sources if s.enabled]),
        "by_source_type": by_type,
        "by_verification_status": by_verification,
        "average_scores": avg_scores,
        "most_reliable": max(all_sources, key=lambda s: s.reliability_score).name if all_sources else None,
        "freshest": max(all_sources, key=lambda s: s.freshness_score).name if all_sources else None,
        "best_coverage": max(all_sources, key=lambda s: s.coverage_score).name if all_sources else None,
    }


@router.put("/{source_id}")
async def update_source_scores(
    source_id: int,
    reliability_score: Optional[float] = None,
    freshness_score: Optional[float] = None,
    coverage_score: Optional[float] = None,
    data_quality_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update qualification scores for a data source"""
    source = db.query(DataSource).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    if reliability_score is not None:
        source.reliability_score = max(0, min(1, reliability_score))
    if freshness_score is not None:
        source.freshness_score = max(0, min(1, freshness_score))
    if coverage_score is not None:
        source.coverage_score = max(0, min(1, coverage_score))
    if data_quality_score is not None:
        source.data_quality_score = max(0, min(1, data_quality_score))

    db.commit()
    db.refresh(source)

    combined_score = get_source_combined_score({
        "reliability_score": source.reliability_score,
        "freshness_score": source.freshness_score,
        "coverage_score": source.coverage_score,
        "data_quality_score": source.data_quality_score,
    })

    return {
        "id": source.id,
        "name": source.name,
        "scores": {
            "reliability": round(source.reliability_score, 3),
            "freshness": round(source.freshness_score, 3),
            "coverage": round(source.coverage_score, 3),
            "data_quality": round(source.data_quality_score, 3),
            "combined": round(combined_score, 3),
        }
    }
