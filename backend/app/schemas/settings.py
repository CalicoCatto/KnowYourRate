from pydantic import BaseModel


class ProviderInfo(BaseModel):
    """Information about a supported LLM provider."""

    id: str
    display_name: str
    models: list[str]
    docs_url: str


class ProviderSetup(BaseModel):
    """Request body to configure an LLM provider."""

    provider: str
    api_key: str
    model: str | None = None


class ProviderResponse(BaseModel):
    """Response with provider config (API key masked)."""

    provider: str
    model: str | None = None
    api_key_masked: str


class TestResult(BaseModel):
    """Result of testing an LLM provider connection."""

    success: bool
    message: str
