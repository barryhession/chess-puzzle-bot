"""
exchange_token.py
-----------------
Refreshes the Instagram access token for another ~60 days.

Locally: reads from .env and writes the new token back into .env.
GitHub Actions: reads from environment variables (set via secrets),
                prints the new token so you can update the secret if needed.

Usage:
    python exchange_token.py
"""

import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()  # no-op in GitHub Actions (env vars already set)

token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
if not token:
    raise SystemExit("ERROR: INSTAGRAM_ACCESS_TOKEN is not set")

print("Refreshing Instagram token...")

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

new_token    = data["access_token"]
expires_in   = data.get("expires_in", 0)
expires_days = expires_in // 86400

print(f"Token refreshed. Expires in ~{expires_days} days.")

# Locally: write new token back into .env
env_path = Path(".env")
if env_path.exists():
    content = env_path.read_text(encoding="utf-8")
    content = re.sub(r"INSTAGRAM_ACCESS_TOKEN=.*", f"INSTAGRAM_ACCESS_TOKEN={new_token}", content)
    env_path.write_text(content, encoding="utf-8")
    print(".env updated with new token.")
else:
    # In GitHub Actions: export for subsequent steps via GITHUB_ENV
    github_env = os.getenv("GITHUB_ENV", "")
    if github_env:
        with open(github_env, "a") as f:
            f.write(f"INSTAGRAM_ACCESS_TOKEN={new_token}\n")
        print("GITHUB_ENV updated with new token.")
    else:
        print(f"New token: {new_token}")
