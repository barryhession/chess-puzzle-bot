"""
exchange_token.py
-----------------
Refreshes the Instagram access token for another ~60 days.

Run this every ~50 days before the token expires, or add it as a
scheduled GitHub Actions job.

Usage:
    python exchange_token.py

It reads INSTAGRAM_ACCESS_TOKEN from .env, refreshes it, and writes
the new token back into .env automatically.
"""

import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
if not token:
    raise SystemExit("ERROR: INSTAGRAM_ACCESS_TOKEN is not set in .env")

print("Refreshing token...")

r = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={
        "grant_type":   "ig_refresh_token",
        "access_token": token,
    },
    timeout=15,
)

data = r.json()

if "error" in data:
    print("\nERROR:", data["error"])
    raise SystemExit(1)

new_token  = data["access_token"]
expires_in = data.get("expires_in", 0)
expires_days = expires_in // 86400

# Write new token back into .env
env_path = Path(".env")
content = env_path.read_text(encoding="utf-8")
content = re.sub(r"INSTAGRAM_ACCESS_TOKEN=.*", f"INSTAGRAM_ACCESS_TOKEN={new_token}", content)
env_path.write_text(content, encoding="utf-8")

print(f"Token refreshed successfully.")
print(f"Expires in: ~{expires_days} days")
print(f".env updated with new token.")
