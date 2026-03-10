from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_settings
from app.config import Settings
from app.models.creator import Creator
from app.models.settings import SettingsModel
from app.schemas.creator import CreatorLookupRequest, CreatorProfile
from app.services.encryption import decrypt_value
from app.services.tiktok import get_tiktok_form_schema

router = APIRouter()


async def _get_youtube_api_key(db: AsyncSession, settings: Settings) -> str | None:
    """Get YouTube API key: first from DB, then from environment variable."""
    row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "youtube_api_key")
    )
    setting = row.scalar_one_or_none()
    if setting:
        return decrypt_value(setting.value, settings.ENCRYPTION_SECRET)
    return settings.YOUTUBE_API_KEY


@router.post("/lookup", response_model=CreatorProfile)
async def lookup_creator(
    body: CreatorLookupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CreatorProfile:
    """Look up a creator by platform and channel URL/handle."""
    if body.platform == "youtube":
        youtube_key = await _get_youtube_api_key(db, settings)
        if not youtube_key:
            raise HTTPException(
                status_code=400,
                detail="YouTube API Key not configured. Please add it in Settings, or use manual input.",
            )

        try:
            from app.services.youtube import fetch_channel_info

            data = await fetch_channel_info(
                body.channel_url,
                api_key=youtube_key,
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

    elif body.platform == "bilibili":
        from app.services.bilibili import get_bilibili_form_schema
        schema = get_bilibili_form_schema()
        raise HTTPException(
            status_code=422,
            detail={
                "message": "B站数据暂不支持自动获取，请手动填写创作者数据。",
                "form_schema": schema,
            },
        )

    elif body.platform == "douyin":
        from app.services.douyin import get_douyin_form_schema
        schema = get_douyin_form_schema()
        raise HTTPException(
            status_code=422,
            detail={
                "message": "抖音数据暂不支持自动获取，请手动填写创作者数据。",
                "form_schema": schema,
            },
        )

    elif body.platform == "kuaishou":
        from app.services.kuaishou import get_kuaishou_form_schema
        schema = get_kuaishou_form_schema()
        raise HTTPException(
            status_code=422,
            detail={
                "message": "快手数据暂不支持自动获取，请手动填写创作者数据。",
                "form_schema": schema,
            },
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {body.platform}")
