"""
image_host.py
-------------
Uploads the rendered PNG to a publicly accessible URL so Instagram's
servers can fetch it during the media-container creation step.

Strategy (in order of preference):
  1. tmpfiles.org  – free, no account needed, files live ~1 hour (enough for the API call)
  2. 0x0.st        – alternative free host, longer retention
  3. IMGUR_CLIENT_ID env var set → use Imgur anonymous upload (more reliable for production)

Set IMGUR_CLIENT_ID in your .env for a more stable production setup.
"""

import os
from pathlib import Path

import requests

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")

_TIMEOUT = 30  # seconds


def _upload_imgur(image_path: Path) -> str:
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.imgur.com/3/image",
            headers=headers,
            files={"image": f},
            timeout=_TIMEOUT,
        )
    resp.raise_for_status()
    data = resp.json()
    url = data["data"]["link"]
    # Force HTTPS
    return url.replace("http://", "https://")


def _upload_tmpfiles(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (image_path.name, f, "image/png")},
            timeout=_TIMEOUT,
        )
    resp.raise_for_status()
    data = resp.json()
    # Response: {"status":"success","data":{"url":"https://tmpfiles.org/XXXXX/file.png"}}
    raw_url: str = data["data"]["url"]
    # Convert to direct download URL: /dl/ prefix
    direct = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    return direct


def _upload_0x0(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://0x0.st",
            files={"file": (image_path.name, f, "image/png")},
            timeout=_TIMEOUT,
        )
    resp.raise_for_status()
    return resp.text.strip()


def upload_image(image_path: Path) -> str:
    """
    Upload `image_path` to a public host and return the direct HTTPS URL.
    Raises RuntimeError if all upload methods fail.
    """
    errors = []

    if IMGUR_CLIENT_ID:
        try:
            url = _upload_imgur(image_path)
            print(f"[image_host] Uploaded to Imgur: {url}")
            return url
        except Exception as e:
            errors.append(f"Imgur: {e}")

    try:
        url = _upload_tmpfiles(image_path)
        print(f"[image_host] Uploaded to tmpfiles.org: {url}")
        return url
    except Exception as e:
        errors.append(f"tmpfiles.org: {e}")

    try:
        url = _upload_0x0(image_path)
        print(f"[image_host] Uploaded to 0x0.st: {url}")
        return url
    except Exception as e:
        errors.append(f"0x0.st: {e}")

    raise RuntimeError("All image upload methods failed:\n" + "\n".join(errors))
