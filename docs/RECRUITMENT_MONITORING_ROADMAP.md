# 🎯 Recruitment Monitoring Roadmap
**GRU Spotter Recruitment Intelligence Platform**

Doel: Identificeer en monitor GRU recruitment activities voor lokale spotters in EU/Benelux.

---

## 📊 Current State (November 2025)

### ✅ Implemented:
- **Telegram Monitoring** - 2283 posts scraped from Russian war channels
- **Recruitment Classifier** - Pattern matching voor recruitment indicators (0-100 score)
- **Flight Forensics** - Post-incident analysis (Orlan-10 launch zones, maritime correlation)
- **Database Schema** - SQLite met incidents, social_media_posts, recruitment_analysis tables
- **Reddit Framework** - Ready to scrape r/aviation, r/flightradar24, r/ATC (needs API credentials)
- **Aviation Forum Strategy** - PPRuNe, FlightRadar24, Airliners.net targeting plan

### 📈 Current Data:
- 49 real drone incidents (EU/Benelux)
- 2283 Telegram posts (Ukrainian war propaganda/news)
- 0 confirmed recruitment posts (current channels are news/propaganda, not recruitment)
- Recruitment classifier: All posts scored LOW (0-20/100)

### 🔍 Key Insight:
Huidige Telegram channels zijn **news OVER recruitment**, niet recruitment posts zelf.
Recruitment gebeurt in:
1. Private Telegram groups (invite-only)
2. West-European platforms (Reddit, aviation forums)
3. VK/OK.ru voor Russische diaspora in EU
4. Dark web forums (Tor)

---

## 🗺️ Roadmap: Multi-Platform Recruitment Monitoring

### Phase 1: West-European Platforms (Maand 1-2)

#### 1.1 Reddit Monitoring ✅ **READY TO DEPLOY**
**Status**: Framework complete, needs API credentials

**Target Subreddits**:
- r/aviation (1.2M members) - General aviation
- r/flightradar24 (50k members) - **HIGH PRIORITY** - Active trackers
- r/aviationspotters - Spotters community
- r/ATC - Air Traffic Controllers (HIGH value targets)
- r/aviation_memes - Sometimes used for coded communication

**Implementation**:
```bash
# 1. Get Reddit API credentials (5 min)
https://www.reddit.com/prefs/apps

# 2. Set environment variables
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
export REDDIT_USER_AGENT="DroneOSINT/1.0 by marcel_researcher"

# 3. Run scraper
python3 backend/reddit_aviation_scraper.py
```

**Expected Results**:
- 50-100 posts/day across all subreddits
- ~1-2 suspicious posts/week
- Database: `reddit_posts` table

**Success Metrics**:
- [ ] 1000+ posts scraped in first week
- [ ] 5+ suspicious posts flagged (score >30)
- [ ] 1+ manual review reveals actual recruitment attempt

---

#### 1.2 Aviation Forums Manual Monitoring ⏳ **NEXT PRIORITY**
**Timeline**: Week 3-4

**Target Forums**:
1. **PPRuNe.org** (Professional Pilots Rumour Network) - 🔴 HIGH PRIORITY
   - Target: Professional pilots, ATC
   - Why: Access to restricted airspace, military flight knowledge
   - Method: Daily manual check of "Military Aviation" section

2. **FlightRadar24 Forums** - 🟠 MEDIUM PRIORITY
   - Target: Aviation enthusiasts, trackers
   - Why: Real-time flight following culture
   - Method: API scraping (needs reverse engineering)

3. **Airliners.net Forums** - 🟡 MEDIUM PRIORITY
   - Target: Aviation photographers
   - Why: Airport access discussions common
   - Method: BeautifulSoup scraping

**Implementation Plan**:
- Week 3: Manual PPRuNe monitoring (build baseline)
- Week 4: Automated scraping prototype
- Week 5-6: Deploy production scrapers

**Red Flags to Monitor**:
```
Pattern 1: Payment for Aviation Data
"Looking for someone near Schiphol who can provide weekly photos
 of cargo aircraft. €200/week via Bitcoin."
Risk: HIGH - Direct recruitment

Pattern 2: Specific Aircraft Tracking
"Need real-time tracking of Russian government flights (RA-96016).
 DM me for details."
Risk: CRITICAL - Intelligence gathering

Pattern 3: Military + Anonymity
"Anyone have access to Kleine Brogel Air Base? Can pay for photos.
 Contact via Telegram @handlerxyz"
Risk: CRITICAL - Espionage recruitment
```

---

### Phase 2: Russian Social Networks (Maand 2-3)

#### 2.1 VK.com (ВКонтакте) Monitoring 📋 **ROADMAP**
**Russian Facebook - Popular in Oost-Europa + Russian diaspora in EU**

**Why Critical for EU Recruitment**:
- ✅ Large Russian-speaking population in EU (2M+ in Germany, 500k+ in Netherlands/Belgium)
- ✅ GRU heeft toegang tot VK databases (ownership connection)
- ✅ Less scrutiny dan Western platforms
- ✅ Natural platform voor Russian diaspora recruitment

**Target Groups/Pages**:
- Aviation enthusiast groups (in Russian)
- EU expat communities (Berlin, Amsterdam, Brussels)
- Military history groups (recruiting military-interested individuals)
- Cryptocurrency/finance groups (payment-focused targets)

**Technical Implementation**:
```python
# VK API - Official but rate-limited
import vk_api

# Target searches:
# - "авиация" + "Европа" (aviation + Europe)
# - "заработок" + "фото" (earnings + photo)
# - "наблюдение" + "аэропорт" (surveillance + airport)
```

**Expected Results**:
- 100-200 posts/day from targeted groups
- ~5-10 suspicious posts/week (higher than Reddit - Russian language = less moderation)
- Potential to find ACTUAL recruitment posts (not just news)

**Challenges**:
- GDPR compliance (VK is Russian company)
- API rate limiting
- Russian language processing (need translation)
- Account suspension risk

**Success Metrics**:
- [ ] 10+ VK groups monitored
- [ ] 1000+ posts scraped weekly
- [ ] 10+ suspicious posts flagged
- [ ] 1+ confirmed recruitment attempt

---

#### 2.2 OK.ru (Odnoklassniki) Monitoring 📋 **ROADMAP**
**Russian social network - Older demographics (40+ years)**

**Why Monitor**:
- ✅ Older demographics = more vulnerable to manipulation
- ✅ Less tech-savvy users = easier to recruit
- ✅ Popular among Russian diaspora in Eastern EU (Poland, Baltic states)

**Target Demographics**:
- Russian expats 40-60 years old
- Blue-collar workers with airport/port access
- Financial difficulties (susceptible to payment offers)

**Implementation**:
- Similar to VK scraping
- Focus on regional groups (Berlin Russians, Amsterdam expats)
- Monitor job boards/classifieds sections

**Expected Results**:
- 50-100 posts/day
- ~2-5 suspicious posts/week
- Higher conversion rate (less tech-savvy = clearer recruitment language)

---

### Phase 3: Dark Web & Encrypted Platforms (Maand 3-4)

#### 3.1 Tor Forum Monitoring 📋 **ADVANCED**
**Dark web forums - Maximum anonymiteit**

**Target Forums**:
- Dread (Reddit clone on Tor)
- RaidForums successors
- Russian-language forums

**Why Monitor**:
- ✅ Handler communication likely happens here AFTER initial contact
- ✅ Payment coordination (crypto wallets, escrow)
- ✅ Advanced recruitment (handlers recruiting sub-handlers)

**Challenges**:
- Legal grey area (monitoring dark web)
- Tor network = slow, unstable
- Account trust building required
- Law enforcement coordination essential

**Recommendation**:
⚠️ Only implement with law enforcement partnership (AIVD, MIVD, Europol)

---

#### 3.2 Encrypted Messaging Monitoring 📋 **INVESTIGATIVE**
**Signal, Wickr, Element (Matrix)**

**Reality Check**:
❌ Cannot monitor encrypted messages without:
- Court order + platform cooperation
- Device seizure
- Informant with handler access

**Alternative Approach**:
✅ Monitor PUBLIC mentions of these platforms:
- "Contact me on Signal: +31..."
- "Wickr ID: handler_europe"
- "Element room: #recruitment:..."

**Implementation**:
- Add keyword detection to existing scrapers
- Flag any post mentioning encrypted platforms + payment
- Automatic high-priority alert

---

## 🎯 Immediate Action Plan (Next 7 Days)

### Day 1-2: Reddit Deployment
```bash
1. Get Reddit API credentials
2. Run reddit_aviation_scraper.py
3. Collect 1000+ posts
4. Analyze recruitment patterns
5. Tune classifier weights
```

### Day 3-4: PPRuNe Manual Monitoring
```bash
1. Create PPRuNe account
2. Monitor "Military Aviation" section
3. Document suspicious posts manually
4. Build red flag database
```

### Day 5-7: VK Research
```bash
1. Research VK API access
2. Identify target VK groups
3. Build scraper prototype
4. Test on 5-10 groups
```

---

## 📊 Success Metrics (Month 1)

### Quantitative:
- [ ] 5000+ posts scraped (Reddit + Telegram combined)
- [ ] 50+ posts flagged as suspicious (score >20)
- [ ] 10+ posts manual review confirmed interesting
- [ ] 1+ post reported to authorities (if CRITICAL)

### Qualitative:
- [ ] Understand recruitment language patterns
- [ ] Identify geographic clusters (which EU regions targeted?)
- [ ] Build handler profile database
- [ ] Establish baseline for normal vs suspicious activity

---

## 🚨 Escalation Procedure

### If CRITICAL recruitment post found:

1. **Immediate**:
   - Screenshot + archive post
   - Document all metadata (author, timestamp, platform)
   - Flag in database as CRITICAL
   - DO NOT interact with post

2. **Within 24 hours**:
   - Report to AIVD/MIVD (Netherlands)
   - Report to Europol (EU-wide)
   - Document in incident log

3. **Within 1 week**:
   - Analyze for patterns (other posts by same author)
   - Check for related accounts (sock puppets)
   - Build network graph

**CRITICAL Indicators**:
- Direct payment offer (>€500) for intelligence gathering
- Specific military/government facility mentioned
- Encrypted communication channel provided
- Multiple recruitment attempts (systematic campaign)

---

## 🔧 Technical Architecture

### Data Flow:
```
[Platform APIs] → [Scrapers] → [Raw Data DB] → [Classifier] → [Scored Posts]
                                                      ↓
                                              [Manual Review]
                                                      ↓
                                          [Handler Profile DB]
                                                      ↓
                                            [Network Graph]
```

### Database Schema Extensions:

```sql
-- Handler profiles (identified recruiters)
CREATE TABLE handlers (
    id INTEGER PRIMARY KEY,
    platform TEXT,  -- 'telegram', 'reddit', 'vk', etc
    username TEXT,
    account_creation_date TIMESTAMP,
    total_posts INTEGER,
    suspicious_posts INTEGER,
    recruitment_score INTEGER,  -- 0-100
    payment_offers_count INTEGER,
    target_regions TEXT,  -- JSON: ["NL", "BE", "DE"]
    crypto_wallets TEXT,  -- JSON: ["bc1...", "XMR..."]
    linked_incidents TEXT,  -- JSON: [1, 5, 12]
    notes TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP
);

-- Spotter network (recruited individuals - if identified)
CREATE TABLE spotters (
    id INTEGER PRIMARY KEY,
    handler_id INTEGER,  -- FK to handlers
    platform_username TEXT,
    real_name TEXT,  -- Only if publicly disclosed
    location TEXT,
    recruitment_date TIMESTAMP,
    payment_received REAL,
    tasks_completed INTEGER,
    linked_incidents TEXT,  -- JSON
    status TEXT,  -- 'active', 'arrested', 'unknown'
    FOREIGN KEY (handler_id) REFERENCES handlers(id)
);

-- Network connections (handler → spotter → incident)
CREATE TABLE recruitment_network (
    id INTEGER PRIMARY KEY,
    handler_id INTEGER,
    spotter_id INTEGER,
    incident_id INTEGER,
    connection_type TEXT,  -- 'recruitment', 'payment', 'task'
    confidence REAL,  -- 0.0-1.0
    evidence TEXT,  -- JSON: URLs, screenshots
    FOREIGN KEY (handler_id) REFERENCES handlers(id),
    FOREIGN KEY (spotter_id) REFERENCES spotters(id),
    FOREIGN KEY (incident_id) REFERENCES incidents(id)
);
```

---

## 💰 Budget Estimate (MVP - Month 1)

| Item | Cost | Notes |
|------|------|-------|
| Reddit API | **FREE** | Rate limits sufficient for MVP |
| VK API | **€0-50/month** | Depends on rate limits |
| Proxy rotation (for scraping) | **€20/month** | BrightData/Oxylabs |
| Cloud storage (backups) | **€5/month** | AWS S3 |
| Translation API (Russian→English) | **€10/month** | Google Translate API |
| **TOTAL** | **€35-85/month** | Scales with data volume |

---

## 📚 Resources & References

### APIs:
- Reddit: https://www.reddit.com/dev/api
- VK: https://dev.vk.com/en/api
- Telegram (unofficial): https://github.com/tdlib/td

### OSINT Tools:
- Bellingcat Toolkit: https://docs.google.com/document/d/1BfLPJpRtyq4RFtHJoNpvWQjmGnyVkfE2HYoICKOGguA
- OSINT Framework: https://osintframework.com/
- IntelTechniques: https://inteltechniques.com/tools/

### Legal/Ethical:
- GDPR Guidelines: https://gdpr.eu/
- EU Cyber Threat Intelligence: https://www.enisa.europa.eu/

---

## ✅ Sign-off

**Created**: 2025-11-16
**Author**: Claude (AI Agent)
**For**: Marcel - Drone CUAS OSINT Dashboard
**Status**: DRAFT - Awaiting approval for Phase 1 execution

**Next Steps**:
1. Marcel approves Phase 1 (Reddit + PPRuNe)
2. Get Reddit API credentials
3. Deploy scrapers
4. Weekly progress reports

---

**End of Roadmap**
