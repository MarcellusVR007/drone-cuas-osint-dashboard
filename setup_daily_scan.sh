#!/bin/bash
#
# Setup automatic daily news scanning
#
# This script configures a cron job to run daily_news_scan.py every day at 6 AM
#

echo "🔧 Setting up daily OSINT news scanning..."

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory
mkdir -p "$DIR/data"

# Cron job command
CRON_CMD="0 6 * * * cd $DIR && /usr/bin/python3 $DIR/daily_news_scan.py >> $DIR/data/daily_scan.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_news_scan.py"; then
    echo "⚠️  Cron job already exists!"
    echo "Current cron jobs:"
    crontab -l | grep "daily_news_scan.py"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📅 Schedule: Every day at 6:00 AM"
    echo "📝 Logs: $DIR/data/daily_scan.log"
    echo "📊 Reports: $DIR/data/scan_report_*.json"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Test the scanner manually:"
echo "   python3 $DIR/daily_news_scan.py"
echo ""
echo "📋 View current cron jobs:"
echo "   crontab -l"
echo ""
echo "🗑  Remove cron job:"
echo "   crontab -e  (then delete the line with daily_news_scan.py)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
