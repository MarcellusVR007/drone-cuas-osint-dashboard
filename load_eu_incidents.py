#!/usr/bin/env python3
"""
Load EU drone incidents from CSV into the database
"""
import csv
import os
import sys
from datetime import datetime, date
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, engine
from models import Base, Incident, RestrictedArea, DroneType, DataSource

# Coordinates for European locations (approximate)
LOCATION_COORDS = {
    'Amsterdam Schiphol Airport': (52.3086, 4.7639),
    'Vliegbasis Gilze-Rijen': (51.5675, 4.9283),
    'Doel Nuclear Power Plant': (51.1956, 4.2467),
    'Port of Antwerp': (51.3429, 4.2894),
    'Brussels Airport (Zaventem)': (50.9010, 4.4844),
    'Liège Airport': (50.6396, 5.4371),
    'SCK CEN Nuclear Research Center, Mol': (51.1945, 5.1517),
    'Kleine-Brogel Air Base': (51.1369, 5.7175),
    'Florennes Air Base': (50.2647, 4.7578),
    'Mourmelon-le-Grand Military Base': (49.1989, 4.0028),
    'Munich Airport': (48.3521, 11.7861),
    'Berlin Brandenburg Airport (BER)': (52.3667, 13.5033),
    'Brunsbüttel Nuclear Power Plant & vicinity': (53.8750, 9.1333),
    'Dubrovnik Airport': (42.5621, 18.2667),
    'Abandoned Airfield (Falcon Autumn Exercise)': (52.0000, 18.0000),
    'Nowe Miasto nad Pilicą Military Base': (51.8389, 19.9286),
    'Eastern Polish Border': (50.5000, 24.0000),
    'Inowrocław': (52.7667, 18.2667),
    'Henri Coandă Airport, Bucharest': (44.5711, 26.0832),
    'Mihail Kogălniceanu Air Base': (44.9289, 28.1461),
    'Multiple Military Bases': (56.0000, 10.0000),
    'Copenhagen, Aalborg, Billund, Esbjerg, Sønderborg Airports & multiple military bases': (56.0000, 10.0000),
    'Adolfo Suárez Madrid-Barajas Airport': (40.4730, -3.6136),
    'Palma de Mallorca Airport': (39.5515, 2.7397),
    'Urban Area': (50.0000, 10.0000),
}

COUNTRY_CODES = {
    'NL': 'Netherlands',
    'BE': 'Belgium',
    'FR': 'France',
    'DE': 'Germany',
    'HR': 'Croatia',
    'PL': 'Poland',
    'RO': 'Romania',
    'DK': 'Denmark',
    'ES': 'Spain',
}

def get_or_create_restricted_area(session, location_name, location_type, country_code):
    """Get or create a restricted area"""
    # Check if it exists
    existing = session.query(RestrictedArea).filter_by(name=location_name).first()
    if existing:
        return existing

    # Get coordinates
    coords = LOCATION_COORDS.get(location_name, (50.0, 10.0))

    # Map location type
    area_type_map = {
        'Airport': 'airport',
        'Military Base': 'military_base',
        'Nuclear Site': 'nuclear_facility',
        'Port': 'port',
        'Urban Area': 'urban',
        'Military Exercise Area': 'military_exercise',
        'Air Defense Zone': 'air_defense_zone',
        'Multiple': 'mixed'
    }

    area_type = area_type_map.get(location_type, 'unknown')

    # Set threat level based on type
    threat_map = {
        'military_base': 5,
        'nuclear_facility': 5,
        'airport': 4,
        'port': 3,
        'military_exercise': 4,
        'air_defense_zone': 5,
        'urban': 2,
        'mixed': 4
    }

    area = RestrictedArea(
        name=location_name,
        area_type=area_type,
        country=country_code,
        latitude=coords[0],
        longitude=coords[1],
        radius_km=5.0,
        threat_level=threat_map.get(area_type, 3),
        description=f"{COUNTRY_CODES.get(country_code, country_code)} - {location_type}"
    )

    session.add(area)
    session.flush()
    return area

def get_or_create_drone_type(session, drone_description):
    """Get or create a drone type"""
    if not drone_description:
        drone_description = 'Unknown Drone'

    if drone_description == 'Unknown':
        drone_description = 'Unknown Drone'

    existing = session.query(DroneType).filter_by(model=drone_description).first()
    if existing:
        return existing

    # Create basic drone type entry
    drone_type = DroneType(
        model=drone_description,
        manufacturer='Unknown',
        country_of_origin='Unknown',
        notes=f"From OSINT CSV data"
    )

    session.add(drone_type)
    session.flush()
    return drone_type

def get_or_create_news_source(session):
    """Get or create the news data source"""
    existing = session.query(DataSource).filter_by(name='OSINT News Monitoring').first()
    if existing:
        return existing

    source = DataSource(
        name='OSINT News Monitoring',
        source_type='news',
        url='https://news.osint.community',
        reliability_score=0.75,
        freshness_score=0.85,
        coverage_score=0.70,
        data_quality_score=0.75,
        verification_status='verified',
        capabilities='["drone_detection", "location_analysis"]',  # JSON string
        coverage_regions='["EU", "NATO", "Belgium", "Netherlands", "Germany", "France", "Denmark", "Poland", "Romania", "Spain", "Croatia"]',  # JSON string
        drone_types_detected='["Unknown", "Small drones", "Large drones", "Commercial drone", "Polish Military Training Drone", "Suspected Russian Orlan-10"]'  # JSON string
    )

    session.add(source)
    session.flush()
    return source

def parse_csv_and_load(csv_path):
    """Parse CSV and load incidents into database"""
    session = SessionLocal()

    try:
        # Ensure data source exists
        news_source = get_or_create_news_source(session)
        session.commit()

        loaded = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                try:
                    # Parse date
                    incident_date = datetime.strptime(row['incident_date'], '%Y-%m-%d').date()

                    # Get or create restricted area
                    area = get_or_create_restricted_area(
                        session,
                        row['location'],
                        row['location_type'],
                        row['country']
                    )

                    # Get or create drone type
                    drone_type = None
                    if row['drone_type'] and row['drone_type'] != 'Unknown':
                        drone_type = get_or_create_drone_type(session, row['drone_type'])

                    # Create incident
                    incident = Incident(
                        sighting_date=incident_date,
                        report_date=datetime.utcnow(),

                        # Location from restricted area
                        latitude=area.latitude,
                        longitude=area.longitude,
                        altitude_m=None,

                        # Drone info
                        drone_type_id=drone_type.id if drone_type else None,
                        drone_description=row['drone_type'] if row['drone_type'] != 'Unknown' else None,

                        # Identification
                        identification_method='intelligence' if row['source_type'] == 'News' else 'intelligence',
                        identification_confidence=float(row.get('certainty_score', 3)) / 5.0,  # Convert 1-5 to 0-1
                        identification_evidence=row['flight_path_summary'],
                        identified_by=row['source_type'],

                        # Restricted area
                        restricted_area_id=area.id,
                        distance_to_restricted_m=0,

                        # Duration
                        duration_minutes=parse_duration(row['flight_duration']),

                        # Source
                        source='news',
                        confidence_score=float(row.get('certainty_score', 3)) / 5.0,

                        # Title and description
                        title=f"Drone sighting at {row['location']} ({row['country']})",
                        description=row['description'],
                        details=f"Source: {row['source_url']}",

                        # Attribution
                        suspected_operator='Unknown',
                        purpose_assessment='reconnaissance'
                    )

                    session.add(incident)
                    loaded += 1

                    if loaded % 5 == 0:
                        print(f"  Loaded {loaded} incidents...")
                        session.commit()
                        session.close()
                        session = SessionLocal()

                except Exception as e:
                    print(f"⚠️  Row {row_num}: {e}")
                    session.rollback()
                    continue

        # Final commit
        session.commit()
        print(f"\n✅ Successfully loaded {loaded} incidents from OSINT DATA!")

    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

def parse_duration(duration_str):
    """Parse duration string to minutes"""
    if not duration_str or duration_str == 'Unknown':
        return None

    # Try various patterns
    if 'min' in duration_str.lower():
        try:
            return int(duration_str.split()[0])
        except:
            pass

    if 'hour' in duration_str.lower():
        try:
            return int(duration_str.split()[0]) * 60
        except:
            pass

    return None

if __name__ == '__main__':
    csv_path = '/Users/marcelruijken/MarLLM/OSINT DATA/drone_incidents_eu.csv'

    print("\n📊 Loading EU OSINT drone incidents...")
    print(f"📂 CSV: {csv_path}\n")

    # First, create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created\n")

    parse_csv_and_load(csv_path)
