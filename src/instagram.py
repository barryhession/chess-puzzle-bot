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
_BACKOFF_SECONDS = (20, 40, 80, 160, 320)
_PUBLISH_RECOVERY_BACKOFF_SECONDS = (30, 60, 120)
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_RETRYABLE_GRAPH_ERRORS = {
    (4, 2207051),  # Application request limit reached
    (4, 2207052),  # Action blocked / temporary restrictions
    (-1, 2207085),  # Generic internal error / try again later
}


def _is_retryable_meta_error(resp: requests.Response, error: dict | None) -> bool:
    if resp.status_code in _RETRYABLE_STATUS_CODES:
        return True

    if not isinstance(error, dict):
        return False

    code = error.get("code")
    subcode = error.get("error_subcode")
    if (code, subcode) in _RETRYABLE_GRAPH_ERRORS:
        return True

    if code != -1:
        return False

    if str(error.get("type", "")) == "OAuthException":
        return True

    title = str(error.get("error_user_title", "")).lower()
    message = str(error.get("error_user_msg", "")).lower()
    return "internal error" in title or "internal server error" in message


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


def _is_retryable_publish_failure(error_text: str) -> bool:
    lowered = error_text.lower()
    if "oauthexception" not in lowered:
        return False
    return (
        '"code":-1' in lowered
        or '"code": -1' in lowered
        or "2207085" in lowered
        or "generic internal error" in lowered
        or "internal server error" in lowered
    )


def _post(endpoint: str, payload: dict) -> dict:
    """POST to the Graph API; retry selected transient failures."""

    for attempt in range(len(_BACKOFF_SECONDS) + 1):
        resp = requests.post(
            f"{_BASE}/{endpoint}",
            data=payload,
            timeout=_TIMEOUT,
        )

        try:
            body = resp.json()
        except ValueError:
            body = {}

        error = body.get("error") if isinstance(body, dict) else None
        code = error.get("code") if isinstance(error, dict) else None
        subcode = error.get("error_subcode") if isinstance(error, dict) else None
        retryable = _is_retryable_meta_error(resp, error)

        if resp.ok and not error:
            return body

        if retryable and attempt < len(_BACKOFF_SECONDS):
            delay = _BACKOFF_SECONDS[attempt]
            print(
                f"[instagram] Transient Meta API failure "
                f"(status={resp.status_code}, code={code}, subcode={subcode}); "
                f"retrying in {delay}s ({attempt + 1}/{len(_BACKOFF_SECONDS)})..."
            )
            time.sleep(delay)
            continue

        if not resp.ok:
            raise RuntimeError(f"Meta API HTTP {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Meta API error: {error}")

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

    for attempt in range(len(_PUBLISH_RECOVERY_BACKOFF_SECONDS) + 1):
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
        try:
            publish_data = _post(
                f"{account_id}/media_publish",
                {
                    "creation_id":  container_id,
                    "access_token": token,
                },
            )
        except RuntimeError as exc:
            if (
                attempt < len(_PUBLISH_RECOVERY_BACKOFF_SECONDS)
                and _is_retryable_publish_failure(str(exc))
            ):
                delay = _PUBLISH_RECOVERY_BACKOFF_SECONDS[attempt]
                print(
                    "[instagram] Publish failed with transient internal Meta error; "
                    f"recreating container in {delay}s "
                    f"({attempt + 1}/{len(_PUBLISH_RECOVERY_BACKOFF_SECONDS)})..."
                )
                time.sleep(delay)
                continue
            raise

        media_id = publish_data["id"]
        print(f"[instagram] Published! Media ID: {media_id}")
        return media_id

    raise RuntimeError("Meta publish failed after container recreation retries")


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
