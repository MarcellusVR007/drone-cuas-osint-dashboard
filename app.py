#!/usr/bin/env python3
"""
OSINT CUAS Dashboard Launcher
Starts the FastAPI backend and opens the dashboard in your browser
"""

import os
import sys
import threading
import time
import urllib.error
import urllib.request

import uvicorn
import webbrowser

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app


def start_keep_alive_thread() -> None:
    """Ping the external Render URL periodically to prevent idling."""
    if not os.getenv("RENDER"):
        return

    external_url = os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if not external_url:
        print("⚠ KEEP_ALIVE_URL or RENDER_EXTERNAL_URL not set; keep-alive disabled")
        return

    ping_url = external_url.rstrip("/") + "/health"
    interval = int(os.getenv("KEEP_ALIVE_INTERVAL", "540"))  # default every 9 minutes

    def ping_forever():
        while True:
            try:
                with urllib.request.urlopen(ping_url, timeout=10) as response:
                    status = getattr(response, "status", None) or response.getcode()
                    if status == 200:
                        print(f"↻ Keep-alive ping ok -> {ping_url}")
                    else:
                        print(f"⚠ Keep-alive ping returned {status}")
            except urllib.error.URLError as exc:
                print(f"⚠ Keep-alive ping failed: {exc}")
            time.sleep(interval)

    threading.Thread(target=ping_forever, daemon=True).start()


def run():
    """Launch the dashboard"""
    # Use 0.0.0.0 if RENDER env var is set (for production), else localhost
    host = "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1"
    port = int(os.getenv("PORT", 8000))

    print("\n" + "=" * 60)
    print("  OSINT CUAS Dashboard")
    print("  Counter-UAS Intelligence System")
    print("=" * 60)
    print(f"\n📡 Starting server on {host}:{port}")
    print(f"🌐 Dashboard: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("\n💡 Press Ctrl+C to stop the server\n")

    if not os.getenv("RENDER"):
        # Try to open browser after brief delay when running locally
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open(f"http://{host}:{port}")
                print("✓ Browser opened")
            except Exception as exc:
                print(f"⚠ Could not auto-open browser: {exc}")
                print(f"  Please manually visit: http://{host}:{port}")

        threading.Thread(target=open_browser, daemon=True).start()

    # Start keep-alive loop when running on Render
    start_keep_alive_thread()

    # Run server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard stopped")
        sys.exit(0)


if __name__ == "__main__":
    run()
