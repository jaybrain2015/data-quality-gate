"""Slack notification via incoming webhook -- the 'API integration' piece.
Uses only the stdlib, so the Lambda needs no extra dependency for this."""
from __future__ import annotations
import json
import os
import urllib.request


def notify_slack(message, webhook_url=None):
    webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("No SLACK_WEBHOOK_URL set; skipping notification.")
        return False
    payload = json.dumps({"text": message}).encode()
    req = urllib.request.Request(
        webhook_url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:  # noqa: BLE001
        print(f"Slack notify failed: {e}")
        return False