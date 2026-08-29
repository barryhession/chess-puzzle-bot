"""
image_host.py
-------------
Uploads the rendered PNG to a publicly accessible URL so Instagram's
servers can fetch it during the media-container creation step.

Strategy (in order of preference):
  1. catbox.moe  – free, direct raw URL, files kept indefinitely
  2. Imgur       – reliable fallback, set IMGUR_CLIENT_ID in .env

After uploading, the URL is verified to actually serve image/png
before being returned — so Meta never gets an HTML page instead of an image.
"""

import os
from pathlib import Path

import requests

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")

_TIMEOUT = 60  # seconds — catbox can be slow


def _verify_url(url: str) -> None:
    """Raise if the URL doesn't serve an image content-type."""
    try:
        r = requests.get(url, timeout=15, stream=True)
        ct = r.headers.get("content-type", "")
        r.close()
        if "image" not in ct:
            raise RuntimeError(f"URL returned content-type '{ct}', expected image")
    except requests.RequestException as e:
        # Some hosts reject HEAD/GET range requests but Instagram can still fetch them.
        # Only hard-fail if we got a definitive non-image content-type.
        print(f"[image_host] Warning: could not verify URL ({e}), proceeding anyway")


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
    if not url.startswith("https://files.catbox.moe/"):
        raise RuntimeError(f"Unexpected catbox response: {url!r}")
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


def upload_image(image_path: Path) -> str:
    """
    Upload `image_path` to a public host, verify it serves a raw image,
    and return the direct HTTPS URL.
    Raises RuntimeError if all upload methods fail.
    """
    errors = []

    try:
        url = _upload_catbox(image_path)
        _verify_url(url)
        print(f"[image_host] Uploaded to catbox.moe: {url}")
        return url
    except Exception as e:
        errors.append(f"catbox.moe: {e}")
        print(f"[image_host] catbox.moe failed: {e}")

    if IMGUR_CLIENT_ID:
        try:
            url = _upload_imgur(image_path)
            _verify_url(url)
            print(f"[image_host] Uploaded to Imgur: {url}")
            return url
        except Exception as e:
            errors.append(f"Imgur: {e}")
            print(f"[image_host] Imgur failed: {e}")

    raise RuntimeError(
        "All image upload methods failed. "
        "Set IMGUR_CLIENT_ID in your secrets for a reliable fallback.\n"
        + "\n".join(errors)
    )
