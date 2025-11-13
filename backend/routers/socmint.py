"""
Social Media Intelligence (SOCMINT) API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db
import json

router = APIRouter()

@router.get("/incident/{incident_id}/social-media")
async def get_incident_social_media(incident_id: int, db: Session = Depends(get_db)):
    """Get social media posts linked to an incident"""
    query = text("""
        SELECT
            smp.*,
            a.name as author_name,
            a.alias as author_alias,
            a.affiliation as author_affiliation,
            a.confidence_score as author_confidence
        FROM social_media_posts smp
        LEFT JOIN actors a ON smp.author_id = a.id
        WHERE smp.linked_incident_id = :incident_id
        ORDER BY smp.post_date DESC
    """)

    result = db.execute(query, {"incident_id": incident_id})
    posts = [dict(row._mapping) for row in result]

    return {"posts": posts, "total": len(posts)}

@router.get("/incident/{incident_id}/crypto-transactions")
async def get_incident_crypto(incident_id: int, db: Session = Depends(get_db)):
    """Get crypto transactions linked to an incident"""
    query = text("""
        SELECT
            ct.*,
            a1.name as sender_name,
            a1.alias as sender_alias,
            a2.name as recipient_name,
            a2.alias as recipient_alias
        FROM crypto_transactions ct
        LEFT JOIN actors a1 ON ct.sender_actor_id = a1.id
        LEFT JOIN actors a2 ON ct.recipient_actor_id = a2.id
        WHERE ct.linked_incident_id = :incident_id
        ORDER BY ct.transaction_date DESC
    """)

    result = db.execute(query, {"incident_id": incident_id})
    transactions = [dict(row._mapping) for row in result]

    return {"transactions": transactions, "total": len(transactions)}

@router.get("/actors")
async def list_actors(db: Session = Depends(get_db)):
    """List all known threat actors"""
    query = text("""
        SELECT
            a.*,
            COUNT(DISTINCT smp.id) as posts_count,
            COUNT(DISTINCT ct.id) as transactions_count
        FROM actors a
        LEFT JOIN social_media_posts smp ON a.id = smp.author_id
        LEFT JOIN crypto_transactions ct ON a.id = ct.sender_actor_id OR a.id = ct.recipient_actor_id
        GROUP BY a.id
        ORDER BY a.confidence_score DESC
    """)

    result = db.execute(query)
    actors = [dict(row._mapping) for row in result]

    return {"actors": actors, "total": len(actors)}

@router.get("/actors/{actor_id}")
async def get_actor_details(actor_id: int, db: Session = Depends(get_db)):
    """Get detailed actor profile with activities"""
    # Get actor info
    actor_query = text("SELECT * FROM actors WHERE id = :actor_id")
    actor_result = db.execute(actor_query, {"actor_id": actor_id})
    actor = dict(actor_result.fetchone()._mapping) if actor_result.rowcount > 0 else None

    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    # Get posts
    posts_query = text("""
        SELECT * FROM social_media_posts
        WHERE author_id = :actor_id
        ORDER BY post_date DESC
    """)
    posts_result = db.execute(posts_query, {"actor_id": actor_id})
    posts = [dict(row._mapping) for row in posts_result]

    # Get transactions
    tx_query = text("""
        SELECT * FROM crypto_transactions
        WHERE sender_actor_id = :actor_id OR recipient_actor_id = :actor_id
        ORDER BY transaction_date DESC
    """)
    tx_result = db.execute(tx_query, {"actor_id": actor_id})
    transactions = [dict(row._mapping) for row in tx_result]

    # Get relationships
    rel_query = text("""
        SELECT
            ar.*,
            a1.name as actor1_name,
            a2.name as actor2_name
        FROM actor_relationships ar
        JOIN actors a1 ON ar.actor1_id = a1.id
        JOIN actors a2 ON ar.actor2_id = a2.id
        WHERE ar.actor1_id = :actor_id OR ar.actor2_id = :actor_id
    """)
    rel_result = db.execute(rel_query, {"actor_id": actor_id})
    relationships = [dict(row._mapping) for row in rel_result]

    return {
        "actor": actor,
        "posts": posts,
        "transactions": transactions,
        "relationships": relationships
    }

@router.get("/timeline/{incident_id}")
async def get_incident_timeline(incident_id: int, db: Session = Depends(get_db)):
    """Get complete timeline: posts → transactions → incident"""
    # Get incident
    incident_query = text("SELECT * FROM incidents WHERE id = :incident_id")
    incident_result = db.execute(incident_query, {"incident_id": incident_id})
    incident = dict(incident_result.fetchone()._mapping) if incident_result.rowcount > 0 else None

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get related posts
    posts_query = text("""
        SELECT
            smp.*,
            a.name as author_name,
            a.affiliation as author_affiliation
        FROM social_media_posts smp
        LEFT JOIN actors a ON smp.author_id = a.id
        WHERE smp.linked_incident_id = :incident_id
        ORDER BY smp.post_date ASC
    """)
    posts_result = db.execute(posts_query, {"incident_id": incident_id})
    posts = [dict(row._mapping) for row in posts_result]

    # Get related transactions
    tx_query = text("""
        SELECT
            ct.*,
            a1.name as sender_name,
            a2.name as recipient_name
        FROM crypto_transactions ct
        LEFT JOIN actors a1 ON ct.sender_actor_id = a1.id
        LEFT JOIN actors a2 ON ct.recipient_actor_id = a2.id
        WHERE ct.linked_incident_id = :incident_id
        ORDER BY ct.transaction_date ASC
    """)
    tx_result = db.execute(tx_query, {"incident_id": incident_id})
    transactions = [dict(row._mapping) for row in tx_result]

    # Build timeline
    timeline = []

    for post in posts:
        timeline.append({
            "type": "post",
            "timestamp": post["post_date"],
            "data": post
        })

    for tx in transactions:
        timeline.append({
            "type": "transaction",
            "timestamp": tx["transaction_date"],
            "data": tx
        })

    timeline.append({
        "type": "incident",
        "timestamp": f"{incident['sighting_date']} {incident.get('sighting_time', '00:00:00')}",
        "data": incident
    })

    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"])

    return {
        "incident_id": incident_id,
        "timeline": timeline,
        "total_events": len(timeline)
    }

@router.get("/network/actors")
async def get_actor_network(db: Session = Depends(get_db)):
    """Get actor network data for visualization"""
    # Get all actors as nodes
    actors_query = text("SELECT * FROM actors")
    actors_result = db.execute(actors_query)
    nodes = []

    for actor in actors_result:
        actor_dict = dict(actor._mapping)
        nodes.append({
            "id": actor_dict["id"],
            "label": actor_dict["name"],
            "alias": actor_dict["alias"],
            "type": actor_dict["actor_type"],
            "affiliation": actor_dict["affiliation"],
            "confidence": actor_dict["confidence_score"]
        })

    # Get relationships as edges
    rel_query = text("""
        SELECT
            ar.*,
            a1.name as actor1_name,
            a2.name as actor2_name
        FROM actor_relationships ar
        JOIN actors a1 ON ar.actor1_id = a1.id
        JOIN actors a2 ON ar.actor2_id = a2.id
    """)
    rel_result = db.execute(rel_query)
    edges = []

    for rel in rel_result:
        rel_dict = dict(rel._mapping)
        edges.append({
            "from": rel_dict["actor1_id"],
            "to": rel_dict["actor2_id"],
            "label": rel_dict["relationship_type"],
            "confidence": rel_dict["confidence_score"]
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
