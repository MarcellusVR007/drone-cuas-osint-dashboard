# Keep Mac Awake During AI Analysis

## 🖥️ Optie 1: Caffeinate (Simpelste, Tijdelijk)

Open een **nieuwe Terminal tab** en run:

```bash
caffeinate -d -t 3600
```

**Wat dit doet:**
- `-d` = Display blijft aan
- `-t 3600` = 3600 seconden (60 minuten)
- Computer blijft wakker, ook met scherm dicht!

**Status check:**
```bash
ps aux | grep caffeinate
# Als je output ziet = caffeinate draait nog
```

**Stop het:**
Druk `Ctrl+C` in de terminal waar caffeinate draait

---

## ⚙️ Optie 2: System Preferences (Permanenter)

**macOS Ventura/Sonoma (2023+):**
1. Open **System Settings**
2. Ga naar **Lock Screen**
3. Onder "Turn display off on battery when inactive": Zet op **Never**
4. Onder "Turn display off on power adapter when inactive": Zet op **Never**

**macOS Monterey en ouder:**
1. Open **System Preferences**
2. Klik **Battery** (of **Energy Saver**)
3. Zet **"Prevent computer from sleeping automatically when the display is off"** aan
4. Zet slider "Turn display off after" op **Never**

**Vergeet niet:** Zet dit weer terug na de analyse!

---

## 🔋 Optie 3: Caffeinate + Specific Process (Meest Slim)

Dit houdt de Mac wakker **zolang** het Python proces draait:

```bash
caffeinate -w $(pgrep -f analyze_top200.py)
```

**Voordeel:** Stopt automatisch wanneer analyse klaar is!

---

## ✅ Aanbevolen Setup (30 min analyse)

**In Terminal:**
```bash
# Stap 1: Start caffeinate (open laten draaien)
caffeinate -d -t 3600 &

# Stap 2: Check status
./check_analysis_status.sh

# Stap 3: Laptop dichtdoen = OK!
```

**Check na 30 min:**
```bash
./check_analysis_status.sh
```

---

## 🚨 Troubleshooting

**Computer ging toch slapen:**
```bash
# Check of proces nog draait
ps aux | grep analyze_top200.py

# Als niet:
# - Database heeft laatste checkpoint (elke 10 posts)
# - Herstart analyse:
python3 backend/analyze_top200.py > /tmp/ai_analysis_live.log 2>&1 &
```

**Laptop moet dicht:**
```bash
# Gebruik caffeinate -d (display sleep prevention)
caffeinate -d -t 3600
```

**Wil zien hoeveel progress zonder laptop te openen:**
- Kan niet, moet laptop openen
- OF: SSH setup (advanced)
- OF: Laat laptop open, scherm dimmen (druk F1 meerdere keren)

---

## 📱 Alternatief: Run Overnight

Als het nu 16:00 is en presentatie is morgen 10:00:

```bash
# Start analyse
python3 backend/analyze_top200.py > /tmp/ai_analysis_live.log 2>&1 &

# Keep awake for 12 hours
caffeinate -d -t 43200 &

# Laptop dicht, morgenochtend checken
```

Morgenochtend:
```bash
./check_analysis_status.sh
# Zie resultaten!
```

---

## ✅ Current Status Check

Run dit **NU** om te zien of het werkt:

```bash
./check_analysis_status.sh
```

Als je output ziet zoals:
```
✅ RUNNING (PID: 72538, Runtime: 00:05:23)
Analyzed: 3 / 200 target
```

Dan werkt alles! 🎉
