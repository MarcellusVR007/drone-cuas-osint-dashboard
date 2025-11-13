from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db

router = APIRouter()

@router.get("/wallets")
async def get_wallets(
    db: Session = Depends(get_db),
    entity_type: Optional[str] = None,
    min_risk_score: Optional[float] = None
):
    """Get all wallet profiles"""

    query = """
        SELECT * FROM wallet_profiles
        WHERE 1=1
    """
    params = {}

    if entity_type:
        query += " AND entity_type = :entity_type"
        params["entity_type"] = entity_type

    if min_risk_score is not None:
        query += " AND risk_score >= :min_risk_score"
        params["min_risk_score"] = min_risk_score

    query += " ORDER BY risk_score DESC"

    result = db.execute(text(query), params)
    wallets = [dict(row._mapping) for row in result]

    return {
        "wallets": wallets,
        "total": len(wallets)
    }

@router.get("/wallets/{wallet_id}")
async def get_wallet_details(wallet_id: int, db: Session = Depends(get_db)):
    """Get detailed wallet information"""

    # Get wallet profile
    wallet_query = text("SELECT * FROM wallet_profiles WHERE id = :id")
    wallet_result = db.execute(wallet_query, {"id": wallet_id})
    wallet_row = wallet_result.fetchone()

    if not wallet_row:
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet = dict(wallet_row._mapping)

    # Get relationships (outgoing)
    outgoing_query = text("""
        SELECT
            wr.*,
            wp.address as to_address,
            wp.label as to_label,
            wp.entity_type as to_entity_type
        FROM wallet_relationships wr
        JOIN wallet_profiles wp ON wr.to_wallet_id = wp.id
        WHERE wr.from_wallet_id = :wallet_id
    """)
    outgoing = db.execute(outgoing_query, {"wallet_id": wallet_id})
    wallet["outgoing_relationships"] = [dict(row._mapping) for row in outgoing]

    # Get relationships (incoming)
    incoming_query = text("""
        SELECT
            wr.*,
            wp.address as from_address,
            wp.label as from_label,
            wp.entity_type as from_entity_type
        FROM wallet_relationships wr
        JOIN wallet_profiles wp ON wr.from_wallet_id = wp.id
        WHERE wr.to_wallet_id = :wallet_id
    """)
    incoming = db.execute(incoming_query, {"wallet_id": wallet_id})
    wallet["incoming_relationships"] = [dict(row._mapping) for row in incoming]

    # Get exchange connections
    exchange_query = text("""
        SELECT * FROM exchange_connections
        WHERE wallet_id = :wallet_id
    """)
    exchanges = db.execute(exchange_query, {"wallet_id": wallet_id})
    wallet["exchange_connections"] = [dict(row._mapping) for row in exchanges]

    return wallet

@router.get("/transaction-graph")
async def get_transaction_graph(db: Session = Depends(get_db)):
    """Get complete transaction graph for visualization"""

    # Get all wallets as nodes
    wallets_query = text("""
        SELECT id, address, label, entity_type, risk_score, is_exchange, is_mixer
        FROM wallet_profiles
    """)
    wallets = db.execute(wallets_query)
    nodes = [dict(row._mapping) for row in wallets]

    # Get all relationships as edges
    edges_query = text("""
        SELECT
            from_wallet_id,
            to_wallet_id,
            total_amount,
            transaction_count,
            relationship_type
        FROM wallet_relationships
    """)
    edges = db.execute(edges_query)
    links = [dict(row._mapping) for row in edges]

    return {
        "nodes": nodes,
        "links": links
    }

@router.get("/exchange-connections")
async def get_exchange_connections(
    db: Session = Depends(get_db),
    jurisdiction: Optional[str] = None
):
    """Get exchange connections with law enforcement info"""

    query = """
        SELECT
            ec.*,
            wp.address,
            wp.label as wallet_label,
            wp.entity_type,
            wp.risk_score
        FROM exchange_connections ec
        JOIN wallet_profiles wp ON ec.wallet_id = wp.id
        WHERE 1=1
    """
    params = {}

    if jurisdiction:
        query += " AND ec.jurisdiction = :jurisdiction"
        params["jurisdiction"] = jurisdiction

    query += " ORDER BY ec.total_volume_eur DESC"

    result = db.execute(text(query), params)
    connections = [dict(row._mapping) for row in result]

    return {
        "connections": connections,
        "total": len(connections)
    }

@router.get("/law-enforcement-report/{incident_id}")
async def generate_law_enforcement_report(incident_id: int, db: Session = Depends(get_db)):
    """Generate law enforcement report for incident"""

    # Get incident
    incident_query = text("SELECT * FROM incidents WHERE id = :id")
    incident_result = db.execute(incident_query, {"id": incident_id})
    incident_row = incident_result.fetchone()

    if not incident_row:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = dict(incident_row._mapping)

    # Get linked crypto transactions
    crypto_query = text("""
        SELECT * FROM crypto_transactions
        WHERE linked_incident_id = :incident_id
    """)
    crypto = db.execute(crypto_query, {"incident_id": incident_id})
    transactions = [dict(row._mapping) for row in crypto]

    # Get wallet profiles involved
    wallet_addresses = set()
    for tx in transactions:
        if tx.get('from_address'):
            wallet_addresses.add(tx['from_address'])
        if tx.get('to_address'):
            wallet_addresses.add(tx['to_address'])

    wallets = []
    for address in wallet_addresses:
        wallet_query = text("SELECT * FROM wallet_profiles WHERE address = :address")
        wallet_result = db.execute(wallet_query, {"address": address})
        wallet_row = wallet_result.fetchone()
        if wallet_row:
            wallets.append(dict(wallet_row._mapping))

    # Get exchange connections for these wallets
    exchange_contacts = []
    for wallet in wallets:
        if wallet.get('id'):
            exchange_query = text("""
                SELECT * FROM exchange_connections WHERE wallet_id = :wallet_id
            """)
            exchanges = db.execute(exchange_query, {"wallet_id": wallet['id']})
            exchange_contacts.extend([dict(row._mapping) for row in exchanges])

    return {
        "incident": incident,
        "transactions": transactions,
        "wallets": wallets,
        "exchange_contacts": exchange_contacts,
        "report_generated": True
    }
