from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.database import init_db, seed_db

# Initialize app
app = FastAPI(
    title="OSINT CUAS Dashboard",
    description="Counter-UAS Intelligence Dashboard for EU Drone Incident Tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    from backend.database import SessionLocal
    from backend.models import Incident
    from backend.data_ingestion import initialize_data_sources

    db = SessionLocal()
    try:
        # Seed database (imports from JSON export if available)
        seed_db()

        # Initialize data sources
        initialize_data_sources(db)
    finally:
        db.close()
    print("✓ OSINT CUAS Dashboard Ready")

# Import and include routers
from backend.routers import incidents, drone_types, restricted_areas, patterns, interventions, general, data_sources, sources, intelligence, socmint, blockchain, forums, gru_monitoring

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

# Mount static files
if os.path.exists("frontend/src"):
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

# Serve frontend
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health endpoint for uptime checks."""
    return JSONResponse({"status": "ok"})

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/forensics")
async def serve_forensics():
    """Flight forensics demo page"""
    return FileResponse("frontend/flight_forensics_demo.html")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA - return index.html for all non-API routes"""
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}, 404
    if full_path.endswith(".html"):
        return FileResponse(f"frontend/{full_path}")
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
