# 🔄 Change Management Protocol
**Voor alle AI Agents werkend aan drone-cuas-osint-dashboard**

> **CRITICAL**: Alle code- en database wijzigingen MOETEN door dit protocol voordat ze worden toegepast.

---

## 📋 Protocol Overzicht

**Doel**: Voorkom conflicten tussen meerdere agents, behoud code kwaliteit, bescherm productie data.

**Workflow**: ANNOUNCE → REVIEW → APPROVE → MERGE

---

## 🚦 STAP 1: ANNOUNCE (Verplicht voor ELKE change)

Voordat je IETS wijzigt, presenteer een **Change Proposal**:

```markdown
📋 CHANGE PROPOSAL

Agent: [Jouw naam/ID]
Branch: [feature/naam-van-feature]
Type: [CODE | DATABASE | BEIDE]
Risk Level: [LOW | MEDIUM | HIGH | CRITICAL]

FILES MODIFIED:
- backend/file1.py (+50 lines, -20 lines)
- frontend/file2.js (+15 lines, -5 lines)
- NEW: backend/new_feature.py (200 lines)

DATABASE CHANGES:
- ALTER TABLE social_media_posts ADD COLUMN sentiment TEXT
- CREATE INDEX idx_sentiment ON social_media_posts(sentiment)

REASON:
[Waarom is deze change nodig?]

IMPACT:
- API changes: [YES/NO] - [Details]
- Breaking changes: [YES/NO] - [Details]
- Data migration required: [YES/NO]

TEST STATUS:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

ROLLBACK PLAN:
[Hoe maak je deze change ongedaan als het fout gaat?]
```

**WAIT** voor user approval: `approve`, `reject`, of `modify: [instructions]`

---

## 🔍 STAP 2: CREATE FEATURE BRANCH

```bash
# Check current status
git status

# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/descriptive-name

# Make your changes
[... code changes ...]

# Commit with descriptive message
git add .
git commit -m "feat: Add [feature description]

- Detail 1
- Detail 2

Refs: CHANGE-PROPOSAL-ID"
```

---

## 📊 STAP 3: SHOW DIFF

Laat de gebruiker EXACT zien wat er verandert:

```bash
# Show all changes vs main
git diff main...HEAD

# For large diffs, show summary
git diff --stat main...HEAD

# Show specific file changes
git diff main...HEAD -- backend/specific_file.py
```

**Voor Database Changes**:
```bash
# Show migration SQL
cat migrations/YYYYMMDD_HHMMSS_description.sql

# Preview affected tables
sqlite3 data/drone_cuas.db ".schema table_name"
```

---

## ✅ STAP 4: WAIT FOR APPROVAL

**STOP HIER** - Geen merge zonder expliciete approval!

User responses:
- `approve` → Ga door naar STAP 5
- `reject` → Discard branch: `git checkout main && git branch -D feature/name`
- `modify: [instructions]` → Make changes, show new diff, wait again
- `diff [filename]` → Show detailed diff for specific file

---

## 🔀 STAP 5: MERGE (Alleen na approval)

```bash
# Switch to main
git checkout main

# Pull latest changes (andere agents kunnen gemerged hebben)
git pull origin main

# Check for conflicts
git merge --no-ff feature/your-feature

# If conflicts:
# 1. Resolve manually
# 2. Show user the conflict resolution
# 3. Get approval again
# 4. Then commit

# Push to remote
git push origin main

# Delete feature branch
git branch -d feature/your-feature
```

---

## 💾 DATABASE MIGRATION PROTOCOL

Database changes zijn **EXTRA RISKANT** - volg strict:

### Migration File Template

Maak altijd een migration file in `migrations/`:

```python
# migrations/20251114_123045_add_sentiment_analysis.py
"""
Migration: Add sentiment analysis to social_media_posts
Author: Agent-Claude-1
Date: 2025-11-14 12:30:45
Reversible: YES
Risk: LOW - Only adds columns, no data deletion

Dependencies:
- None (or list dependencies)

Estimated Time: < 1 second
Data Loss Risk: NONE
"""

import sqlite3
from datetime import datetime

def upgrade(db_path='data/drone_cuas.db'):
    """Apply migration - add sentiment columns"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("⏳ Running migration: add_sentiment_analysis...")

    # Migration SQL
    cursor.execute("""
        ALTER TABLE social_media_posts
        ADD COLUMN sentiment TEXT
    """)

    cursor.execute("""
        ALTER TABLE social_media_posts
        ADD COLUMN sentiment_score REAL
    """)

    conn.commit()
    conn.close()

    print("✅ Migration completed successfully")
    return True

def downgrade(db_path='data/drone_cuas.db'):
    """Rollback migration"""
    # SQLite doesn't support DROP COLUMN easily
    # Document workaround
    print("⚠️  SQLite doesn't support DROP COLUMN")
    print("   Manual rollback: Restore from backup")
    return False

def verify(db_path='data/drone_cuas.db'):
    """Verify migration was applied correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check columns exist
    cursor.execute("PRAGMA table_info(social_media_posts)")
    columns = [col[1] for col in cursor.fetchall()]

    assert 'sentiment' in columns, "sentiment column not found"
    assert 'sentiment_score' in columns, "sentiment_score column not found"

    conn.close()
    print("✅ Migration verification passed")
    return True

if __name__ == '__main__':
    # Run migration
    upgrade()
    verify()
```

### Database Change Workflow

1. **Create migration file** (shown above)
2. **Show user**:
   ```
   📋 DATABASE MIGRATION

   File: migrations/20251114_123045_add_sentiment_analysis.py
   Tables Affected: social_media_posts
   Type: ALTER TABLE (add columns)
   Risk: LOW
   Reversible: NO (SQLite limitation)
   Backup Required: YES

   SQL Preview:
   ALTER TABLE social_media_posts ADD COLUMN sentiment TEXT;
   ALTER TABLE social_media_posts ADD COLUMN sentiment_score REAL;
   ```

3. **WAIT for approval**

4. **Create backup BEFORE running**:
   ```bash
   cp data/drone_cuas.db data/backup_$(date +%Y%m%d_%H%M%S).db
   ```

5. **Run migration**:
   ```bash
   python3 migrations/20251114_123045_add_sentiment_analysis.py
   ```

6. **Verify**:
   ```bash
   sqlite3 data/drone_cuas.db "PRAGMA table_info(social_media_posts);"
   ```

---

## ⚠️ CONFLICT RESOLUTION

Als 2+ agents dezelfde file willen wijzigen:

```
🚨 CONFLICT DETECTED

Agent-1 (telegram-scraper):
  Branch: feature/telegram-enhancement
  Files: backend/routers/socmint.py, backend/models.py
  Status: PENDING APPROVAL

Agent-2 (sentiment-analysis):
  Branch: feature/sentiment
  Files: backend/routers/socmint.py
  Status: WANTS TO MODIFY

OVERLAP: backend/routers/socmint.py

OPTIONS:
1. Sequential: Agent-1 first, then Agent-2 rebases on top
2. Parallel: Agents work on different parts, manual merge
3. Cancel: One agent abandons their change

User Decision Required: [1/2/3]?
```

---

## 🎯 RISK LEVELS

**LOW**:
- New files only
- Add-only changes (new functions, no modifications)
- No database changes
- No API changes

**MEDIUM**:
- Modify existing functions
- Add database columns (no deletion)
- Add optional API parameters

**HIGH**:
- Delete/rename functions
- Delete database columns
- Breaking API changes
- Dependency updates

**CRITICAL**:
- Database schema restructuring
- Authentication/security changes
- Data deletion/migration
- Production deployment

---

## 📝 COMMIT MESSAGE FORMAT

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance
- `db`: Database migration

**Example**:
```
feat(socmint): Add sentiment analysis to Telegram posts

- Add sentiment column to social_media_posts table
- Implement sentiment analyzer using TextBlob
- Add API endpoint /api/socmint/sentiment/{post_id}
- Add unit tests for sentiment analysis

Migration: 20251114_123045_add_sentiment_analysis.py
Risk: LOW
Approved-By: Marcel
```

---

## 🔒 PROTECTED FILES

Deze files NOOIT wijzigen zonder expliciete approval + backup:

- `data/drone_cuas.db` - Production database
- `backend/database.py` - Core database logic
- `.env` - Environment variables
- `backend/main.py` - Application entry point

---

## 🧪 TESTING REQUIREMENTS

Voor ELKE change:

**Minimum**:
- [ ] Code runs without errors
- [ ] No breaking changes to existing features
- [ ] Manual testing done

**Recommended**:
- [ ] Unit tests added for new code
- [ ] Integration tests pass
- [ ] API endpoints tested with curl/Postman

**For Database Changes**:
- [ ] Backup created
- [ ] Migration runs successfully
- [ ] Rollback tested (if possible)
- [ ] Data integrity verified

---

## 📦 EXAMPLE: Complete Change Flow

```bash
# 1. ANNOUNCE
echo "📋 CHANGE PROPOSAL: Add flight forensics view"
echo "Files: frontend/index.html, frontend/src/app.js"
echo "Risk: LOW - UI only, no backend changes"

# 2. WAIT for approval...
# User: "approve"

# 3. Create branch
git checkout -b feature/flight-forensics-ui

# 4. Make changes
vim frontend/index.html
vim frontend/src/app.js

# 5. Commit
git add frontend/
git commit -m "feat(ui): Add flight forensics view

- Add Flight Forensics menu item
- Add incident selector dropdown
- Add launch zone visualization
- Add recommendations display

Risk: LOW
Approved-By: Marcel"

# 6. Show diff
git diff main...HEAD --stat

# 7. WAIT for final approval...
# User: "approve"

# 8. Merge
git checkout main
git merge --no-ff feature/flight-forensics-ui
git push origin main

# 9. Cleanup
git branch -d feature/flight-forensics-ui

# Done!
echo "✅ Change merged successfully"
```

---

## 🚨 EMERGENCY ROLLBACK

Als een change de productie breekt:

```bash
# 1. Identify problematic commit
git log --oneline -10

# 2. Create rollback branch
git checkout -b hotfix/rollback-bad-change

# 3. Revert specific commit
git revert <commit-hash>

# 4. Show user what will be reverted
git show <commit-hash>

# 5. WAIT for approval

# 6. Merge rollback
git checkout main
git merge hotfix/rollback-bad-change
git push origin main

# 7. For database: restore backup
cp data/backup_TIMESTAMP.db data/drone_cuas.db
```

---

## ✅ CHECKLIST - Gebruik voor ELKE change

```
Change Checklist - [Feature Name]
Date: [YYYY-MM-DD]
Agent: [Agent ID]

PRE-CHANGE:
[ ] Change proposal written and shown to user
[ ] Risk level assessed
[ ] Backup created (if database change)
[ ] Feature branch created
[ ] User gave initial approval

DURING CHANGE:
[ ] Changes made only in feature branch
[ ] Code tested locally
[ ] No errors in console/logs
[ ] Diff shown to user
[ ] User gave final approval

POST-CHANGE:
[ ] Merged to main
[ ] Pushed to remote
[ ] Feature branch deleted
[ ] Migration verified (if applicable)
[ ] Production tested
[ ] User confirmed working

ROLLBACK PLAN:
[How to undo this change if needed]
```

---

## 📞 SUPPORT

Vragen over het protocol? Check:
1. This document (`.claude/change-protocol.md`)
2. Git best practices: `git help workflows`
3. Ask user for clarification

---

**Version**: 1.0.0
**Last Updated**: 2025-11-14
**Maintained By**: All AI Agents + Marcel
