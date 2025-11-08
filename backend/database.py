import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.models import Base

# Use absolute path to SQLite database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "drone_cuas.db")
DATABASE_URL = f"sqlite:///{db_path}?check_same_thread=False&timeout=30"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Configure SQLite pragmas for better concurrency handling
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better file handling on macOS"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Use Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
    cursor.execute("PRAGMA temp_store=MEMORY")  # Use in-memory temp storage
    cursor.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")

def seed_db():
    """Add initial sample data"""
    db = SessionLocal()
    try:
        from backend.models import RestrictedArea, DroneType, Incident

        # Check if already seeded - if there are incidents, skip seeding
        if db.query(Incident).count() > 0:
            print("✓ Database already seeded with custom data")
            return

        # Also check restricted areas to avoid duplicates
        if db.query(RestrictedArea).count() > 0:
            print("✓ Database already seeded")
            return

        # Add major EU airports and military bases
        restricted_areas = [
            RestrictedArea(
                name="Brussels Airport (Zaventem)",
                area_type="airport",
                country="BE",
                latitude=50.9009,
                longitude=4.4844,
                threat_level=5,
                description="Major EU airport, NATO nuclear storage suspected"
            ),
            RestrictedArea(
                name="Kleine Brogel Air Base",
                area_type="military_base",
                country="BE",
                latitude=51.3167,
                longitude=5.3833,
                threat_level=5,
                description="US tactical nuclear weapons storage"
            ),
            RestrictedArea(
                name="Ramstein Air Base",
                area_type="military_base",
                country="DE",
                latitude=49.4372,
                longitude=7.6084,
                threat_level=5,
                description="US air base, NATO hub"
            ),
            RestrictedArea(
                name="Rotterdam Airport",
                area_type="airport",
                country="NL",
                latitude=51.8560,
                longitude=4.4432,
                threat_level=4,
                description="Major cargo hub"
            ),
            RestrictedArea(
                name="Volkel Air Base",
                area_type="military_base",
                country="NL",
                latitude=51.5378,
                longitude=5.6864,
                threat_level=5,
                description="Dutch air force base, NATO assets"
            ),
            RestrictedArea(
                name="Paris Orly Airport",
                area_type="airport",
                country="FR",
                latitude=48.7250,
                longitude=2.3592,
                threat_level=4,
                description="Major EU capital airport"
            ),
        ]

        # Add known drone types used in EU reconnaissance
        drone_types = [
            DroneType(
                model="DJI Matrice 300 RTK",
                manufacturer="DJI (China)",
                country_of_origin="CN",
                range_km=15,
                endurance_minutes=55,
                max_altitude_m=2500,
                payload_type="camera",
                difficulty_intercept=4,
                estimated_cost_usd=15000,
                notes="Commercial but capable of long-range surveillance, often found in EU incidents"
            ),
            DroneType(
                model="DJI Phantom 4 Pro V2.0",
                manufacturer="DJI (China)",
                country_of_origin="CN",
                range_km=10,
                endurance_minutes=31,
                max_altitude_m=2700,
                payload_type="camera",
                difficulty_intercept=3,
                estimated_cost_usd=1500,
                notes="Popular commercial drone, easy to repurpose"
            ),
            DroneType(
                model="Orlan-10",
                manufacturer="Russian Armed Forces",
                country_of_origin="RU",
                range_km=40,
                endurance_minutes=90,
                max_altitude_m=4000,
                payload_type="signals_intelligence",
                difficulty_intercept=5,
                estimated_cost_usd=200000,
                notes="Military reconnaissance drone, frequent over EU airbases"
            ),
            DroneType(
                model="RQ-35 Heidrun",
                manufacturer="Quantum Systems (Germany)",
                country_of_origin="DE",
                range_km=50,
                endurance_minutes=120,
                max_altitude_m=4000,
                payload_type="camera",
                difficulty_intercept=4,
                estimated_cost_usd=500000,
                notes="Professional COTS used by militaries"
            ),
            DroneType(
                model="Unidentified Quadcopter",
                manufacturer="Unknown",
                country_of_origin="UNKNOWN",
                range_km=5,
                endurance_minutes=20,
                max_altitude_m=500,
                payload_type="unknown",
                difficulty_intercept=2,
                estimated_cost_usd=300,
                notes="Generic consumer drone, often modified"
            ),
        ]

        db.add_all(restricted_areas)
        db.add_all(drone_types)
        db.commit()
        print(f"✓ Seeded {len(restricted_areas)} restricted areas")
        print(f"✓ Seeded {len(drone_types)} drone types")
    finally:
        db.close()
