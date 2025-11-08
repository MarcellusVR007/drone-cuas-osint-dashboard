#!/usr/bin/env python3
"""
OSINT CUAS Dashboard Launcher
Starts the FastAPI backend and opens the dashboard in your browser
"""

import uvicorn
import webbrowser
import time
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

def run():
    """Launch the dashboard"""
    # Use 0.0.0.0 if RENDER env var is set (for production), else localhost
    HOST = "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1"
    PORT = int(os.getenv("PORT", 8000))

    print("\n" + "="*60)
    print("  OSINT CUAS Dashboard")
    print("  Counter-UAS Intelligence System")
    print("="*60)
    print(f"\n📡 Starting server on {HOST}:{PORT}")
    print(f"🌐 Dashboard: http://{HOST}:{PORT}")
    print(f"📚 API Docs: http://{HOST}:{PORT}/docs")
    print("\n💡 Press Ctrl+C to stop the server\n")

    # Try to open browser after brief delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open(f"http://{HOST}:{PORT}")
            print("✓ Browser opened")
        except Exception as e:
            print(f"⚠ Could not auto-open browser: {e}")
            print(f"  Please manually visit: http://{HOST}:{PORT}")

    import threading
    thread = threading.Thread(target=open_browser, daemon=True)
    thread.start()

    # Run server
    try:
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard stopped")
        sys.exit(0)

if __name__ == "__main__":
    run()
