"""
GRU Recruitment Monitoring API
Real-time insights from Dutch Telegram channel monitoring
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import sqlite3
from typing import List, Dict
from datetime import datetime, timedelta

router = APIRouter()

DB_PATH = "data/drone_cuas.db"

@router.get("/stats")
async def get_monitoring_stats():
    """Get overall GRU recruitment monitoring statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total posts
    cursor.execute("SELECT COUNT(*) FROM social_media_posts")
    total_posts = cursor.fetchone()[0]

    # Posts by score category
    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score >= 50")
    critical = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score >= 30 AND gru_recruitment_score < 50")
    high = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score >= 20 AND gru_recruitment_score < 30")
    medium = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score > 0 AND gru_recruitment_score < 20")
    low = cursor.fetchone()[0]

    # Dutch channels specifically
    cursor.execute("""
        SELECT COUNT(*) FROM social_media_posts
        WHERE channel_name IN ('FVDNL', 'Cafe_Weltschmerz')
    """)
    dutch_posts = cursor.fetchone()[0]

    # Russian channels
    cursor.execute("""
        SELECT COUNT(*) FROM social_media_posts
        WHERE channel_name IN ('intelslava', 'rybar', 'grey_zone')
    """)
    russian_posts = cursor.fetchone()[0]

    conn.close()

    return {
        "total_posts": total_posts,
        "score_distribution": {
            "critical": critical,  # 50+
            "high": high,          # 30-49
            "medium": medium,      # 20-29
            "low": low,            # 1-19
            "normal": total_posts - critical - high - medium - low  # 0
        },
        "by_origin": {
            "dutch_channels": dutch_posts,
            "russian_channels": russian_posts
        },
        "assessment": {
            "recruitment_detected": critical > 0,
            "status": "CRITICAL" if critical > 0 else "HIGH" if high > 0 else "MONITORING" if medium > 0 else "BASELINE"
        }
    }

@router.get("/channels")
async def get_channel_breakdown():
    """Get breakdown by channel"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            channel_name,
            COUNT(*) as post_count,
            AVG(gru_recruitment_score) as avg_score,
            MAX(gru_recruitment_score) as max_score,
            SUM(CASE WHEN gru_recruitment_score >= 50 THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN gru_recruitment_score >= 30 AND gru_recruitment_score < 50 THEN 1 ELSE 0 END) as high_count
        FROM social_media_posts
        GROUP BY channel_name
        ORDER BY avg_score DESC
    """)

    channels = []
    for row in cursor.fetchall():
        channels.append({
            "channel": row[0],
            "post_count": row[1],
            "avg_score": round(row[2], 1),
            "max_score": row[3],
            "critical_posts": row[4],
            "high_posts": row[5],
            "type": "dutch" if row[0] in ['FVDNL', 'Cafe_Weltschmerz'] else "russian"
        })

    conn.close()
    return {"channels": channels}

@router.get("/top-posts")
async def get_top_scoring_posts(limit: int = 20):
    """Get highest scoring posts (potential recruitment)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            channel_name,
            content,
            gru_recruitment_score,
            post_date,
            post_url
        FROM social_media_posts
        WHERE gru_recruitment_score > 0
        ORDER BY gru_recruitment_score DESC
        LIMIT ?
    """, (limit,))

    posts = []
    for row in cursor.fetchall():
        full_content = row[1] if row[1] else ""
        posts.append({
            "channel": row[0],
            "content_preview": full_content[:200] if len(full_content) > 200 else full_content,
            "content_full": full_content,
            "score": row[2],
            "date": row[3],
            "url": row[4],
            "severity": "CRITICAL" if row[2] >= 50 else "HIGH" if row[2] >= 30 else "MEDIUM" if row[2] >= 20 else "LOW"
        })

    conn.close()
    return {"posts": posts}

@router.get("/timeline")
async def get_timeline_data(days: int = 30):
    """Get score timeline for last N days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get posts from last N days
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute("""
        SELECT
            DATE(post_date) as day,
            COUNT(*) as total_posts,
            AVG(gru_recruitment_score) as avg_score,
            MAX(gru_recruitment_score) as max_score,
            SUM(CASE WHEN gru_recruitment_score >= 30 THEN 1 ELSE 0 END) as suspicious_count
        FROM social_media_posts
        WHERE post_date >= ?
        GROUP BY DATE(post_date)
        ORDER BY day
    """, (start_date,))

    timeline = []
    for row in cursor.fetchall():
        timeline.append({
            "date": row[0],
            "total_posts": row[1],
            "avg_score": round(row[2], 1),
            "max_score": row[3],
            "suspicious_posts": row[4]
        })

    conn.close()
    return {"timeline": timeline, "period_days": days}

@router.get("/dutch-channels")
async def get_dutch_channel_focus():
    """Get detailed stats for Dutch channels only (FvD, Café Weltschmerz)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    dutch_channels = ['FVDNL', 'Cafe_Weltschmerz']
    results = {}

    for channel in dutch_channels:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(gru_recruitment_score) as avg_score,
                MAX(gru_recruitment_score) as max_score,
                SUM(CASE WHEN gru_recruitment_score >= 20 THEN 1 ELSE 0 END) as medium_plus
            FROM social_media_posts
            WHERE channel_name = ?
        """, (channel,))

        row = cursor.fetchone()

        # Get top posts for this channel
        cursor.execute("""
            SELECT content, gru_recruitment_score, post_date
            FROM social_media_posts
            WHERE channel_name = ? AND gru_recruitment_score > 0
            ORDER BY gru_recruitment_score DESC
            LIMIT 5
        """, (channel,))

        top_posts = []
        for post_row in cursor.fetchall():
            top_posts.append({
                "content": post_row[0][:150] if post_row[0] else "",
                "score": post_row[1],
                "date": post_row[2]
            })

        results[channel] = {
            "total_posts": row[0],
            "avg_score": round(row[1], 1),
            "max_score": row[2],
            "medium_plus_posts": row[3],
            "top_posts": top_posts,
            "assessment": "BASELINE - Normal activity" if row[1] < 5 else "MONITORING - Some signals"
        }

    conn.close()
    return {"dutch_channels": results}

@router.get("/hypothesis-scores")
async def get_hypothesis_testing():
    """
    Calculate H1 vs H2 hypothesis scores based on evidence

    H1: Local Recruitment (GRU recruiting Dutch sympathizers)
    H2: State Actors (Russian professionals on visas, no recruitment)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Evidence for H1 (LOCAL RECRUITMENT)
    # Only count posts with ACTUAL recruitment indicators (score 70+)
    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score >= 70")
    critical_posts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE gru_recruitment_score >= 40")
    high_posts = cursor.fetchone()[0]

    # Calculate H1 score (recruitment evidence)
    h1_score = 6  # baseline (no evidence yet)
    if critical_posts > 5:
        h1_score += 50  # Strong evidence of recruitment campaign
    elif critical_posts > 0:
        h1_score += 20  # Some recruitment posts (could be false positives)

    if high_posts > 10:
        h1_score += 20  # Pattern of recruitment attempts

    # H2 score (STATE ACTORS - no recruitment needed)
    h2_score = 33  # baseline
    if critical_posts == 0:
        h2_score += 40  # No recruitment found = supports state actor theory
    elif critical_posts < 5:
        h2_score += 20  # Minimal recruitment = probably state actors

    conn.close()

    return {
        "hypotheses": {
            "H1_local_recruitment": {
                "score": min(h1_score, 100),
                "evidence": {
                    "critical_posts": critical_posts,
                    "high_posts": high_posts
                },
                "verdict": "UNLIKELY" if h1_score < 30 else "POSSIBLE" if h1_score < 60 else "LIKELY"
            },
            "H2_state_actors": {
                "score": min(h2_score, 100),
                "evidence": {
                    "no_recruitment_found": critical_posts == 0 and high_posts == 0,
                    "professional_ops": True  # Based on incident characteristics
                },
                "verdict": "UNLIKELY" if h2_score < 30 else "POSSIBLE" if h2_score < 60 else "LIKELY"
            }
        },
        "conclusion": "H2 (State Actors) more likely - no recruitment detected" if h2_score > h1_score else "H1 (Local Recruitment) detected - evidence found",
        "confidence": "LOW" if abs(h1_score - h2_score) < 20 else "MEDIUM" if abs(h1_score - h2_score) < 40 else "HIGH"
    }
