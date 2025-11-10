#!/usr/bin/env python3
"""
Import data from JSON export file into the database.
This runs on deployment to sync data from version control.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

def import_database():
    """Import data from JSON export into database."""
    export_path = Path("data/database_export.json")
    if not export_path.exists():
        print(f"ℹ️  No export file found at {export_path}, skipping import")
        return False

    db_path = Path("data/drone_cuas.db")

    # Load export data
    with open(export_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)

    print(f"📥 Importing data from {export_data.get('export_timestamp', 'unknown date')}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    tables = export_data.get("tables", {})
    imported_count = {}

    # Import each table
    for table_name, rows in tables.items():
        if not rows:
            print(f"  - {table_name}: No data to import")
            continue

        # Get column names from first row
        columns = list(rows[0].keys())
        placeholders = ','.join(['?' for _ in columns])
        column_names = ','.join(columns)

        # Clear existing data (optional - remove if you want to merge)
        cursor.execute(f"DELETE FROM {table_name}")

        # Insert all rows
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        for row in rows:
            values = [row[col] for col in columns]
            try:
                cursor.execute(insert_sql, values)
            except sqlite3.IntegrityError as e:
                print(f"  ⚠️  Skipping duplicate in {table_name}: {e}")
                continue

        conn.commit()
        imported_count[table_name] = len(rows)
        print(f"  ✓ {table_name}: Imported {len(rows)} records")

    conn.close()

    print(f"\n✓ Import complete!")
    print(f"  Total tables: {len(imported_count)}")

    return True

if __name__ == "__main__":
    import_database()
