from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_settings
from app.config import Settings
from app.llm.provider import LLMClient
from app.llm.registry import SUPPORTED_PROVIDERS
from app.models.settings import SettingsModel
from app.schemas.settings import (
    ProviderInfo,
    ProviderResponse,
    ProviderSetup,
    TestResult,
)
from app.services.encryption import decrypt_value, encrypt_value

router = APIRouter()


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List all supported LLM providers."""
    providers = []
    for key, info in SUPPORTED_PROVIDERS.items():
        providers.append(
            ProviderInfo(
                id=key,
                display_name=info["display_name"],
                models=info["models"],
                docs_url=info["docs_url"],
            )
        )
    return providers


@router.post("/provider", response_model=ProviderResponse)
async def save_provider(
    body: ProviderSetup,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProviderResponse:
    """Save the chosen LLM provider and encrypted API key."""
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {body.provider}")

    encrypted_key = encrypt_value(body.api_key, settings.ENCRYPTION_SECRET)

    for key, value in [
        ("llm_provider", body.provider),
        ("llm_api_key", encrypted_key),
        ("llm_model", body.model or SUPPORTED_PROVIDERS[body.provider]["models"][0]),
    ]:
        row = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
        existing = row.scalar_one_or_none()
        if existing:
            existing.value = value
        else:
            db.add(SettingsModel(key=key, value=value))

    await db.flush()

    return ProviderResponse(
        provider=body.provider,
        model=body.model or SUPPORTED_PROVIDERS[body.provider]["models"][0],
        api_key_masked=_mask_key(body.api_key),
    )


@router.get("/provider", response_model=ProviderResponse | None)
async def get_provider(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProviderResponse | None:
    """Get the current LLM provider configuration (API key masked)."""
    provider_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_provider")
    )
    provider_setting = provider_row.scalar_one_or_none()
    if not provider_setting:
        return None

    api_key_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_api_key")
    )
    api_key_setting = api_key_row.scalar_one_or_none()

    model_row = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "llm_model")
    )
    model_setting = model_row.scalar_one_or_none()

    masked = ""
    if api_key_setting:
        decrypted = decrypt_value(api_key_setting.value, settings.ENCRYPTION_SECRET)
        masked = _mask_key(decrypted)

    return ProviderResponse(
        provider=provider_setting.value,
        model=model_setting.value if model_setting else None,
        api_key_masked=masked,
    )


@router.delete("/provider")
async def delete_provider(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Remove the stored LLM provider configuration."""
    for key in ("llm_provider", "llm_api_key", "llm_model"):
        row = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
        existing = row.scalar_one_or_none()
        if existing:
            await db.delete(existing)
    return {"status": "deleted"}


@router.post("/provider/test", response_model=TestResult)
async def test_provider(
    body: ProviderSetup,
) -> TestResult:
    """Test an API key by making a simple LLM call."""
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {body.provider}")

    model = body.model or SUPPORTED_PROVIDERS[body.provider]["models"][0]

    try:
        client = LLMClient(provider=body.provider, api_key=body.api_key, model=model)
        response = await client.chat(
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            temperature=0.0,
        )
        return TestResult(success=True, message=f"Connection successful. Response: {response[:100]}")
    except Exception as e:
        return TestResult(success=False, message=f"Connection failed: {str(e)}")


def _mask_key(key: str) -> str:
    """Mask an API key, showing only the first 4 and last 4 characters."""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
