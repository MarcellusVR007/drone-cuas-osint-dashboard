#!/bin/bash
echo "=== AI ANALYSIS STATUS ==="
echo ""
if ps aux | grep -q "[a]nalyze_top200.py"; then
    echo "✅ Process RUNNING"
    ps aux | grep "[a]nalyze_top200.py" | awk '{print "   PID: "$2}'
else
    echo "⏹️ Process STOPPED"
fi
echo ""
echo "📊 Database:"
sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts WHERE verification_status != 'PENDING_ANALYSIS'" | xargs echo "   Analyzed:"
echo ""
echo "📝 Recent log:"
tail -10 /tmp/ai_analysis_live.log 2>/dev/null || echo "   No log yet"
