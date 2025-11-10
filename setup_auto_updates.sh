#!/bin/bash
# Setup Automatic Daily Updates for OSINT CUAS Dashboard

echo "Setting up automatic incident updates..."
echo ""

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory
mkdir -p "$DIR/logs"

# Python executable
PYTHON="/usr/bin/python3"

# Cron job commands (run twice daily: 6 AM and 6 PM)
CRON_CMD_MORNING="0 6 * * * cd $DIR && $PYTHON $DIR/auto_update_incidents.py >> $DIR/logs/cron.log 2>&1"
CRON_CMD_EVENING="0 18 * * * cd $DIR && $PYTHON $DIR/auto_update_incidents.py >> $DIR/logs/cron.log 2>&1"

# Check if cron jobs already exist
EXISTING_JOBS=$(crontab -l 2>/dev/null | grep -c "auto_update_incidents.py")

if [ "$EXISTING_JOBS" -gt 0 ]; then
    echo "Warning: Auto-update cron jobs already exist!"
    echo ""
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "auto_update_incidents.py"
    echo ""
    read -p "Do you want to replace them? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    # Remove existing jobs
    crontab -l 2>/dev/null | grep -v "auto_update_incidents.py" | crontab -
    echo "Removed old cron jobs"
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "$CRON_CMD_MORNING") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_CMD_EVENING") | crontab -

echo "Cron jobs added successfully!"
echo ""
echo "Schedule: Every day at 6:00 AM and 6:00 PM"
echo "Logs: $DIR/logs/"
echo "Reports: $DIR/data/scan_report_*.json"
echo ""
echo "Test manually: python3 $DIR/auto_update_incidents.py"
echo "View cron jobs: crontab -l"
echo ""
echo "Setup complete!"
