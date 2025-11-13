from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db

router = APIRouter()

@router.get("/monitored-forums")
async def get_monitored_forums(
    db: Session = Depends(get_db),
    threat_level: Optional[str] = None
):
    """Get all monitored aviation forums"""

    query = "SELECT * FROM monitored_forums WHERE 1=1"
    params = {}

    if threat_level:
        query += " AND threat_level = :threat_level"
        params["threat_level"] = threat_level

    query += " ORDER BY CASE threat_level WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 END"

    result = db.execute(text(query), params)
    forums = [dict(row._mapping) for row in result]

    return {
        "forums": forums,
        "total": len(forums)
    }

@router.get("/suspicious-accounts")
async def get_suspicious_accounts(
    db: Session = Depends(get_db),
    min_score: Optional[float] = None,
    investigation_status: Optional[str] = None
):
    """Get suspicious forum accounts"""

    query = """
        SELECT
            sfa.*,
            mf.name as forum_name,
            mf.url as forum_url
        FROM suspicious_forum_accounts sfa
        JOIN monitored_forums mf ON sfa.forum_id = mf.id
        WHERE 1=1
    """
    params = {}

    if min_score is not None:
        query += " AND sfa.suspicious_score >= :min_score"
        params["min_score"] = min_score

    if investigation_status:
        query += " AND sfa.investigation_status = :status"
        params["status"] = investigation_status

    query += " ORDER BY sfa.suspicious_score DESC"

    result = db.execute(text(query), params)
    accounts = [dict(row._mapping) for row in result]

    return {
        "accounts": accounts,
        "total": len(accounts)
    }

@router.get("/suspicious-accounts/{account_id}")
async def get_account_details(account_id: int, db: Session = Depends(get_db)):
    """Get detailed account information"""

    # Get account
    account_query = text("""
        SELECT
            sfa.*,
            mf.name as forum_name,
            mf.url as forum_url,
            mf.platform as forum_platform
        FROM suspicious_forum_accounts sfa
        JOIN monitored_forums mf ON sfa.forum_id = mf.id
        WHERE sfa.id = :id
    """)
    account_result = db.execute(account_query, {"id": account_id})
    account_row = account_result.fetchone()

    if not account_row:
        raise HTTPException(status_code=404, detail="Account not found")

    account = dict(account_row._mapping)

    # Get suspicious content
    content_query = text("""
        SELECT * FROM suspicious_forum_content
        WHERE account_id = :account_id
        ORDER BY post_date DESC
    """)
    content = db.execute(content_query, {"account_id": account_id})
    account["suspicious_content"] = [dict(row._mapping) for row in content]

    # Parse red flags
    if account.get('red_flags'):
        account["red_flags_parsed"] = [
            flag.strip() for flag in account['red_flags'].split(',')
        ]

    return account

@router.get("/red-flags")
async def get_red_flags(
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Get behavioral red flags library"""

    query = "SELECT * FROM forum_red_flags WHERE 1=1"
    params = {}

    if category:
        query += " AND category = :category"
        params["category"] = category

    query += " ORDER BY weight DESC"

    result = db.execute(text(query), params)
    flags = [dict(row._mapping) for row in result]

    # Group by category
    by_category = {}
    for flag in flags:
        cat = flag['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(flag)

    return {
        "red_flags": flags,
        "by_category": by_category,
        "total": len(flags)
    }

@router.get("/detection-summary")
async def get_detection_summary(db: Session = Depends(get_db)):
    """Get overall detection summary"""

    # Count accounts by status
    status_query = text("""
        SELECT
            investigation_status,
            COUNT(*) as count,
            AVG(suspicious_score) as avg_score
        FROM suspicious_forum_accounts
        GROUP BY investigation_status
    """)
    status = db.execute(status_query)
    by_status = [dict(row._mapping) for row in status]

    # Count forums by threat level
    forum_query = text("""
        SELECT
            threat_level,
            COUNT(*) as count
        FROM monitored_forums
        GROUP BY threat_level
    """)
    forums = db.execute(forum_query)
    by_threat_level = [dict(row._mapping) for row in forums]

    # Get high-priority accounts
    priority_query = text("""
        SELECT COUNT(*) as count
        FROM suspicious_forum_accounts
        WHERE suspicious_score >= 0.75
    """)
    priority = db.execute(priority_query).fetchone()
    high_priority_count = priority[0] if priority else 0

    # Recent activity
    recent_query = text("""
        SELECT COUNT(*) as count
        FROM suspicious_forum_accounts
        WHERE last_activity >= datetime('now', '-7 days')
    """)
    recent = db.execute(recent_query).fetchone()
    recent_active = recent[0] if recent else 0

    return {
        "by_status": by_status,
        "by_threat_level": by_threat_level,
        "high_priority_count": high_priority_count,
        "recent_active_count": recent_active,
        "total_accounts": sum([s['count'] for s in by_status])
    }
