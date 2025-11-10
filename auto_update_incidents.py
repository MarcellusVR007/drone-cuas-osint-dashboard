#!/usr/bin/env python3
"""
Automatic Incident Update Pipeline

This script combines the daily news scan and batch import process:
1. Scans news sources for new drone incidents
2. Automatically imports high-quality incidents into the dashboard
3. Logs all activity for monitoring

Designed to run via cron job for daily automated updates.

Usage:
    python3 auto_update_incidents.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

def log(message: str, level: str = "INFO"):
    """Timestamped logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)

    # Also write to log file
    log_file = LOG_DIR / f"auto_update_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, 'a') as f:
        f.write(log_message + "\n")

def run_command(cmd: list, description: str) -> tuple:
    """Run a command and return success status and output"""
    try:
        log(f"Running: {description}")
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            log(f"✓ Success: {description}", "SUCCESS")
            return True, result.stdout
        else:
            log(f"✗ Failed: {description}", "ERROR")
            log(f"Error output: {result.stderr}", "ERROR")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        log(f"✗ Timeout: {description}", "ERROR")
        return False, "Command timed out"
    except Exception as e:
        log(f"✗ Exception: {description} - {e}", "ERROR")
        return False, str(e)

def get_latest_scan_report() -> Path:
    """Find the most recent scan report"""
    scan_reports = list(DATA_DIR.glob("scan_report_*.json"))
    if not scan_reports:
        return None
    return max(scan_reports, key=lambda p: p.stat().st_mtime)

def parse_import_summary(output: str) -> dict:
    """Extract statistics from batch import output"""
    stats = {
        'successful': 0,
        'duplicates': 0,
        'skipped': 0,
        'failed': 0,
        'total': 0
    }

    for line in output.split('\n'):
        if 'Successfully imported:' in line:
            stats['successful'] = int(line.split(':')[-1].strip())
        elif 'Duplicates skipped:' in line:
            stats['duplicates'] = int(line.split(':')[-1].strip())
        elif 'Skipped (no match):' in line:
            stats['skipped'] = int(line.split(':')[-1].strip())
        elif 'Failed:' in line and '❌' in line:
            stats['failed'] = int(line.split(':')[-1].strip())
        elif 'Total processed:' in line:
            stats['total'] = int(line.split(':')[-1].strip())

    return stats

def main():
    log("=" * 80)
    log("🚁 OSINT CUAS Dashboard - Automatic Update Pipeline")
    log("=" * 80)

    # Step 1: Run daily news scan
    log("\n📰 STEP 1: Scanning news sources for new incidents...")
    success, output = run_command(
        [sys.executable, "daily_news_scan.py"],
        "Daily news scan"
    )

    if not success:
        log("❌ News scan failed. Aborting pipeline.", "ERROR")
        sys.exit(1)

    # Check if scan found any potential incidents
    if "No new articles found" in output:
        log("ℹ️  No new articles found. Nothing to import.")
        log("✓ Pipeline complete (no updates)")
        return

    # Find the latest scan report
    latest_report = get_latest_scan_report()
    if not latest_report:
        log("⚠️  No scan report found. Skipping import.", "WARNING")
        log("✓ Pipeline complete (scan only)")
        return

    log(f"📄 Found scan report: {latest_report.name}")

    # Load report to check incident count
    with open(latest_report, 'r') as f:
        report_data = json.load(f)
        incident_count = report_data.get('potential_incidents_found', 0)

    if incident_count == 0:
        log("ℹ️  No potential incidents in report. Nothing to import.")
        log("✓ Pipeline complete (no updates)")
        return

    log(f"📊 Report contains {incident_count} potential incidents")

    # Step 2: Batch import incidents
    log("\n📥 STEP 2: Importing incidents into dashboard...")
    success, output = run_command(
        [sys.executable, "batch_import_incidents.py", str(latest_report)],
        "Batch import incidents"
    )

    if not success:
        log("❌ Batch import failed.", "ERROR")
        sys.exit(1)

    # Parse import statistics
    stats = parse_import_summary(output)

    log("\n" + "=" * 80)
    log("📊 PIPELINE SUMMARY")
    log("=" * 80)
    log(f"✅ Incidents imported:  {stats['successful']}")
    log(f"🔁 Duplicates skipped:  {stats['duplicates']}")
    log(f"⚠️  Incidents skipped:   {stats['skipped']}")
    log(f"❌ Import failures:     {stats['failed']}")
    log(f"📋 Total processed:     {stats['total']}")
    log("=" * 80)

    if stats['successful'] > 0:
        log(f"\n🎉 Successfully added {stats['successful']} new incidents to dashboard!")
        log("🔗 View at: http://localhost:8000")
    else:
        log("\nℹ️  No new incidents were added this run.")

    log("✓ Pipeline complete")

    # Archive old scan reports (keep last 7 days)
    log("\n🧹 Cleaning up old scan reports...")
    scan_reports = sorted(DATA_DIR.glob("scan_report_*.json"), key=lambda p: p.stat().st_mtime)
    if len(scan_reports) > 7:
        for old_report in scan_reports[:-7]:
            old_report.unlink()
            log(f"  🗑️  Deleted: {old_report.name}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n👋 Pipeline cancelled by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n❌ Fatal error: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
