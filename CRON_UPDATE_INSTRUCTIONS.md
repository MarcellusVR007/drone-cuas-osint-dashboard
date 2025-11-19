# Cron Update Instructions - 4x Daily Schedule

## Current Problem
- Scraper runs only 2x daily (06:00, 18:00)
- **Terneuzen incident (Nov 18 evening) was missed**
- RSS feeds cycle out news within 24 hours

## Solution: Increase to 4x Daily

Run this command manually:

```bash
crontab -e
```

Then replace with:

```cron
# OSINT CUAS Dashboard - 4x daily for breaking news
0 0 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 6 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 12 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 18 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
```

Save and exit (`:wq` in vim).

## Verify

```bash
crontab -l
```

Should show 4 entries at 00:00, 06:00, 12:00, 18:00.

## What's Been Fixed

1. ✅ **Expanded NL keywords** - "drone Terneuzen", "drone havengebied", "meerdere drones"
2. ✅ **Added RSS fallback** - Direct RSS from RTL, NU.nl, AD, Telegraaf
3. ⏳ **4x daily schedule** - Needs manual `crontab -e` (macOS permission issue)

## Test Run

Test the improved scraper now:

```bash
python3 auto_update_incidents.py
```

This will use the new keywords + RSS fallback immediately.
