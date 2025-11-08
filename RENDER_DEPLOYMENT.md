# Render Deployment Guide

## Overview

This guide covers deploying the Drone CUAS OSINT Dashboard to Render and keeping it awake to prevent auto-logout.

---

## 1. Keep-Alive System

### How It Works

The application includes a built-in keep-alive mechanism that prevents Render from spinning down your instance due to inactivity:

1. **Health Check Endpoint** (`backend/main.py` line 65-68)
   ```python
   @app.get("/health", tags=["health"])
   async def health_check():
       """Simple health endpoint for uptime checks."""
       return JSONResponse({"status": "ok"})
   ```

2. **Keep-Alive Thread** (`app.py` line 23-49)
   - Runs as daemon thread in background
   - Periodically pings the `/health` endpoint
   - Default interval: **9 minutes** (configurable)
   - Only activates when deployed on Render

### Environment Variables Required

Add these to your Render service environment variables:

```bash
RENDER=true
RENDER_EXTERNAL_URL=https://drone-cuas-osint-dashboard.onrender.com
KEEP_ALIVE_INTERVAL=540  # 9 minutes in seconds (optional, defaults to 540)
```

### Configuration Steps

1. Go to your Render service dashboard
2. Navigate to **Environment** tab
3. Add the following variables:

   | Key | Value | Notes |
   |-----|-------|-------|
   | `RENDER` | `true` | Enables keep-alive functionality |
   | `RENDER_EXTERNAL_URL` | `https://drone-cuas-osint-dashboard.onrender.com` | Replace with your actual Render URL |
   | `KEEP_ALIVE_INTERVAL` | `540` | Optional: seconds between pings (default 9 min) |

4. Redeploy your service

### Testing Keep-Alive

Once deployed, you can verify the keep-alive is working:

```bash
# Check health endpoint
curl https://drone-cuas-osint-dashboard.onrender.com/health

# Expected response:
{"status":"ok"}

# Monitor Render logs for keep-alive pings
# Look for: "↻ Keep-alive ping ok -> https://..."
```

---

## 2. Alternative Keep-Alive Methods

If the built-in keep-alive doesn't work, you can also use:

### Option A: UptimeRobot (Free)
- Create free account at https://uptimerobot.com
- Add monitor for `https://drone-cuas-osint-dashboard.onrender.com/health`
- Set check interval to every 5 minutes
- Benefit: Also gives you uptime alerts

### Option B: GitHub Actions
Create `.github/workflows/keepalive.yml`:

```yaml
name: Keep Alive

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping health endpoint
        run: curl -f https://drone-cuas-osint-dashboard.onrender.com/health
```

### Option C: Render Cron Jobs
If Render plan supports it, create a cron job that calls `/health` endpoint.

---

## 3. Deployment Checklist

### Pre-Deployment
- [ ] Push all changes to GitHub
- [ ] Test locally: `python3 app.py`
- [ ] Verify database: `python3 load_eu_incidents.py`
- [ ] Test API endpoints with curl

### Render Configuration
- [ ] Create/connect GitHub repository
- [ ] Set environment variables (see above)
- [ ] Configure build command: `pip install -r requirements.txt`
- [ ] Configure start command: `python3 app.py`
- [ ] Set PORT to `8000` (if required)

### Post-Deployment
- [ ] Visit dashboard URL
- [ ] Check FastAPI docs: `/docs`
- [ ] Test API: `/api/incidents?limit=5`
- [ ] Monitor logs for keep-alive pings
- [ ] Test after 15+ minutes of inactivity

---

## 4. Common Issues

### Issue: "KEEP_ALIVE_URL or RENDER_EXTERNAL_URL not set"

**Solution:** Add `RENDER_EXTERNAL_URL` to environment variables in Render dashboard.

### Issue: Keep-Alive Pings Failing

**Solution:** Check that:
1. Health endpoint is accessible: `curl https://your-url/health`
2. `RENDER=true` is set
3. `RENDER_EXTERNAL_URL` matches your actual URL
4. No authentication required on `/health` endpoint

### Issue: Instance Still Spinning Down

**Solution:** Use UptimeRobot as backup (Option A above) or increase keep-alive frequency:
```bash
KEEP_ALIVE_INTERVAL=300  # Check every 5 minutes instead of 9
```

---

## 5. Monitoring

### View Keep-Alive Activity

In Render dashboard, check **Logs** tab for entries like:

```
↻ Keep-alive ping ok -> https://drone-cuas-osint-dashboard.onrender.com/health
```

### Metrics to Monitor

- **Response Time:** Should be <500ms
- **Success Rate:** Should be 100% (200 status)
- **Error Messages:** Check for failed connections

---

## 6. Database Management on Render

### Persistent Data
- Database file is stored in SQLite at `data/drone_cuas.db`
- For production, consider upgrading to PostgreSQL

### Initial Load
Add these steps to Render build command:

```bash
pip install -r requirements.txt && python3 load_eu_incidents.py
```

### Backup & Restore
```bash
# Backup database
python3 << 'EOF'
import shutil
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy("data/drone_cuas.db", f"backups/drone_cuas_{timestamp}.db")
print(f"Backup created")
EOF
```

---

## 7. Environment Variables Reference

### Required
- `RENDER` - Set to `true` to enable keep-alive
- `RENDER_EXTERNAL_URL` - Your Render application URL

### Optional
- `KEEP_ALIVE_INTERVAL` - Seconds between health checks (default: 540)
- `DATABASE_URL` - If using PostgreSQL instead of SQLite
- `LOG_LEVEL` - Application log level (default: info)

### Example Complete .env for Render
```bash
RENDER=true
RENDER_EXTERNAL_URL=https://drone-cuas-osint-dashboard.onrender.com
KEEP_ALIVE_INTERVAL=540
PYTHONUNBUFFERED=1
```

---

## 8. Performance Optimization

### For Render Free Tier
1. Keep-alive interval at 9 minutes (default) to reduce requests
2. Use SQLite (already configured)
3. Compress assets (already done)

### For Paid Tier
1. Upgrade to PostgreSQL
2. Reduce keep-alive interval to 5 minutes
3. Enable caching headers
4. Consider CDN for static files

---

## 9. Troubleshooting Guide

### Check 1: Verify Health Endpoint
```bash
curl -v https://drone-cuas-osint-dashboard.onrender.com/health
```
Should return:
- Status: 200 OK
- Body: `{"status":"ok"}`

### Check 2: Verify Environment Variables
In Render dashboard, Environment tab should show:
```
RENDER = true
RENDER_EXTERNAL_URL = https://drone-cuas-osint-dashboard.onrender.com
```

### Check 3: Review Logs
In Render dashboard, Logs tab should show:
- Application startup messages
- Keep-alive ping confirmations (after 9 minutes)
- Any errors or warnings

### Check 4: Test API Endpoints
```bash
# Test incidents endpoint
curl https://drone-cuas-osint-dashboard.onrender.com/api/incidents?limit=5

# Should return JSON with incident data
```

---

## 10. Upgrading from Render Free to Paid

When upgrading:
1. Keep-alive becomes more reliable
2. Can reduce interval for faster recovery
3. Consider switching to PostgreSQL
4. Enable more advanced monitoring

---

**Last Updated:** November 8, 2025
**Status:** Keep-alive infrastructure implemented and ready for deployment
