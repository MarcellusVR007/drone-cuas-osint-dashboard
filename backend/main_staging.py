#!/usr/bin/env python3
"""
STAGING SERVER - OSINT CUAS Dashboard
Port: 8001
Database: data/drone_cuas_staging.db
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

# IMPORTANT: Set database path BEFORE importing any backend modules
STAGING_DB = 'data/drone_cuas_staging.db'
PRODUCTION_DB = 'data/drone_cuas.db'
os.environ['DB_PATH'] = STAGING_DB

# Now import database module (will use STAGING_DB from environment)
from backend.database import init_db

# Copy production database to staging if not exists
if not os.path.exists(STAGING_DB):
    print(f"🔄 Creating staging database from production...")
    if os.path.exists(PRODUCTION_DB):
        shutil.copy2(PRODUCTION_DB, STAGING_DB)
        print(f"✅ Staging database created: {STAGING_DB}")
    else:
        print(f"⚠️  Production database not found, initializing new staging DB...")
        init_db()

# Initialize staging app
app = FastAPI(
    title="OSINT CUAS Dashboard - STAGING",
    description="🚧 Staging Environment - Counter-UAS Intelligence Dashboard",
    version="1.0.0-staging"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers (after setting DB_PATH)
from backend.routers import (
    incidents,
    drone_types,
    restricted_areas,
    patterns,
    interventions,
    general,
    data_sources,
    sources,
    intelligence,
    socmint,
    blockchain,
    forums,
    gru_monitoring,
    correlation,
    flight_forensics
)

# Include routers
app.include_router(general.router, prefix="/api", tags=["general"])
app.include_router(data_sources.router, prefix="/api/data-sources", tags=["data-sources"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["intelligence"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(drone_types.router, prefix="/api/drone-types", tags=["drone-types"])
app.include_router(restricted_areas.router, prefix="/api/restricted-areas", tags=["restricted-areas"])
app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])
app.include_router(interventions.router, prefix="/api/interventions", tags=["interventions"])
app.include_router(socmint.router, prefix="/api/socmint", tags=["socmint"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(forums.router, prefix="/api/forums", tags=["forums"])
app.include_router(gru_monitoring.router, prefix="/api/gru-monitoring", tags=["gru-monitoring"])
app.include_router(correlation.router, prefix="/api/correlation", tags=["correlation"])
app.include_router(flight_forensics.router, prefix="/api/flight-forensics", tags=["flight-forensics"])

# Mount static files
if os.path.exists("frontend/src"):
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

# Mount frontend directory for JSON data files
if os.path.exists("frontend"):
    app.mount("/data", StaticFiles(directory="frontend"), name="data")

# Root endpoint - serve index.html
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

# Serve all HTML pages
@app.get("/{page_name}.html")
async def read_page(page_name: str):
    file_path = f"frontend/{page_name}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "Page not found"}, status_code=404)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "STAGING",
        "database": STAGING_DB,
        "port": 8001,
        "warning": "🚧 This is a staging environment - changes here do NOT affect production"
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print("🚧 STAGING SERVER - OSINT CUAS Dashboard")
    print("=" * 80)
    print(f"📊 Database: {STAGING_DB}")
    print(f"🌐 URL: http://127.0.0.1:8001")
    print(f"⚠️  WARNING: This is a STAGING environment")
    print(f"   All changes are isolated from production (port 8000)")
    print("=" * 80)
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
