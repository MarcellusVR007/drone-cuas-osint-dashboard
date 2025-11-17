#!/bin/bash
# Setup cron job for daily news scraper
# Runs every day at 06:00 AM

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRAPER_PATH="$SCRIPT_DIR/backend/daily_news_scraper.py"
LOG_PATH="/tmp/daily_news_scraper.log"

# Create cron job entry
CRON_CMD="0 6 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCRAPER_PATH >> $LOG_PATH 2>&1"

echo "================================================================"
echo "DAILY NEWS SCRAPER - CRON JOB SETUP"
echo "================================================================"
echo ""
echo "This will add a cron job to run the news scraper daily at 06:00 AM"
echo ""
echo "Cron entry:"
echo "$CRON_CMD"
echo ""
echo "Log file: $LOG_PATH"
echo ""
read -p "Do you want to add this cron job? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "daily_news_scraper.py"; then
        echo "⚠️  Cron job already exists. Removing old one..."
        crontab -l 2>/dev/null | grep -v "daily_news_scraper.py" | crontab -
    fi

    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

    echo "✅ Cron job added successfully!"
    echo ""
    echo "To verify:"
    echo "  crontab -l"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_PATH"
    echo ""
    echo "To test manually:"
    echo "  python3 $SCRAPER_PATH"
else
    echo "❌ Cron job setup cancelled"
fi

echo ""
echo "================================================================"
