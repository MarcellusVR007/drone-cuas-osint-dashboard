# QUICK TELEGRAM SEARCH - Before 15:30 KMar Presentation

## IMMEDIATE PRIORITY SEARCHES (Next 30 Minutes)

### Search 1: Amsterdam Schiphol (Incident #1, Sept 27)
**Search in Telegram Global Search**:
```
Schiphol surveillance €
```
```
Amsterdam airport intelligence payment
```
```
EHAM Bitcoin
```

**Time range**: Filter for July-Sept 2025

**What to look for**:
- Posts mentioning "Schiphol" or "EHAM" or "Amsterdam"
- Payment amounts (€1500, €2000)
- Bitcoin addresses (bc1... or 1... or 3...)
- Intelligence requirements (photos, documentation)

---

### Search 2: Copenhagen (Incident #20, Sept 22)
**Search in Telegram Global Search**:
```
Copenhagen airport drone €
```
```
Denmark airports surveillance Bitcoin
```
```
EKCH intelligence payment
```

**Time range**: Filter for July-Sept 2025

**What to look for**:
- Multiple Danish airports mentioned together
- Coordinated campaign indicators
- "Tier 1" or "high priority" language

---

### Search 3: Brussels (Incident #5, Nov 4-7)
**Search in Telegram Global Search**:
```
Brussels airport surveillance €
```
```
Belgium airports Bitcoin
```
```
EBBR intelligence payment
```

**Time range**: Filter for Sept-Oct 2025

---

## HOW TO SEARCH (Telegram Desktop - Best Results)

### Step 1: Open Telegram Desktop
Better search functionality than mobile app

### Step 2: Use Global Search Bar
- Click search icon (top left)
- Type search query
- Click "Search for messages"

### Step 3: Filter Results
- Look for channels/groups (not private chats)
- Check post dates (must be BEFORE incidents)
- Look for posts with:
  - ✓ Payment amounts (€, $, BTC)
  - ✓ Target locations (cities, airports)
  - ✓ Intelligence requirements
  - ✓ Contact methods (@username, Signal)

### Step 4: Save Findings
For each relevant post found:
1. Copy full message text
2. Note channel name
3. Note post date/time
4. Screenshot (evidence)

---

## QUICK DATA ENTRY (After Search)

### Option 1: Manual Entry Tool
```bash
cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard
python3 backend/manual_telegram_entry.py
```

Choose **Option 2: Quick Entry** for fastest input.

### Option 2: Text File (Very Quick)
Create file: `telegram_findings.txt`

Format per post:
```
===== POST 1 =====
Channel: @ChannelName
Date: 2025-08-15
Location: Amsterdam
Payment: 1500
Content:
[paste full text here]

===== POST 2 =====
...
```

---

## REALISTIC EXPECTATIONS (30-Minute Search)

### Likely Results:
- **Best case**: 3-5 relevant posts
- **Good case**: 1-2 strong matches
- **Worst case**: 0 posts (channels deleted/private)

### Why Low Results Are OK:
Even finding 1-2 posts will:
- ✓ Demonstrate Telegram correlation methodology
- ✓ Show attribution chain concept
- ✓ Prove predictive timeline (post + 14-30 days = incident)
- ✓ Justify need for systematic monitoring

---

## ALTERNATIVE: PUBLIC OSINT SOURCES

If Telegram search yields nothing, try:

### Google Search:
```
site:t.me "Schiphol" "€" "surveillance" 2025
site:t.me "Copenhagen" "airport" "Bitcoin" 2025
```

### Archive.org:
```
https://web.archive.org/web/*/https://t.me/s/*
```

Search for archived Telegram channel pages mentioning your keywords.

---

## FOR YOUR 15:30 PRESENTATION

### If You Find Posts:
Present as **PROOF OF CONCEPT**:
- "We discovered X recruitment posts targeting Dutch airports"
- "Timeline correlation: Post dated [date], incident dated [date] = [X] days later"
- "Payment structure: €[amount] in Bitcoin to wallet [address]"
- "Handler identified: @[username]"

### If You Find Nothing:
Present as **INTELLIGENCE GAP**:
- "Current dataset: 2 demo posts (insufficient)"
- "Recommendation: Deploy systematic Telegram monitoring"
- "Target channels: [list from telegram_intelligence.py]"
- "Expected yield: 50-100 posts over 90-day lookback"
- "Enables: Attribution chains, predictive alerts, handler tracking"

---

## SEARCH CHECKLIST

Before 15:30, try to find:
- [ ] At least 1 post mentioning Schiphol (validates Incident #1)
- [ ] At least 1 post mentioning Copenhagen (validates Incident #20)
- [ ] Any posts with Bitcoin addresses (enables blockchain forensics demo)
- [ ] Any posts with payment amounts (demonstrates bounty economics)
- [ ] Any posts from Aug-Sept 2025 (proves timeline correlation)

**Time budget**: 30 minutes maximum, then prepare presentation.

---

## BACKUP PLAN (If No Time)

Present with **EXISTING 2 DEMO POSTS** + framework:
1. Show current 2 posts in Threat Intel view
2. Explain classification algorithm (amateur vs professional)
3. Demonstrate Copenhagen analysis (100% state actor)
4. Present `TELEGRAM_SCRAPING_GUIDE.md` as future roadmap
5. Request resources for systematic monitoring

**Key message**: "We have proof of concept. Now we need resources to scale."

---

## AFTER PRESENTATION

Full Telegram intelligence gathering:
1. Set up Telethon library (pip install telethon)
2. Get API credentials (https://my.telegram.org)
3. Run `backend/telegram_scraper.py --days 90`
4. Schedule cron job (every 6 hours)
5. Build 50-100 post dataset over next 2 weeks

**This will enable**:
- Real attribution chains
- Predictive alerting
- Handler profiling
- Bitcoin forensics
- Network disruption operations
