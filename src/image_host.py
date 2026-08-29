"""
image_host.py
-------------
Uploads the rendered PNG to a publicly accessible URL so Instagram's
servers can fetch it during the media-container creation step.

Strategy (in order of preference):
  1. catbox.moe    – free, direct raw URL, no account needed, files kept indefinitely
  2. Imgur         – reliable, set IMGUR_CLIENT_ID in .env for this
  3. tmpfiles.org  – last resort, short-lived

Set IMGUR_CLIENT_ID in your .env for a more stable production backup.
"""

import os
from pathlib import Path

import requests

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")

_TIMEOUT = 30  # seconds


def _upload_catbox(image_path: Path) -> str:
    """Upload to catbox.moe — returns a direct https://files.catbox.moe/xxx.png URL."""
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (image_path.name, f, "image/png")},
            timeout=_TIMEOUT,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"Unexpected catbox response: {url}")
    return url


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
    raw_url: str = data["data"]["url"]
    return raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")


def upload_image(image_path: Path) -> str:
    """
    Upload `image_path` to a public host and return the direct HTTPS URL.
    Raises RuntimeError if all upload methods fail.
    """
    errors = []

    try:
        url = _upload_catbox(image_path)
        print(f"[image_host] Uploaded to catbox.moe: {url}")
        return url
    except Exception as e:
        errors.append(f"catbox.moe: {e}")

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

    raise RuntimeError("All image upload methods failed:\n" + "\n".join(errors))
