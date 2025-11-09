# Render Deployment Checklist - Voor Morgen

## Status: Ready for Demo ✓

De render.yaml is compleet geconfigureerd met:
- ✓ Web service met keep-alive functionaliteit
- ✓ Watchdog worker voor monitoring
- ✓ Alle environment variables

---

## Pre-Demo Checklist

### 1. Push naar GitHub
```bash
git push origin main
```
**Status:** 5 commits klaarstaan lokaal (waaronder de nieuwe render.yaml)

### 2. Render Setup (Eerste Keer)

#### A. Connect GitHub Repository
1. Ga naar [render.com](https://render.com)
2. Click **New** → **Blueprint**
3. Connect je GitHub account
4. Selecteer repository: `MarcellusVR007/drone-cuas-osint-dashboard`
5. Render detecteert automatisch `render.yaml`

#### B. Configureer Environment Variables (Watchdog)
De web service krijgt automatisch de env vars uit render.yaml, maar de watchdog heeft één handmatige setting nodig:

1. Na deployment, ga naar de **watchdog service**
2. Environment tab
3. Voeg toe:
   ```
   WATCHDOG_TARGET_URL = https://drone-cuas-dashboard.onrender.com/health
   ```
   (Vervang met je actual Render URL)

### 3. Verify Deployment

#### Test de Health Endpoints
```bash
# Basic health check
curl https://drone-cuas-dashboard.onrender.com/health
# Expected: {"status":"ok"}

# Detailed API health
curl https://drone-cuas-dashboard.onrender.com/api/health
# Expected: JSON met timestamp en service info

# Dashboard stats
curl https://drone-cuas-dashboard.onrender.com/api/stats
# Expected: JSON met incident counts, drone types, etc.
```

#### Check de Watchdog Logs
1. Ga naar Render dashboard
2. Open de **drone-cuas-watchdog** worker service
3. Bekijk Logs tab
4. Verwacht output elke 3 minuten:
   ```
   [2024-11-09T19:00:00Z] Watchdog agent monitoring https://... every 180s
   [2024-11-09T19:03:00Z] ✓ Health check succeeded (status 200)
   ```

#### Check de Keep-Alive Logs
1. Open de **drone-cuas-dashboard** web service
2. Bekijk Logs tab
3. Verwacht output elke 9 minuten:
   ```
   ↻ Keep-alive ping ok -> https://.../health
   ```

---

## Demo Flow voor Morgen

### 1. Dashboard Tonen
```
Open: https://drone-cuas-dashboard.onrender.com
```

**Features om te demonstreren:**
- **Dashboard Overview**: 34 incidents, 30 restricted areas, 16 drone types
- **Interactive Map**: Leaflet kaart met markers voor incidents
- **Incident List**: Filter op datum, land, purpose
- **Stats**: Top targeted locations, common drone types
- **API Docs**: Swagger UI op `/docs`

### 2. API Demonstratie

#### Incidents ophalen
```bash
curl https://drone-cuas-dashboard.onrender.com/api/incidents?limit=5
```

#### Top drone types
```bash
curl https://drone-cuas-dashboard.onrender.com/api/stats | jq '.top_drone_types'
```

#### Spatial query (incidents near Brussels Airport)
```bash
curl https://drone-cuas-dashboard.onrender.com/api/incidents/spatial/near/1
```

### 3. Monitoring & Reliability Features

**Highlight:**
- ✓ Dual keep-alive system (built-in + watchdog)
- ✓ Auto-recovery from Render free-tier spin-down
- ✓ Health monitoring every 3 minutes
- ✓ 34 EU drone incidents pre-loaded
- ✓ Production-ready architecture

---

## Architecture Overview (Voor Technical Questions)

### Services Deployed
```yaml
1. Web Service (drone-cuas-dashboard)
   - FastAPI backend + Vue.js frontend
   - Port: 10000 (Render default)
   - Keep-alive: Self-ping elke 9 minuten
   - Region: Frankfurt (EU)

2. Worker Service (drone-cuas-watchdog)
   - Health monitoring
   - Check interval: 3 minuten
   - Alert threshold: 3 consecutive failures
   - Webhook support voor notifications
```

### Database
- SQLite file-based (`data/drone_cuas.db`)
- 34 pre-loaded OSINT incidents
- Auto-initialized on startup

### Keep-Alive Strategy
```
┌─────────────────────────────────────────┐
│  External Monitoring (Watchdog Worker)  │
│  Checks every 3 min                     │
│  → Alerts on failure                    │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Web Service                            │
│  - Serves API & Frontend                │
│  - Self-ping every 9 min                │
│  - /health endpoint                     │
└─────────────────────────────────────────┘
```

---

## Troubleshooting (Als Iets Niet Werkt)

### Issue: Service is niet bereikbaar
**Check:**
1. Render dashboard → Service status = "Live"
2. Recent deploy succesvol? (geen build errors)
3. Logs tonen "Application startup complete"

**Fix:** Redeploy via Render dashboard

### Issue: Keep-alive werkt niet
**Check:**
1. Environment variables zijn gezet (zie boven)
2. `RENDER_EXTERNAL_URL` matches actual URL
3. Logs tonen keep-alive pings

**Fix:** Update `RENDER_EXTERNAL_URL` en redeploy

### Issue: Watchdog geeft geen output
**Check:**
1. `WATCHDOG_TARGET_URL` is correct gezet
2. Worker service is "Running" in Render dashboard

**Fix:** Set `WATCHDOG_TARGET_URL` handmatig

### Issue: Database is leeg
**Check:**
1. `data/drone_cuas.db` bestaat
2. Logs tonen "Loaded X incidents"

**Fix:** Build command draait `rm -f data/drone_cuas.db` - dit is normaal
        Startup script laadt automatisch de data

---

## Post-Demo: Next Steps

### Phase 2 Features to Discuss
- [ ] Automated news scanning (daily_news_scan.py al klaar!)
- [ ] RSS feed integration voor real-time updates
- [ ] Email alerts voor nieuwe high-threat incidents
- [ ] Pattern detection dashboard
- [ ] Intervention effectiveness tracking
- [ ] Export to PDF reports

### Potential Upgrades
- [ ] Switch to PostgreSQL (betere multi-user support)
- [ ] Upgrade Render plan (geen spin-down)
- [ ] Add authentication (OAuth2/LDAP)
- [ ] Connect to EASA/CAA APIs
- [ ] Machine learning voor pattern detection

---

## Environment Variables Reference

### Web Service (drone-cuas-dashboard)
| Variable | Value | Auto-configured? |
|----------|-------|------------------|
| `RENDER` | `true` | ✓ Yes (via render.yaml) |
| `RENDER_EXTERNAL_URL` | `https://...` | ✓ Yes (generateValue) |
| `KEEP_ALIVE_INTERVAL` | `540` | ✓ Yes (9 minutes) |
| `PYTHONUNBUFFERED` | `1` | ✓ Yes |

### Worker Service (drone-cuas-watchdog)
| Variable | Value | Auto-configured? |
|----------|-------|------------------|
| `WATCHDOG_TARGET_URL` | `https://.../health` | **⚠ Manual setup** |
| `WATCHDOG_INTERVAL_SECONDS` | `180` | ✓ Yes (3 minutes) |
| `WATCHDOG_TIMEOUT_SECONDS` | `10` | ✓ Yes |
| `WATCHDOG_FAILURE_THRESHOLD` | `3` | ✓ Yes |
| `PYTHONUNBUFFERED` | `1` | ✓ Yes |

---

## Quick Commands

### Local Testing
```bash
# Start dashboard
python3 app.py

# Test health
curl http://127.0.0.1:8000/health

# View API docs
open http://127.0.0.1:8000/docs
```

### Production Testing
```bash
# Health check
curl https://drone-cuas-dashboard.onrender.com/health

# Stats
curl https://drone-cuas-dashboard.onrender.com/api/stats

# Incidents
curl https://drone-cuas-dashboard.onrender.com/api/incidents?limit=5
```

---

**Status:** Ready for deployment ✓
**Last Updated:** November 9, 2024
**Local Commits:** 5 ready to push
**Next Action:** `git push origin main` + Render blueprint deployment
