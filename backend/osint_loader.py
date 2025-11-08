"""
Automatically load OSINT data from CSV on startup
"""
import os
import csv
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from backend.models import Incident, RestrictedArea, DroneType

# EU location coordinates
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
    'Göteborg-Landvetter Airport': (57.6628, 12.2788),
    'Stockholm Arlanda Airport': (59.6519, 17.9289),
    'Vilnius Airport': (54.6274, 25.2879),
    'Camp Reedo Military Base': (58.8500, 25.2000),
    'Elva Parish, Tartu County': (58.2500, 26.5000),
    'Southeastern Estonian Airspace': (57.5000, 27.5000),
    'Coast of Liivi Bay, Pärnumaa': (58.3000, 24.8000),
    'Šiauliai Air Base (NATO)': (55.9347, 23.5311),
    'Jonava District Training Ground': (55.0667, 24.2500),
    'Lithuanian Airspace (from Belarus)': (54.5000, 24.0000),
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
    'SE': 'Sweden',
    'EE': 'Estonia',
    'LT': 'Lithuania',
}

def get_or_create_restricted_area(db: Session, location_name: str, location_type: str, country_code: str):
    """Get or create a restricted area"""
    existing = db.query(RestrictedArea).filter_by(name=location_name).first()
    if existing:
        return existing

    coords = LOCATION_COORDS.get(location_name, (50.0, 10.0))

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
        area_type=area_type_map.get(location_type, 'unknown'),
        country=country_code,
        latitude=coords[0],
        longitude=coords[1],
        radius_km=5.0,
        threat_level=threat_map.get(area_type_map.get(location_type, 'unknown'), 3),
        description=f"{COUNTRY_CODES.get(country_code, country_code)} - {location_type}"
    )

    db.add(area)
    db.flush()
    return area

def get_or_create_drone_type(db: Session, drone_description: str):
    """Get or create a drone type"""
    if not drone_description:
        drone_description = 'Unknown Drone'
    if drone_description == 'Unknown':
        drone_description = 'Unknown Drone'

    existing = db.query(DroneType).filter_by(model=drone_description).first()
    if existing:
        return existing

    drone_type = DroneType(
        model=drone_description,
        manufacturer='Unknown',
        country_of_origin='Unknown',
        notes='From OSINT CSV data'
    )

    db.add(drone_type)
    db.flush()
    return drone_type

def parse_duration(duration_str: str) -> int:
    """Parse duration string to minutes"""
    if not duration_str or duration_str == 'Unknown':
        return None

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

def infer_purpose(description: str, location_type: str, location_name: str) -> str:
    """Infer incident purpose from description and location"""
    if not description:
        return 'reconnaissance'

    desc_lower = description.lower()
    loc_lower = (location_name + ' ' + location_type).lower()

    # Military incursion / hostile act
    if any(keyword in desc_lower for keyword in ['shot down', 'jamming', 'jammed', 'military incursion', 'violation', 'airspace violation']):
        return 'military_incursion'

    # Espionage / intelligence gathering
    if any(keyword in desc_lower for keyword in ['espionage', 'intelligence', 'sigint', 'signals']):
        return 'espionage'

    # Sabotage / disruption
    if any(keyword in desc_lower for keyword in ['sabotage', 'hybrid', 'disruption', 'attack', 'disrupted', 'suspended', 'paralyzed', 'closed']):
        return 'sabotage'

    # Testing / Training
    if any(keyword in desc_lower for keyword in ['training', 'test', 'exercise', 'failed', 'crash']):
        return 'testing'

    # Commercial / Civilian
    if any(keyword in desc_lower for keyword in ['civilian', 'commercial', 'advertising', 'filming']):
        return 'civilian'

    # Default to reconnaissance
    return 'reconnaissance'

def load_osint_data(db: Session):
    """Load OSINT data from CSV if it exists"""
    # Check if OSINT data CSV exists - use relative path for portability
    osint_csv = Path(__file__).parent / 'data' / 'drone_incidents_eu.csv'

    if not osint_csv.exists():
        print("ℹ️  No OSINT DATA CSV found")
        return

    # Count existing incidents
    existing_count = db.query(Incident).count()

    print("📊 Loading OSINT EU drone incidents...")

    loaded = 0
    skipped_duplicates = 0
    try:
        with open(osint_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    incident_date = datetime.strptime(row['incident_date'], '%Y-%m-%d').date()

                    # Check if this incident already exists (prevent duplicates)
                    existing = db.query(Incident).filter_by(
                        sighting_date=incident_date,
                        title=f"Drone sighting at {row['location']} ({row['country']})"
                    ).first()

                    if existing:
                        skipped_duplicates += 1
                        continue

                    # Get or create restricted area
                    area = get_or_create_restricted_area(
                        db,
                        row['location'],
                        row['location_type'],
                        row['country']
                    )

                    # Get or create drone type
                    drone_type = None
                    if row['drone_type'] and row['drone_type'] != 'Unknown':
                        drone_type = get_or_create_drone_type(db, row['drone_type'])
                    else:
                        drone_type = get_or_create_drone_type(db, 'Unknown Drone')

                    # Infer purpose from description
                    purpose = infer_purpose(row['description'], row['location_type'], row['location'])

                    # Create incident
                    incident = Incident(
                        sighting_date=incident_date,
                        report_date=datetime.utcnow(),
                        latitude=area.latitude,
                        longitude=area.longitude,
                        altitude_m=None,
                        drone_type_id=drone_type.id if drone_type else None,
                        drone_description=row['drone_type'] if row['drone_type'] != 'Unknown' else None,
                        identification_method='intelligence',
                        identification_confidence=float(row.get('certainty_score', 3)) / 5.0,
                        identification_evidence=row['flight_path_summary'],
                        identified_by=row['source_type'],
                        restricted_area_id=area.id,
                        distance_to_restricted_m=0,
                        duration_minutes=parse_duration(row['flight_duration']),
                        source=row['source_type'],
                        source_url=row.get('source_url'),
                        corroborating_sources=None,
                        confidence_score=float(row.get('certainty_score', 3)) / 5.0,
                        title=f"Drone sighting at {row['location']} ({row['country']})",
                        description=row['description'],
                        details=f"Source: {row['source_url']}",
                        suspected_operator='Unknown',
                        purpose_assessment=purpose
                    )

                    db.add(incident)
                    loaded += 1

                    if loaded % 5 == 0:
                        db.commit()

                except Exception as e:
                    print(f"⚠️  Error loading incident: {e}")
                    db.rollback()
                    continue

        db.commit()
        new_total = db.query(Incident).count()
        print(f"✅ Loaded {loaded} OSINT EU drone incidents (skipped {skipped_duplicates} duplicates)")
        print(f"   Total incidents in database: {new_total}")

    except FileNotFoundError:
        print(f"❌ CSV file not found: {osint_csv}")
    except Exception as e:
        print(f"❌ Error loading OSINT data: {e}")
        db.rollback()
