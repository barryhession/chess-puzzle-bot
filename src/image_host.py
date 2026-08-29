"""
image_host.py
-------------
Uploads the rendered PNG to a publicly accessible URL so Instagram's
servers can fetch it during the media-container creation step.

Strategy:
  Primary:  GitHub Release asset upload via GH_PAT secret.
            GitHub's CDN (objects.githubusercontent.com) is fully
            accessible by Meta's servers and has no IP restrictions.
  Fallback: catbox.moe (works locally, may be blocked in CI).

GH_PAT must have 'repo' scope.
GH_REPO should be set to 'owner/repo' (e.g. 'barryhession/chess-puzzle-bot').
"""

import os
from pathlib import Path

import requests

GH_PAT  = os.getenv("GH_PAT", "")
GH_REPO = os.getenv("GH_REPO", "barryhession/chess-puzzle-bot")

_TIMEOUT = 60
_GH_API  = "https://api.github.com"


def _get_or_create_release(tag: str = "puzzle-images") -> dict:
    """Get the puzzle-images release, creating it if it doesn't exist."""
    headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github+json",
    }
    # Try to get existing release
    r = requests.get(
        f"{_GH_API}/repos/{GH_REPO}/releases/tags/{tag}",
        headers=headers,
        timeout=_TIMEOUT,
    )
    if r.status_code == 200:
        return r.json()

    # Create it
    r = requests.post(
        f"{_GH_API}/repos/{GH_REPO}/releases",
        headers=headers,
        json={
            "tag_name":    tag,
            "name":        "Puzzle Images",
            "body":        "Auto-generated chess puzzle images for Instagram posts.",
            "prerelease":  True,
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def _cleanup_old_assets(release_id: int, keep_count: int = 8) -> None:
    """Keep only the latest `keep_count` assets in the release, delete older ones."""
    headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github+json",
    }
    try:
        r = requests.get(
            f"{_GH_API}/repos/{GH_REPO}/releases/{release_id}/assets",
            headers=headers,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return
        assets = r.json()
        if len(assets) <= keep_count:
            return

        # Sort assets by updated_at descending (newest first)
        assets.sort(key=lambda a: a.get("updated_at", ""), reverse=True)

        # Delete anything beyond keep_count
        to_delete = assets[keep_count:]
        for asset in to_delete:
            asset_id = asset["id"]
            requests.delete(
                f"{_GH_API}/repos/{GH_REPO}/releases/assets/{asset_id}",
                headers=headers,
                timeout=_TIMEOUT,
            )
            print(f"[image_host] Cleaned up old release asset: {asset['name']}")
    except Exception as e:
        print(f"[image_host] Warning: failed to cleanup old assets: {e}")


def _upload_github(image_path: Path) -> str:
    """Upload image as a GitHub release asset and return the download URL."""
    release = _get_or_create_release()
    upload_url = release["upload_url"].split("{")[0]  # strip {?name,label}

    headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Content-Type":  "image/png",
    }
    with open(image_path, "rb") as f:
        r = requests.post(
            upload_url,
            headers=headers,
            params={"name": image_path.name},
            data=f,
            timeout=_TIMEOUT,
        )

    # 422 = asset with this name already exists — fetch its URL instead
    if r.status_code == 422:
        assets = requests.get(
            f"{_GH_API}/repos/{GH_REPO}/releases/{release['id']}/assets",
            headers={"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"},
            timeout=_TIMEOUT,
        ).json()
        for asset in assets:
            if asset["name"] == image_path.name:
                # Delete and re-upload so we always get the freshest image
                requests.delete(
                    f"{_GH_API}/repos/{GH_REPO}/releases/assets/{asset['id']}",
                    headers={"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"},
                    timeout=_TIMEOUT,
                )
                break
        # Re-upload after deletion
        with open(image_path, "rb") as f:
            r = requests.post(
                upload_url,
                headers=headers,
                params={"name": image_path.name},
                data=f,
                timeout=_TIMEOUT,
            )

    r.raise_for_status()

    # Cleanup old assets keeping only the latest 8
    _cleanup_old_assets(release["id"], keep_count=8)

    return r.json()["browser_download_url"]


def _upload_catbox(image_path: Path) -> str:
    """Upload to catbox.moe — works locally, may be blocked in CI."""
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
    Raises RuntimeError if all methods fail.
    """
    errors = []

    if GH_PAT:
        try:
            url = _upload_github(image_path)
            print(f"[image_host] Uploaded to GitHub Releases: {url}")
            return url
        except Exception as e:
            errors.append(f"GitHub Releases: {e}")
            print(f"[image_host] GitHub Releases failed: {e}")

    try:
        url = _upload_catbox(image_path)
        print(f"[image_host] Uploaded to catbox.moe: {url}")
        return url
    except Exception as e:
        errors.append(f"catbox.moe: {e}")
        print(f"[image_host] catbox.moe failed: {e}")

    raise RuntimeError(
        "All image upload methods failed. Ensure GH_PAT is set in your secrets.\n"
        + "\n".join(errors)
    )
