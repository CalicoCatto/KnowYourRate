"""
Hardcoded pricing reference data tables.

These tables are the foundation of the pricing engine — they provide
structured anchoring so that prices are consistent regardless of which
LLM model is used.
"""

from __future__ import annotations

import math
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. Niche CPM Baselines (USD per 1,000 views)
# ---------------------------------------------------------------------------

NICHE_CPM_TABLE: dict[str, dict[str, dict[str, int]]] = {
    "youtube": {
        "finance_investing":    {"low": 30, "mid": 50, "high": 75},
        "technology":           {"low": 20, "mid": 35, "high": 55},
        "business_saas":        {"low": 25, "mid": 40, "high": 60},
        "health_fitness":       {"low": 15, "mid": 25, "high": 40},
        "beauty_skincare":      {"low": 12, "mid": 22, "high": 35},
        "food_cooking":         {"low": 10, "mid": 18, "high": 30},
        "gaming":               {"low": 5,  "mid": 12, "high": 20},
        "lifestyle_vlog":       {"low": 8,  "mid": 15, "high": 25},
        "education":            {"low": 15, "mid": 28, "high": 45},
        "entertainment_comedy": {"low": 5,  "mid": 10, "high": 18},
        "travel":               {"low": 10, "mid": 20, "high": 35},
        "parenting_family":     {"low": 12, "mid": 22, "high": 35},
        "diy_crafts":           {"low": 8,  "mid": 15, "high": 25},
        "automotive":           {"low": 15, "mid": 30, "high": 50},
        "pets_animals":         {"low": 8,  "mid": 15, "high": 25},
    },
    "tiktok": {
        "finance_investing":    {"low": 20, "mid": 35, "high": 55},
        "technology":           {"low": 15, "mid": 25, "high": 40},
        "business_saas":        {"low": 18, "mid": 30, "high": 45},
        "health_fitness":       {"low": 10, "mid": 18, "high": 30},
        "beauty_skincare":      {"low": 8,  "mid": 15, "high": 28},
        "food_cooking":         {"low": 8,  "mid": 14, "high": 22},
        "gaming":               {"low": 4,  "mid": 8,  "high": 15},
        "lifestyle_vlog":       {"low": 6,  "mid": 12, "high": 20},
        "education":            {"low": 12, "mid": 20, "high": 35},
        "entertainment_comedy": {"low": 3,  "mid": 7,  "high": 14},
        "travel":               {"low": 8,  "mid": 15, "high": 28},
        "parenting_family":     {"low": 8,  "mid": 16, "high": 28},
        "diy_crafts":           {"low": 6,  "mid": 12, "high": 20},
        "automotive":           {"low": 10, "mid": 22, "high": 40},
        "pets_animals":         {"low": 5,  "mid": 10, "high": 18},
    },
}

# Average engagement rates by niche (used for modifier calculation)
NICHE_AVG_ENGAGEMENT: dict[str, dict[str, float]] = {
    "youtube": {
        "finance_investing": 3.5, "technology": 3.0, "business_saas": 2.5,
        "health_fitness": 3.8, "beauty_skincare": 3.5, "food_cooking": 4.0,
        "gaming": 5.0, "lifestyle_vlog": 3.5, "education": 4.0,
        "entertainment_comedy": 5.5, "travel": 3.0, "parenting_family": 4.0,
        "diy_crafts": 4.5, "automotive": 3.0, "pets_animals": 5.0,
    },
    "tiktok": {
        "finance_investing": 4.0, "technology": 3.5, "business_saas": 3.0,
        "health_fitness": 5.0, "beauty_skincare": 4.5, "food_cooking": 5.5,
        "gaming": 6.0, "lifestyle_vlog": 5.0, "education": 5.0,
        "entertainment_comedy": 7.0, "travel": 4.5, "parenting_family": 5.5,
        "diy_crafts": 5.5, "automotive": 4.0, "pets_animals": 6.5,
    },
}

# Niche display names (human-readable labels)
NICHE_DISPLAY_NAMES: dict[str, str] = {
    "finance_investing": "金融投资",
    "technology": "科技评测",
    "business_saas": "商业/SaaS",
    "health_fitness": "健康健身",
    "beauty_skincare": "美妆护肤",
    "food_cooking": "美食烹饪",
    "gaming": "游戏",
    "lifestyle_vlog": "生活方式",
    "education": "教育",
    "entertainment_comedy": "娱乐搞笑",
    "travel": "旅行",
    "parenting_family": "亲子家庭",
    "diy_crafts": "手工DIY",
    "automotive": "汽车",
    "pets_animals": "宠物动物",
}

# Fallback CPM for unknown niches
DEFAULT_CPM = {"low": 10, "mid": 18, "high": 30}

# ---------------------------------------------------------------------------
# 2. Tier Classification
# ---------------------------------------------------------------------------

TIER_TABLE: dict[str, dict[str, dict[str, int | str]]] = {
    "youtube": {
        "nano":     {"min_subs": 1_000,    "max_subs": 10_000,    "typical_range": "$50-$500"},
        "micro":    {"min_subs": 10_000,   "max_subs": 100_000,   "typical_range": "$200-$5,000"},
        "mid_tier": {"min_subs": 100_000,  "max_subs": 500_000,   "typical_range": "$1,000-$20,000"},
        "macro":    {"min_subs": 500_000,  "max_subs": 1_000_000, "typical_range": "$10,000-$50,000"},
        "mega":     {"min_subs": 1_000_000, "max_subs": 999_999_999, "typical_range": "$50,000+"},
    },
    "tiktok": {
        "nano":     {"min_subs": 1_000,    "max_subs": 10_000,    "typical_range": "$50-$300"},
        "micro":    {"min_subs": 10_000,   "max_subs": 100_000,   "typical_range": "$200-$2,000"},
        "mid_tier": {"min_subs": 100_000,  "max_subs": 500_000,   "typical_range": "$1,000-$10,000"},
        "macro":    {"min_subs": 500_000,  "max_subs": 1_000_000, "typical_range": "$5,000-$20,000"},
        "mega":     {"min_subs": 1_000_000, "max_subs": 999_999_999, "typical_range": "$20,000+"},
    },
}


def classify_tier(platform: str, subscribers: int) -> str:
    """Return tier name based on subscriber count."""
    tiers = TIER_TABLE.get(platform, TIER_TABLE["youtube"])
    for tier_name, bounds in tiers.items():
        if bounds["min_subs"] <= subscribers <= bounds["max_subs"]:
            return tier_name
    return "nano" if subscribers < 1000 else "mega"


# ---------------------------------------------------------------------------
# 3. Deliverable Type Multipliers
# ---------------------------------------------------------------------------

DELIVERABLE_MULTIPLIERS: dict[str, dict[str, float]] = {
    "youtube": {
        "dedicated_video":     1.0,
        "integrated_mention":  0.5,
        "pre_roll_mention":    0.35,
        "shorts":              0.25,
        "community_post":      0.1,
        "pinned_comment":      0.05,
        "livestream_mention":  0.4,
    },
    "tiktok": {
        "dedicated_video":     1.0,
        "integrated_mention":  0.6,
        "series_3_posts":      2.5,
        "duet_stitch":         0.4,
        "livestream_mention":  0.5,
    },
}

# ---------------------------------------------------------------------------
# 4. Usage Rights & Exclusivity Premiums
# ---------------------------------------------------------------------------

USAGE_RIGHTS_PREMIUMS: dict[str, float] = {
    "organic_only":           0.0,
    "brand_repost_30d":       0.15,
    "brand_repost_perpetual": 0.40,
    "whitelisting_30d":       0.30,
    "whitelisting_90d":       0.60,
    "whitelisting_perpetual": 1.0,
    "website_use":            0.20,
    "email_marketing":        0.15,
    "paid_ads":               0.50,
    "tv_print":               2.0,
    "perpetual_all_media":    3.0,
}

EXCLUSIVITY_PREMIUMS: dict[str, float] = {
    "none":                   0.0,
    "category_30d":           0.25,
    "category_90d":           0.50,
    "category_6m":            0.75,
    "category_12m":           1.0,
    "full_exclusivity_30d":   0.50,
    "full_exclusivity_90d":   1.0,
}

# ---------------------------------------------------------------------------
# 5. Known Brand Patterns
# ---------------------------------------------------------------------------

KNOWN_BRAND_PATTERNS: dict[str, dict] = {
    "nordvpn": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 50],
        "common_requirements": ["30s-60s mid-roll", "custom tracking link", "talking points provided"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "surfshark": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [25, 45],
        "common_requirements": ["mid-roll placement", "tracking link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "skillshare": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["free trial link", "personal endorsement style"],
        "known_issues": ["frequently offers below-market rates to new creators"],
        "payment_reliability": "good",
    },
    "squarespace": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [25, 45],
        "common_requirements": ["website demo", "promo code mention"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "raid shadow legends": {
        "category": "gaming",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "very_high",
        "negotiation_flexibility": "high",
        "typical_cpm_range": [20, 60],
        "common_requirements": ["60-90s gameplay demo", "download link"],
        "known_issues": ["strict script requirements"],
        "payment_reliability": "excellent",
    },
    "audible": {
        "category": "education",
        "typical_deal_type": "pre_roll_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["personal book recommendation", "free trial link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "betterhelp": {
        "category": "health_fitness",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [25, 50],
        "common_requirements": ["personal story angle", "tracking link"],
        "known_issues": ["controversial brand — some audiences react negatively"],
        "payment_reliability": "good",
    },
    "hello fresh": {
        "category": "food_cooking",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["cooking demo", "promo code"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "manscaped": {
        "category": "lifestyle_vlog",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 35],
        "common_requirements": ["product demo", "promo code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "honey": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["browser extension demo", "savings demonstration"],
        "known_issues": ["standardized rates, limited negotiation room"],
        "payment_reliability": "excellent",
    },
    "expressvpn": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 55],
        "common_requirements": ["mid-roll placement", "tracking link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "brilliant": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["learning demo", "personal experience"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "shopify": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 55],
        "common_requirements": ["success story angle", "free trial link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "notion": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["workflow demo", "template showcase"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "raycon": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [12, 25],
        "common_requirements": ["product review", "promo code"],
        "known_issues": ["standardized low rates"],
        "payment_reliability": "good",
    },
    "ag1": {
        "category": "health_fitness",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["product demo", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "ridge wallet": {
        "category": "lifestyle_vlog",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["product showcase", "promo code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "established titles": {
        "category": "entertainment_comedy",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [10, 25],
        "common_requirements": ["novelty angle", "affiliate link"],
        "known_issues": ["controversial product claims"],
        "payment_reliability": "good",
    },
    "casetify": {
        "category": "lifestyle_vlog",
        "typical_deal_type": "dedicated_video",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["product showcase", "custom design feature"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "wix": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [25, 45],
        "common_requirements": ["website building demo", "promo code"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "grammarly": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["writing demo", "free trial link"],
        "known_issues": ["strict script approval"],
        "payment_reliability": "excellent",
    },
    "dashlane": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["security demo", "free trial link"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "dollar shave club": {
        "category": "lifestyle_vlog",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["product unboxing", "promo code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "blue apron": {
        "category": "food_cooking",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 35],
        "common_requirements": ["meal prep demo", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "athletic greens": {
        "category": "health_fitness",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [25, 50],
        "common_requirements": ["morning routine angle", "affiliate link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "fiverr": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [18, 35],
        "common_requirements": ["freelancer success story", "sign-up link"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "curiositystream": {
        "category": "education",
        "typical_deal_type": "pre_roll_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [12, 25],
        "common_requirements": ["documentary recommendation", "free trial link"],
        "known_issues": ["lower budgets for smaller creators"],
        "payment_reliability": "good",
    },
    "private internet access": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [20, 40],
        "common_requirements": ["privacy demo", "tracking link"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "keeps": {
        "category": "health_fitness",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [18, 35],
        "common_requirements": ["personal testimonial", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "masterclass": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [20, 45],
        "common_requirements": ["learning journey angle", "gift-giving angle"],
        "known_issues": ["seasonal campaigns only"],
        "payment_reliability": "excellent",
    },
    "coinbase": {
        "category": "finance_investing",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "very_high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [40, 75],
        "common_requirements": ["crypto education angle", "sign-up bonus link"],
        "known_issues": ["regulatory restrictions by region"],
        "payment_reliability": "excellent",
    },
    "public.com": {
        "category": "finance_investing",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [35, 60],
        "common_requirements": ["investing demo", "sign-up bonus"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "morning brew": {
        "category": "business_saas",
        "typical_deal_type": "pre_roll_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [12, 25],
        "common_requirements": ["newsletter sign-up CTA"],
        "known_issues": ["flat-rate offers, limited negotiation"],
        "payment_reliability": "good",
    },
    "best fiends": {
        "category": "gaming",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 40],
        "common_requirements": ["gameplay demo", "download link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "genshin impact": {
        "category": "gaming",
        "typical_deal_type": "dedicated_video",
        "budget_tier": "very_high",
        "negotiation_flexibility": "high",
        "typical_cpm_range": [25, 70],
        "common_requirements": ["gameplay feature showcase", "download link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "dbrand": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 35],
        "common_requirements": ["product showcase", "promo code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "tradingview": {
        "category": "finance_investing",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 55],
        "common_requirements": ["charting demo", "premium trial link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "canva": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [22, 42],
        "common_requirements": ["design workflow demo", "free trial link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "hubspot": {
        "category": "business_saas",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "very_high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [35, 65],
        "common_requirements": ["CRM demo", "free tier sign-up"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "adobe": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "very_high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [30, 55],
        "common_requirements": ["creative workflow demo", "free trial link"],
        "known_issues": ["long approval process"],
        "payment_reliability": "excellent",
    },
    "samsung": {
        "category": "technology",
        "typical_deal_type": "dedicated_video",
        "budget_tier": "very_high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 60],
        "common_requirements": ["product review", "launch event tie-in"],
        "known_issues": ["strict brand guidelines"],
        "payment_reliability": "excellent",
    },
    "dyson": {
        "category": "technology",
        "typical_deal_type": "dedicated_video",
        "budget_tier": "very_high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [35, 60],
        "common_requirements": ["product demo", "before/after comparison"],
        "known_issues": ["strict creative approval"],
        "payment_reliability": "excellent",
    },
    "seatgeek": {
        "category": "entertainment_comedy",
        "typical_deal_type": "pre_roll_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 35],
        "common_requirements": ["event angle", "promo code"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "mvmt watches": {
        "category": "lifestyle_vlog",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [12, 28],
        "common_requirements": ["product showcase", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "away luggage": {
        "category": "travel",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 32],
        "common_requirements": ["travel story angle", "promo code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "nord security": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [28, 50],
        "common_requirements": ["security awareness angle", "tracking link"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "state farm": {
        "category": "finance_investing",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "very_high",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [35, 70],
        "common_requirements": ["brand safety compliance", "pre-approved messaging"],
        "known_issues": ["very strict content guidelines"],
        "payment_reliability": "excellent",
    },
    "rocket money": {
        "category": "finance_investing",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 55],
        "common_requirements": ["personal savings demo", "sign-up link"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "incogni": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [18, 38],
        "common_requirements": ["privacy concern angle", "tracking link"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "factor meals": {
        "category": "food_cooking",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [18, 38],
        "common_requirements": ["meal unboxing", "promo code"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "liquid iv": {
        "category": "health_fitness",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 30],
        "common_requirements": ["product demo", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
    "stamps.com": {
        "category": "business_saas",
        "typical_deal_type": "pre_roll_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",
        "typical_cpm_range": [12, 25],
        "common_requirements": ["business use case", "free trial link"],
        "known_issues": ["standardized rates"],
        "payment_reliability": "good",
    },
    "babbel": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [15, 32],
        "common_requirements": ["language learning demo", "discount code"],
        "known_issues": [],
        "payment_reliability": "good",
    },
}

# ---------------------------------------------------------------------------
# 6. Contract Red Flag Rules
# ---------------------------------------------------------------------------

CONTRACT_RED_FLAGS: dict[str, dict[str, str]] = {
    "perpetual_rights_no_premium": {
        "condition": "perpetual usage rights without additional compensation",
        "severity": "high",
        "advice": "Reject or demand 200-300% premium for perpetual rights",
    },
    "unlimited_revisions": {
        "condition": "unlimited content revision rounds",
        "severity": "medium",
        "advice": "Limit to 2-3 revision rounds in the contract",
    },
    "full_exclusivity_no_premium": {
        "condition": "full category exclusivity without extra compensation",
        "severity": "high",
        "advice": "Demand at least 50-100% premium for exclusivity",
    },
    "payment_net_90_plus": {
        "condition": "payment terms exceeding Net 90",
        "severity": "medium",
        "advice": "Request 50% upfront or shorten to Net 30",
    },
    "unilateral_termination": {
        "condition": "brand can unilaterally terminate without penalty",
        "severity": "medium",
        "advice": "Add a kill fee clause (25-50% of contract value)",
    },
    "vague_deliverables": {
        "condition": "deliverable descriptions are vague or open-ended",
        "severity": "medium",
        "advice": "Require specific quantities, formats, and deadlines",
    },
    "content_ownership_transfer": {
        "condition": "full content ownership transfer to brand",
        "severity": "high",
        "advice": "Change to license/usage rights — retain ownership",
    },
    "no_kill_fee": {
        "condition": "no termination/kill fee clause",
        "severity": "medium",
        "advice": "Add kill fee of 25-50% of contract value",
    },
}

# ---------------------------------------------------------------------------
# 7. Seasonal Modifiers
# ---------------------------------------------------------------------------

# Q4 = holiday season, highest ad spend
SEASONAL_MODIFIERS: dict[int, dict[str, float]] = {
    1:  {"default": 0.95, "health_fitness": 1.15},  # New Year fitness boom
    2:  {"default": 0.95},
    3:  {"default": 1.0},
    4:  {"default": 1.0},
    5:  {"default": 1.0},
    6:  {"default": 0.90, "travel": 1.10},  # Summer travel
    7:  {"default": 0.85, "travel": 1.10},
    8:  {"default": 0.90},
    9:  {"default": 1.05},  # Back to school
    10: {"default": 1.20},  # Q4 ramp
    11: {"default": 1.35},  # Black Friday
    12: {"default": 1.50},  # Holiday peak
}


# ---------------------------------------------------------------------------
# 8. Geo Modifiers
# ---------------------------------------------------------------------------

GEO_TIERS: dict[str, float] = {
    "US": 1.0,
    "UK": 0.95,
    "CA": 0.90,
    "AU": 0.90,
    "DE": 0.85,
    "FR": 0.80,
    "JP": 0.80,
    "KR": 0.75,
    "BR": 0.45,
    "IN": 0.30,
    "ID": 0.30,
    "PH": 0.35,
    "VN": 0.30,
    "TH": 0.35,
    "MX": 0.40,
}

DEFAULT_GEO_MODIFIER = 0.60  # Unknown geo fallback

# ---------------------------------------------------------------------------
# Calculation Functions
# ---------------------------------------------------------------------------


def get_niche_cpm(platform: str, niche: str) -> dict[str, int]:
    """Get CPM values for a platform+niche combo."""
    platform_cpms = NICHE_CPM_TABLE.get(platform, NICHE_CPM_TABLE["youtube"])
    return platform_cpms.get(niche, DEFAULT_CPM)


def calculate_base_price(
    platform: str,
    niche: str,
    avg_views: int,
) -> dict[str, float]:
    """Calculate base price range from CPM and average views."""
    cpm = get_niche_cpm(platform, niche)
    return {
        "low": cpm["low"] * avg_views / 1000,
        "mid": cpm["mid"] * avg_views / 1000,
        "high": cpm["high"] * avg_views / 1000,
    }


def calculate_engagement_modifier(
    engagement_rate: float,
    platform: str,
    niche: str,
) -> tuple[float, str]:
    """Calculate engagement-based price modifier."""
    niche_avg = NICHE_AVG_ENGAGEMENT.get(platform, {}).get(niche, 3.5)
    ratio = engagement_rate / niche_avg if niche_avg > 0 else 1.0

    if ratio < 0.5:
        modifier = 0.7
        reason = f"Engagement {engagement_rate}% is well below {niche} average {niche_avg}%"
    elif ratio < 1.0:
        # Linear interpolation: 0.5→0.85, 1.0→1.0
        modifier = 0.85 + (ratio - 0.5) * 0.3
        reason = f"Engagement {engagement_rate}% is below {niche} average {niche_avg}%"
    elif ratio <= 2.0:
        # Linear interpolation: 1.0→1.0, 2.0→1.3
        modifier = 1.0 + (ratio - 1.0) * 0.3
        reason = f"Engagement {engagement_rate}% is {(ratio - 1) * 100:.0f}% above {niche} average {niche_avg}%"
    else:
        modifier = 1.3  # Cap
        reason = f"Engagement {engagement_rate}% is exceptionally high vs {niche} average {niche_avg}%"

    return round(modifier, 2), reason


def calculate_geo_modifier(top_geo: str | None) -> tuple[float, str]:
    """Calculate geo-based price modifier."""
    if not top_geo:
        return 1.0, "No geo data available, using default"

    # Extract country code (handle formats like "US 65%, UK 12%")
    country = top_geo.strip().split()[0].upper().rstrip(",")
    modifier = GEO_TIERS.get(country, DEFAULT_GEO_MODIFIER)

    if modifier >= 0.9:
        reason = f"Primary audience in {country} — high commercial value region"
    elif modifier >= 0.7:
        reason = f"Primary audience in {country} — moderate commercial value"
    else:
        reason = f"Primary audience in {country} — lower commercial value region"

    return modifier, reason


def calculate_growth_modifier(monthly_growth_rate: float | None) -> tuple[float, str]:
    """Calculate growth-based price modifier."""
    if monthly_growth_rate is None:
        return 1.0, "No growth data available"

    if monthly_growth_rate > 10:
        return 1.15, f"Rapid growth ({monthly_growth_rate:.1f}%/mo) — rising creator premium"
    elif monthly_growth_rate > 3:
        return 1.05, f"Steady growth ({monthly_growth_rate:.1f}%/mo)"
    elif monthly_growth_rate >= 0:
        return 1.0, f"Stable channel ({monthly_growth_rate:.1f}%/mo)"
    else:
        return 0.9, f"Declining channel ({monthly_growth_rate:.1f}%/mo)"


def calculate_seasonal_modifier(niche: str, month: int | None = None) -> tuple[float, str]:
    """Calculate seasonal price modifier."""
    if month is None:
        month = datetime.now().month

    month_data = SEASONAL_MODIFIERS.get(month, {"default": 1.0})
    modifier = month_data.get(niche, month_data["default"])

    quarter = (month - 1) // 3 + 1
    if modifier > 1.1:
        reason = f"Q{quarter} peak season — higher demand drives premium pricing"
    elif modifier < 0.95:
        reason = f"Q{quarter} slower season — consider flexible pricing"
    else:
        reason = f"Q{quarter} — standard seasonal pricing"

    return round(modifier, 2), reason


def calculate_quality_modifier(
    avg_watch_time_pct: float | None = None,
    like_ratio: float | None = None,
) -> tuple[float, str]:
    """Calculate quality-based price modifier from watch time and like ratio."""
    modifier = 1.0
    reasons: list[str] = []

    if avg_watch_time_pct is not None and avg_watch_time_pct > 50:
        modifier *= 1.1
        reasons.append(f"High avg watch time ({avg_watch_time_pct:.0f}%) → 1.1×")

    if like_ratio is not None and like_ratio > 5:
        modifier *= 1.05
        reasons.append(f"Strong like ratio ({like_ratio:.1f}%) → 1.05×")

    if not reasons:
        reason = "No quality premium applied"
    else:
        reason = "; ".join(reasons)

    return round(modifier, 2), reason


def apply_all_modifiers(
    base_price: dict[str, float],
    engagement_rate: float,
    platform: str,
    niche: str,
    top_geo: str | None = None,
    monthly_growth_rate: float | None = None,
    avg_watch_time_pct: float | None = None,
    like_ratio: float | None = None,
) -> tuple[dict[str, float], dict[str, dict]]:
    """Apply all modifiers to base price and return adjusted price + breakdown."""
    eng_mod, eng_reason = calculate_engagement_modifier(engagement_rate, platform, niche)
    geo_mod, geo_reason = calculate_geo_modifier(top_geo)
    growth_mod, growth_reason = calculate_growth_modifier(monthly_growth_rate)
    seasonal_mod, seasonal_reason = calculate_seasonal_modifier(niche)
    quality_mod, quality_reason = calculate_quality_modifier(avg_watch_time_pct, like_ratio)

    total_modifier = eng_mod * geo_mod * growth_mod * seasonal_mod * quality_mod

    adjusted = {
        "low": round(base_price["low"] * total_modifier, 2),
        "mid": round(base_price["mid"] * total_modifier, 2),
        "high": round(base_price["high"] * total_modifier, 2),
    }

    modifiers = {
        "engagement_modifier": {"value": eng_mod, "reason": eng_reason},
        "geo_modifier": {"value": geo_mod, "reason": geo_reason},
        "growth_modifier": {"value": growth_mod, "reason": growth_reason},
        "seasonal_modifier": {"value": seasonal_mod, "reason": seasonal_reason},
        "quality_modifier": {"value": quality_mod, "reason": quality_reason},
    }

    return adjusted, modifiers


def calculate_deal_adjusted_price(
    base_range: dict[str, float],
    platform: str,
    deliverable_type: str,
    usage_rights: str = "organic_only",
    exclusivity: str = "none",
) -> tuple[dict[str, float], dict[str, float | str]]:
    """Apply deal condition multipliers to the base price range."""
    platform_deliverables = DELIVERABLE_MULTIPLIERS.get(platform, DELIVERABLE_MULTIPLIERS["youtube"])
    deliverable_mult = platform_deliverables.get(deliverable_type, 1.0)
    usage_premium = USAGE_RIGHTS_PREMIUMS.get(usage_rights, 0.0)
    exclusivity_premium = EXCLUSIVITY_PREMIUMS.get(exclusivity, 0.0)

    total_multiplier = deliverable_mult * (1 + usage_premium + exclusivity_premium)

    adjusted = {
        "low": round(base_range["low"] * total_multiplier, 2),
        "mid": round(base_range["mid"] * total_multiplier, 2),
        "high": round(base_range["high"] * total_multiplier, 2),
    }

    breakdown = {
        "deliverable_multiplier": deliverable_mult,
        "usage_rights_premium": usage_premium,
        "exclusivity_premium": exclusivity_premium,
        "total_multiplier": round(total_multiplier, 2),
    }

    return adjusted, breakdown


def generate_package_tiers(
    adjusted_price_mid: float,
    platform: str,
) -> dict[str, dict]:
    """Generate bronze/silver/gold package tiers."""
    return {
        "starter": {
            "name": "Starter",
            "price": round(adjusted_price_mid * 0.8),
            "includes": ["1 sponsored video"],
            "duration": "One-time",
        },
        "standard": {
            "name": "Standard",
            "price": round(adjusted_price_mid * 2.2),
            "includes": ["3 sponsored videos", "1 community post / story"],
            "duration": "3 months",
            "savings_vs_individual": "27%",
        },
        "premium": {
            "name": "Premium",
            "price": round(adjusted_price_mid * 4.0),
            "includes": ["6 sponsored videos", "3 stories/posts", "Brand social repost rights 30d"],
            "duration": "6 months",
            "savings_vs_individual": "33%",
        },
    }


def lookup_brand(brand_name: str) -> dict | None:
    """Look up known brand info (case-insensitive)."""
    return KNOWN_BRAND_PATTERNS.get(brand_name.lower().strip())


def detect_contract_red_flags(
    usage_rights: str,
    exclusivity: str,
    usage_premium_applied: float,
    exclusivity_premium_applied: float,
) -> list[dict]:
    """Detect contract red flags based on deal conditions."""
    flags = []

    # Perpetual rights without adequate premium
    if "perpetual" in usage_rights and usage_premium_applied < 0.3:
        flags.append(CONTRACT_RED_FLAGS["perpetual_rights_no_premium"])

    # Full exclusivity without premium
    if "full_exclusivity" in exclusivity and exclusivity_premium_applied < 0.3:
        flags.append(CONTRACT_RED_FLAGS["full_exclusivity_no_premium"])

    # Content ownership transfer
    if usage_rights == "perpetual_all_media":
        flags.append(CONTRACT_RED_FLAGS["content_ownership_transfer"])

    return flags


def route_complexity(
    brand_name: str | None,
    exclusivity: str,
    usage_rights: str,
    niche: str,
    is_first_brand_deal: bool = False,
) -> str:
    """Determine pipeline complexity: 'fast_track' or 'full_pipeline'."""
    HIGH_VARIANCE_NICHES = {"finance_investing", "technology", "business_saas", "automotive"}

    score = 0
    if brand_name:
        score += 2
    if exclusivity != "none":
        score += 2
    if usage_rights != "organic_only":
        score += 2
    if niche in HIGH_VARIANCE_NICHES:
        score += 1
    if is_first_brand_deal:
        score += 1

    return "full_pipeline" if score >= 3 else "fast_track"


def calculate_confidence(
    has_api_data: bool,
    has_engagement: bool,
    has_geo: bool,
    has_growth: bool,
    has_brand_intel: bool,
) -> float:
    """Calculate confidence score (0-1) based on data completeness."""
    score = 0.4  # base confidence for having subscriber + view count
    if has_api_data:
        score += 0.15
    if has_engagement:
        score += 0.15
    if has_geo:
        score += 0.1
    if has_growth:
        score += 0.1
    if has_brand_intel:
        score += 0.1
    return min(round(score, 2), 1.0)
