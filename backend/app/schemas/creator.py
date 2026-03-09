from datetime import datetime

from pydantic import BaseModel


class CreatorLookupRequest(BaseModel):
    """Request to look up a creator by platform and URL/handle."""

    platform: str
    channel_url: str


class CreatorProfile(BaseModel):
    """Full creator profile returned from lookup."""

    id: str
    platform: str
    platform_id: str
    handle: str
    display_name: str
    subscriber_count: int | None = None
    avg_views: int | None = None
    engagement_rate: float | None = None
    content_niche: str | None = None
    raw_data: dict | None = None
    fetched_at: datetime | None = None
