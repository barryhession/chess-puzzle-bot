"""
instagram.py
------------
Publishes a single image post to Instagram via the Meta Graph API.

Required environment variables:
    INSTAGRAM_ACCESS_TOKEN  – long-lived page/user access token
    INSTAGRAM_ACCOUNT_ID    – numeric IG User ID (found in Meta Business Suite)

API flow:
  1. POST /{ig-user-id}/media          → creates a media container, returns container_id
  2. POST /{ig-user-id}/media_publish  → publishes the container
"""

import os
import time

import requests

_BASE = "https://graph.instagram.com/v20.0"
_TIMEOUT = 30


def _token() -> str:
    t = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    if not t:
        raise EnvironmentError(
            "INSTAGRAM_ACCESS_TOKEN is not set. "
            "Add it to your .env file or GitHub secret."
        )
    return t


def _account_id() -> str:
    aid = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    if not aid:
        raise EnvironmentError(
            "INSTAGRAM_ACCOUNT_ID is not set. "
            "Add it to your .env file or GitHub secret."
        )
    return aid


def _post(endpoint: str, payload: dict) -> dict:
    """POST to the Graph API; raise on HTTP or API errors."""
    resp = requests.post(
        f"{_BASE}/{endpoint}",
        data=payload,
        timeout=_TIMEOUT,
    )
    if not resp.ok:
        raise RuntimeError(f"Meta API HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Meta API error: {data['error']}")
    return data


def publish(image_url: str, caption: str) -> str:
    """
    Create a media container and publish it.

    Args:
        image_url: publicly accessible HTTPS URL of the image
        caption:   post caption text

    Returns:
        The published media's numeric ID string.
    """
    account_id = _account_id()
    token = _token()

    # Step 1 – create container
    print("[instagram] Creating media container…")
    container_data = _post(
        f"{account_id}/media",
        {
            "image_url": image_url,
            "caption":   caption,
            "access_token": token,
        },
    )
    container_id = container_data["id"]
    print(f"[instagram] Container created: {container_id}")

    # Give Meta a moment to process the image (recommended in docs)
    time.sleep(5)

    # Step 2 – publish
    print("[instagram] Publishing…")
    publish_data = _post(
        f"{account_id}/media_publish",
        {
            "creation_id":  container_id,
            "access_token": token,
        },
    )
    media_id = publish_data["id"]
    print(f"[instagram] Published! Media ID: {media_id}")
    return media_id
