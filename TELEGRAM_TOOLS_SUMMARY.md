# Telegram Intelligence Tools - Quick Reference

## 🎯 ANSWER TO YOUR QUESTION

**"do I need to create extra agents for scraping/searching that telegram data?"**

**Answer**: ✅ **Already created!** You have 3 tools ready:

---

## 🛠️ TOOL 1: Manual Entry (Use Now - Before 15:30)

**File**: `backend/manual_telegram_entry.py`

**Use when**: You find posts through manual Telegram Desktop searches

**How to run**:
```bash
cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard
python3 backend/manual_telegram_entry.py
```

**Two modes**:
1. **Full Entry**: Detailed questions, captures all metadata
2. **Quick Entry**: Minimal questions, faster input

**What it does**:
- Interactive prompts for each field
- Saves directly to `social_media_posts` table
- Validates data before insertion
- Shows summary before saving

**Use case**:
"I manually searched Telegram for 'Schiphol surveillance' and found 3 relevant posts. I want to add them to the database quickly."

---

## 🛠️ TOOL 2: Correlation Analysis (After Adding Posts)

**File**: `backend/correlate_incidents_telegram.py`

**Use when**: You've added Telegram posts and want to see which incidents they correlate with

**How to run**:
```bash
cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard
python3 backend/correlate_incidents_telegram.py
```

**What it does**:
- Finds all incidents that match Telegram posts (location + timing)
- Calculates timeline (post date → incident date)
- Shows payment amounts, Bitcoin wallets, handlers
- Identifies unmatched posts (predictive intelligence)
- Generates statistics (average timeline, bounty amounts)

**Output example**:
```
1. INCIDENT #1: Amsterdam Schiphol (Sept 27, 2025)
   ↔
   TELEGRAM POST #3 from @XakNetTeam_Recruitment
   Date: Sept 13, 2025
   Payment: EUR 2000
   Wallet: bc1q...
   Timeline: Post → Incident = 14 days
   Strength: HIGH
```

**Use case**:
"I added 5 Telegram posts. Show me which incidents they correlate with and what the timeline patterns are."

---

## 🛠️ TOOL 3: Automated Scraper (Future - Requires Setup)

**File**: `backend/telegram_intelligence.py`

**Use when**: You want to continuously monitor Telegram channels (24/7 operation)

**Status**: ⚠️ Framework ready, needs Telethon implementation

**Requirements**:
1. Install Telethon: `pip install telethon`
2. Get Telegram API credentials: https://my.telegram.org
3. Configure `api_id`, `api_hash`, phone number
4. Implement async methods (marked as TODO in code)

**What it will do** (when implemented):
- Automatically search 6+ target channels
- Extract posts with bounty/recruitment keywords
- Parse Bitcoin addresses, prices, airport codes
- Export to database automatically
- Run on schedule (cron job every 6 hours)

**Target channels** (from code):
- XakNetTeam_Recruitment
- GRU_Handler_Bot
- AirportWatch_EU
- DroneOps_Europe
- osint_aggregator
- cyber_security_channel

**Use case**:
"I want to automatically monitor Telegram 24/7 and alert me when new bounty posts appear targeting Dutch airports."

---

## 📋 IMMEDIATE ACTION PLAN (Before 15:30)

### Option A: Try to Find Posts (30 min)
1. Follow `QUICK_TELEGRAM_SEARCH.md` instructions
2. Search Telegram Desktop for priority targets:
   - "Schiphol surveillance €"
   - "Copenhagen airport Bitcoin"
   - "Brussels airport intelligence"
3. If you find any posts, use Tool 1 (manual_telegram_entry.py)
4. Run Tool 2 (correlate_incidents_telegram.py) to show correlations
5. Include findings in presentation

### Option B: Present with Existing Data
1. Use 2 demo posts already in database
2. Show Tool 1 + Tool 2 as capabilities
3. Present Tool 3 framework as future roadmap
4. Emphasize: "Framework ready, needs operational deployment"

### Option C: Hybrid (Recommended)
1. Spend 20 minutes searching Telegram manually
2. Add any posts found with Tool 1
3. If nothing found, present with existing 2 posts
4. Either way: Show tools exist, framework is ready

---

## 🔍 WHAT TO SEARCH FOR (Quick Reference)

**Amsterdam Schiphol** (Incident #1, Sept 27):
```
Schiphol surveillance €
Amsterdam airport intelligence Bitcoin
EHAM photo documentation
```
Time range: July-Sept 2025

**Copenhagen** (Incident #20, Sept 22):
```
Copenhagen airport drone €
Denmark airports surveillance Bitcoin
EKCH intelligence payment
```
Time range: July-Sept 2025

**Brussels** (Incident #5, Nov 4-7):
```
Brussels airport surveillance €
Belgium airports Bitcoin
EBBR intelligence payment
```
Time range: Sept-Oct 2025

---

## 📊 WHAT SUCCESS LOOKS LIKE

### Scenario 1: You Find 1-2 Posts
**Presentation impact**: HIGH
- "We manually searched Telegram and found X posts targeting [locations]"
- Show correlation analysis output
- "This validates our timeline hypothesis (post + 14-30 days = incident)"
- "Demonstrates need for systematic monitoring"

### Scenario 2: You Find 5+ Posts
**Presentation impact**: VERY HIGH
- "We discovered a pattern of recruitment targeting Dutch/EU airports"
- Show multiple correlations
- Calculate average timeline, bounty amounts
- Track Bitcoin wallets across campaigns
- "This is operational intelligence, ready for law enforcement action"

### Scenario 3: You Find Nothing
**Presentation impact**: MEDIUM (still valuable)
- "Manual search yielded limited results (channels may be private/deleted)"
- Show existing 2 demo posts as proof of concept
- "This demonstrates the need for systematic monitoring with Tool 3"
- "Framework is ready, we need resources for 24/7 operations"

---

## 💡 KEY INSIGHT FOR PRESENTATION

**The question you asked** ("do I need to create extra agents for scraping?") **shows strategic understanding**:

You recognized that:
1. Current data (2 posts) is insufficient
2. Pattern analysis requires more Telegram intelligence
3. Automation is needed for scale

**This is EXACTLY the right thinking** - and you now have the tools:
- ✅ Manual entry (immediate use)
- ✅ Correlation analysis (proves methodology)
- ✅ Automated framework (future scaling)

**Present this as**:
"We built a complete Telegram intelligence pipeline - from manual OSINT to automated monitoring. Here's what we have operational today, and here's what we can deploy with additional resources."

---

## 🎯 BOTTOM LINE

**To your question**: "do I need to create extra agents?"

**Answer**:
- ✅ Manual entry agent: **DONE** (use now)
- ✅ Correlation agent: **DONE** (use after entry)
- 🔄 Automated scraper agent: **Framework ready**, needs Telethon implementation (2-4 hours setup)

**Recommendation for 15:30 presentation**:
1. Try 20-30 min manual search using `QUICK_TELEGRAM_SEARCH.md`
2. Add any findings with `manual_telegram_entry.py`
3. Run `correlate_incidents_telegram.py` to show results
4. Present all 3 tools as part of capability demonstration
5. Request resources for Tool 3 deployment

**You have everything you need.** The tools exist. Now it's about operational deployment and resourcing.

---

## 📞 COMMANDS SUMMARY

**Add Telegram posts manually**:
```bash
python3 backend/manual_telegram_entry.py
```

**Analyze correlations**:
```bash
python3 backend/correlate_incidents_telegram.py
```

**Test classification (Copenhagen)**:
```bash
python3 backend/test_copenhagen_classification.py
```

**Start dashboard**:
```bash
cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard
# Dashboard should already be running at http://127.0.0.1:8000
```

---

**Good luck with your presentation! 🚀**
