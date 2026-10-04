"""Verified Instagram Content Publishing boundary.

The publisher is deliberately not cacheable: publishing is an external side effect.
Credentials are read only from environment variables.
"""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

GRAPH_VERSION = os.getenv("INSTAGRAM_GRAPH_VERSION", "v26.0")
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"


class InstagramPublishError(RuntimeError):
    pass


def _request(method: str, path: str, params: dict[str, object]) -> dict:
    query = urlencode({k: v for k, v in params.items() if v is not None})
    request = Request(f"{GRAPH_BASE}/{path}?{query}", method=method)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InstagramPublishError(f"Instagram API {exc.code}: {detail}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstagramPublishError("Instagram API returned non-JSON data") from exc


def publish_image(*, image_url: str, caption: str = "", alt_text: str = "", approved: bool = False) -> dict:
    if not approved:
        raise InstagramPublishError("Explicit publish approval is required")
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
    if not token or not ig_user_id:
        raise InstagramPublishError("Instagram is not configured: set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID")
    if not image_url.startswith(("https://", "http://")):
        raise InstagramPublishError("image_url must be an HTTP(S) URL that Instagram can fetch")

    container = _request("POST", f"{ig_user_id}/media", {
        "image_url": image_url,
        "caption": caption[:2200],
        "alt_text": alt_text[:1000],
        "access_token": token,
    })
    creation_id = container.get("id")
    if not creation_id:
        raise InstagramPublishError(f"Instagram did not return a container id: {container}")

    status = _request("GET", creation_id, {
        "fields": "status_code",
        "access_token": token,
    })
    if status.get("status_code") not in {"FINISHED", "PUBLISHED"}:
        raise InstagramPublishError(f"Instagram container is not publishable: {status}")

    published = _request("POST", f"{ig_user_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": token,
    })
    media_id = published.get("id")
    if not media_id:
        raise InstagramPublishError(f"Instagram did not return a published media id: {published}")

    receipt = _request("GET", media_id, {
        "fields": "id,media_type,permalink,timestamp",
        "access_token": token,
    })
    if receipt.get("id") != media_id:
        raise InstagramPublishError("Independent publication read-back did not match the published media id")

    return {
        "status": "VERIFIED",
        "creation_id": creation_id,
        "media_id": media_id,
        "receipt": receipt,
    }
