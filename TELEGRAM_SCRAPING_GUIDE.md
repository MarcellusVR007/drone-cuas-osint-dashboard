# Telegram Intelligence Gathering - Implementation Guide

## Problem: We Need More Data!

**Current situation**: 2 demo Telegram posts
**Required**: 50-100+ posts to build real patterns

**Why it matters**:
- Incident correlation (post date → incident date = 14-30 days)
- Bitcoin wallet tracking (same handler across campaigns)
- Target prediction (new bounty = high risk location)
- Attribution chains (handler → operative mapping)

---

## Option 1: Automated Scraping (Best - Requires Setup)

### Requirements:
```bash
pip install telethon
```

### Setup Steps:

1. **Get Telegram API Credentials**:
   - Go to https://my.telegram.org
   - Login with your phone number
   - Click "API development tools"
   - Create new application
   - Save `api_id` and `api_hash`

2. **Configure** (`backend/telegram_config.py`):
```python
TELEGRAM_API_ID = 12345678  # Your API ID
TELEGRAM_API_HASH = "abcdef1234567890"  # Your API hash
TELEGRAM_PHONE = "+31612345678"  # Your phone number
```

3. **Run Scraper**:
```bash
python3 backend/telegram_scraper.py --days 90 --channels all
```

### Target Channels (Need to Find):

**Known Recruitment Channels** (Examples - may be taken down):
- `@XakNetTeam_Recruitment`
- `@GRU_Handler_Bot`
- `@AirportWatch_EU`

**Public OSINT Channels** (Search these):
- `@osint_aggregator`
- `@cyber_security_channel`
- `@darknet_news`
- `@crypto_bounties`

**How to Find More Channels**:
1. Search Telegram for keywords: "airport surveillance", "drone intelligence", "crypto bounty"
2. Monitor channels that discuss hybrid warfare
3. Check who reposts known recruitment content
4. Use Telegram search operators

### Automated Schedule:
```bash
# Add to crontab
0 */6 * * * cd /path/to/project && python3 backend/telegram_scraper.py --incremental
```

---

## Option 2: Manual OSINT (Quick - Start Now)

### Manual Search Process:

1. **Open Telegram Desktop** (better search than mobile)

2. **Search Global Messages**:
   - Search bar → "airport surveillance €"
   - Search bar → "Bitcoin drone intelligence"
   - Search bar → "Amsterdam airport photo"
   - Search bar → "Copenhagen drone"
   - Date filter: Last 6 months

3. **Check Public Channels**:
   - Join OSINT/cybersecurity channels
   - Monitor for reposted bounty content
   - Track handlers/usernames mentioned

4. **Save Findings**:
   - Copy message text
   - Note: Channel name, post date, Bitcoin addresses
   - Screenshot (for evidence)

5. **Manual Database Entry**:
```bash
python3 backend/manual_telegram_entry.py
# Follow prompts to enter post details
```

---

## Option 3: Web Scraping Telegram (No API Required)

### Using Telegram Web Archives:

Some Telegram channels are publicly indexed. Use:

1. **Google Search**:
```
site:t.me "airport surveillance" "€" "Bitcoin"
site:t.me "drone intelligence" "payment" 2025
```

2. **Archive.org**:
```
https://web.archive.org/web/*/https://t.me/*
```

3. **OSINT Tools**:
- Telegago (Telegram search engine)
- Telegram Analytics platforms
- Social media aggregators

---

## What to Look For (Detection Patterns)

### Bounty Post Indicators:

✅ **Payment Terms**:
- "€1500 per airport"
- "Bitcoin payment: bc1q..."
- "Initial: €500, Final: €900"
- "Performance bonus: €500"

✅ **Target Specifications**:
- Airport ICAO codes (EHAM, EKCH, EDDF)
- City names (Amsterdam, Copenhagen, Brussels)
- "Tier 1 targets: €2000"
- "Military base surveillance"

✅ **Intelligence Requirements**:
- "Photo documentation required"
- "Daily monitoring (30 days)"
- "Military aircraft movements"
- "Flight tracking data"

✅ **Operational Security**:
- "VPN mandatory"
- "Burner phone recommended"
- "Cover story: aviation hobby"
- "Public WiFi only"

✅ **Equipment Lists**:
- "Camera (phone OK, DSLR better)"
- "Binoculars 200mm+"
- "ADS-B receiver (bonus €200)"
- "Drone for aerial views"

✅ **Contact Methods**:
- "@Username_Recruitment"
- "Signal: [number]"
- "Tor: [onion address]"
- "Verification code: SKYWATCH-2025"

---

## Priority Search Targets

### Based on Existing Incidents:

1. **Amsterdam Schiphol** (Incident #1, Sept 27):
   - Search: "Schiphol" OR "EHAM" OR "Amsterdam airport"
   - Time range: July-Sept 2025
   - Expected: Tier 1 bounty post (€2000)

2. **Copenhagen** (Incident #20, Sept 22):
   - Search: "Copenhagen" OR "EKCH" OR "Denmark airports"
   - Time range: July-Sept 2025
   - Hypothesis: Multiple bounty posts (5 airports)

3. **Brussels** (Incident #5, Nov 4-7):
   - Search: "Brussels" OR "EBBR" OR "Liège"
   - Time range: Sept-Oct 2025
   - Pattern: Coordinated campaign

4. **Brunsbüttel Nuclear** (Multiple incidents):
   - Search: "Brunsbüttel" OR "nuclear power"
   - Time range: All 2025
   - Expected: NO bounty posts (state actor operation)

---

## Data Quality Checklist

For each post found, extract:

- [ ] **Post date** (YYYY-MM-DD HH:MM)
- [ ] **Channel/username** (e.g., @Handler_Name)
- [ ] **Content** (full text, up to 5000 chars)
- [ ] **Payment amount** (€ or $)
- [ ] **Payment currency** (EUR, USD, BTC)
- [ ] **Bitcoin addresses** (bc1... or 1... or 3...)
- [ ] **Target location** (city/airport name)
- [ ] **Target type** (airport, military_base, nuclear_facility)
- [ ] **Intelligence requirements** (photos, tracking, etc.)
- [ ] **Equipment mentioned** (drones, cameras, etc.)
- [ ] **Handler usernames** (@XakNet, @GRU_Handler, etc.)

---

## Expected Results

### Success Metrics:

**Baseline** (Current): 2 posts
**Good**: 20-30 posts (enables basic correlation)
**Excellent**: 50-100 posts (enables prediction modeling)
**Ideal**: 100+ posts (full attribution chains)

### What You'll Find:

1. **Recruitment Campaigns**:
   - Regular posts (every 2-3 weeks)
   - Same handler, different targets
   - Payment progression (€1000 → €1500 → €2000)

2. **Target Prioritization**:
   - Tier 1: Major airports (€2000)
   - Tier 2: Regional airports (€1500)
   - Tier 3: Secondary targets (€1000)

3. **Temporal Patterns**:
   - Post frequency increases before incidents
   - Same locations reappear (repeat targeting)
   - Payment amounts correlate with risk level

4. **Bitcoin Wallets**:
   - Same wallet across multiple campaigns = same handler
   - Wallet age indicates campaign duration
   - Transaction history shows operative payments

---

## Integration with Dashboard

Once posts are collected:

### 1. Import to Database:
```bash
python3 backend/import_telegram_posts.py --file posts.json
```

### 2. Run Correlation Analysis:
```bash
python3 backend/correlate_incidents_telegram.py
# Output: Which incidents match which Telegram posts (±30 days)
```

### 3. Update Dashboard:
- Patterns view: Shows Telegram correlation per pattern
- Threat Intel view: Enriched with post dates
- New view: "Telegram Timeline" (post → incident visualization)

---

## Legal & Ethical Considerations

**✅ Legal**:
- Public Telegram channels/groups (no privacy violation)
- OSINT methodology (open-source intelligence)
- Law enforcement coordination (share with authorities)

**⚠️ Caution**:
- DO NOT infiltrate private/closed channels without authorization
- DO NOT engage with handlers (creates operational risk)
- DO share findings with law enforcement (FIOD, MIVD, etc.)

**🎯 Purpose**:
- Counter-intelligence (detect threats before incidents)
- Attribution (identify handlers and operatives)
- Disruption (enable law enforcement action)
- Protection (safeguard critical infrastructure)

---

## Quick Start (Now):

### Step 1: Manual Search (5 minutes)
Open Telegram, search: `"Schiphol" "€" "surveillance"`

### Step 2: Document Findings
Save to: `telegram_posts_manual.txt`

### Step 3: Share with Team
Forward to law enforcement contacts

### Step 4: Setup Automated (Later)
Install Telethon, configure API, run scraper

---

## Next Steps After Data Collection:

1. **Correlation Analysis**: Match posts to incidents
2. **Handler Profiling**: Track same handlers across campaigns
3. **Bitcoin Tracking**: Follow payment flows
4. **Predictive Alerts**: New post = new target warning
5. **Law Enforcement**: Share with FIOD/MIVD for action

