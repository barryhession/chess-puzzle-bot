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
from pathlib import Path

import requests

_BASE = "https://graph.instagram.com/v20.0"
_TIMEOUT = 30
_MEDIA_DOWNLOAD_ERROR_SUBCODE = 2207052
_MEDIA_DOWNLOAD_RETRIES = 3
_MEDIA_DOWNLOAD_RETRY_DELAY = 5


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


def _response_json(resp: requests.Response) -> dict:
    """Best-effort JSON decoding for Meta API responses."""
    try:
        data = resp.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_retryable_media_download_error(resp: requests.Response, data: dict) -> bool:
    """Return True for Meta's intermittent media-download failure."""
    error = data.get("error", {})
    return (
        resp.status_code == 400
        and isinstance(error, dict)
        and error.get("error_subcode") == _MEDIA_DOWNLOAD_ERROR_SUBCODE
    )


def _post(endpoint: str, payload: dict, *, retry_media_download_errors: bool = False) -> dict:
    """POST to the Graph API; optionally retry transient media-download failures."""
    attempts = _MEDIA_DOWNLOAD_RETRIES if retry_media_download_errors else 1

    for attempt in range(1, attempts + 1):
        resp = requests.post(
            f"{_BASE}/{endpoint}",
            data=payload,
            timeout=_TIMEOUT,
        )
        data = _response_json(resp)
        if resp.ok and "error" not in data:
            return data

        if (
            retry_media_download_errors
            and attempt < attempts
            and _is_retryable_media_download_error(resp, data)
        ):
            print(
                "[instagram] Meta could not fetch the media URL "
                f"(attempt {attempt}/{attempts}); retrying..."
            )
            time.sleep(_MEDIA_DOWNLOAD_RETRY_DELAY)
            continue

        if not resp.ok:
            raise RuntimeError(f"Meta API HTTP {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Meta API error: {data['error']}")


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
        retry_media_download_errors=True,
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


def post_comment(media_id: str, text: str) -> str:
    """
    Post a comment on an existing Instagram media object.

    Args:
        media_id: the numeric ID of the published post
        text:     comment text

    Returns:
        The comment's numeric ID string.
    """
    account_id = _account_id()
    token = _token()

    print(f"[instagram] Posting solution comment on media {media_id}...")
    data = _post(
        f"{media_id}/comments",
        {
            "message":      text,
            "access_token": token,
        },
    )
    comment_id = data["id"]
    print(f"[instagram] Comment posted! Comment ID: {comment_id}")
    return comment_id


def post_stories_image(image_url: str) -> str:
    """
    Post a static image to Instagram Stories.

    Automatically pads 1080×1350 images to 1080×1920 (9:16) with black bars
    if needed, since Stories requires the taller aspect ratio.

    Args:
        image_url: publicly accessible HTTPS URL of the image

    Returns:
        The published media's numeric ID string.
    """
    from PIL import Image
    import tempfile
    from src.image_host import upload_image

    account_id = _account_id()
    token = _token()

    # Download and check dimensions
    print("[instagram] Checking image dimensions for Stories...")
    resp = requests.get(image_url, timeout=30)
    resp.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    w, h = img.size

    if h < 1920:
        # Pad to 1080×1920
        print(f"[instagram] Padding {w}×{h} to 1080×1920 for Stories...")
        canvas = Image.new("RGB", (1080, 1920), (18, 18, 18))
        y_offset = (1920 - h) // 2
        canvas.paste(img, (0, y_offset))
        padded_path = tmp_path.replace(".png", "_stories.png")
        canvas.save(padded_path, "PNG")

        # Upload padded version
        stories_url = upload_image(Path(padded_path))
        print(f"[instagram] Padded Stories image: {stories_url}")
    else:
        stories_url = image_url
        padded_path = None

    # Clean up temp files
    Path(tmp_path).unlink(missing_ok=True)
    if padded_path:
        Path(padded_path).unlink(missing_ok=True)

    print("[instagram] Creating Stories image container...")
    container_data = _post(
        f"{account_id}/media",
        {
            "media_type":   "STORIES",
            "image_url":    stories_url,
            "access_token": token,
        },
        retry_media_download_errors=True,
    )
    container_id = container_data["id"]
    print(f"[instagram] Stories container created: {container_id}")

    # Give Meta a moment to process the image
    time.sleep(5)

    print("[instagram] Publishing to Stories...")
    publish_data = _post(
        f"{account_id}/media_publish",
        {
            "creation_id":  container_id,
            "access_token": token,
        },
    )
    media_id = publish_data["id"]
    print(f"[instagram] Stories published! Media ID: {media_id}")
    return media_id


def post_stories(video_url: str) -> str:
    """
    Post a video to Instagram Stories.

    Args:
        video_url: publicly accessible HTTPS URL of the MP4 video

    Returns:
        The published media's numeric ID string.
    """
    account_id = _account_id()
    token = _token()

    # Step 1 – create video container
    print("[instagram] Creating Stories container...")
    container_data = _post(
        f"{account_id}/media",
        {
            "media_type":  "STORIES",
            "video_url":   video_url,
            "access_token": token,
        },
        retry_media_download_errors=True,
    )
    container_id = container_data["id"]
    print(f"[instagram] Stories container created: {container_id}")

    # Poll until the video is ready (Meta needs time to download + transcode)
    print("[instagram] Waiting for video to process...")
    for attempt in range(20):
        time.sleep(5)
        status_resp = requests.get(
            f"{_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=_TIMEOUT,
        )
        status = status_resp.json().get("status_code", "UNKNOWN")
        print(f"[instagram] Processing status: {status} (attempt {attempt + 1})")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Video processing failed on Meta's side")

    # Step 2 – publish
    print("[instagram] Publishing to Stories...")
    publish_data = _post(
        f"{account_id}/media_publish",
        {
            "creation_id":  container_id,
            "access_token": token,
        },
    )
    media_id = publish_data["id"]
    print(f"[instagram] Stories published! Media ID: {media_id}")
    return media_id
