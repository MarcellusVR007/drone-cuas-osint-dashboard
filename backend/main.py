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
    try:
        init_db()
        # Seed database if data export exists
        try:
            seed_db()
        except Exception as e:
            print(f"⚠️  Could not seed database: {e}")
        print("✓ OSINT CUAS Dashboard Ready")
    except Exception as e:
        print(f"⚠️  Startup error: {e}")
        print("✓ OSINT CUAS Dashboard started with limited functionality")

# Import and include routers with error handling
def safe_include_router(router_module, router_name, prefix, tag):
    """Safely include a router, catching import errors"""
    try:
        module = __import__(f"backend.routers.{router_module}", fromlist=[router_name])
        router = getattr(module, router_name)
        app.include_router(router, prefix=prefix, tags=[tag])
        print(f"✓ Loaded router: {router_module}")
    except Exception as e:
        print(f"⚠️  Could not load router {router_module}: {e}")

# Core routers (essential for API)
try:
    from backend.routers import incidents, drone_types, restricted_areas, patterns
    app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
    app.include_router(drone_types.router, prefix="/api/drone-types", tags=["drone-types"])
    app.include_router(restricted_areas.router, prefix="/api/restricted-areas", tags=["restricted-areas"])
    app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])
    print("✓ Core routers loaded")
except Exception as e:
    print(f"⚠️  Error loading core routers: {e}")

# Optional routers (nice to have)
safe_include_router("general", "router", "/api", "general")
safe_include_router("health_tests", "router", "/api", "health")
safe_include_router("intelligence", "router", "/api/intelligence", "intelligence")
safe_include_router("interventions", "router", "/api/interventions", "interventions")
safe_include_router("socmint", "router", "/api/socmint", "socmint")
safe_include_router("forums", "router", "/api/forums", "forums")
safe_include_router("flight_forensics", "router", "/api/flight-forensics", "flight-forensics")

# Mount static files
if os.path.exists("frontend/src"):
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health endpoint for uptime checks."""
    return JSONResponse({"status": "ok"})

@app.get("/")
async def serve_frontend():
    """Root endpoint - returns API info if frontend not available"""
    frontend_path = "frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return JSONResponse({
        "app": "OSINT CUAS Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    })

@app.get("/forensics")
async def serve_forensics():
    """Flight forensics demo page"""
    forensics_path = "frontend/flight_forensics_demo.html"
    if os.path.exists(forensics_path):
        return FileResponse(forensics_path)
    return JSONResponse({"detail": "Frontend not deployed"}, status_code=404)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA - return index.html for all non-API routes"""
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    # Try to serve HTML file
    if full_path.endswith(".html"):
        html_path = f"frontend/{full_path}"
        if os.path.exists(html_path):
            return FileResponse(html_path)

    # Try to serve index.html
    index_path = "frontend/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # Fallback to API info
    return JSONResponse({"detail": "Frontend not deployed, use /docs for API documentation"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
