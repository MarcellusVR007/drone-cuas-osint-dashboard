#!/bin/bash
# Update cron to run 4x daily (00:00, 06:00, 12:00, 18:00) for better news coverage

echo "🔄 Updating OSINT CUAS cron schedule to 4x daily..."

# Create new crontab
cat > /tmp/osint_cuas_cron.txt << 'EOF'
# OSINT CUAS Dashboard - Automatic Updates (4x daily for breaking news coverage)
0 0 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 6 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 12 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
0 18 * * * cd /Users/marcel/MarLLM/drone-cuas-osint-dashboard && /usr/bin/python3 auto_update_incidents.py >> logs/cron.log 2>&1
EOF

# Install new crontab
crontab /tmp/osint_cuas_cron.txt

if [ $? -eq 0 ]; then
    echo "✅ Crontab updated successfully!"
    echo ""
    echo "📅 New schedule:"
    echo "   • 00:00 (midnight)"
    echo "   • 06:00 (morning)"
    echo "   • 12:00 (noon)"
    echo "   • 18:00 (evening)"
    echo ""
    echo "Current crontab:"
    crontab -l
else
    echo "❌ Failed to update crontab"
    echo "Please run this manually: crontab /tmp/osint_cuas_cron.txt"
fi
