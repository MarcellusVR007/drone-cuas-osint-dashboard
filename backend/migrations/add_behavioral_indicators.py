"""
Migration: Add behavioral indicators and classification fields to incidents table
Date: 2025-11-13
Purpose: Enable BOUNTY_AMATEUR vs STATE_ACTOR_PROFESSIONAL classification
"""

import sqlite3
import os

def run_migration():
    """Add new columns to incidents table for behavioral analysis"""

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "drone_cuas.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of new columns to add
    migrations = [
        # Behavioral Indicators
        ("lights_observed", "INTEGER"),  # Boolean: 0=False, 1=True, NULL=unknown
        ("flight_pattern", "VARCHAR(50)"),
        ("time_of_day", "VARCHAR(20)"),
        ("estimated_altitude_m", "INTEGER"),
        ("flight_behavior_notes", "TEXT"),

        # Operational Classification
        ("operational_class", "VARCHAR(50)"),
        ("classification_confidence", "REAL"),
        ("classification_reasoning", "TEXT"),

        # Attribution Chain
        ("telegram_post_id", "INTEGER"),
        ("handler_username", "VARCHAR(100)"),
        ("payment_wallet_address", "VARCHAR(100)"),
        ("attribution_chain", "TEXT"),

        # Strategic Intelligence
        ("strategic_assessment", "TEXT"),
        ("launch_analysis", "TEXT"),
    ]

    # Check which columns already exist
    cursor.execute("PRAGMA table_info(incidents)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    # Add each column if it doesn't exist
    added_columns = []
    for column_name, column_type in migrations:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE incidents ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)
                print(f"✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"✗ Failed to add {column_name}: {e}")
        else:
            print(f"- Column already exists: {column_name}")

    conn.commit()
    conn.close()

    print(f"\n✅ Migration completed! Added {len(added_columns)} new columns.")
    return True

if __name__ == "__main__":
    run_migration()
