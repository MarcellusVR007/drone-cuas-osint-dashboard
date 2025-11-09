#!/usr/bin/env python3
"""
Render watchdog agent that pings the deployed CUAS dashboard and logs availability.
Optionally posts to a webhook when repeated failures occur.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional


def log(message: str) -> None:
    """Unified stdout logger with timestamps."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {message}", flush=True)


def notify_webhook(webhook_url: str, payload: dict) -> None:
    """Send JSON payload to webhook and swallow network errors."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "CUAS-Watchdog/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            log("Webhook notification sent")
    except urllib.error.URLError as exc:
        log(f"⚠ Failed to notify webhook: {exc}")


def ping(target_url: str, timeout: int) -> tuple[bool, Optional[int], Optional[str]]:
    """Ping the health endpoint and return tuple(ok, status_code, error_message)."""
    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "CUAS-Watchdog/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return 200 <= response.status < 400, response.status, None
    except urllib.error.HTTPError as exc:
        return False, exc.code, str(exc)
    except urllib.error.URLError as exc:
        return False, None, str(exc)


def main() -> int:
    target_url = os.getenv("WATCHDOG_TARGET_URL")
    if not target_url:
        log("❌ WATCHDOG_TARGET_URL is not set; aborting watchdog agent.")
        return 1

    interval = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "180"))
    timeout = int(os.getenv("WATCHDOG_TIMEOUT_SECONDS", "10"))
    webhook_url = os.getenv("WATCHDOG_WEBHOOK_URL")
    failures_until_alert = int(os.getenv("WATCHDOG_FAILURE_THRESHOLD", "3"))
    consecutive_failures = 0

    log(
        f"Watchdog agent monitoring {target_url} every {interval}s "
        f"(timeout={timeout}s, alert threshold={failures_until_alert})"
    )

    while True:
        ok, status, error = ping(target_url, timeout)
        if ok:
            log(f"✓ Health check succeeded (status {status})")
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            log(
                f"⚠ Health check failed (status={status}, error={error}, "
                f"consecutive_failures={consecutive_failures})"
            )
            if webhook_url and consecutive_failures >= failures_until_alert:
                payload = {
                    "event": "cuas_watchdog_alert",
                    "target": target_url,
                    "failures": consecutive_failures,
                    "status": status,
                    "error": error,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                notify_webhook(webhook_url, payload)

        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
