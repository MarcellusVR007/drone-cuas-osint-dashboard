#!/usr/bin/env python3
"""
Flight Anomaly Detection - OpenSky Network Integration
Detects irregular flight patterns near critical infrastructure
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
import json

# Critical areas to monitor (Netherlands + Belgium)
MONITORED_AREAS = {
    "schiphol": {
        "name": "Amsterdam Schiphol Airport",
        "lat_min": 52.27, "lat_max": 52.33,
        "lon_min": 4.72, "lon_max": 4.82,
        "type": "airport"
    },
    "rotterdam": {
        "name": "Rotterdam The Hague Airport",
        "lat_min": 51.94, "lat_max": 51.98,
        "lon_min": 4.41, "lon_max": 4.48,
        "type": "airport"
    },
    "eindhoven": {
        "name": "Eindhoven Airport",
        "lat_min": 51.43, "lat_max": 51.47,
        "lon_min": 5.36, "lon_max": 5.41,
        "type": "airport"
    },
    "brunssum_nato": {
        "name": "NATO JFC Brunssum",
        "lat_min": 50.93, "lat_max": 50.97,
        "lon_min": 5.96, "lon_max": 6.02,
        "type": "military"
    },
    "volkel_airbase": {
        "name": "Volkel Air Base (F-16)",
        "lat_min": 51.64, "lat_max": 51.68,
        "lon_min": 5.68, "lon_max": 5.74,
        "type": "military"
    },
    "doel_nuclear": {
        "name": "Doel Nuclear Power Plant",
        "lat_min": 51.31, "lat_max": 51.34,
        "lon_min": 4.24, "lon_max": 4.28,
        "type": "nuclear"
    }
}

class FlightAnomalyDetector:
    """Detect anomalous flight patterns using OpenSky Network API"""

    def __init__(self, db_path="data/drone_cuas.db"):
        self.db_path = db_path
        self.api_base = "https://opensky-network.org/api"

    def get_flights_in_area(self, area: Dict) -> List[Dict]:
        """
        Query OpenSky Network for flights in specific area
        Free API: rate limited to 10 requests per minute
        """
        url = f"{self.api_base}/states/all"
        params = {
            "lamin": area["lat_min"],
            "lamax": area["lat_max"],
            "lomin": area["lon_min"],
            "lomax": area["lon_max"]
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or "states" not in data or data["states"] is None:
                return []

            flights = []
            for state in data["states"]:
                # OpenSky state vector format
                flight = {
                    "icao24": state[0],  # Aircraft transponder code
                    "callsign": state[1].strip() if state[1] else None,
                    "origin_country": state[2],
                    "time_position": state[3],
                    "last_contact": state[4],
                    "longitude": state[5],
                    "latitude": state[6],
                    "baro_altitude": state[7],  # meters
                    "on_ground": state[8],
                    "velocity": state[9],  # m/s
                    "true_track": state[10],  # degrees
                    "vertical_rate": state[11],  # m/s
                    "geo_altitude": state[13],
                    "squawk": state[14],
                    "spi": state[15],
                    "position_source": state[16]
                }
                flights.append(flight)

            return flights

        except requests.exceptions.RequestException as e:
            print(f"⚠️  OpenSky API error: {e}")
            return []

    def detect_anomalies(self, flight: Dict, area: Dict) -> Optional[Dict]:
        """
        Detect if flight shows anomalous behavior
        Returns anomaly dict or None
        """
        anomalies = []
        risk_score = 0.0

        # SKIP aircraft on ground (taxiing is not an anomaly)
        if flight["on_ground"]:
            return None

        # AIRPORTS: More lenient (landing/takeoff is normal)
        if area["type"] == "airport":
            # Only flag VERY low altitude (< 50m) when NOT on ground
            if flight["baro_altitude"] and flight["baro_altitude"] < 50:
                anomalies.append(f"Extremely low altitude: {flight['baro_altitude']}m")
                risk_score += 0.4
            # Loitering at airports is normal (holding pattern)
            # Skip velocity checks for airports

        # MILITARY/NUCLEAR: Much stricter detection
        elif area["type"] in ["military", "nuclear"]:
            # 1. ANY low altitude near sensitive sites
            if flight["baro_altitude"] and flight["baro_altitude"] < 2000:  # < 2km
                anomalies.append(f"Low altitude near {area['type']} site: {flight['baro_altitude']}m")
                risk_score += 0.5

            # 2. LOITERING near sensitive sites (circling/surveillance?)
            if flight["velocity"] and flight["velocity"] < 80:  # < 288 km/h
                anomalies.append(f"Loitering near {area['type']} site: {flight['velocity']*3.6:.0f} km/h")
                risk_score += 0.4

            # 3. NO CALLSIGN near sensitive sites (more suspicious)
            if not flight["callsign"]:
                anomalies.append("No callsign near sensitive site")
                risk_score += 0.35

        # 4. NON-COMMERCIAL origin country near military/nuclear
        if area["type"] in ["military", "nuclear"]:
            if flight["origin_country"] not in ["Netherlands", "Belgium", "United States", "Germany", "United Kingdom"]:
                anomalies.append(f"Unusual origin: {flight['origin_country']}")
                risk_score += 0.35

        # 5. SQUAWK codes (emergency/hijack/radio failure)
        if flight["squawk"]:
            if flight["squawk"] == "7500":  # Hijack
                anomalies.append("SQUAWK 7500 - HIJACK")
                risk_score += 1.0
            elif flight["squawk"] == "7600":  # Radio failure
                anomalies.append("SQUAWK 7600 - Radio failure")
                risk_score += 0.4
            elif flight["squawk"] == "7700":  # Emergency
                anomalies.append("SQUAWK 7700 - Emergency")
                risk_score += 0.5

        if anomalies:
            return {
                "flight": flight,
                "area": area["name"],
                "area_type": area["type"],
                "anomalies": anomalies,
                "risk_score": min(risk_score, 1.0),
                "detected_at": datetime.utcnow().isoformat()
            }

        return None

    def scan_all_areas(self) -> List[Dict]:
        """Scan all monitored areas for anomalies"""
        all_anomalies = []

        for area_id, area in MONITORED_AREAS.items():
            print(f"🛩️  Scanning {area['name']}...")

            flights = self.get_flights_in_area(area)
            print(f"   Found {len(flights)} flights")

            for flight in flights:
                anomaly = self.detect_anomalies(flight, area)
                if anomaly:
                    all_anomalies.append(anomaly)
                    print(f"   ⚠️  ANOMALY: {anomaly['anomalies']}")

            # Rate limiting: 10 req/min = 6 seconds between requests
            time.sleep(6)

        return all_anomalies

    def save_anomalies(self, anomalies: List[Dict]):
        """Save detected anomalies to database"""
        if not anomalies:
            print("✓ No anomalies detected")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flight_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icao24 TEXT,
                callsign TEXT,
                area_name TEXT,
                area_type TEXT,
                latitude REAL,
                longitude REAL,
                altitude_m REAL,
                velocity_kmh REAL,
                origin_country TEXT,
                anomalies TEXT,
                risk_score REAL,
                detected_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for anomaly in anomalies:
            flight = anomaly["flight"]
            cursor.execute("""
                INSERT INTO flight_anomalies
                (icao24, callsign, area_name, area_type, latitude, longitude,
                 altitude_m, velocity_kmh, origin_country, anomalies, risk_score, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                flight["icao24"],
                flight["callsign"],
                anomaly["area"],
                anomaly["area_type"],
                flight["latitude"],
                flight["longitude"],
                flight["baro_altitude"],
                flight["velocity"] * 3.6 if flight["velocity"] else None,
                flight["origin_country"],
                json.dumps(anomaly["anomalies"]),
                anomaly["risk_score"],
                anomaly["detected_at"]
            ))

        conn.commit()
        conn.close()
        print(f"✅ Saved {len(anomalies)} anomalies to database")


if __name__ == "__main__":
    print("=== Flight Anomaly Detection ===")
    print("Using OpenSky Network API (real-time ADS-B data)")
    print()

    detector = FlightAnomalyDetector()
    anomalies = detector.scan_all_areas()
    detector.save_anomalies(anomalies)

    print()
    print(f"Total anomalies detected: {len(anomalies)}")
