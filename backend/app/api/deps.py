from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings as _get_settings
from app.database import get_db as _get_db
from app.llm.provider import LLMClient
from app.models.settings import SettingsModel
from app.services.encryption import decrypt_value


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async for session in _get_db():
        yield session


def get_settings() -> Settings:
    """Return application settings."""
    return _get_settings()


async def get_llm_client(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMClient:
    """Build an LLMClient from the stored provider configuration."""
    provider_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_provider")
    )
    provider_setting = provider_row.scalar_one_or_none()

    api_key_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_api_key")
    )
    api_key_setting = api_key_row.scalar_one_or_none()

    model_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_model")
    )
    model_setting = model_row.scalar_one_or_none()

    if not provider_setting or not api_key_setting:
        raise ValueError(
            "LLM provider not configured. Please set up a provider in settings."
        )

    provider = provider_setting.value
    api_key = decrypt_value(api_key_setting.value, settings.ENCRYPTION_SECRET)
    model = model_setting.value if model_setting else None

    return LLMClient(provider=provider, api_key=api_key, model=model)
