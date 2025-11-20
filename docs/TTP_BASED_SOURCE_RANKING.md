# 🎯 TTP-Based Source Ranking
**Reverse Engineering: Waar recruiten state actors spotters in West-Europa?**

## 🔍 Methodologie

**Vraag**: Als jij GRU/MSS officer was die EU spotters moet rekruteren, waar zou je beginnen?

**Aanpak**:
1. Analyseer bekende TTP's van Russian & Chinese intelligence services
2. Map TTP's naar specifieke platforms/communities
3. Rank sources op waarschijnlijkheid basis historical precedent
4. Prioritize monitoring effort accordingly

---

## 📊 Intelligence Service TTP Analysis

### 🇷🇺 Russian Intelligence Services

#### GRU (Main Intelligence Directorate) - Military Intelligence
**Known TTP's**:
- **Unit 29155**: Sabotage, assassinations, recruitment in Europe
- **Unit 26165/74455 (APT28/Fancy Bear)**: Cyber operations, social media manipulation
- **Recruitment Doctrine**: "Motivate with money, blackmail, or ideology"

**Historical Precedent**:
- **Bellingcat investigation (2024)**: GRU recruited MiG-31 pilot via journalist cover, offered $3M + citizenship
- **Czech ammunition depot sabotage (2014)**: Local recruited assets used for explosives placement
- **Salisbury poisoning (2018)**: GRU officers traveled on tourist visas (Alexander Petrov, Ruslan Boshirov)
- **Lithuania railway sabotage (2023)**: Local recruits via Telegram, payment in crypto

**Primary Platforms (GRU)**:
1. **Telegram** - End-to-end encryption, anonymous accounts, Russian-developed
2. **VK.com** - Access to Russian diaspora, GRU has backend access
3. **Gaming forums/Discord** - Young males, anti-establishment sentiment
4. **Aviation forums** - Target-rich (pilots, spotters, ATC)
5. **Dark web forums (Tor)** - Payment coordination, handler communication

**Recruitment Style**:
- Direct approach (not subtle)
- Money first (€500-2000 initial payment)
- Escalation (small tasks → bigger tasks → compromised)
- Telegram as primary communication

---

#### FSB (Federal Security Service) - Domestic Intelligence & Counterintelligence
**Known TTP's**:
- Focus on Russian diaspora (loyalty exploitation)
- Long-term cultivation (sleeper agents)
- Use of "compatriot organizations" (front groups)

**Historical Precedent**:
- **Estonia Bronze Soldier riots (2007)**: FSB mobilized Russian diaspora via community groups
- **Germany spy cases (2020-2023)**: Multiple Russian-Germans arrested for espionage, recruited via cultural centers

**Primary Platforms (FSB)**:
1. **OK.ru (Odnoklassniki)** - Older Russian diaspora, less tech-savvy
2. **VK.com** - Community groups, expat forums
3. **Russian cultural centers** - In-person recruitment (Berlin, Amsterdam, Brussels)
4. **LinkedIn** - Professional targeting (airport workers, logistics)
5. **WhatsApp/Viber** - Russian diaspora communication

**Recruitment Style**:
- Patriotic appeal ("help motherland")
- In-person meetings (cultural events, business conferences)
- Family pressure (relatives in Russia)
- Long-term cultivation (months/years)

---

#### SVR (Foreign Intelligence Service) - Strategic Intelligence
**Known TTP's**:
- Professional, patient, sophisticated
- Target high-value individuals (government, military, industry)
- Deep cover, long-term operations

**Historical Precedent**:
- **Illegals Program (busted 2010)**: Anna Chapman, etc - deep cover agents, years of preparation
- **SVR rarely recruits low-level spotters** - focuses on strategic penetration

**Primary Platforms (SVR)**:
- **Unlikely to recruit spotters** (below their pay grade)
- If involved: LinkedIn, professional conferences, headhunter fronts
- **Bottom line**: SVR doesn't waste time on drone spotters

---

### 🇨🇳 Chinese Intelligence Services

#### MSS (Ministry of State Security) - Civilian Intelligence
**Known TTP's**:
- "Thousand Grains of Sand" - recruit MANY low-level sources
- Focus on technology transfer, economic espionage
- Use of Chinese diaspora, students, businessmen

**Historical Precedent**:
- **Netherlands AIVD report (2024)**: MSS recruiting Chinese students at TU Delft for tech transfer
- **Germany BfV report (2023)**: MSS using LinkedIn to recruit German engineers
- **Belgium (2023)**: Chinese "police stations" used for surveillance of dissidents

**Primary Platforms (MSS)**:
1. **WeChat** - Chinese diaspora communication, MSS has backend access
2. **LinkedIn** - Professional targeting (engineers, researchers, airport workers)
3. **WhatsApp** - Cross-cultural communication
4. **Xiaohongshu (Little Red Book)** - Chinese social media, diaspora
5. **University forums** - Chinese students abroad

**Recruitment Style**:
- Gradual approach (build relationship over months)
- Leverage Chinese identity ("help your country")
- Small payments initially (€100-500)
- Technology/data focus (not military surveillance typically)

**Likelihood for drone spotting**:
- LOWER than Russia (MSS focuses on tech, not military surveillance)
- BUT possible if drones target commercial/tech facilities

---

#### PLA Strategic Support Force (Unit 61398, etc) - Military Cyber
**Known TTP's**:
- Cyber espionage, APT attacks
- Social engineering via spear-phishing
- **Rarely human intelligence (HUMINT)** - mostly cyber

**Primary Platforms**:
- LinkedIn (spear-phishing)
- GitHub (developer targeting)
- **Unlikely to recruit spotters** - cyber-focused

---

## 🎯 TTP-Mapped Source Ranking

### Scenario 1: Russian Attribution (GRU-led operation)

**Ranked by likelihood based on GRU TTP's**:

| Rank | Platform/Source | Likelihood | Reasoning | Access Difficulty |
|------|----------------|------------|-----------|-------------------|
| **1** | **Telegram channels** (aviation, military, urbex) | **95%** | GRU's primary tool, encrypted, anonymous, proven track record (Lithuania, Czech cases) | EASY - Public channels |
| **2** | **VK.com groups** (Russian diaspora in EU) | **85%** | Access to Russian-speakers in Berlin/Amsterdam/Brussels, GRU has backend access | MEDIUM - Need VK API |
| **3** | **Aviation forums** (PPRuNe, FlightRadar24) | **75%** | Target-rich environment (pilots, spotters), GRU precedent (MiG-31 case via "journalist") | EASY - Public forums |
| **4** | **Gaming Discord servers** (military simulation games) | **65%** | Young males, anti-establishment, DCS World/Arma players familiar with military aviation | MEDIUM - Need infiltration |
| **5** | **Reddit** (r/aviation, r/flightradar24) | **60%** | Western platform, anonymous accounts easy, large user base | EASY - Reddit API |
| **6** | **OK.ru** (Odnoklassniki) | **50%** | Older Russian diaspora, less tech-savvy (easier to manipulate) | MEDIUM - Need OK API |
| **7** | **Dark web forums** (Tor, Dread) | **40%** | Payment coordination, handler communication AFTER initial contact | HARD - Requires Tor, trust-building |
| **8** | **LinkedIn** | **30%** | Professional targeting (airport workers), but GRU typically more direct than LinkedIn approach | EASY - LinkedIn API |
| **9** | **4chan/8kun** (/k/ weapons board) | **25%** | Anonymous, military enthusiasts, but chaotic/low signal-to-noise | EASY - Public boards |
| **10** | **Facebook groups** (aviation enthusiast groups) | **20%** | Real names required (less anonymity), GRU prefers pseudonymous platforms | EASY - Facebook Graph API |

**GRU Recruitment Funnel (most likely)**:
```
Step 1: Telegram public channel (aviation/military interest)
        ↓ "DM me for paid work"
Step 2: Private Telegram chat (handler introduces himself)
        ↓ Small task (€200 - photo of airport)
Step 3: Payment via Bitcoin
        ↓ Spotter proves reliability
Step 4: Bigger task (€1000 - drone flight, surveillance)
        ↓ Spotter now compromised (illegal activity)
Step 5: Ongoing tasking (handler has leverage)
```

---

### Scenario 2: Chinese Attribution (MSS-led operation)

**Ranked by likelihood based on MSS TTP's**:

| Rank | Platform/Source | Likelihood | Reasoning | Access Difficulty |
|------|----------------|------------|-----------|-------------------|
| **1** | **LinkedIn** (airport workers, engineers, logistics) | **90%** | MSS proven track record, professional cover, target-rich | EASY - LinkedIn API |
| **2** | **WeChat groups** (Chinese diaspora in EU) | **85%** | MSS has backend access, Chinese nationals in EU vulnerable to pressure | HARD - WeChat restricted outside China |
| **3** | **University forums/groups** (TU Delft, RWTH Aachen, ETH Zurich) | **70%** | Chinese students, researchers, MSS precedent for campus recruitment | MEDIUM - Requires access to edu forums |
| **4** | **WhatsApp groups** (Chinese business associations) | **60%** | Cross-cultural communication, business cover | HARD - Private groups, invitation-only |
| **5** | **Xiaohongshu (Little Red Book)** | **50%** | Chinese social media, diaspora, MSS access | HARD - Chinese platform, language barrier |
| **6** | **Aviation forums** (less likely for MSS - tech focus) | **40%** | Possible but not primary MSS target | EASY - Public forums |
| **7** | **Telegram** (less common for MSS - prefers WeChat) | **30%** | Not MSS's primary tool | EASY - Public channels |
| **8** | **Facebook/Instagram** (Chinese diaspora) | **25%** | Real names, but possible for initial contact | EASY - Social APIs |
| **9** | **Reddit** | **20%** | Western platform, not MSS primary focus | EASY - Reddit API |
| **10** | **VK.com** | **10%** | No Chinese presence, unlikely for MSS | MEDIUM - VK API |

**MSS Recruitment Funnel (most likely)**:
```
Step 1: LinkedIn connection (recruiter/headhunter cover)
        ↓ "Market research opportunity - €500 for interview"
Step 2: In-person meeting (coffee, restaurant)
        ↓ Build rapport, assess ideology
Step 3: Small task (€500 - provide airport shift schedules)
        ↓ Gradual escalation
Step 4: Bigger task (€2000 - access badge, surveillance)
        ↓ Long-term cultivation
Step 5: Asset fully developed (years-long relationship)
```

---

## 🔍 Reverse Engineering Decision Tree

```
START: You are a state intelligence officer
       Goal: Recruit EU-based spotter for drone operations

DECISION POINT 1: What's your nationality?
│
├─ Russian (GRU/FSB)
│  │
│  ├─ Target has Russian heritage?
│  │  ├─ YES → VK.com, OK.ru, cultural centers (FSB style)
│  │  └─ NO → Telegram, aviation forums (GRU style)
│  │
│  └─ Budget for operation?
│     ├─ LOW (€500-2000 per recruit) → Telegram mass recruitment
│     └─ HIGH (€5000+) → Aviation forum professional targeting
│
└─ Chinese (MSS)
   │
   ├─ Target has Chinese heritage?
   │  ├─ YES → WeChat, university groups, family pressure
   │  └─ NO → LinkedIn professional approach
   │
   └─ Target type?
      ├─ Technical (engineer, researcher) → LinkedIn, conferences
      └─ Operational (airport worker) → WhatsApp, business associations

COMMON PATTERN:
All services converge on → Encrypted messaging for operations
(Telegram for Russians, WeChat for Chinese, Signal for cautious operators)
```

---

## 📈 Monitoring Priority Matrix

### Phase 1 (Week 1-2): Quick Wins - High Likelihood + Easy Access

| Platform | Likelihood (Russia) | Likelihood (China) | Access | PRIORITY |
|----------|--------------------|--------------------|--------|----------|
| **Telegram** | 95% | 30% | EASY | ⭐⭐⭐⭐⭐ |
| **Reddit** (r/aviation, r/flightradar24) | 60% | 20% | EASY | ⭐⭐⭐⭐ |
| **Aviation forums** (PPRuNe, FR24) | 75% | 40% | EASY | ⭐⭐⭐⭐ |

**Action**: Deploy existing scrapers immediately (Reddit, Telegram classifiers already built)

---

### Phase 2 (Week 3-4): Russian Diaspora - High Likelihood + Medium Access

| Platform | Likelihood (Russia) | Likelihood (China) | Access | PRIORITY |
|----------|--------------------|--------------------|--------|----------|
| **VK.com** | 85% | 10% | MEDIUM | ⭐⭐⭐⭐ |
| **OK.ru** | 50% | 5% | MEDIUM | ⭐⭐⭐ |

**Action**: Build VK/OK scrapers, focus on Russian expat groups in Berlin, Amsterdam, Brussels

---

### Phase 3 (Week 5-6): Professional Networks - MSS Focus

| Platform | Likelihood (Russia) | Likelihood (China) | Access | PRIORITY |
|----------|--------------------|--------------------|--------|----------|
| **LinkedIn** | 30% | 90% | EASY | ⭐⭐⭐⭐ |
| **WeChat** | 10% | 85% | HARD | ⭐⭐⭐ |

**Action**: LinkedIn scraping (airport workers, engineers near incident locations), WeChat research (hard to access)

---

### Phase 4 (Month 2): Gaming/Niche Communities

| Platform | Likelihood (Russia) | Likelihood (China) | Access | PRIORITY |
|----------|--------------------|--------------------|--------|----------|
| **Discord** (DCS World, Arma servers) | 65% | 10% | MEDIUM | ⭐⭐⭐ |
| **4chan/8kun** (/k/ board) | 25% | 5% | EASY | ⭐⭐ |

**Action**: Infiltrate gaming communities (military simulation players = ideal recruits)

---

### Phase 5 (Month 2+): Dark Web & Encrypted

| Platform | Likelihood (Russia) | Likelihood (China) | Access | PRIORITY |
|----------|--------------------|--------------------|--------|----------|
| **Tor forums** (Dread, Russian forums) | 40% | 15% | HARD | ⭐⭐⭐ |
| **Signal groups** | 30% | 20% | IMPOSSIBLE | ⭐ |

**Action**: Monitor dark web for handler communication (AFTER recruitment happens elsewhere)

---

## 🎯 Immediate Action Plan (Data-Driven)

### Week 1: Deploy Existing Assets
```bash
1. ✅ Telegram monitoring (ALREADY RUNNING - 2283 posts)
2. 🔄 Reddit scraper deployment
   - Get API credentials
   - Target: r/aviation, r/flightradar24, r/aviationspotters, r/ATC
   - Expected: 100+ posts/day

3. 🔄 Aviation forum manual monitoring
   - PPRuNe "Military Aviation" section
   - FlightRadar24 forums
   - Document suspicious posts
```

### Week 2: Russian Diaspora Platforms
```bash
1. Build VK.com scraper
   - Target groups: "Russians in Berlin", "Russians in Amsterdam", "Aviation enthusiasts (RU)"
   - Expected: 200+ posts/day

2. Build OK.ru scraper
   - Target: Older demographics (40-60 years), blue-collar workers
   - Expected: 50+ posts/day
```

### Week 3: Professional Networks (MSS Detection)
```bash
1. LinkedIn scraping
   - Target: Airport workers, aviation engineers, logistics within 50km of incidents
   - Search keywords: "airport", "aviation", "logistics" + location
   - Flag: Job offers, "market research", headhunter contacts

2. WeChat research
   - Research public groups (if accessible)
   - Document Chinese diaspora organizations in EU
```

### Week 4: Gaming Communities (GRU Young Male Targeting)
```bash
1. Discord server list
   - DCS World servers (flight simulation)
   - Arma 3 milsim servers
   - War Thunder communities

2. Monitor for:
   - "Paid aviation photography jobs"
   - "Real-world flight data collection"
   - Suspicious job offers
```

---

## 🚨 Red Flags by Platform

### Telegram (GRU-style)
```
🔴 CRITICAL:
- "€500/week for airport photos"
- "Need someone near [specific location]"
- "DM @username for paid work"
- "Bitcoin payment, anonymous"

🟠 HIGH:
- Aviation channel + financial keywords
- "Looking for people" + location
- Telegram contact in post signature
```

### VK.com (FSB-style)
```
🔴 CRITICAL:
- Posts in Russian offering payment for surveillance
- "Помогите родине" (Help the motherland)
- Private group invitations for "patriotic work"

🟠 HIGH:
- Expat groups with sudden job postings
- "Cultural exchange" with suspicious requirements
- Payment in Rubles/crypto for "simple tasks"
```

### LinkedIn (MSS-style)
```
🔴 CRITICAL:
- Headhunter from Hong Kong/China contacting airport workers
- "Market research" €500 for 1-hour interview
- Job offers WAY above market rate

🟠 HIGH:
- Connection request from recruiter, no company info
- "Consulting opportunity" vague description
- Request to meet in person (coffee, dinner)
```

### Aviation Forums (GRU professional targeting)
```
🔴 CRITICAL:
- Direct payment offers for specific aircraft photos
- "Need someone with airport access"
- "Paying €1000 for tail number tracking"

🟠 HIGH:
- Posts asking for real-time flight updates
- Specific military aircraft interest + payment
- "Contact me privately" for paid collaboration
```

### Gaming Discord (GRU young male recruitment)
```
🔴 CRITICAL:
- "Real-world aviation job opportunity"
- "Looking for DCS pilots for real flights"
- Payment offers for "consulting"

🟠 HIGH:
- Suspicious private messages after posting flight knowledge
- "Aviation industry" recruiters in gaming servers
- Too-good-to-be-true job offers
```

---

## 📊 Expected Results by Platform

| Platform | Expected Posts/Day | Suspicious Posts/Week | Confirmed Recruitment/Month |
|----------|-------------------|-----------------------|------------------------------|
| **Telegram** | 50-100 | 2-5 | 0-1 |
| **Reddit** | 100-200 | 1-3 | 0 (too public) |
| **VK.com** | 200-400 | 5-10 | 1-2 |
| **OK.ru** | 50-100 | 2-3 | 0-1 |
| **LinkedIn** | 20-50 | 1-2 | 0-1 |
| **Aviation forums** | 50-100 | 1-2 | 0-1 |
| **Discord** | 500-1000 | 3-5 | 0-1 |
| **Dark web** | 10-20 | 1-2 | 0 (handler comms) |

**Total Expected**: ~10-30 suspicious posts/week across all platforms
**Actionable Intelligence**: ~1-3 confirmed recruitment attempts/month (if lucky)

---

## ✅ Success Metrics

**Phase 1 Success (Month 1)**:
- [ ] 5000+ posts collected across Telegram, Reddit, VK
- [ ] 50+ flagged suspicious (recruitment score >30)
- [ ] 5+ manual review confirmed interesting
- [ ] 1+ reported to AIVD/MIVD if CRITICAL

**Phase 2 Success (Month 2)**:
- [ ] Pattern recognition (what language, what platforms work)
- [ ] Handler profiling (identify repeat actors)
- [ ] Geographic correlation (incidents → recruitment posts)

**Phase 3 Success (Month 3)**:
- [ ] Network graph (handlers → spotters)
- [ ] Attribution confidence >70% (H1 vs H2)
- [ ] Law enforcement partnership established

---

## 🔑 Key Insight

**Bottom Line**: If recruitment IS happening, we WILL find it by monitoring:
1. **Telegram** (95% for GRU)
2. **VK.com** (85% for FSB)
3. **LinkedIn** (90% for MSS)

**If we monitor all three exhaustively for 2-3 months and find NOTHING**:
→ Strong evidence for **H2 (State Actors using own personnel)**
→ Recruitment not needed = they're sending GRU officers on tourist visas

**Absence of evidence = Evidence of absence** (if search is exhaustive enough)

---

**Created**: 2025-11-16
**Status**: OPERATIONAL GUIDE
**Next Update**: After Week 2 (Reddit + VK deployment complete)
