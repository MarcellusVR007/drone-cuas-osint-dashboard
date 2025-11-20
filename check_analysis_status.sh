#!/bin/bash
# Quick AI Analysis Status Checker
# Run this anytime: ./check_analysis_status.sh

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     AI ANALYSIS STATUS CHECKER                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if process is running
echo "🔍 Process Status:"
if ps aux | grep -q "[a]nalyze_top200.py"; then
    PID=$(ps aux | grep "[a]nalyze_top200.py" | awk '{print $2}')
    RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
    echo "   ✅ RUNNING (PID: $PID, Runtime: $RUNTIME)"
else
    echo "   ⏹️  STOPPED (Analysis complete or failed)"
fi
echo ""

# Check database progress
echo "📊 Database Progress:"
TOTAL=$(sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts" 2>/dev/null || echo "0")
ANALYZED=$(sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts WHERE verification_status != 'PENDING_ANALYSIS'" 2>/dev/null || echo "0")
HIGH_INTEL=$(sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts WHERE credibility_score >= 0.7" 2>/dev/null || echo "0")

echo "   Total posts:      $TOTAL"
echo "   Analyzed:         $ANALYZED / 200 target"
echo "   High-intel (≥7):  $HIGH_INTEL"

if [ "$ANALYZED" -gt 0 ]; then
    PERCENT=$((ANALYZED * 100 / 200))
    echo "   Progress:         $PERCENT%"

    # Calculate ETA (assuming 8 sec/post average)
    REMAINING=$((200 - ANALYZED))
    ETA_SEC=$((REMAINING * 8))
    ETA_MIN=$((ETA_SEC / 60))
    echo "   ETA:              ~$ETA_MIN minutes"
fi
echo ""

# Show recent activity
echo "📝 Recent Activity (last 10 lines):"
if [ -f /tmp/ai_analysis_live.log ]; then
    tail -10 /tmp/ai_analysis_live.log | sed 's/^/   /'
else
    echo "   No log file yet (starting up...)"
fi
echo ""

# Dashboard status
echo "🌐 Dashboard:"
if curl -s http://localhost:8000/api/incidents > /dev/null 2>&1; then
    echo "   ✅ Server running: http://127.0.0.1:8000/telegram-intel.html"
else
    echo "   ❌ Server not running"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  💡 Commands:                                              ║"
echo "║     Live monitor:  tail -f /tmp/ai_analysis_live.log      ║"
echo "║     Stop analysis: pkill -f analyze_top200                 ║"
echo "║     This script:   ./check_analysis_status.sh             ║"
echo "╚════════════════════════════════════════════════════════════╝"
