# Database Migrations

This directory contains database migration scripts for the drone-cuas-osint-dashboard project.

## 📋 Overview

All database schema changes MUST be done through migrations to:
- Track changes over time
- Allow rollback if needed
- Document why changes were made
- Prevent data loss

## 🗂️ Migration Naming Convention

```
YYYYMMDD_HHMMSS_descriptive_name.py
```

Example: `20251114_123045_add_sentiment_analysis.py`

## 📝 Migration Template

See `.claude/change-protocol.md` for the full migration template.

Quick example:

```python
"""
Migration: [Description]
Author: [Agent name]
Date: [YYYY-MM-DD HH:MM:SS]
Reversible: [YES/NO]
Risk: [LOW/MEDIUM/HIGH/CRITICAL]
"""

def upgrade(db_path='data/drone_cuas.db'):
    """Apply migration"""
    # SQL here
    pass

def downgrade(db_path='data/drone_cuas.db'):
    """Rollback migration"""
    # Rollback SQL here
    pass

def verify(db_path='data/drone_cuas.db'):
    """Verify migration was applied"""
    # Verification checks
    pass
```

## ⚠️ CRITICAL RULES

1. **NEVER run migrations without user approval**
2. **ALWAYS create backup before migration**
3. **ALWAYS test migration on copy first**
4. **Document all changes in migration file**

## 🚀 Running Migrations

```bash
# 1. Create backup
cp data/drone_cuas.db data/backup_$(date +%Y%m%d_%H%M%S).db

# 2. Run migration
python3 migrations/YYYYMMDD_HHMMSS_name.py

# 3. Verify
sqlite3 data/drone_cuas.db ".schema table_name"
```

## 📊 Migration Status

| ID | Date | Description | Status | Rollback Available |
|----|------|-------------|--------|-------------------|
| - | - | No migrations yet | - | - |

## 🔙 Rollback Procedure

If a migration breaks something:

```bash
# 1. Stop application
killall python3

# 2. Restore backup
cp data/backup_TIMESTAMP.db data/drone_cuas.db

# 3. Restart application
python3 -m uvicorn backend.main:app --reload
```

## 📞 Need Help?

Check `.claude/change-protocol.md` section "DATABASE MIGRATION PROTOCOL"
