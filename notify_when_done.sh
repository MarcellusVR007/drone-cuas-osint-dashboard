#!/bin/bash
# Wait for AI analysis to complete and notify

echo "🔔 Notification script started - watching for completion..."
echo "   Process PID: $(pgrep -f analyze_top200.py || echo 'not found')"
echo ""

# Wait for process to finish
while ps aux | grep -q "[a]nalyze_top200.py"; do
    sleep 30
done

# Analysis is done!
ANALYZED=$(sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts WHERE verification_status != 'PENDING_ANALYSIS'" 2>/dev/null || echo "0")
HIGH_INTEL=$(sqlite3 data/drone_cuas.db "SELECT COUNT(*) FROM social_media_posts WHERE credibility_score >= 0.7" 2>/dev/null || echo "0")

# macOS notification
osascript -e "display notification \"✅ $ANALYZED posts analyzed, $HIGH_INTEL high-intel found!\" with title \"AI Analysis Complete\" sound name \"Glass\""

# Terminal bell
echo -e "\a"

# Create completion file
cat > /tmp/ANALYSIS_COMPLETE.txt << EOF
╔═══════════════════════════════════════════════════════╗
║          AI ANALYSIS COMPLETE!                        ║
╚═══════════════════════════════════════════════════════╝

📊 Final Results:
   Total analyzed:     $ANALYZED posts
   High-intel (≥7.0):  $HIGH_INTEL posts
   Completion time:    $(date)

🎯 Next Steps:
   1. Run correlations:  python3 backend/correlate_incidents_telegram.py
   2. Test dashboards:   http://127.0.0.1:8000/telegram-intel.html
   3. Review high-intel: sqlite3 data/drone_cuas.db "SELECT * FROM social_media_posts WHERE credibility_score >= 0.7"

📋 Full log: /tmp/ai_analysis_live.log
EOF

cat /tmp/ANALYSIS_COMPLETE.txt

# Open terminal with notification
open -a Terminal /tmp/ANALYSIS_COMPLETE.txt 2>/dev/null

echo ""
echo "✅ Notification sent! Check /tmp/ANALYSIS_COMPLETE.txt for details"
