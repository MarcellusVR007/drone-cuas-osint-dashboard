#!/usr/bin/env python3
"""
Blockchain Intelligence Layer for OSINT Dashboard
Tracks Bitcoin wallets, transaction graphs, and exchange connections.
Enables law enforcement handoff with FATF-compliant reporting.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def add_blockchain_schema():
    """Add blockchain intelligence tables"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("🔗 Adding Blockchain Intelligence Schema...")

    # Wallet profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address VARCHAR(255) UNIQUE NOT NULL,
            blockchain VARCHAR(50) DEFAULT 'Bitcoin',
            label VARCHAR(255),
            entity_type VARCHAR(100),
            first_seen DATETIME,
            last_active DATETIME,
            total_received FLOAT DEFAULT 0,
            total_sent FLOAT DEFAULT 0,
            transaction_count INTEGER DEFAULT 0,
            balance FLOAT DEFAULT 0,
            risk_score FLOAT DEFAULT 0,
            exchange_linked VARCHAR(255),
            kyc_entity VARCHAR(255),
            cluster_id INTEGER,
            is_mixer BOOLEAN DEFAULT 0,
            is_exchange BOOLEAN DEFAULT 0,
            is_darknet BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created wallet_profiles table")

    # Wallet relationships (transaction graph)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_wallet_id INTEGER NOT NULL,
            to_wallet_id INTEGER NOT NULL,
            total_amount FLOAT DEFAULT 0,
            transaction_count INTEGER DEFAULT 0,
            first_transaction DATETIME,
            last_transaction DATETIME,
            relationship_type VARCHAR(100),
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(from_wallet_id) REFERENCES wallet_profiles(id),
            FOREIGN KEY(to_wallet_id) REFERENCES wallet_profiles(id)
        )
    """)
    print("  ✓ Created wallet_relationships table")

    # Exchange connections (for law enforcement queries)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchange_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER NOT NULL,
            exchange_name VARCHAR(255) NOT NULL,
            connection_type VARCHAR(100),
            confidence FLOAT DEFAULT 0,
            deposit_address VARCHAR(255),
            withdrawal_address VARCHAR(255),
            first_interaction DATETIME,
            last_interaction DATETIME,
            total_volume_eur FLOAT DEFAULT 0,
            kyc_required BOOLEAN DEFAULT 1,
            jurisdiction VARCHAR(10),
            law_enforcement_contact TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(wallet_id) REFERENCES wallet_profiles(id)
        )
    """)
    print("  ✓ Created exchange_connections table")

    # Law enforcement reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS law_enforcement_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type VARCHAR(100) NOT NULL,
            incident_id INTEGER,
            wallet_addresses TEXT,
            transaction_ids TEXT,
            total_amount_eur FLOAT,
            report_format VARCHAR(50),
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            submitted_to VARCHAR(255),
            submission_date DATETIME,
            reference_number VARCHAR(255),
            status VARCHAR(50) DEFAULT 'draft',
            report_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(incident_id) REFERENCES incidents(id)
        )
    """)
    print("  ✓ Created law_enforcement_reports table")

    conn.commit()
    conn.close()
    print("\n✓ Blockchain intelligence schema created!")

def populate_wallet_profiles():
    """Create wallet profiles for known addresses"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n💰 Populating Wallet Profiles...")

    wallets = [
        # Handler/GRU wallets (suspicious)
        {
            "address": "bc1q7xke9m4p2tn3wl8vhqr9j5s2a8ftn3x9pk4wlh",
            "blockchain": "Bitcoin",
            "label": "VWarrior Handler Wallet - Zuid-Limburg Bounty",
            "entity_type": "threat_actor",
            "first_seen": "2025-11-01 10:00:00",
            "last_active": "2025-11-08 20:30:00",
            "total_received": 15.8,
            "total_sent": 12.3,
            "transaction_count": 47,
            "balance": 3.5,
            "risk_score": 0.95,
            "exchange_linked": None,
            "kyc_entity": None,
            "cluster_id": 1001,
            "is_mixer": 0,
            "is_exchange": 0,
            "is_darknet": 1,
            "notes": "Primary payment wallet for VWarrior Telegram channel. Multiple bounty payments. Linked to GRU operations cluster. No KYC trail."
        },
        {
            "address": "bc1qn4r8d7k2p3tm5wv9hxqf6j8s7a2ftn4xke9m0h",
            "blockchain": "Bitcoin",
            "label": "VWarrior - Brunsbüttel Nuclear Bounty",
            "entity_type": "threat_actor",
            "first_seen": "2025-08-01 14:00:00",
            "last_active": "2025-08-09 09:15:00",
            "total_received": 8.2,
            "total_sent": 7.1,
            "transaction_count": 23,
            "balance": 1.1,
            "risk_score": 0.92,
            "exchange_linked": None,
            "kyc_entity": None,
            "cluster_id": 1001,
            "is_mixer": 0,
            "is_exchange": 0,
            "is_darknet": 1,
            "notes": "Nuclear facility reconnaissance bounty wallet. Same cluster as Zuid-Limburg handler. Likely GRU-operated."
        },

        # Mixing service (intermediate)
        {
            "address": "bc1qmixer5a8b9c2d3e4f5g6h7i8j9k0l1m2n3o4p5",
            "blockchain": "Bitcoin",
            "label": "Wasabi Wallet CoinJoin Mixer",
            "entity_type": "mixer",
            "first_seen": "2024-01-15 00:00:00",
            "last_active": "2025-11-13 08:00:00",
            "total_received": 1250.5,
            "total_sent": 1248.2,
            "transaction_count": 8943,
            "balance": 2.3,
            "risk_score": 0.75,
            "exchange_linked": None,
            "kyc_entity": None,
            "cluster_id": None,
            "is_mixer": 1,
            "is_exchange": 0,
            "is_darknet": 0,
            "notes": "Wasabi Wallet CoinJoin coordinator. Used to obfuscate transaction trails. High volume, low individual amounts."
        },

        # Exchange wallets (KYC trail)
        {
            "address": "bc1qbitonic_nl_deposit_addr123456789abcdef",
            "blockchain": "Bitcoin",
            "label": "Bitonic NL - Deposit Address",
            "entity_type": "exchange",
            "first_seen": "2023-06-01 00:00:00",
            "last_active": "2025-11-13 07:30:00",
            "total_received": 5420.8,
            "total_sent": 5380.2,
            "transaction_count": 2341,
            "balance": 40.6,
            "risk_score": 0.15,
            "exchange_linked": "Bitonic",
            "kyc_entity": "Bitonic B.V. (Netherlands)",
            "cluster_id": 2001,
            "is_mixer": 0,
            "is_exchange": 1,
            "is_darknet": 0,
            "notes": "Bitonic Netherlands exchange. Full KYC/AML compliant. Dutch FIOD jurisdiction. Can be queried by law enforcement."
        },
        {
            "address": "bc1qkraken_eur_hot_wallet_addr9876543210fedcba",
            "blockchain": "Bitcoin",
            "label": "Kraken EUR Hot Wallet",
            "entity_type": "exchange",
            "first_seen": "2022-01-01 00:00:00",
            "last_active": "2025-11-13 09:00:00",
            "total_received": 18250.4,
            "total_sent": 18100.1,
            "transaction_count": 9823,
            "balance": 150.3,
            "risk_score": 0.10,
            "exchange_linked": "Kraken",
            "kyc_entity": "Payward Inc. (USA)",
            "cluster_id": 2002,
            "is_mixer": 0,
            "is_exchange": 1,
            "is_darknet": 0,
            "notes": "Kraken exchange hot wallet (EUR pairs). US-based, responds to Europol/FBI requests. Full transaction logs."
        },
        {
            "address": "bc1qbinance_withdrawal_addr_eu_region123abc",
            "blockchain": "Bitcoin",
            "label": "Binance EU Withdrawal Address",
            "entity_type": "exchange",
            "first_seen": "2021-03-15 00:00:00",
            "last_active": "2025-11-12 18:45:00",
            "total_received": 32100.7,
            "total_sent": 31850.4,
            "transaction_count": 15482,
            "balance": 250.3,
            "risk_score": 0.20,
            "exchange_linked": "Binance",
            "kyc_entity": "Binance Europe (Malta)",
            "cluster_id": 2003,
            "is_mixer": 0,
            "is_exchange": 1,
            "is_darknet": 0,
            "notes": "Binance EU entity. Subject to MiCA regulations. Can be subpoenaed via Maltese authorities."
        },

        # Operative wallets (cash-out attempts)
        {
            "address": "bc1qoperative_cashout_nl_addr_suspected_local",
            "blockchain": "Bitcoin",
            "label": "Suspected Local Operative - Netherlands",
            "entity_type": "operative",
            "first_seen": "2025-11-07 16:20:00",
            "last_active": "2025-11-08 22:15:00",
            "total_received": 0.0456,
            "total_sent": 0.0450,
            "transaction_count": 3,
            "balance": 0.0006,
            "risk_score": 0.85,
            "exchange_linked": "Bitonic",
            "kyc_entity": None,
            "cluster_id": None,
            "is_mixer": 0,
            "is_exchange": 0,
            "is_darknet": 0,
            "notes": "Received 0.0456 BTC (€2100) 18h before Zuid-Limburg incident. Attempted cash-out via Bitonic (€2000 withdrawn to IBAN NL**RABO***5678). KYC records available via Dutch authorities."
        }
    ]

    for wallet in wallets:
        cursor.execute("""
            INSERT INTO wallet_profiles
            (address, blockchain, label, entity_type, first_seen, last_active,
             total_received, total_sent, transaction_count, balance, risk_score,
             exchange_linked, kyc_entity, cluster_id, is_mixer, is_exchange, is_darknet, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wallet["address"], wallet["blockchain"], wallet["label"], wallet["entity_type"],
            wallet["first_seen"], wallet["last_active"], wallet["total_received"],
            wallet["total_sent"], wallet["transaction_count"], wallet["balance"],
            wallet["risk_score"], wallet["exchange_linked"], wallet["kyc_entity"],
            wallet["cluster_id"], wallet["is_mixer"], wallet["is_exchange"],
            wallet["is_darknet"], wallet["notes"]
        ))

    conn.commit()
    print(f"  ✓ Added {len(wallets)} wallet profiles")

    conn.close()

def populate_exchange_connections():
    """Document exchange connections for law enforcement queries"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🏦 Mapping Exchange Connections...")

    # Get wallet IDs
    cursor.execute("SELECT id, address, label FROM wallet_profiles WHERE is_exchange = 0 AND exchange_linked IS NOT NULL")
    operative_wallets = cursor.fetchall()

    exchanges = [
        # Bitonic connection (Zuid-Limburg operative)
        {
            "wallet_id": 7,  # Suspected local operative
            "exchange_name": "Bitonic",
            "connection_type": "cash_out_attempt",
            "confidence": 0.95,
            "deposit_address": "bc1qbitonic_nl_deposit_addr123456789abcdef",
            "withdrawal_address": None,
            "first_interaction": "2025-11-08 20:45:00",
            "last_interaction": "2025-11-08 22:15:00",
            "total_volume_eur": 2000.0,
            "kyc_required": 1,
            "jurisdiction": "NL",
            "law_enforcement_contact": "FIOD (Dutch Tax Investigation): +31 20 574 3774 | crypto@fiod.nl | Contact: Team Digital Assets",
            "notes": "Operative attempted €2000 cash-out to Dutch IBAN (NL**RABO***5678). Bitonic has full KYC: Name, address, ID scan, bank account. Contact FIOD for subpoena."
        },
        # Kraken connection (potential handler cash-out)
        {
            "wallet_id": 1,  # VWarrior handler
            "exchange_name": "Kraken",
            "connection_type": "suspected_cash_out",
            "confidence": 0.70,
            "deposit_address": "bc1qkraken_eur_hot_wallet_addr9876543210fedcba",
            "withdrawal_address": None,
            "first_interaction": "2025-09-15 14:20:00",
            "last_interaction": "2025-10-22 09:30:00",
            "total_volume_eur": 8500.0,
            "kyc_required": 1,
            "jurisdiction": "US",
            "law_enforcement_contact": "Kraken LEA: law-enforcement@kraken.com | +1-855-450-0606 | Requires court order/subpoena",
            "notes": "Handler wallet sent €8500 to Kraken hot wallet Sept-Oct 2025. Likely cash-out via US entity. Requires FBI/Europol formal request."
        }
    ]

    for exchange in exchanges:
        cursor.execute("""
            INSERT INTO exchange_connections
            (wallet_id, exchange_name, connection_type, confidence, deposit_address,
             withdrawal_address, first_interaction, last_interaction, total_volume_eur,
             kyc_required, jurisdiction, law_enforcement_contact, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exchange["wallet_id"], exchange["exchange_name"], exchange["connection_type"],
            exchange["confidence"], exchange["deposit_address"], exchange["withdrawal_address"],
            exchange["first_interaction"], exchange["last_interaction"],
            exchange["total_volume_eur"], exchange["kyc_required"], exchange["jurisdiction"],
            exchange["law_enforcement_contact"], exchange["notes"]
        ))

    conn.commit()
    print(f"  ✓ Mapped {len(exchanges)} exchange connections")

    conn.close()

def populate_wallet_relationships():
    """Map transaction flows between wallets"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🔀 Mapping Wallet Relationships...")

    relationships = [
        # GRU handler → Mixer → Operative
        {
            "from_wallet_id": 1,  # VWarrior handler
            "to_wallet_id": 3,    # Wasabi mixer
            "total_amount": 0.0500,
            "transaction_count": 1,
            "first_transaction": "2025-11-07 14:00:00",
            "last_transaction": "2025-11-07 14:00:00",
            "relationship_type": "obfuscation_attempt",
            "notes": "Handler sent 0.05 BTC to Wasabi mixer (CoinJoin) 24h before operative received payment."
        },
        {
            "from_wallet_id": 3,  # Wasabi mixer
            "to_wallet_id": 7,    # Local operative
            "total_amount": 0.0456,
            "transaction_count": 1,
            "first_transaction": "2025-11-07 16:20:00",
            "last_transaction": "2025-11-07 16:20:00",
            "relationship_type": "payment",
            "notes": "Mixed funds emerged from CoinJoin, sent to operative wallet. €2100 (0.0456 BTC) matches bounty amount."
        },
        {
            "from_wallet_id": 7,  # Local operative
            "to_wallet_id": 4,    # Bitonic exchange
            "total_amount": 0.0450,
            "transaction_count": 1,
            "first_transaction": "2025-11-08 20:45:00",
            "last_transaction": "2025-11-08 20:45:00",
            "relationship_type": "cash_out",
            "notes": "Operative cashed out €2000 via Bitonic to Dutch bank account. KYC trail available."
        }
    ]

    for rel in relationships:
        cursor.execute("""
            INSERT INTO wallet_relationships
            (from_wallet_id, to_wallet_id, total_amount, transaction_count,
             first_transaction, last_transaction, relationship_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel["from_wallet_id"], rel["to_wallet_id"], rel["total_amount"],
            rel["transaction_count"], rel["first_transaction"],
            rel["last_transaction"], rel["relationship_type"], rel["notes"]
        ))

    conn.commit()
    print(f"  ✓ Mapped {len(relationships)} wallet relationships")

    conn.close()

if __name__ == "__main__":
    print("🔗 Blockchain Intelligence System")
    print("=" * 70)

    add_blockchain_schema()
    populate_wallet_profiles()
    populate_exchange_connections()
    populate_wallet_relationships()

    print("\n" + "=" * 70)
    print("✓ Complete! Blockchain intelligence system ready.")
    print("\n📊 What you can now track:")
    print("  - 7 wallet profiles (threat actors, mixers, exchanges, operatives)")
    print("  - 2 exchange connections with law enforcement contacts")
    print("  - 3 transaction flow relationships")
    print("\n🔍 Use Cases:")
    print("  - Law enforcement queries (Bitonic KYC, Kraken subpoena)")
    print("  - Transaction graph analysis (handler → mixer → operative)")
    print("  - Risk scoring (0.95 for GRU wallets, 0.10 for exchanges)")
    print("  - IBAN tracing (Dutch bank account linked to operative)")
    print("\nReady for frontend wallet explorer!")
