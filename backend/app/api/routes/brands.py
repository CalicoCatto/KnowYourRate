"""Brand database search API for CN edition."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter()

# Load brand DB at module level
_BRAND_DB: dict | None = None


def _load_brand_db() -> dict:
    global _BRAND_DB
    if _BRAND_DB is not None:
        return _BRAND_DB
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "brand_db_cn.json"
    if not db_path.exists():
        logger.warning("Brand DB not found at %s", db_path)
        _BRAND_DB = {"brands": [], "bilibili_details": {}, "category_traits": []}
        return _BRAND_DB
    with open(db_path, encoding="utf-8") as f:
        _BRAND_DB = json.load(f)
    return _BRAND_DB


@router.get("/search")
async def search_brands(
    q: str = Query("", description="Search query (brand name, category, etc.)"),
    platform: str = Query("", description="Filter by platform: bilibili, douyin, kuaishou"),
    category: str = Query("", description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Search the brand database."""
    db = _load_brand_db()
    brands = db.get("brands", [])

    results = []
    q_lower = q.lower().strip()

    for brand in brands:
        # Platform filter
        if platform:
            if not brand.get(platform, False):
                continue

        # Category filter
        if category and category.lower() not in (brand.get("category", "") or "").lower():
            continue

        # Text search
        if q_lower:
            searchable = " ".join([
                brand.get("name", ""),
                brand.get("name_en", ""),
                brand.get("category", ""),
                brand.get("sub_category", ""),
                brand.get("notes", ""),
            ]).lower()
            if q_lower not in searchable:
                continue

        # Enrich with bilibili details if available
        brand_copy = dict(brand)
        bilibili_details = db.get("bilibili_details", {})
        if brand["id"] in bilibili_details:
            brand_copy["bilibili_details"] = bilibili_details[brand["id"]]

        results.append(brand_copy)

        if len(results) >= limit:
            break

    # Get unique categories for filter
    categories = sorted(set(b.get("category", "") for b in brands if b.get("category")))

    return {
        "brands": results,
        "total": len(results),
        "categories": categories,
    }


@router.get("/categories")
async def get_brand_categories() -> dict:
    """Get category investment characteristics for B站."""
    db = _load_brand_db()
    return {
        "category_traits": db.get("category_traits", []),
    }
