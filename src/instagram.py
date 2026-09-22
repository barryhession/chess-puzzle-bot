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
_RETRY_DELAYS = (20, 40, 80)
_RETRYABLE_ERROR_CODES = {4, 17, 32, 613}
_RETRYABLE_ERROR_SUBCODES = {2207051, 2207052}


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


def _extract_error(resp: requests.Response) -> tuple[str, dict]:
    """Return a consistent error message and Meta error object for a response."""
    try:
        data = resp.json()
    except ValueError:
        return resp.text, {}

    if not isinstance(data, dict):
        return resp.text, {}

    error = data.get("error")
    if isinstance(error, dict):
        return str(error), error
    if error is not None:
        return str(error), {}
    return resp.text, {}


def _is_retryable_error(status_code: int, error: dict) -> bool:
    """Return True when Meta indicates the request should be retried later."""
    code = error.get("code")
    subcode = error.get("error_subcode")
    if status_code == 429:
        return True
    if 500 <= status_code < 600:
        return True
    if status_code == 403 and code in _RETRYABLE_ERROR_CODES:
        return True
    if status_code == 403 and subcode in _RETRYABLE_ERROR_SUBCODES:
        return True
    return False


def _retry_reason(status_code: int, error: dict) -> str:
    """Return a short explanation for why a request is being retried."""
    if status_code == 429:
        return "Meta API rate limit"
    if 500 <= status_code < 600:
        return f"Meta API server error ({status_code})"
    if error.get("error_subcode") in _RETRYABLE_ERROR_SUBCODES:
        return f"Meta API transient error subcode {error['error_subcode']}"
    if error.get("code") in _RETRYABLE_ERROR_CODES:
        return f"Meta API transient error code {error['code']}"
    return "Meta API transient error"


def _post(endpoint: str, payload: dict) -> dict:
    """POST to the Graph API; raise on HTTP or API errors."""
    for attempt in range(len(_RETRY_DELAYS) + 1):
        resp = requests.post(
            f"{_BASE}/{endpoint}",
            data=payload,
            timeout=_TIMEOUT,
        )
        if resp.ok:
            try:
                data = resp.json()
            except ValueError as exc:
                raise RuntimeError(f"Meta API returned invalid JSON: {resp.text}") from exc
            if not isinstance(data, dict):
                raise RuntimeError(f"Meta API returned unexpected JSON payload: {data!r}")
            if "error" not in data:
                return data
            raw_error = data["error"]
            error = raw_error if isinstance(raw_error, dict) else {}
            message = f"Meta API error: {raw_error}"
            status_code = resp.status_code
        else:
            message, error = _extract_error(resp)
            status_code = resp.status_code
            message = f"Meta API HTTP {status_code}: {message}"

        if attempt < len(_RETRY_DELAYS) and _is_retryable_error(status_code, error):
            delay = _RETRY_DELAYS[attempt]
            print(
                f"[instagram] {_retry_reason(status_code, error)}; "
                f"retrying in {delay}s (attempt {attempt + 2}/{len(_RETRY_DELAYS) + 1})..."
            )
            time.sleep(delay)
            continue

        raise RuntimeError(message)

    raise RuntimeError("Meta API request failed after retries")


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
