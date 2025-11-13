#!/usr/bin/env python3
"""
Add operational classification and counter-measures to the OSINT dashboard.
Distinguishes between state actors, recruited locals, and unknown operators.
"""

import sqlite3
from pathlib import Path

def add_classification_schema():
    """Add operational classification columns and counter-measures table"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("📊 Adding Operational Classification Schema...")

    # Add operational_class to incidents
    try:
        cursor.execute("""
            ALTER TABLE incidents
            ADD COLUMN operational_class VARCHAR(50)
        """)
        print("  ✓ Added operational_class column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("  ⚠ operational_class already exists")
        else:
            raise

    # Add strategic_assessment to incidents
    try:
        cursor.execute("""
            ALTER TABLE incidents
            ADD COLUMN strategic_assessment TEXT
        """)
        print("  ✓ Added strategic_assessment column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("  ⚠ strategic_assessment already exists")
        else:
            raise

    # Add launch_analysis to incidents (for Orlan/military)
    try:
        cursor.execute("""
            ALTER TABLE incidents
            ADD COLUMN launch_analysis TEXT
        """)
        print("  ✓ Added launch_analysis column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("  ⚠ launch_analysis already exists")
        else:
            raise

    # Create counter_measures table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counter_measures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT,
            effective_against TEXT,
            range_km FLOAT,
            deployment_time_hours INTEGER,
            cost_estimate_eur INTEGER,
            requires_authorization BOOLEAN DEFAULT 0,
            mobile BOOLEAN DEFAULT 0,
            specifications TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created counter_measures table")

    # Create incident_recommendations table (links incidents to counter-measures)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            counter_measure_id INTEGER NOT NULL,
            priority VARCHAR(20),
            reasoning TEXT,
            estimated_effectiveness FLOAT,
            deployment_location_lat FLOAT,
            deployment_location_lon FLOAT,
            deployment_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(incident_id) REFERENCES incidents(id),
            FOREIGN KEY(counter_measure_id) REFERENCES counter_measures(id)
        )
    """)
    print("  ✓ Created incident_recommendations table")

    conn.commit()
    conn.close()
    print("\n✓ Schema updated!")

def classify_existing_incidents():
    """Classify existing incidents based on available intelligence"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🔍 Classifying Existing Incidents...")

    # Classify Orlan-10 at Brunsbüttel
    cursor.execute("""
        UPDATE incidents
        SET operational_class = 'STATE_ACTOR',
            strategic_assessment = 'Russian military-grade reconnaissance drone (Orlan-10) conducting critical infrastructure surveillance. Range: ~120km. Indicates state-level intelligence operation targeting nuclear facility.',
            launch_analysis = 'Orlan-10 has 120km operational range. Possible launch sites: (1) Baltic Sea vessel within 100km, (2) Land-based site near Polish/Russian border, (3) Belarus territory. Weather conditions and flight duration suggest maritime launch. Recommend correlation with AIS vessel tracking data.'
        WHERE id = 10
    """)
    print("  ✓ Classified incident #10 as STATE_ACTOR (Orlan-10)")

    # Classify Polish Military Training
    cursor.execute("""
        UPDATE incidents
        SET operational_class = 'AUTHORIZED_MILITARY',
            strategic_assessment = 'Polish military training exercise. Authorized operation in restricted airspace. No threat assessment required.'
        WHERE id = 15
    """)
    print("  ✓ Classified incident #15 as AUTHORIZED_MILITARY")

    # Classify Zuid-Limburg (Telegram bounty)
    cursor.execute("""
        UPDATE incidents
        SET operational_class = 'RECRUITED_LOCAL',
            strategic_assessment = 'Recruited local operative responding to GRU Telegram bounty (2000 EUR Bitcoin payment). Part of systematic reconnaissance campaign targeting NATO infrastructure. Actor: VWarrior channel. Low-sophistication but high-volume threat vector.'
        WHERE id = 189
    """)
    print("  ✓ Classified incident #189 as RECRUITED_LOCAL (Telegram bounty)")

    conn.commit()
    conn.close()
    print("\n✓ Classification complete!")

def populate_counter_measures():
    """Add realistic C-UAS counter-measures"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n🛡️ Populating Counter-Measures Database...")

    counter_measures = [
        # RF Jamming Systems
        {
            "name": "DroneDefender 3.0",
            "type": "RF_JAMMER",
            "description": "Handheld directional RF jammer for GNSS and ISM bands",
            "effective_against": "Consumer drones, DJI models, low-end reconnaissance UAVs",
            "range_km": 1.5,
            "deployment_time_hours": 0,
            "cost_estimate_eur": 35000,
            "requires_authorization": 1,
            "mobile": 1,
            "specifications": "Frequency: 400MHz-6GHz | Weight: 6.8kg | Battery: 2hr continuous | Effective angle: 30° cone"
        },
        {
            "name": "AUDS (Anti-UAV Defence System)",
            "type": "RF_JAMMER",
            "description": "Vehicle-mounted RF disruption system with optical tracking",
            "effective_against": "Military UAVs (Orlan-10), tactical reconnaissance drones, consumer drones",
            "range_km": 10,
            "deployment_time_hours": 2,
            "cost_estimate_eur": 850000,
            "requires_authorization": 1,
            "mobile": 1,
            "specifications": "Radar detection + EO/IR tracking + 2.4/5.8GHz jamming | Vehicle-mounted | Crew: 2 operators"
        },
        {
            "name": "HP 47 Counter-UAV Jammer",
            "type": "RF_JAMMER",
            "description": "Multi-band directional jammer for tactical deployment",
            "effective_against": "Consumer and prosumer drones, FPV racing drones",
            "range_km": 3,
            "deployment_time_hours": 0,
            "cost_estimate_eur": 28000,
            "requires_authorization": 1,
            "mobile": 1,
            "specifications": "Bands: 433MHz, 900MHz, 1.2GHz, 2.4GHz, 5.8GHz | Backpack-portable | Battery: 90min"
        },

        # Detection Systems
        {
            "name": "RfPatrol MK2",
            "type": "RF_DETECTOR",
            "description": "Passive RF detection for drone activity monitoring",
            "effective_against": "All RF-controlled drones (detection only)",
            "range_km": 5,
            "deployment_time_hours": 1,
            "cost_estimate_eur": 15000,
            "requires_authorization": 0,
            "mobile": 1,
            "specifications": "360° omnidirectional | Detects: 2.4/5.8GHz ISM, GNSS signals | Alert system integrated"
        },
        {
            "name": "AARTOS C-UAS Radar",
            "type": "RADAR",
            "description": "3D surveillance radar for small UAV detection",
            "effective_against": "All drones including stealth/low-RCS models",
            "range_km": 15,
            "deployment_time_hours": 4,
            "cost_estimate_eur": 1200000,
            "requires_authorization": 0,
            "mobile": 0,
            "specifications": "360° coverage | Micro-Doppler classification | Tracks 500+ targets | Weather-resistant"
        },

        # Kinetic Systems
        {
            "name": "SkyWall 100",
            "type": "NET_CAPTURE",
            "description": "Handheld pneumatic net launcher for drone capture",
            "effective_against": "Small consumer drones (DJI Phantom, Mavic class)",
            "range_km": 0.1,
            "deployment_time_hours": 0,
            "cost_estimate_eur": 45000,
            "requires_authorization": 0,
            "mobile": 1,
            "specifications": "Range: 100m | Net size: 8m² | Parachute recovery | Reusable cartridges"
        },
        {
            "name": "DroneGun Tactical",
            "type": "RF_JAMMER",
            "description": "Rifle-style RF/GNSS jammer for tactical response",
            "effective_against": "Consumer drones, DJI models, short-range UAVs",
            "range_km": 2,
            "deployment_time_hours": 0,
            "cost_estimate_eur": 18000,
            "requires_authorization": 1,
            "mobile": 1,
            "specifications": "Bands: GNSS L1/L2, 2.4/5.8GHz | Weight: 4kg | Battery: 2hr | Point-and-shoot operation"
        },

        # Cyber/Electronic Warfare
        {
            "name": "DroneSentry-X",
            "type": "EW_SUITE",
            "description": "Integrated electronic warfare suite with protocol hijacking",
            "effective_against": "Consumer drones, tactical UAVs, can force-land DJI drones",
            "range_km": 5,
            "deployment_time_hours": 3,
            "cost_estimate_eur": 450000,
            "requires_authorization": 1,
            "mobile": 0,
            "specifications": "RF detection + jamming + protocol exploitation | DJI force-land capability | Automatic threat response"
        },

        # Directed Energy
        {
            "name": "Leonidas HPM System",
            "type": "MICROWAVE",
            "description": "High-powered microwave system for electronic disruption",
            "effective_against": "Drone swarms, military UAVs, all electronic systems",
            "range_km": 1,
            "deployment_time_hours": 6,
            "cost_estimate_eur": 2500000,
            "requires_authorization": 1,
            "mobile": 0,
            "specifications": "Instant effect on electronics | Wide area coverage | No physical damage | Repeated use"
        },

        # Layered Defense Systems
        {
            "name": "NINJA Mobile C-UAS",
            "type": "INTEGRATED_SYSTEM",
            "description": "Mobile integrated detection and defeat platform",
            "effective_against": "All drone types, swarms, military reconnaissance UAVs",
            "range_km": 8,
            "deployment_time_hours": 1,
            "cost_estimate_eur": 1800000,
            "requires_authorization": 1,
            "mobile": 1,
            "specifications": "Vehicle-mounted | 360° radar + RF + EO/IR | Multi-band jamming | Automatic threat tracking"
        }
    ]

    for cm in counter_measures:
        cursor.execute("""
            INSERT INTO counter_measures
            (name, type, description, effective_against, range_km, deployment_time_hours,
             cost_estimate_eur, requires_authorization, mobile, specifications)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cm["name"], cm["type"], cm["description"], cm["effective_against"],
            cm["range_km"], cm["deployment_time_hours"], cm["cost_estimate_eur"],
            cm["requires_authorization"], cm["mobile"], cm["specifications"]
        ))

    conn.commit()
    print(f"  ✓ Added {len(counter_measures)} counter-measures")

    conn.close()

def generate_recommendations():
    """Generate counter-measure recommendations for classified incidents"""
    db_path = Path("data/drone_cuas.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n💡 Generating Counter-Measure Recommendations...")

    # Recommendation for Orlan-10 at Brunsbüttel (STATE_ACTOR)
    # Need heavy-duty system for military drone
    cursor.execute("""
        INSERT INTO incident_recommendations
        (incident_id, counter_measure_id, priority, reasoning, estimated_effectiveness,
         deployment_location_lat, deployment_location_lon, deployment_notes)
        VALUES
        (10, 2, 'CRITICAL',
         'Military-grade Orlan-10 requires advanced RF disruption. AUDS system effective against military UAVs with 10km range. Deploy at nuclear facility perimeter for critical infrastructure protection.',
         0.85, 53.8917, 9.1280,
         'Position on north perimeter of Brunsbüttel facility. Provides coverage of approach vectors from Baltic Sea. Requires 24/7 operator staffing.'),
        (10, 5, 'HIGH',
         'AARTOS radar provides early warning for incoming military UAVs. 15km range allows detection before RF countermeasures needed. Essential for layered defense.',
         0.90, 53.8917, 9.1280,
         'Install at highest point of facility. Clear line-of-sight to north (sea approach). Integrate with AUDS for automatic handoff.'),
        (10, 9, 'MEDIUM',
         'Leonidas HPM as last-resort hard-kill option if RF jamming fails. Effective against hardened military electronics.',
         0.75, 53.8917, 9.1280,
         'Backup system. Deploy only if drone penetrates RF jamming zone. Requires special authorization for nuclear site.')
    """)
    print("  ✓ Generated 3 recommendations for Brunsbüttel Orlan incident")

    # Recommendation for Zuid-Limburg (RECRUITED_LOCAL)
    # Consumer-grade threat, lighter systems
    cursor.execute("""
        INSERT INTO incident_recommendations
        (incident_id, counter_measure_id, priority, reasoning, estimated_effectiveness,
         deployment_location_lat, deployment_location_lon, deployment_notes)
        VALUES
        (189, 7, 'HIGH',
         'Consumer drone threat (recruited local with DJI-class equipment). DroneGun Tactical provides mobile response for security patrols around NATO JFC Brunssum.',
         0.90, 50.9449, 5.9694,
         'Issue to mobile security patrols (4 units recommended). Training required: 2 hours. Immediate response capability.'),
        (189, 4, 'HIGH',
         'RfPatrol passive detection for 24/7 monitoring of NATO compound perimeter. Alerts security when consumer drones approach.',
         0.85, 50.9449, 5.9694,
         'Install 4 units around JFC perimeter (north, south, east, west). 5km detection radius covers approach routes. No authorization required.'),
        (189, 8, 'MEDIUM',
         'DroneSentry-X can force-land DJI drones via protocol exploitation. Useful for non-destructive neutralization near populated areas.',
         0.80, 50.9449, 5.9694,
         'Fixed installation at JFC command center. Covers facility + Maastricht Airport approach. DJI-specific countermeasures most relevant for bounty hunters.')
    """)
    print("  ✓ Generated 3 recommendations for Zuid-Limburg incident")

    conn.commit()
    conn.close()
    print("\n✓ Recommendations generated!")

if __name__ == "__main__":
    print("🚀 Operational Classification & Counter-Measures System")
    print("=" * 70)

    add_classification_schema()
    classify_existing_incidents()
    populate_counter_measures()
    generate_recommendations()

    print("\n" + "=" * 70)
    print("✓ Complete! Database now includes:")
    print("  - Operational classification (STATE_ACTOR, RECRUITED_LOCAL, etc.)")
    print("  - Strategic assessment for incidents")
    print("  - Launch analysis for military drones")
    print("  - 10 C-UAS counter-measures with specifications")
    print("  - 6 tactical recommendations for classified incidents")
    print("\nReady for Pattern Analysis frontend!")
