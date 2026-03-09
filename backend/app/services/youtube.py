import logging
import re

logger = logging.getLogger(__name__)


async def test_youtube_key(api_key: str) -> dict:
    """Test a YouTube Data API key by making a simple channel lookup."""
    try:
        from pyyoutube import Client

        client = Client(api_key=api_key)
        # Look up YouTube's own channel as a connectivity test
        response = client.channels.list(channel_id="UCBR8-60-B28hp2BmDPdntcQ", return_json=True)
        if response and response.get("items"):
            title = response["items"][0]["snippet"]["title"]
            return {"success": True, "message": f"Connection successful. Found channel: {title}"}
        return {"success": False, "message": "API key works but returned no data."}
    except Exception as e:
        return {"success": False, "message": f"YouTube API test failed: {str(e)}"}


async def fetch_channel_info(
    channel_url_or_handle: str,
    api_key: str | None = None,
) -> dict:
    """
    Fetch YouTube channel information using the pyyoutube library.

    Supports:
      - https://www.youtube.com/@handle
      - https://www.youtube.com/channel/UC...
      - @handle
      - UC... (channel ID directly)
    """
    if not api_key:
        raise ValueError(
            "YouTube API key is required. Add it in Settings page."
        )

    from pyyoutube import Client

    client = Client(api_key=api_key)

    channel_id = _extract_channel_id(channel_url_or_handle)
    handle = _extract_handle(channel_url_or_handle)

    # Try to resolve channel
    response = None
    if channel_id:
        response = client.channels.list(
            channel_id=channel_id,
            parts=["snippet", "statistics", "contentDetails"],
            return_json=True,
        )
    elif handle:
        clean_handle = handle.lstrip("@")
        response = client.channels.list(
            for_handle=clean_handle,
            parts=["snippet", "statistics", "contentDetails"],
            return_json=True,
        )
    else:
        # Try as handle without @
        response = client.channels.list(
            for_handle=channel_url_or_handle.strip(),
            parts=["snippet", "statistics", "contentDetails"],
            return_json=True,
        )

    if not response or not response.get("items"):
        raise ValueError(f"Channel not found: {channel_url_or_handle}")

    channel = response["items"][0]
    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})

    subscriber_count = int(stats.get("subscriberCount", 0))
    view_count = int(stats.get("viewCount", 0))
    video_count = int(stats.get("videoCount", 0))

    # Estimate avg views per video
    avg_views = view_count // video_count if video_count > 0 else 0

    # Rough engagement rate estimate (views per subscriber ratio)
    engagement_rate = round(avg_views / subscriber_count * 100, 2) if subscriber_count > 0 else 0.0

    content_niche = _guess_niche(snippet.get("description", ""), snippet.get("title", ""))

    resolved_handle = snippet.get("customUrl", "")
    if not resolved_handle and handle:
        resolved_handle = handle

    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = ""
    if thumbnails.get("high"):
        thumbnail_url = thumbnails["high"].get("url", "")

    return {
        "channel_id": channel.get("id", ""),
        "title": snippet.get("title", ""),
        "handle": resolved_handle,
        "description": snippet.get("description", ""),
        "subscriber_count": subscriber_count,
        "view_count": view_count,
        "video_count": video_count,
        "avg_views": avg_views,
        "engagement_rate": engagement_rate,
        "content_niche": content_niche,
        "thumbnail_url": thumbnail_url,
        "country": snippet.get("country", ""),
    }


def _extract_channel_id(url: str) -> str | None:
    """Extract a UC... channel ID from a URL."""
    match = re.search(r"(?:channel/)(UC[\w-]{22})", url)
    if match:
        return match.group(1)
    if url.startswith("UC") and len(url) == 24:
        return url
    return None


def _extract_handle(url: str) -> str | None:
    """Extract a @handle from a URL."""
    match = re.search(r"@([\w.-]+)", url)
    if match:
        return f"@{match.group(1)}"
    return None


def _guess_niche(description: str, title: str) -> str:
    """Make a rough guess at the content niche from channel metadata."""
    text = f"{title} {description}".lower()

    niches = {
        "gaming": ["game", "gaming", "gamer", "gameplay", "esport", "twitch"],
        "tech": ["tech", "technology", "gadget", "review", "software", "coding", "programming"],
        "beauty": ["beauty", "makeup", "skincare", "cosmetic", "tutorial"],
        "fashion": ["fashion", "style", "outfit", "clothing", "wear"],
        "food": ["food", "cook", "recipe", "kitchen", "chef", "baking"],
        "fitness": ["fitness", "workout", "gym", "exercise", "health"],
        "education": ["education", "learn", "tutorial", "course", "teach"],
        "entertainment": ["entertainment", "comedy", "funny", "vlog", "prank"],
        "music": ["music", "song", "artist", "producer", "beat"],
        "travel": ["travel", "adventure", "explore", "destination"],
        "finance": ["finance", "money", "invest", "crypto", "trading", "stock"],
        "lifestyle": ["lifestyle", "daily", "life", "vlog"],
    }

    for niche, keywords in niches.items():
        if any(kw in text for kw in keywords):
            return niche

    return "general"
