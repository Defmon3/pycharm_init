#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

"""
Send Discord webhook notification.

Usage: python send_discord_notification.py '<json_payload>'
Requires COMMIT_WEBHOOK environment variable.
"""

import json
import os
import sys

import httpx

MAX_RETRIES = 3
TIMEOUT_SECONDS = 15


def send_notification(webhook_url: str, payload: dict) -> bool:
    """Send notification to Discord webhook with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            response = httpx.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            print(f"Notification sent (Status: {response.status_code}).")
            return True
        except httpx.HTTPStatusError as e:
            print(f"Attempt {attempt + 1} failed: HTTP {e.response.status_code}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"Attempt {attempt + 1} failed: {e}", file=sys.stderr)

    return False


def main() -> None:
    webhook_url = os.getenv("COMMIT_WEBHOOK")
    if not webhook_url:
        print("::warning::COMMIT_WEBHOOK not set. Skipping notification.", file=sys.stderr)
        sys.exit(0)

    if len(sys.argv) != 2:
        print("Usage: python send_discord_notification.py '<json_payload>'", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(1)

    if not send_notification(webhook_url, payload):
        print(f"::warning::Failed to send notification after {MAX_RETRIES} attempts.")

    # Don't fail the build for notification failures
    sys.exit(0)


if __name__ == "__main__":
    main()
