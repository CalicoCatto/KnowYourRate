import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.database import Base
from app.services.encryption import decrypt_value, encrypt_value


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    """Return test settings (no real DB or external services needed)."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        ENCRYPTION_SECRET="test-secret-key-for-unit-tests!!",
        YOUTUBE_API_KEY=None,
    )


@pytest_asyncio.fixture
async def db_engine(settings: Settings):
    """Create an in-memory async engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def encryption_secret() -> str:
    """Return a test encryption secret."""
    return "test-secret-key-for-unit-tests!!"


def test_encryption_roundtrip(encryption_secret: str) -> None:
    """Verify that encrypting and decrypting returns the original value."""
    original = "sk-test-api-key-12345"
    encrypted = encrypt_value(original, encryption_secret)
    assert encrypted != original
    decrypted = decrypt_value(encrypted, encryption_secret)
    assert decrypted == original
