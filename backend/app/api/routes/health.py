from fastapi import APIRouter

from app.edition import is_cn

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "edition": "cn" if is_cn() else "international"}
