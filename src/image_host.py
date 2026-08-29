"""
image_host.py
-------------
Uploads the rendered PNG to a publicly accessible URL so Instagram's
servers can fetch it during the media-container creation step.

Strategy (in order of preference):
  1. ImgBB       – free API, no IP blocking, direct image URLs (set IMGBB_API_KEY)
  2. Imgur        – fallback, set IMGUR_CLIENT_ID
  3. catbox.moe  – local fallback only (blocked by GitHub Actions IPs)
"""

import base64
import os
from pathlib import Path

import requests

IMGBB_API_KEY   = os.getenv("IMGBB_API_KEY", "")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")

_TIMEOUT = 60  # seconds


def _upload_imgbb(image_path: Path) -> str:
    """Upload to ImgBB — returns a direct image URL."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": img_b64},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"ImgBB error: {data}")
    return data["data"]["url"]


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


def _upload_catbox(image_path: Path) -> str:
    """Upload to catbox.moe — works locally, blocked by some CI IP ranges."""
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (image_path.name, f, "image/png")},
            timeout=_TIMEOUT,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("https://files.catbox.moe/"):
        raise RuntimeError(f"Unexpected catbox response: {url!r}")
    return url


def upload_image(image_path: Path) -> str:
    """
    Upload `image_path` to a public host and return the direct HTTPS URL.
    Raises RuntimeError if all upload methods fail.
    """
    errors = []

    if IMGBB_API_KEY:
        try:
            url = _upload_imgbb(image_path)
            print(f"[image_host] Uploaded to ImgBB: {url}")
            return url
        except Exception as e:
            errors.append(f"ImgBB: {e}")
            print(f"[image_host] ImgBB failed: {e}")

    if IMGUR_CLIENT_ID:
        try:
            url = _upload_imgur(image_path)
            print(f"[image_host] Uploaded to Imgur: {url}")
            return url
        except Exception as e:
            errors.append(f"Imgur: {e}")
            print(f"[image_host] Imgur failed: {e}")

    try:
        url = _upload_catbox(image_path)
        print(f"[image_host] Uploaded to catbox.moe: {url}")
        return url
    except Exception as e:
        errors.append(f"catbox.moe: {e}")
        print(f"[image_host] catbox.moe failed: {e}")

    raise RuntimeError(
        "All image upload methods failed. "
        "Ensure IMGBB_API_KEY is set in your secrets.\n"
        + "\n".join(errors)
    )
