"""
Daily Update Mechanism for OSINT CUAS Dashboard

Monitors EU news sources and incident feeds for new drone incidents.
Designed to run as a scheduled task or background worker.

Usage:
    python -m backend.daily_update

Environment Variables:
    UPDATE_INTERVAL_HOURS: How often to check for updates (default: 24)
    ENABLE_DAILY_UPDATES: Set to true to enable (default: false)
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Incident, RestrictedArea
from backend.trusted_sources import get_all_trusted_domains
import requests
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyUpdateChecker:
    """
    Checks for new drone incidents from trusted EU sources
    and adds them to the dashboard if new.
    """

    def __init__(self, check_interval_hours: int = 24):
        self.check_interval = timedelta(hours=check_interval_hours)
        self.last_check = None
        self.trusted_domains = get_all_trusted_domains()

    def get_last_incident_date(self, db: Session) -> datetime:
        """Get the most recent incident in the database"""
        recent = db.query(Incident).order_by(
            Incident.sighting_date.desc()
        ).first()

        if recent:
            return recent.sighting_date
        return datetime.utcnow().date() - timedelta(days=60)

    def check_news_sources(self, db: Session) -> list:
        """
        Poll major EU news sources for new drone incident reports.

        Returns:
            List of potential new incidents: [{"title": str, "url": str, "source": str, "date": str}]
        """
        new_incidents = []

        # Define EU news source RSS feeds and news endpoints
        news_sources = [
            # Reuters
            {
                "name": "Reuters",
                "url": "https://www.reuters.com/world/",
                "keywords": ["drone", "uav", "unmanned aircraft", "incident"]
            },
            # BBC
            {
                "name": "BBC News",
                "url": "https://www.bbc.com/news/world",
                "keywords": ["drone", "uav", "unmanned aircraft"]
            },
            # Eurocontrol
            {
                "name": "Eurocontrol",
                "url": "https://www.eurocontrol.int/news",
                "keywords": ["drone", "safety", "incident"]
            },
            # EASA
            {
                "name": "EASA",
                "url": "https://www.easa.europa.eu/newsroom-and-events",
                "keywords": ["drone", "incident", "safety"]
            },
            # Various national defense ministries would go here
            # This is a placeholder structure
        ]

        logger.info(f"Checking {len(news_sources)} news sources for new incidents...")

        for source in news_sources:
            try:
                response = requests.get(
                    source["url"],
                    timeout=10,
                    headers={"User-Agent": "OSINT-CUAS-Dashboard/1.0"}
                )

                if response.status_code == 200:
                    # In a real implementation, you would parse HTML/RSS
                    # and extract relevant articles mentioning drones
                    logger.info(f"✓ Successfully checked {source['name']}")
                else:
                    logger.warning(f"✗ {source['name']} returned status {response.status_code}")

            except requests.exceptions.Timeout:
                logger.error(f"✗ Timeout checking {source['name']}")
            except Exception as e:
                logger.error(f"✗ Error checking {source['name']}: {str(e)}")

        return new_incidents

    def check_senhive_api(self, db: Session) -> list:
        """
        Check Senhive API for real-time drone detection data.

        Returns:
            List of new detections: [{"location": str, "drone_type": str, "confidence": float}]
        """
        new_detections = []

        senhive_api = os.getenv("SENHIVE_API_KEY")
        if not senhive_api:
            logger.warning("Senhive API key not set in environment variables")
            return new_detections

        try:
            # This is a placeholder for Senhive API integration
            # You would call their API here with proper authentication
            logger.info("Checking Senhive API for new detections...")
            # response = requests.get(
            #     "https://api.senhive.com/incidents",
            #     headers={"Authorization": f"Bearer {senhive_api}"},
            #     timeout=10
            # )
            # if response.status_code == 200:
            #     data = response.json()
            #     # Process new detections
            #     logger.info(f"Found {len(data)} new Senhive detections")

        except Exception as e:
            logger.error(f"Error checking Senhive API: {str(e)}")

        return new_detections

    def run_update_check(self):
        """
        Main update check routine.
        Call this periodically (e.g., via cron, scheduler, or background worker)
        """
        db = SessionLocal()

        try:
            logger.info("=" * 60)
            logger.info("Starting daily update check...")
            start_time = datetime.utcnow()

            # Get last incident date
            last_incident_date = self.get_last_incident_date(db)
            logger.info(f"Last incident in database: {last_incident_date}")

            # Check news sources
            news_incidents = self.check_news_sources(db)
            logger.info(f"Found {len(news_incidents)} potential new incidents from news sources")

            # Check Senhive API
            senhive_detections = self.check_senhive_api(db)
            logger.info(f"Found {len(senhive_detections)} new Senhive detections")

            # Summary
            total_new = len(news_incidents) + len(senhive_detections)
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info(f"Daily update check completed in {elapsed:.2f}s")
            logger.info(f"New incidents found: {total_new}")
            logger.info("=" * 60)

            self.last_check = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error in daily update check: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            db.close()


async def start_daily_updates():
    """
    Background task that runs the daily update check periodically.

    Add this to FastAPI startup events if you want automatic checks.
    """
    checker = DailyUpdateChecker(
        check_interval_hours=int(os.getenv("UPDATE_INTERVAL_HOURS", "24"))
    )

    while True:
        try:
            checker.run_update_check()
            # Wait before next check
            await asyncio.sleep(checker.check_interval.total_seconds())

        except Exception as e:
            logger.error(f"Daily update task error: {str(e)}")
            # Wait 5 minutes before retrying
            await asyncio.sleep(300)


def manual_check():
    """Run a single update check (useful for testing)"""
    checker = DailyUpdateChecker()
    checker.run_update_check()


if __name__ == "__main__":
    # When run directly, perform a single check
    manual_check()
