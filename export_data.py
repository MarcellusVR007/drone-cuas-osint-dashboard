#!/usr/bin/env python3
"""
Export all database data to JSON for version control and deployment.
This allows us to keep the database in .gitignore while still syncing data.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

def export_database():
    """Export all tables to JSON format."""
    db_path = Path("data/drone_cuas.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "tables": {}
    }

    # Export each table
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        # Convert rows to dictionaries
        table_data = []
        for row in rows:
            table_data.append(dict(row))

        export_data["tables"][table] = table_data
        print(f"✓ Exported {len(table_data)} rows from {table}")

    conn.close()

    # Save to JSON
    output_path = Path("data/database_export.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Database exported to {output_path}")
    print(f"  Total tables: {len(tables)}")
    print(f"  Total size: {output_path.stat().st_size / 1024:.1f} KB")

    # Print summary
    print("\n📊 Summary:")
    for table, data in export_data["tables"].items():
        print(f"  - {table}: {len(data)} records")

if __name__ == "__main__":
    export_database()
