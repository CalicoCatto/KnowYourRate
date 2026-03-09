from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_settings
from app.config import Settings
from app.models.creator import Creator
from app.schemas.creator import CreatorLookupRequest, CreatorProfile
from app.services.tiktok import get_tiktok_form_schema
from app.services.youtube import fetch_channel_info

router = APIRouter()


@router.post("/lookup", response_model=CreatorProfile)
async def lookup_creator(
    body: CreatorLookupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CreatorProfile:
    """Look up a creator by platform and channel URL/handle."""
    if body.platform == "youtube":
        try:
            data = await fetch_channel_info(
                body.channel_url,
                api_key=settings.YOUTUBE_API_KEY,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"YouTube lookup failed: {str(e)}")

        creator = Creator(
            platform="youtube",
            platform_id=data.get("channel_id", ""),
            handle=data.get("handle", ""),
            display_name=data.get("title", ""),
            subscriber_count=data.get("subscriber_count"),
            avg_views=data.get("avg_views"),
            engagement_rate=data.get("engagement_rate"),
            content_niche=data.get("content_niche"),
            raw_data=data,
        )
        db.add(creator)
        await db.flush()

        return CreatorProfile(
            id=creator.id,
            platform=creator.platform,
            platform_id=creator.platform_id,
            handle=creator.handle,
            display_name=creator.display_name,
            subscriber_count=creator.subscriber_count,
            avg_views=creator.avg_views,
            engagement_rate=creator.engagement_rate,
            content_niche=creator.content_niche,
            raw_data=creator.raw_data,
            fetched_at=creator.fetched_at,
        )

    elif body.platform == "tiktok":
        schema = get_tiktok_form_schema()
        raise HTTPException(
            status_code=422,
            detail={
                "message": "TikTok API not available. Please provide creator data manually.",
                "form_schema": schema,
            },
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {body.platform}")
