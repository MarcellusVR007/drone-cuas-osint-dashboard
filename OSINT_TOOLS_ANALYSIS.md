# OSINT TOOLS ANALYSIS FOR C-UAS INTELLIGENCE
**Datum:** 20 november 2025
**Doel:** Evalueren Spiderfoot, Maltego, Shodan functionaliteiten voor drone/C-UAS intelligence

---

## 🎯 SPIDERFOOT ANALYSIS

### Wat is Spiderfoot?
**Automated OSINT reconnaissance framework** - "set and forget" intelligence gathering

### Core Capabilities:
1. **Automated footprinting** - Passive reconnaissance
2. **200+ modules** - DNS, WHOIS, social media, leaked data, dark web
3. **Entity correlation** - Automatic relationship discovery
4. **Continuous monitoring** - Alert on new findings

### Relevante Modules voor C-UAS:

#### 🔴 **HIGH VALUE voor Drone Intelligence:**

**1. Social Media Intelligence (SOCMINT)**
```python
# Modules:
- sfp_instagram: Instagram profile/post scraping
- sfp_twitter: Twitter/X account monitoring
- sfp_telegram: Telegram channel discovery (JA! We hebben dit al)
- sfp_youtube: YouTube channel/video analysis
```
**C-UAS Use Case:**
- Drone operator recruitment posts (Instagram, TikTok)
- FPV drone communities op Twitter/X
- YouTube tutorials voor drone modifications
- **Actie:** Integreer Instagram/TikTok scraping voor visual intelligence

**2. Domain/Infrastructure Intelligence**
```python
# Modules:
- sfp_dnsresolve: DNS resolution voor command servers
- sfp_whois: WHOIS data voor attribution
- sfp_subdomain_takeover: Detect vulnerable C2 infrastructure
- sfp_ssl_certificate: SSL cert analysis
```
**C-UAS Use Case:**
- C2 server identification (drone control servers)
- Attribution via domain registration data
- Infrastructure mapping voor GRU operations
- **Actie:** Build domain tracker voor suspect drone C2 servers

**3. Leaked Data & Breach Detection**
```python
# Modules:
- sfp_haveibeenpwned: Email breach detection
- sfp_leakix: Infrastructure leaks
- sfp_dehashed: Credential leaks
- sfp_ghostproject: Password dumps
```
**C-UAS Use Case:**
- Identify compromised accounts gebruikt voor drone ops
- Find leaked credentials van operators
- Dark web intel op drone sales/services
- **Actie:** Monitor breach data voor drone operator emails

**4. Phone Number & Person Intelligence**
```python
# Modules:
- sfp_truecaller: Phone number lookup
- sfp_numverify: Phone validation
- sfp_hunter: Email finder
- sfp_fullcontact: Person enrichment
```
**C-UAS Use Case:**
- Operator identification via phone numbers in posts
- Link phone numbers → Telegram accounts → operations
- Build dossiers op suspected operators
- **Actie:** Phone number extraction from Telegram messages

#### 🟡 **MEDIUM VALUE:**

**5. Dark Web Monitoring**
```python
# Modules:
- sfp_onyphe: Dark web search
- sfp_darksearch: Tor search engine
- sfp_psbdmp: Pastebin dumps
```
**C-UAS Use Case:**
- Drone-for-hire services op dark web
- Payment discussions (crypto wallets)
- Leaked operational plans

**6. Geolocation Intelligence**
```python
# Modules:
- sfp_ipinfo: IP geolocation
- sfp_shodan: Internet-connected devices (zie Shodan sectie)
```

#### ⚪ **LOW VALUE voor C-UAS:**
- Email validation (spam/marketing)
- Company data (Crunchbase, etc.)
- Stock market intelligence

---

## 🕸️ MALTEGO ANALYSIS

### Wat is Maltego?
**Graph-based intelligence platform** - Visual relationship mapping & transformation engine

### Core Capabilities:
1. **Visual link analysis** - Interactive network graphs
2. **Transforms** - Automated entity enrichment (API queries)
3. **Entity types** - Person, Phone, Email, Website, Location, etc.
4. **Graph algorithms** - Shortest path, centrality, clustering

### Maltego Entities Relevant voor C-UAS:

#### 🔴 **HIGH VALUE Entities:**

**1. Person → Phone → Telegram Chain**
```
[Person] --owns--> [Phone Number] --registered--> [Telegram Account] --posts--> [Drone Content]
```
**Transform:**
- Input: Phone number in Telegram message
- Query: Truecaller, Telegram API, social media
- Output: Person identity, location, other accounts
- **C-UAS Value:** Operator identification

**2. Telegram Channel → Forward Network**
```
[Channel A] --forwards--> [Channel B] --forwards--> [Channel C]
                |                          |
            [Incident]                [Location]
```
**Transform:**
- Input: Telegram channel
- Query: Message forwards, mentions
- Output: Network graph van coordinated channels
- **C-UAS Value:** Command chain mapping (WAT WE NU HEBBEN!)

**3. Crypto Wallet → Payment → Person**
```
[Bitcoin Address] --transacts--> [Exchange] --KYC--> [Person Identity]
```
**Transform:**
- Input: Crypto address from Telegram
- Query: Blockchain explorer, exchange leaks
- Output: Person behind payment
- **C-UAS Value:** Financial attribution

**4. IP Address → Infrastructure → Organization**
```
[IP Address] --hosts--> [C2 Server] --owned-by--> [Organization/Person]
```
**Transform:**
- Input: IP from drone C2 traffic
- Query: WHOIS, Shodan, DNS
- Output: Infrastructure owner
- **C-UAS Value:** C2 attribution

#### 🟡 **MEDIUM VALUE Transforms:**

**5. Location → Incidents → Patterns**
```
[GPS Coordinates] --near--> [Restricted Area] --has--> [Incidents]
```

**6. Email → Breaches → Credentials**
```
[Email] --found-in--> [Breach] --leaked--> [Password]
```

#### ⚪ **LOW VALUE:**
- Company org charts
- Stock relationships
- Marketing intelligence

### Maltego Integration Strategy:

**Optie A: Custom Transforms (Python)**
```python
# Build custom Maltego transforms:
class TelegramChannelToForwardNetwork(Transform):
    def do_transform(self, channel_username):
        # Query our database
        forwards = get_forward_network(channel_username)
        # Return Maltego entities
        return [MaltegoEntity('telegram.Channel', username) for username in forwards]
```

**Optie B: Export to Maltego Format**
```python
# Export our graph data → Maltego XML
def export_to_maltego(graph):
    maltego_xml = generate_maltego_graph(
        entities=graph.nodes,
        links=graph.edges
    )
    return maltego_xml
```

**Recommendation:** **Optie B is sneller** - We hebben de data al (command chain, social graph). Export naar Maltego voor visual analysis.

---

## 🔍 SHODAN ANALYSIS

### Wat is Shodan?
**Internet-connected device search engine** - "Google for IoT"

### Core Capabilities:
1. **IoT device discovery** - Find exposed cameras, routers, servers
2. **Port scanning results** - Historical scan data
3. **Vulnerability detection** - CVEs, misconfigurations
4. **Geolocation** - Map devices globally

### Shodan Queries Relevant voor C-UAS:

#### 🔴 **HIGH VALUE Searches:**

**1. Drone Detection Systems**
```
# Find public drone detection sensors:
product:"DJI AeroScope"
product:"DroneShield"
product:"Dedrone"
port:8080 "drone detection"
```
**C-UAS Value:**
- Map existing C-UAS infrastructure
- Find vulnerable/exposed detection systems
- Identify gaps in coverage
- **Actie:** Monthly Shodan scan for drone detection systems Nederland

**2. FPV Drone Streaming Servers**
```
# Find live drone video streams:
port:554 title:"drone"
port:1935 "live stream" drone
"DJI" port:8080
```
**C-UAS Value:**
- Detect active drone operations
- Geo-locate drone control stations
- Monitor FPV racing events (dual-use intel)

**3. Vulnerable C2 Infrastructure**
```
# Find exposed drone control systems:
"autopilot" port:14550  # MAVLink protocol
"ArduPilot"
"PX4"
port:5760 "ground control"
```
**C-UAS Value:**
- Identify vulnerable drone C2 servers
- Potential hijacking targets (defensive)
- Attribution via infrastructure patterns

**4. WiFi Pineapple / Rogue Access Points**
```
# Used for drone jamming/hijacking:
"WiFi Pineapple"
"deauth" port:80
ssid:"DJI-" -port:443
```
**C-UAS Value:**
- Detect jamming equipment near restricted areas
- Identify hostile actors with counter-drone tech

**5. IP Cameras Near Restricted Areas**
```
# Monitor locations:
city:"Amsterdam" port:80 "IP Camera"
geo:"52.308,4.764,5"  # Schiphol area
has_screenshot:true port:8080
```
**C-UAS Value:**
- CCTV intelligence near target locations
- Detect surveillance of restricted areas

#### 🟡 **MEDIUM VALUE:**

**6. ISP Infrastructure**
```
# Track network patterns:
asn:"AS1103"  # SURFnet (Dutch edu)
country:"NL" org:"KPN"
```

**7. VPN/Proxy Servers**
```
# Operational security analysis:
"OpenVPN" country:"NL"
"WireGuard"
```

#### ⚪ **LOW VALUE:**
- Random IoT devices (fridges, etc.)
- Corporate websites

### Shodan API Integration:

```python
import shodan

api = shodan.Shodan(API_KEY)

# Search for drone detection systems in NL
results = api.search('product:"drone detection" country:"NL"')

for result in results['matches']:
    print(f"IP: {result['ip_str']}")
    print(f"Port: {result['port']}")
    print(f"Organization: {result.get('org', 'N/A')}")
    print(f"Location: {result['location']}")
```

**Actie:** Build automated Shodan monitor voor:
1. Drone detection systems (monthly scan)
2. Vulnerable C2 infrastructure (alert on new findings)
3. IP cameras near Schiphol/Eindhoven (weekly)

---

## 🎯 INTEGRATION PRIORITY MATRIX

| Tool | Feature | C-UAS Value | Implementation Effort | Priority |
|------|---------|-------------|----------------------|----------|
| **Spiderfoot** | Social media scraping | ⭐⭐⭐⭐⭐ | Medium | **P0 - DO NOW** |
| **Spiderfoot** | Phone number lookup | ⭐⭐⭐⭐ | Low | **P0 - DO NOW** |
| **Spiderfoot** | Breach monitoring | ⭐⭐⭐⭐ | Low | **P1 - This week** |
| **Maltego** | Graph export | ⭐⭐⭐⭐⭐ | Low | **P0 - DO NOW** |
| **Maltego** | Custom transforms | ⭐⭐⭐ | High | P2 - Later |
| **Shodan** | Drone detection systems | ⭐⭐⭐⭐⭐ | Low | **P0 - DO NOW** |
| **Shodan** | C2 infrastructure | ⭐⭐⭐⭐ | Low | **P1 - This week** |
| **Shodan** | IP cameras | ⭐⭐⭐ | Low | P1 - This week |
| **Spiderfoot** | Dark web monitoring | ⭐⭐ | Medium | P3 - Future |
| **Spiderfoot** | Domain tracking | ⭐⭐⭐ | Low | P2 - Later |

---

## 🚀 RECOMMENDED IMPLEMENTATION PLAN

### **Phase 1: Quick Wins (Vandaag)**

**1. Shodan Integration**
```python
# File: backend/shodan_monitor.py
# - Scan for drone detection systems NL
# - Alert on new C2 infrastructure
# - Export results to database
```
**Output:** Monthly intelligence report on C-UAS infrastructure

**2. Maltego Graph Export**
```python
# File: backend/export_maltego_graph.py
# - Export command chain → Maltego XML
# - Export social network → Maltego XML
# - Export incident correlations → Maltego XML
```
**Output:** Visual intelligence graphs voor analysts

**3. Phone Number Extraction**
```python
# File: backend/extract_phone_numbers.py
# - Scan all Telegram messages for phone patterns
# - Lookup via Truecaller API
# - Link to person entities
```
**Output:** Operator identification pipeline

### **Phase 2: Spiderfoot Integration (Deze Week)**

**4. Instagram/TikTok Scraper**
```python
# File: backend/spiderfoot_socmint.py
# - Monitor #drone #fpv hashtags
# - Track known operator accounts
# - Visual analysis (image recognition)
```

**5. Breach Data Monitor**
```python
# File: backend/breach_monitor.py
# - Check operator emails in HaveIBeenPwned
# - Monitor dark web for credential leaks
# - Alert on compromised accounts
```

### **Phase 3: Advanced (Volgende Week)**

**6. Full Spiderfoot Automation**
- Deploy Spiderfoot instance
- Configure custom modules
- Automated weekly scans

---

## 💡 KEY INSIGHTS

### **What Makes These Tools Valuable for C-UAS:**

1. **Spiderfoot** = **Breadth**
   - Cast wide net across 200+ data sources
   - Automated = "set and forget"
   - Best for: Discovery phase, finding new leads

2. **Maltego** = **Depth**
   - Deep dive into specific entities
   - Visual relationship mapping
   - Best for: Attribution, building dossiers

3. **Shodan** = **Infrastructure**
   - Technical/network intelligence
   - Real-time device discovery
   - Best for: C2 detection, vulnerability analysis

### **Combined Power:**
```
Spiderfoot discovers → Maltego maps → Shodan validates
     (OSINT)              (Analysis)      (Technical)
```

**Example workflow:**
1. **Spiderfoot** finds Telegram channel with crypto wallet
2. **Maltego** maps wallet → exchange → person identity
3. **Shodan** finds person's home IP → exposed devices → location confirmation

---

## ✅ CONCLUSION

**Top 3 Implementations for Maximum C-UAS Impact:**

1. **Shodan Drone Detection Monitor** (2 hours)
   - Immediate value: Map C-UAS infrastructure gaps
   - Low effort, high impact

2. **Maltego Graph Export** (3 hours)
   - Leverage existing data
   - Visual intelligence for leadership briefings

3. **Phone Number Intelligence Pipeline** (4 hours)
   - Operator identification
   - Direct attribution capability

**Total effort:** ~1 working day for 3x force multipliers

**ROI:** 🚀🚀🚀🚀🚀

Ready to implement?
