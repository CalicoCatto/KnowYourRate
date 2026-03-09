import logging
import re

from youtube import Channel, Video

logger = logging.getLogger(__name__)


async def fetch_channel_info(
    channel_url_or_handle: str,
    api_key: str | None = None,
) -> dict:
    """
    Fetch YouTube channel information using the python-youtube library.

    Supports URLs like:
      - https://www.youtube.com/@handle
      - https://www.youtube.com/channel/UC...
      - @handle
      - UC... (channel ID directly)

    Falls back gracefully if no API key is provided.
    """
    if not api_key:
        raise ValueError(
            "YouTube API key is required. Set YOUTUBE_API_KEY in your environment."
        )

    channel_id = _extract_channel_id(channel_url_or_handle)
    handle = _extract_handle(channel_url_or_handle)

    from youtube import Api

    api = Api(api_key=api_key)

    # Resolve channel
    if channel_id:
        channel_response = api.get_channel_info(channel_id=channel_id)
    elif handle:
        clean_handle = handle.lstrip("@")
        channel_response = api.get_channel_info(for_handle=clean_handle)
    else:
        # Try as a search query
        channel_response = api.get_channel_info(for_handle=channel_url_or_handle)

    if not channel_response or not channel_response.items:
        raise ValueError(f"Channel not found: {channel_url_or_handle}")

    channel = channel_response.items[0]
    snippet = channel.snippet
    stats = channel.statistics

    subscriber_count = int(stats.subscriberCount) if stats.subscriberCount else 0
    view_count = int(stats.viewCount) if stats.viewCount else 0
    video_count = int(stats.videoCount) if stats.videoCount else 0

    # Estimate avg views per video
    avg_views = view_count // video_count if video_count > 0 else 0

    # Rough engagement rate estimate (views per subscriber ratio)
    engagement_rate = round(avg_views / subscriber_count * 100, 2) if subscriber_count > 0 else 0.0

    # Try to determine content niche from channel description/category
    content_niche = _guess_niche(snippet.description or "", snippet.title or "")

    resolved_handle = ""
    if hasattr(snippet, "customUrl") and snippet.customUrl:
        resolved_handle = snippet.customUrl
    elif handle:
        resolved_handle = handle

    return {
        "channel_id": channel.id,
        "title": snippet.title or "",
        "handle": resolved_handle,
        "description": snippet.description or "",
        "subscriber_count": subscriber_count,
        "view_count": view_count,
        "video_count": video_count,
        "avg_views": avg_views,
        "engagement_rate": engagement_rate,
        "content_niche": content_niche,
        "thumbnail_url": snippet.thumbnails.high.url if snippet.thumbnails and snippet.thumbnails.high else "",
        "country": getattr(snippet, "country", ""),
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
