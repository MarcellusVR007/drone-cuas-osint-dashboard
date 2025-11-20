#!/usr/bin/env python3
"""
Migration: Add Intelligence Collection Tables
Date: 2025-11-18
Description: Adds tables for:
  - Telegram social graph analysis
  - Aviation forum monitoring
  - LinkedIn OSINT
  - Incident correlation engine
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import engine, SessionLocal
from backend.models import Base
from sqlalchemy import inspect, text

def check_table_exists(table_name):
    """Check if a table already exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate():
    """Run the migration"""
    print("=" * 60)
    print("INTELLIGENCE COLLECTION TABLES MIGRATION")
    print("=" * 60)

    # List of new tables being added
    new_tables = [
        "telegram_channels",
        "telegram_messages",
        "telegram_participants",
        "channel_participation",
        "message_forwards",
        "private_channel_leaks",
        "aviation_forum_posts",
        "forum_keyword_matches",
        "linkedin_profiles",
        "persona_matches",
        "incident_correlations"
    ]

    print("\n📋 Checking existing tables...")
    existing_tables = []
    missing_tables = []

    for table in new_tables:
        if check_table_exists(table):
            existing_tables.append(table)
            print(f"  ✓ {table} (already exists)")
        else:
            missing_tables.append(table)
            print(f"  ⊕ {table} (will be created)")

    if not missing_tables:
        print("\n✓ All intelligence tables already exist!")
        return True

    print(f"\n🔨 Creating {len(missing_tables)} new tables...")

    try:
        # Create all tables defined in models.py
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")

        # Verify creation
        print("\n🔍 Verifying new tables...")
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        for table in missing_tables:
            if table in all_tables:
                # Get column count
                columns = inspector.get_columns(table)
                print(f"  ✓ {table} ({len(columns)} columns)")
            else:
                print(f"  ✗ {table} (FAILED TO CREATE)")
                return False

        print("\n" + "=" * 60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print("\nNew capabilities enabled:")
        print("  • Telegram social graph analysis")
        print("  • Message forward tracking")
        print("  • Aviation forum monitoring (PPRuNe, AvHerald)")
        print("  • LinkedIn OSINT via Google dorking")
        print("  • Incident-correlation temporal analysis")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def rollback():
    """Rollback the migration (drop new tables)"""
    print("\n⚠️  ROLLBACK: Dropping intelligence tables...")

    new_tables = [
        "incident_correlations",
        "persona_matches",
        "linkedin_profiles",
        "forum_keyword_matches",
        "aviation_forum_posts",
        "private_channel_leaks",
        "message_forwards",
        "channel_participation",
        "telegram_participants",
        "telegram_messages",
        "telegram_channels",
    ]

    db = SessionLocal()
    try:
        for table in new_tables:
            if check_table_exists(table):
                db.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"  ✓ Dropped {table}")
        db.commit()
        print("\n✓ Rollback complete")
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Intelligence tables migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        success = migrate()
        sys.exit(0 if success else 1)
