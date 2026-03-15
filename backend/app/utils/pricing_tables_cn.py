"""
Hardcoded pricing reference data tables for the CN (China) edition.

Covers Bilibili (B站), Douyin (抖音), and Kuaishou (快手) platforms.
All prices are in CNY (Chinese Yuan / 人民币).

Key differences from international edition:
- Additive modifier system (vs multiplicative in international)
- VF ratio (粉丝播放比) as core metric
- Platform-specific signals (B站投币/收藏, 抖音完播率, 快手回访率)
- Content longevity modifier (B站长尾效应)
- City tier geo modifiers (一线/新一线/二线/三线)
- Livestream commerce pricing (坑位费 + 佣金)
- Platform official system fees (花火/星图/磁力聚星)
- Tax estimation (劳务报酬/个体/公司)
"""

from __future__ import annotations

import math
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. Niche CPM Baselines (CNY per 1,000 views)
# ---------------------------------------------------------------------------

NICHE_CPM_TABLE_CN: dict[str, dict[str, dict[str, int | str]]] = {
    "bilibili": {
        "finance_investing":    {"low": 40, "mid": 70,  "high": 120, "confidence": "medium", "sample_size": 15, "last_calibrated": "2025-Q1"},
        "technology":           {"low": 30, "mid": 50,  "high": 80,  "confidence": "high",   "sample_size": 42, "last_calibrated": "2025-Q1"},
        "gaming":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "high",   "sample_size": 45, "last_calibrated": "2025-Q1"},
        "anime_acg":            {"low": 12, "mid": 25,  "high": 45,  "confidence": "medium", "sample_size": 18, "last_calibrated": "2025-Q1"},
        "beauty_skincare":      {"low": 20, "mid": 40,  "high": 65,  "confidence": "medium", "sample_size": 16, "last_calibrated": "2025-Q1"},
        "food_cooking":         {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium", "sample_size": 14, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium", "sample_size": 12, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 25, "mid": 45,  "high": 75,  "confidence": "high",   "sample_size": 38, "last_calibrated": "2025-Q1"},
        "health_fitness":       {"low": 20, "mid": 35,  "high": 55,  "confidence": "low",    "sample_size": 6,  "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium", "sample_size": 13, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 35, "mid": 60,  "high": 100, "confidence": "medium", "sample_size": 17, "last_calibrated": "2025-Q1"},
        "digital_3c":           {"low": 25, "mid": 45,  "high": 70,  "confidence": "high",   "sample_size": 35, "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 18, "mid": 35,  "high": 55,  "confidence": "low",    "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 15, "mid": 30,  "high": 50,  "confidence": "low",    "sample_size": 4,  "last_calibrated": "2025-Q1"},
        "travel":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium", "sample_size": 11, "last_calibrated": "2025-Q1"},
        "music_dance":          {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",    "sample_size": 7,  "last_calibrated": "2025-Q1"},
        "entertainment_funny":  {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium", "sample_size": 19, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "low",    "sample_size": 5,  "last_calibrated": "2025-Q1"},
    },
    "douyin": {
        "finance_investing":    {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium", "sample_size": 14, "last_calibrated": "2025-Q1"},
        "technology":           {"low": 20, "mid": 38,  "high": 60,  "confidence": "medium", "sample_size": 16, "last_calibrated": "2025-Q1"},
        "gaming":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium", "sample_size": 12, "last_calibrated": "2025-Q1"},
        "beauty_skincare":      {"low": 25, "mid": 45,  "high": 70,  "confidence": "high",   "sample_size": 48, "last_calibrated": "2025-Q1"},
        "food_cooking":         {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium", "sample_size": 15, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "medium", "sample_size": 13, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 20, "mid": 35,  "high": 60,  "confidence": "medium", "sample_size": 11, "last_calibrated": "2025-Q1"},
        "health_fitness":       {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium", "sample_size": 18, "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 20, "mid": 40,  "high": 65,  "confidence": "high",   "sample_size": 40, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium", "sample_size": 15, "last_calibrated": "2025-Q1"},
        "digital_3c":           {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium", "sample_size": 17, "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 15, "mid": 28,  "high": 45,  "confidence": "medium", "sample_size": 10, "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 18, "mid": 32,  "high": 50,  "confidence": "medium", "sample_size": 14, "last_calibrated": "2025-Q1"},
        "travel":               {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium", "sample_size": 12, "last_calibrated": "2025-Q1"},
        "music_dance":          {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low",    "sample_size": 6,  "last_calibrated": "2025-Q1"},
        "entertainment_funny":  {"low": 3,  "mid": 8,   "high": 15,  "confidence": "medium", "sample_size": 20, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",    "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "livestream_ecommerce": {"low": 5,  "mid": 12,  "high": 25,  "confidence": "low",    "sample_size": 8,  "last_calibrated": "2025-Q1"},
    },
    "kuaishou": {
        "finance_investing":    {"low": 15, "mid": 30,  "high": 55,  "confidence": "low",    "sample_size": 4,  "last_calibrated": "2025-Q1"},
        "technology":           {"low": 10, "mid": 22,  "high": 40,  "confidence": "low",    "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "gaming":               {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium", "sample_size": 11, "last_calibrated": "2025-Q1"},
        "beauty_skincare":      {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium", "sample_size": 18, "last_calibrated": "2025-Q1"},
        "food_cooking":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium", "sample_size": 15, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 6,  "mid": 14,  "high": 25,  "confidence": "medium", "sample_size": 13, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 12, "mid": 22,  "high": 40,  "confidence": "low",    "sample_size": 3,  "last_calibrated": "2025-Q1"},
        "health_fitness":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "low",    "sample_size": 6,  "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "medium", "sample_size": 14, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 18, "mid": 35,  "high": 60,  "confidence": "low",    "sample_size": 7,  "last_calibrated": "2025-Q1"},
        "digital_3c":           {"low": 10, "mid": 22,  "high": 38,  "confidence": "low",    "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium", "sample_size": 12, "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 12, "mid": 22,  "high": 38,  "confidence": "medium", "sample_size": 16, "last_calibrated": "2025-Q1"},
        "travel":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",    "sample_size": 4,  "last_calibrated": "2025-Q1"},
        "agriculture_rural":    {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium", "sample_size": 19, "last_calibrated": "2025-Q1"},
        "entertainment_funny":  {"low": 3,  "mid": 6,   "high": 12,  "confidence": "medium", "sample_size": 17, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low",    "sample_size": 6,  "last_calibrated": "2025-Q1"},
        "livestream_ecommerce": {"low": 3,  "mid": 8,   "high": 18,  "confidence": "medium", "sample_size": 20, "last_calibrated": "2025-Q1"},
    },
}

DEFAULT_CPM_CN = {"low": 8, "mid": 18, "high": 30, "confidence": "low"}

# ---------------------------------------------------------------------------
# 2. Niche Display Names (CN)
# ---------------------------------------------------------------------------

NICHE_DISPLAY_NAMES_CN: dict[str, str] = {
    "finance_investing": "财经投资",
    "technology": "科技评测",
    "gaming": "游戏",
    "anime_acg": "二次元/ACG",
    "beauty_skincare": "美妆护肤",
    "food_cooking": "美食烹饪",
    "lifestyle_vlog": "生活方式",
    "education_knowledge": "知识科普",
    "health_fitness": "健康健身",
    "fashion_ootd": "时尚穿搭",
    "automotive": "汽车",
    "digital_3c": "数码3C",
    "home_decoration": "家居装饰",
    "parenting_family": "亲子家庭",
    "travel": "旅行",
    "music_dance": "音乐舞蹈",
    "entertainment_funny": "娱乐搞笑",
    "pets_animals": "宠物动物",
    "agriculture_rural": "三农",
    "livestream_ecommerce": "直播电商",
}

# ---------------------------------------------------------------------------
# 3. Engagement Rate Benchmarks by Platform × Niche
# ---------------------------------------------------------------------------

NICHE_AVG_ENGAGEMENT_CN: dict[str, dict[str, float]] = {
    "bilibili": {
        "technology": 5.0, "gaming": 6.0, "anime_acg": 7.0,
        "beauty_skincare": 4.5, "food_cooking": 5.5, "lifestyle_vlog": 4.0,
        "education_knowledge": 4.5, "finance_investing": 3.5, "automotive": 3.0,
        "digital_3c": 4.8, "entertainment_funny": 5.5, "music_dance": 6.5,
        "pets_animals": 5.0, "home_decoration": 4.0, "parenting_family": 4.0,
        "travel": 4.0, "fashion_ootd": 4.0, "health_fitness": 4.0,
    },
    "douyin": {
        "technology": 3.0, "gaming": 4.0, "beauty_skincare": 4.5,
        "food_cooking": 4.0, "lifestyle_vlog": 3.5, "education_knowledge": 3.0,
        "finance_investing": 2.5, "automotive": 2.0, "digital_3c": 3.0,
        "entertainment_funny": 5.0, "music_dance": 5.5, "pets_animals": 4.5,
        "home_decoration": 3.5, "parenting_family": 4.0, "travel": 3.5,
        "fashion_ootd": 4.0, "health_fitness": 3.5,
    },
    "kuaishou": {
        "technology": 3.5, "gaming": 4.5, "beauty_skincare": 4.0,
        "food_cooking": 5.0, "lifestyle_vlog": 4.5, "education_knowledge": 3.0,
        "finance_investing": 2.5, "automotive": 2.5, "digital_3c": 3.5,
        "entertainment_funny": 5.5, "music_dance": 5.0, "pets_animals": 5.0,
        "home_decoration": 4.0, "parenting_family": 5.0, "agriculture_rural": 6.0,
        "travel": 3.5, "fashion_ootd": 3.5, "health_fitness": 3.5,
    },
}

# ---------------------------------------------------------------------------
# 4. Tier Classification (CN)
# ---------------------------------------------------------------------------

TIER_TABLE_CN: dict[str, dict[str, dict[str, int | None | str]]] = {
    "bilibili": {
        "素人/KOC":     {"min": 1000,    "max": 10000,   "typical_range": "¥200-¥2,000"},
        "小UP主":       {"min": 10000,   "max": 100000,  "typical_range": "¥1,000-¥15,000"},
        "中腰部UP主":   {"min": 100000,  "max": 500000,  "typical_range": "¥5,000-¥80,000"},
        "头部UP主":     {"min": 500000,  "max": 2000000, "typical_range": "¥30,000-¥200,000"},
        "超头部UP主":   {"min": 2000000, "max": None,    "typical_range": "¥100,000-¥500,000+"},
    },
    "douyin": {
        "素人/KOC":     {"min": 1000,    "max": 10000,    "typical_range": "¥100-¥800"},
        "小达人":       {"min": 10000,   "max": 100000,   "typical_range": "¥500-¥8,000"},
        "中腰部达人":   {"min": 100000,  "max": 1000000,  "typical_range": "¥3,000-¥50,000"},
        "头部达人":     {"min": 1000000, "max": 5000000,  "typical_range": "¥20,000-¥150,000"},
        "超头部达人":   {"min": 5000000, "max": None,     "typical_range": "¥80,000-¥500,000+"},
    },
    "kuaishou": {
        "素人/KOC":     {"min": 1000,    "max": 10000,    "typical_range": "¥80-¥500"},
        "小主播":       {"min": 10000,   "max": 100000,   "typical_range": "¥300-¥5,000"},
        "中腰部主播":   {"min": 100000,  "max": 1000000,  "typical_range": "¥2,000-¥30,000"},
        "头部主播":     {"min": 1000000, "max": 5000000,  "typical_range": "¥15,000-¥100,000"},
        "超头部主播":   {"min": 5000000, "max": None,     "typical_range": "¥50,000-¥300,000+"},
    },
}


def classify_tier_cn(platform: str, followers: int) -> str:
    """Return tier name based on follower count for CN platforms."""
    tiers = TIER_TABLE_CN.get(platform, TIER_TABLE_CN["bilibili"])
    for tier_name, bounds in tiers.items():
        max_val = bounds["max"]
        if bounds["min"] <= followers and (max_val is None or followers <= max_val):
            return tier_name
    return list(tiers.keys())[0] if followers < 1000 else list(tiers.keys())[-1]


# ---------------------------------------------------------------------------
# 5. Deliverable Type Multipliers (CN)
# ---------------------------------------------------------------------------

DELIVERABLE_MULTIPLIERS_CN: dict[str, dict[str, float]] = {
    "bilibili": {
        "dedicated_video": 1.0,
        "bilibili_custom_video": 1.0,
        "integrated_mention": 0.5,
        "pre_roll_mention": 0.3,
        "end_card_mention": 0.15,
        "bilibili_dynamic": 0.1,
        "dynamic_post": 0.1,
        "column_article": 0.2,
        "bilibili_image_text": 0.2,
        "livestream_collab": 0.6,
        "livestream_slot": 0.6,
        "livestream_clip": 0.3,
        "pinned_comment": 0.03,
        "bilibili_story": 0.15,
        "charging_video": 0.7,
    },
    "douyin": {
        "dedicated_video": 1.0,
        "douyin_video": 1.0,
        "integrated_mention": 0.5,
        "series_3_posts": 2.5,
        "series_5_posts": 4.0,
        "livestream_mention": 0.4,
        "livestream_slot": 0.0,
        "livestream_clip": 0.3,
        "challenge_collab": 1.5,
        "duet_video": 0.35,
        "douyin_image": 0.2,
        "product_showcase": 0.2,
        "search_seo_video": 0.8,
    },
    "kuaishou": {
        "dedicated_video": 1.0,
        "kuaishou_video": 1.0,
        "integrated_mention": 0.5,
        "series_3_posts": 2.3,
        "livestream_mention": 0.4,
        "livestream_slot": 0.0,
        "livestream_clip": 0.3,
        "quickshop_link": 0.15,
        "private_domain_push": 0.6,
    },
}

# ---------------------------------------------------------------------------
# 6. Usage Rights & Exclusivity Premiums (CN)
# ---------------------------------------------------------------------------

USAGE_RIGHTS_PREMIUMS_CN: dict[str, float] = {
    "organic_only": 0.0,
    "brand_repost_30d": 0.10,
    "brand_repost_social_30d": 0.10,
    "brand_repost_perpetual": 0.30,
    "brand_ecommerce_page": 0.20,
    "ecommerce_detail": 0.20,
    "brand_douyin_ad_boost": 0.25,
    "feed_ads_30d": 0.35,
    "brand_ad_boost_30d": 0.35,
    "feed_ads_90d": 0.60,
    "brand_ad_boost_90d": 0.60,
    "brand_ad_boost_perpetual": 0.90,
    "offline_use": 0.40,
    "tv_broadcast": 1.5,
    "cross_platform_repost": 0.15,
    "secondary_creation_auth": 0.20,
    "livestream_loop": 0.25,
    "perpetual_all_media": 2.5,
}

EXCLUSIVITY_PREMIUMS_CN: dict[str, float] = {
    "none": 0.0,
    "category_30d": 0.20,
    "category_90d": 0.40,
    "category_6m": 0.65,
    "category_12m": 0.90,
    "full_exclusivity_30d": 0.40,
    "full_exclusivity_90d": 0.80,
    "competitor_brand_30d": 0.25,
    "competitor_brand_90d": 0.50,
    "platform_exclusivity": 0.30,
}

# ---------------------------------------------------------------------------
# 7. Known Brand Patterns (CN)
# ---------------------------------------------------------------------------

KNOWN_BRAND_PATTERNS_CN: dict[str, dict] = {
    "得物_dewu": {
        "category": "fashion_ecommerce", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [30, 60],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["产品开箱", "真实使用体验", "挂链接"],
        "payment_reliability": "良好",
    },
    "拼多多_pinduoduo": {
        "category": "ecommerce", "budget_tier": "very_high",
        "negotiation_flexibility": "low", "typical_cpm_cny": [8, 20],
        "platforms": ["douyin", "kuaishou", "bilibili"],
        "requirements": ["低价好物推荐", "APP下载引导"],
        "known_issues": ["报价通常偏低但量大", "适合走量合作"],
        "payment_reliability": "优秀",
    },
    "饿了么_eleme": {
        "category": "food_delivery", "budget_tier": "medium_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [12, 30],
        "platforms": ["douyin", "bilibili"],
        "requirements": ["到店/到家场景", "优惠活动推广"],
        "payment_reliability": "优秀",
    },
    "完美日记_perfect_diary": {
        "category": "beauty_skincare", "budget_tier": "medium_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [25, 50],
        "platforms": ["douyin", "bilibili", "kuaishou"],
        "requirements": ["试色/测评", "前后对比", "购买链接"],
        "known_issues": ["内容审核较严格", "可能要求多轮修改"],
        "payment_reliability": "良好",
    },
    "花西子_florasis": {
        "category": "beauty_skincare", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [30, 55],
        "platforms": ["douyin", "bilibili"],
        "requirements": ["国风调性", "产品细节展示"],
        "payment_reliability": "良好",
    },
    "珀莱雅_proya": {
        "category": "beauty_skincare", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [25, 50],
        "platforms": ["douyin", "bilibili", "kuaishou"],
        "requirements": ["功效展示", "适合成分党内容"],
        "payment_reliability": "优秀",
    },
    "瑞幸咖啡_luckin": {
        "category": "food_beverage", "budget_tier": "high",
        "negotiation_flexibility": "low", "typical_cpm_cny": [15, 35],
        "platforms": ["douyin", "bilibili"],
        "requirements": ["到店体验", "新品推荐", "优惠码"],
        "payment_reliability": "优秀",
    },
    "元气森林_genki_forest": {
        "category": "food_beverage", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [15, 35],
        "platforms": ["douyin", "bilibili", "kuaishou"],
        "requirements": ["生活场景植入", "健康概念"],
        "payment_reliability": "优秀",
    },
    "三只松鼠_three_squirrels": {
        "category": "food_snacks", "budget_tier": "medium",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [10, 25],
        "platforms": ["douyin", "kuaishou", "bilibili"],
        "requirements": ["开箱试吃", "节日礼盒推荐"],
        "payment_reliability": "良好",
    },
    "蔚来_nio": {
        "category": "automotive", "budget_tier": "very_high",
        "negotiation_flexibility": "high", "typical_cpm_cny": [50, 100],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["试驾体验", "技术讲解", "不允许竞品对比"],
        "payment_reliability": "优秀",
    },
    "比亚迪_byd": {
        "category": "automotive", "budget_tier": "very_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [40, 80],
        "platforms": ["bilibili", "douyin", "kuaishou"],
        "requirements": ["产品体验", "技术亮点"],
        "payment_reliability": "优秀",
    },
    "理想_lixiang": {
        "category": "automotive", "budget_tier": "very_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [45, 90],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["家庭用车场景", "智能座舱体验"],
        "payment_reliability": "优秀",
    },
    "米哈游_mihoyo": {
        "category": "gaming", "budget_tier": "very_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [25, 55],
        "platforms": ["bilibili"],
        "requirements": ["游戏实况", "角色/活动展示", "严格内容审核"],
        "known_issues": ["审核非常严格", "不允许任何负面评价"],
        "payment_reliability": "优秀",
    },
    "网易游戏_netease": {
        "category": "gaming", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [20, 45],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["游戏体验", "玩法介绍"],
        "payment_reliability": "优秀",
    },
    "学而思_xueersi": {
        "category": "education", "budget_tier": "medium",
        "negotiation_flexibility": "low", "typical_cpm_cny": [20, 40],
        "platforms": ["bilibili", "douyin"],
        "known_issues": ["教育行业政策风险", "双减后策略变化大"],
        "payment_reliability": "良好",
    },
    "wps_office": {
        "category": "productivity_tool", "budget_tier": "medium",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [18, 35],
        "platforms": ["bilibili"],
        "requirements": ["功能演示", "使用场景"],
        "payment_reliability": "优秀",
    },
    "夸克_quark": {
        "category": "productivity_tool", "budget_tier": "medium_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [15, 30],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["AI功能展示", "学习/办公场景"],
        "payment_reliability": "优秀",
    },
    "小米_xiaomi": {
        "category": "digital_3c", "budget_tier": "high",
        "negotiation_flexibility": "low", "typical_cpm_cny": [25, 50],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["产品评测", "性价比对比"],
        "known_issues": ["可能限制负面评价", "新品发布期预算集中"],
        "payment_reliability": "优秀",
    },
    "OPPO/vivo": {
        "category": "digital_3c", "budget_tier": "very_high",
        "negotiation_flexibility": "low", "typical_cpm_cny": [20, 45],
        "platforms": ["douyin", "bilibili", "kuaishou"],
        "requirements": ["产品体验", "拍照效果展示"],
        "known_issues": ["报价通常是固定package"],
        "payment_reliability": "优秀",
    },
    "追觅_dreame": {
        "category": "digital_3c", "budget_tier": "medium_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [20, 40],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["产品实测", "清洁效果对比"],
        "payment_reliability": "良好",
    },
}

# ---------------------------------------------------------------------------
# 8. Contract Red Flags (CN) — 15+ rules
# ---------------------------------------------------------------------------

CONTRACT_RED_FLAGS_CN: dict[str, dict[str, str]] = {
    "perpetual_rights_no_premium": {
        "condition": "永久使用权但未加价",
        "severity": "high",
        "advice": "强烈建议拒绝或加价200-300%",
    },
    "ad_boost_rights_hidden": {
        "condition": "品牌要求拿内容投信息流广告（Dou+/巨量引擎）但合同未明确",
        "severity": "high",
        "advice": "必须单独约定并加价",
    },
    "unlimited_revisions": {
        "condition": "无限修改轮次",
        "severity": "medium",
        "advice": "限制为2轮，第3轮起按原价20%收费",
    },
    "full_exclusivity_no_premium": {
        "condition": "全品类排他但未额外补偿",
        "severity": "high",
        "advice": "至少加价50-100%",
    },
    "payment_after_publish": {
        "condition": "发布后才付款",
        "severity": "medium",
        "advice": "要求50%预付，发布后7天内付尾款",
    },
    "payment_net_60_plus": {
        "condition": "付款周期超过60天",
        "severity": "medium",
        "advice": "缩短至30天或加收账期费用",
    },
    "vague_deliverables": {
        "condition": "交付物描述模糊（如'若干条视频'）",
        "severity": "medium",
        "advice": "必须明确数量、时长、格式",
    },
    "content_ownership_transfer": {
        "condition": "要求转让内容所有权",
        "severity": "high",
        "advice": "改为授权使用，保留所有权",
    },
    "no_kill_fee": {
        "condition": "无终止费条款",
        "severity": "medium",
        "advice": "加入终止费（合同金额的25-50%）",
    },
    "livestream_no_refund_clause": {
        "condition": "直播带货合同无退货成本分担条款",
        "severity": "medium",
        "advice": "明确退货成本由谁承担",
    },
    "forced_positive_review": {
        "condition": "合同要求必须给好评/不能提缺点",
        "severity": "medium",
        "advice": "违反广告法真实性要求，建议拒绝",
    },
    "no_ad_disclosure": {
        "condition": "合同未要求标注广告",
        "severity": "medium",
        "advice": "广告法规定必须标注'广告'或'推广'",
    },
    "cross_platform_hidden": {
        "condition": "合同包含跨平台发布但未额外计价",
        "severity": "medium",
        "advice": "每个平台应单独计价",
    },
    "portrait_rights_perpetual": {
        "condition": "品牌要求永久使用达人肖像/形象",
        "severity": "high",
        "advice": "肖像权授权必须有明确期限和范围，永久授权至少加价100%",
    },
    "data_sharing_forced": {
        "condition": "要求达人提供后台数据截图/账号密码",
        "severity": "high",
        "advice": "绝不提供账号密码，数据截图需脱敏",
    },
    "ai_training_rights_hidden": {
        "condition": "品牌方将达人内容用于AI模型训练但合同未明确",
        "severity": "medium",
        "advice": "合同中必须明确是否授权AI训练用途，如授权需单独加价",
    },
    "content_modification_no_approval": {
        "condition": "品牌可修改达人内容且不需要达人审核",
        "severity": "high",
        "advice": "任何内容修改必须经过达人书面确认",
    },
    "backdated_exclusivity": {
        "condition": "排他条款追溯到合同签署之前",
        "severity": "high",
        "advice": "排他期限只能从合同签署日起算，拒绝任何追溯条款",
    },
    "gmv_guarantee_on_creator": {
        "condition": "合同要求达人对GMV负责（未达标需退款）",
        "severity": "high",
        "advice": "达人不应对销售结果负责，坑位费与佣金应独立计算",
    },
    "derivative_works_unlimited": {
        "condition": "允许品牌对内容进行无限二次创作",
        "severity": "medium",
        "advice": "二次创作授权需限定范围和期限，建议加价20-40%",
    },
    "penalty_clause_one_sided": {
        "condition": "只有达人的违约金条款，品牌方无对等约束",
        "severity": "medium",
        "advice": "违约金条款必须对等，品牌方违约也需承担同等责任",
    },
    "no_minimum_guarantee_livestream": {
        "condition": "直播带货合同无最低保底条款",
        "severity": "medium",
        "advice": "直播合作应有坑位费保底，纯佣金模式需谨慎评估",
    },
}

# ---------------------------------------------------------------------------
# 9. Seasonal Modifiers (CN)
# ---------------------------------------------------------------------------

SEASONAL_MATRIX_CN: dict[str, dict] = {
    "category_groups": {
        "ecommerce_all":     ["beauty_skincare", "fashion_ootd", "home_decoration", "digital_3c", "food_cooking"],
        "education":         ["education_knowledge"],
        "gaming_acg":        ["gaming", "anime_acg"],
        "travel_outdoor":    ["travel", "health_fitness"],
        "auto_finance":      ["automotive", "finance_investing"],
        "entertainment":     ["entertainment_funny", "music_dance", "pets_animals", "lifestyle_vlog"],
        "parenting":         ["parenting_family"],
        "agriculture":       ["agriculture_rural"],
    },
    "monthly_multipliers": {
        #                  Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
        "ecommerce_all":  [0.90, 0.85, 0.90, 0.95, 1.10, 1.30, 0.90, 0.90, 0.95, 1.20, 1.50, 1.20],
        "education":      [1.00, 1.10, 1.00, 0.95, 1.00, 1.10, 1.10, 1.15, 1.20, 1.05, 1.10, 1.00],
        "gaming_acg":     [1.05, 1.10, 1.00, 1.00, 1.00, 1.05, 1.15, 1.15, 1.00, 1.10, 1.15, 1.10],
        "travel_outdoor": [0.85, 0.90, 0.95, 1.10, 1.15, 1.05, 1.15, 1.10, 1.20, 1.30, 0.95, 0.90],
        "auto_finance":   [1.10, 0.90, 1.00, 1.10, 1.05, 1.00, 0.95, 0.95, 1.10, 1.15, 1.20, 1.10],
        "entertainment":  [1.05, 1.10, 0.95, 0.95, 1.00, 1.00, 1.05, 1.05, 0.95, 1.05, 1.10, 1.05],
        "parenting":      [1.00, 1.05, 1.00, 1.00, 1.05, 1.15, 1.00, 1.10, 1.15, 1.05, 1.15, 1.10],
        "agriculture":    [1.20, 1.10, 0.90, 0.95, 1.00, 1.00, 1.00, 0.95, 1.05, 1.10, 1.20, 1.15],
    },
    "key_events": {
        1:  "元旦/年货节",
        2:  "春节",
        3:  "38女神节",
        5:  "618预热期",
        6:  "618大促",
        7:  "暑期",
        8:  "开学季",
        9:  "中秋/国庆预热",
        10: "双11预热期",
        11: "双11大促",
        12: "双12/年货节",
    },
}


def calculate_seasonal_modifier_cn(current_date: datetime, niche: str) -> float:
    """Calculate seasonal modifier for CN edition."""
    month = current_date.month
    for group_name, niches in SEASONAL_MATRIX_CN["category_groups"].items():
        if niche in niches:
            return SEASONAL_MATRIX_CN["monthly_multipliers"][group_name][month - 1]
    return 1.0


# ---------------------------------------------------------------------------
# 10. VF Ratio (粉丝播放比) Benchmarks
# ---------------------------------------------------------------------------

VF_RATIO_BENCHMARKS: dict[str, dict[str, float]] = {
    "bilibili":  {"excellent": 0.5, "good": 0.25, "poor": 0.1},
    "douyin":    {"excellent": 0.3, "good": 0.15, "poor": 0.05},
    "kuaishou":  {"excellent": 0.35, "good": 0.2, "poor": 0.08},
}


def calculate_vf_ratio_modifier(avg_views: int, followers: int, platform: str) -> tuple[float, float]:
    """Calculate VF ratio and its modifier.

    Returns (vf_ratio, vf_modifier) where vf_modifier is centered at 1.0.
    """
    if followers <= 0:
        return 0.0, 1.0
    vf_ratio = avg_views / followers
    bench = VF_RATIO_BENCHMARKS.get(platform, VF_RATIO_BENCHMARKS["bilibili"])

    if vf_ratio >= bench["excellent"]:
        vf_modifier = 1.2
    elif vf_ratio >= bench["good"]:
        vf_modifier = 1.0 + 0.2 * (vf_ratio - bench["good"]) / (bench["excellent"] - bench["good"])
    elif vf_ratio >= bench["poor"]:
        vf_modifier = 0.7 + 0.3 * (vf_ratio - bench["poor"]) / (bench["good"] - bench["poor"])
    else:
        vf_modifier = 0.5

    return round(vf_ratio, 4), round(vf_modifier, 3)


# ---------------------------------------------------------------------------
# 11. Content Longevity Modifiers
# ---------------------------------------------------------------------------

LONGEVITY_MODIFIERS: dict[str, float] = {
    "bilibili":  0.10,   # B站长尾价值 +10%
    "douyin":    0.0,    # 抖音无长尾
    "kuaishou":  0.03,   # 快手有轻微长尾（私域回放）
}

# ---------------------------------------------------------------------------
# 12. Livestream Commerce Pricing
# ---------------------------------------------------------------------------

LIVESTREAM_PIT_FEE_TABLE: dict[str, dict[str, tuple[int, int, int]]] = {
    "小达人(1-10万粉)": {
        "beauty_skincare":      (800,   2000,  5000),
        "food":                 (500,   1500,  3000),
        "fashion":              (600,   1800,  4000),
        "digital_3c":           (1000,  2500,  5000),
        "home_goods":           (500,   1200,  3000),
        "health_supplements":   (800,   2000,  5000),
        "general":              (500,   1500,  3000),
    },
    "中腰部(10-100万粉)": {
        "beauty_skincare":      (5000,  15000, 30000),
        "food":                 (3000,  8000,  20000),
        "fashion":              (5000,  12000, 25000),
        "digital_3c":           (5000,  15000, 30000),
        "home_goods":           (3000,  8000,  18000),
        "health_supplements":   (5000,  15000, 35000),
        "general":              (3000,  10000, 25000),
    },
    "头部(100-500万粉)": {
        "beauty_skincare":      (30000, 80000,  150000),
        "food":                 (20000, 50000,  100000),
        "fashion":              (25000, 60000,  120000),
        "digital_3c":           (30000, 80000,  150000),
        "home_goods":           (15000, 40000,  80000),
        "health_supplements":   (30000, 80000,  180000),
        "general":              (20000, 60000,  120000),
    },
    "超头部(500万粉+)": {
        "beauty_skincare":      (150000, 300000, 500000),
        "food":                 (80000,  200000, 400000),
        "fashion":              (120000, 250000, 450000),
        "digital_3c":           (150000, 300000, 500000),
        "home_goods":           (80000,  150000, 300000),
        "health_supplements":   (200000, 400000, 800000),
        "general":              (100000, 250000, 500000),
    },
}

LIVESTREAM_TYPES: dict[str, dict[str, str | float]] = {
    "exclusive_session": {
        "name": "专场直播",
        "pit_fee_multiplier": 3.0,
        "typical_duration": "2-4小时",
    },
    "mixed_session": {
        "name": "混场直播",
        "pit_fee_multiplier": 1.0,
        "typical_duration": "4-8小时",
    },
    "short_mention": {
        "name": "直播口播",
        "pit_fee_multiplier": 0.3,
        "typical_duration": "3-5分钟",
    },
}

COMMISSION_RATE_TABLE: dict[str, dict[str, str]] = {
    "beauty_skincare":    {"rate": "20%-40%", "note": "客单价<100效果最佳"},
    "food":               {"rate": "15%-30%", "note": "复购率高是优势"},
    "fashion":            {"rate": "20%-35%", "note": "退货率高（30-50%），实际佣金需打折"},
    "digital_3c":         {"rate": "5%-15%",  "note": "客单价高但转化率低"},
    "home_goods":         {"rate": "15%-25%", "note": "家居决策周期长，效果延迟"},
    "health_supplements": {"rate": "25%-50%", "note": "高利润品类，佣金空间大"},
}

# ---------------------------------------------------------------------------
# 13. Platform Official System Fees
# ---------------------------------------------------------------------------

OFFICIAL_PLATFORM_INFO: dict[str, dict] = {
    "bilibili_huahuo": {
        "name": "B站花火平台",
        "platform_fee_rate": 0.07,
        "min_followers": 10000,
    },
    "douyin_xingtu": {
        "name": "抖音星图平台",
        "platform_fee_rate": 0.10,
        "min_followers": 10000,
    },
    "kuaishou_cili": {
        "name": "快手磁力聚星",
        "platform_fee_rate": 0.07,
        "min_followers": 5000,
    },
}

PLATFORM_FEE_MAP: dict[str, str] = {
    "bilibili": "bilibili_huahuo",
    "douyin": "douyin_xingtu",
    "kuaishou": "kuaishou_cili",
}


def calculate_platform_adjusted_price(
    base_price: float,
    platform: str,
    through_official: bool = False,
) -> dict:
    """Calculate price adjusted for platform official system fees."""
    if through_official:
        key = PLATFORM_FEE_MAP.get(platform)
        info = OFFICIAL_PLATFORM_INFO.get(key, {}) if key else {}
        fee_rate = info.get("platform_fee_rate", 0.10)
        brand_pays = base_price / (1 - fee_rate)
        return {
            "brand_total": round(brand_pays),
            "creator_receives": round(base_price),
            "platform_fee": round(brand_pays - base_price),
            "fee_rate": f"{fee_rate * 100:.0f}%",
        }
    return {
        "brand_total": round(base_price),
        "creator_receives": round(base_price),
        "platform_fee": 0,
        "note": "私下合作无平台抽成，但需自行处理税务和合同",
    }


# ---------------------------------------------------------------------------
# 14. Tax Estimation (CN)
# ---------------------------------------------------------------------------

TAX_BRACKETS_CN: dict[str, dict] = {
    "劳务报酬（个人直接收款）": {
        "description": "最常见的达人收入方式",
        "brackets": [
            (800,    0.0,   0),
            (4000,   0.20,  800),     # deduct 800 then 20%
            (20000,  0.20,  None),    # deduct 20% then 20%
            (50000,  0.30,  2000),    # 30% minus 2000
            (float("inf"), 0.40, 7000),
        ],
    },
    "个体工商户/工作室": {
        "description": "年收入>¥30万建议注册",
        "effective_rate_range": "3%-5%（核定征收）",
    },
    "公司/MCN": {
        "description": "头部达人或团队化运营",
        "effective_rate": "综合约40%（企业所得税25% + 分红个税20%）",
    },
}


def estimate_tax_cn(gross_income: float) -> dict:
    """Estimate tax under 劳务报酬 for a single payment."""
    if gross_income <= 800:
        tax = 0.0
    elif gross_income <= 4000:
        tax = (gross_income - 800) * 0.20
    elif gross_income <= 20000:
        tax = gross_income * 0.80 * 0.20
    elif gross_income <= 50000:
        tax = gross_income * 0.80 * 0.30 - 2000
    else:
        tax = gross_income * 0.80 * 0.40 - 7000

    net = gross_income - tax
    effective_rate = (tax / gross_income * 100) if gross_income > 0 else 0

    return {
        "gross_income": round(gross_income),
        "tax": round(tax),
        "net_income": round(net),
        "effective_rate": f"{effective_rate:.1f}%",
        "tax_type": "劳务报酬所得",
    }


# ---------------------------------------------------------------------------
# 15. MCN Fee Reference
# ---------------------------------------------------------------------------

MCN_FEE_REFERENCE: dict[str, str] = {
    "新人达人（<10万粉）": "MCN 50-70% : 达人 30-50%",
    "成长期达人（10-50万粉）": "MCN 40-60% : 达人 40-60%",
    "头部达人（50万粉+）": "MCN 20-40% : 达人 60-80%",
    "超头部/自有团队": "MCN 10-20% : 达人 80-90%",
}

# ---------------------------------------------------------------------------
# 16. Ad Law Compliance Checks
# ---------------------------------------------------------------------------

AD_LAW_COMPLIANCE_CHECKS: dict[str, dict] = {
    "disclosure_requirement": {
        "rule": "商业推广内容必须标注'广告'或'推广'",
        "severity": "high",
    },
    "prohibited_claims": {
        "rule": "不得使用'最佳''第一''国家级'等绝对化用语",
        "severity": "medium",
    },
    "medical_health": {
        "rule": "医疗、药品、保健品广告需特殊资质",
        "severity": "high",
        "niches": ["health_fitness"],
    },
    "finance_regulation": {
        "rule": "金融产品推广需持牌机构",
        "severity": "high",
        "niches": ["finance_investing"],
    },
    "education_policy": {
        "rule": "K12阶段学科培训不得投放（双减政策）",
        "severity": "high",
        "niches": ["education_knowledge"],
    },
}

# ---------------------------------------------------------------------------
# Calculation Functions
# ---------------------------------------------------------------------------


def get_niche_cpm_cn(platform: str, niche: str) -> dict:
    """Get CPM values for a platform+niche combo (CN)."""
    platform_cpms = NICHE_CPM_TABLE_CN.get(platform, NICHE_CPM_TABLE_CN.get("bilibili", {}))
    cpm = platform_cpms.get(niche, DEFAULT_CPM_CN)
    return {"low": cpm["low"], "mid": cpm["mid"], "high": cpm["high"]}


def get_cpm_confidence_cn(platform: str, niche: str) -> str:
    """Get confidence level for a CPM data point."""
    platform_cpms = NICHE_CPM_TABLE_CN.get(platform, {})
    cpm = platform_cpms.get(niche, DEFAULT_CPM_CN)
    return cpm.get("confidence", "low")


def calculate_base_price_cn(
    platform: str,
    niche: str,
    avg_views: int,
) -> dict[str, float]:
    """Calculate base price range from CPM and average views (CN, CNY)."""
    cpm = get_niche_cpm_cn(platform, niche)
    return {
        "low": cpm["low"] * avg_views / 1000,
        "mid": cpm["mid"] * avg_views / 1000,
        "high": cpm["high"] * avg_views / 1000,
    }


def validate_input_data_cn(
    platform: str,
    followers: int,
    avg_views: int | None = None,
    engagement_rate: float | None = None,
    niche: str | None = None,
) -> dict:
    """Pre-validate input data before running agents. Returns quality report."""
    warnings: list[str] = []
    anomalies: list[str] = []

    if followers < 500:
        warnings.append("粉丝数低于500，商业报价意义有限")

    if avg_views and followers > 0:
        vf = avg_views / followers
        if vf > 5.0:
            anomalies.append(f"粉丝播放比异常高({vf:.1f})，可能是病毒视频拉高均值")
        if vf < 0.01:
            anomalies.append(f"粉丝播放比极低({vf:.3f})，疑似大量僵尸粉")

    if engagement_rate is not None:
        if engagement_rate > 30:
            anomalies.append(f"互动率 {engagement_rate}% 异常高，可能是计算口径问题或刷量")
        if 0 < engagement_rate < 0.1:
            anomalies.append(f"互动率 {engagement_rate}% 极低，数据可能有误")

    if platform == "kuaishou" and niche == "anime_acg":
        warnings.append("快手ACG/二次元类达人极少，CPM数据置信度很低")

    # Determine degradation level
    if anomalies and len(anomalies) >= 2:
        degradation = "partial"
    elif followers < 100:
        degradation = "minimal"
    else:
        degradation = "full"

    return {
        "warnings": warnings,
        "anomalies": anomalies,
        "degradation_level": degradation,
    }


def calculate_all_modifiers_cn(
    engagement_rate: float,
    platform: str,
    niche: str,
    avg_views: int,
    followers: int,
    monthly_growth_rate: float | None = None,
    audience_city_distribution: dict | None = None,
    coin_rate: float = 0,
    favorite_rate: float = 0,
    completion_rate: float = 0,
    share_rate: float = 0,
    revisit_rate: float = 0,
    live_viewer_follower_ratio: float = 0,
    current_date: datetime | None = None,
) -> tuple[float, dict[str, dict]]:
    """
    Additive modifier system for CN edition.

    total_modifier = 1.0 + sum(deltas), capped to [0.4, 2.0]

    Returns (total_modifier, modifier_details).
    """
    if current_date is None:
        current_date = datetime.now()

    modifier_details: dict[str, dict] = {}

    # 1. Engagement modifier (with orthogonalization against VF ratio)
    niche_avg = NICHE_AVG_ENGAGEMENT_CN.get(platform, {}).get(niche, 4.0)
    # Orthogonalization: adjust engagement baseline based on VF ratio
    # so that high-VF-ratio creators don't get double-rewarded
    vf_ratio_raw = avg_views / followers if followers > 0 else 0
    vf_bench = VF_RATIO_BENCHMARKS.get(platform, {}).get("good", 0.2)
    vf_deviation = (vf_ratio_raw - vf_bench) / max(vf_bench, 0.01) if vf_bench > 0 else 0
    adjusted_niche_avg = niche_avg * (1 + vf_deviation * 0.3)
    adjusted_niche_avg = max(niche_avg * 0.6, min(niche_avg * 1.5, adjusted_niche_avg))
    ratio = engagement_rate / adjusted_niche_avg if adjusted_niche_avg > 0 else 1.0

    if ratio < 0.5:
        eng_delta = -0.3
        eng_reason = f"互动率 {engagement_rate}% 远低于{niche}平均 {niche_avg}%"
    elif ratio < 1.0:
        eng_delta = -0.15 + 0.15 * (ratio - 0.5) / 0.5
        eng_reason = f"互动率 {engagement_rate}% 低于{niche}平均 {niche_avg}%"
    elif ratio < 2.0:
        eng_delta = 0.0 + 0.25 * (ratio - 1.0) / 1.0
        eng_reason = f"互动率 {engagement_rate}% 高于{niche}平均 {niche_avg}% {(ratio-1)*100:.0f}%"
    else:
        eng_delta = 0.25
        eng_reason = f"互动率 {engagement_rate}% 远高于平均（封顶）"

    modifier_details["engagement"] = {"delta": round(eng_delta, 3), "reason": eng_reason}

    # 2. VF ratio modifier
    vf_ratio, vf_mod = calculate_vf_ratio_modifier(avg_views, followers, platform)
    vf_delta = vf_mod - 1.0
    if vf_ratio >= VF_RATIO_BENCHMARKS.get(platform, {}).get("excellent", 0.5):
        vf_reason = f"粉丝播放比 {vf_ratio:.2f} 优秀"
    elif vf_ratio >= VF_RATIO_BENCHMARKS.get(platform, {}).get("good", 0.25):
        vf_reason = f"粉丝播放比 {vf_ratio:.2f} 正常"
    elif vf_ratio >= VF_RATIO_BENCHMARKS.get(platform, {}).get("poor", 0.1):
        vf_reason = f"粉丝播放比 {vf_ratio:.2f} 偏低"
    else:
        vf_reason = f"粉丝播放比 {vf_ratio:.2f} 危险信号（可能存在僵尸粉）"

    modifier_details["vf_ratio"] = {"delta": round(vf_delta, 3), "reason": vf_reason, "vf_ratio": vf_ratio}

    # 3. City tier modifier
    city_delta = 0.0
    if audience_city_distribution:
        city_value = (
            audience_city_distribution.get("tier_1", 0) * 1.0 +
            audience_city_distribution.get("new_tier_1", 0) * 0.8 +
            audience_city_distribution.get("tier_2", 0) * 0.5 +
            audience_city_distribution.get("tier_3_below", 0) * 0.2
        ) / 100
        city_delta = (city_value - 0.5) * 0.4
        city_reason = f"城市线级加权分 {city_value:.2f}"
    else:
        city_reason = "无城市线级数据，不修正"

    modifier_details["city_tier"] = {"delta": round(city_delta, 3), "reason": city_reason}

    # 4. Growth modifier
    if monthly_growth_rate is not None:
        if monthly_growth_rate > 10:
            growth_delta = 0.15
            growth_reason = f"快速增长（月增长率 {monthly_growth_rate:.1f}%）"
        elif monthly_growth_rate > 3:
            growth_delta = 0.05 + 0.10 * (monthly_growth_rate - 3) / 7
            growth_reason = f"稳定增长（月增长率 {monthly_growth_rate:.1f}%）"
        elif monthly_growth_rate >= 0:
            growth_delta = 0.0
            growth_reason = f"稳定期（月增长率 {monthly_growth_rate:.1f}%）"
        else:
            growth_delta = max(-0.15, monthly_growth_rate * 0.015)
            growth_reason = f"下降期（月增长率 {monthly_growth_rate:.1f}%）"
    else:
        growth_delta = 0.0
        growth_reason = "无增长数据"

    modifier_details["growth"] = {"delta": round(growth_delta, 3), "reason": growth_reason}

    # 5. Platform-specific signal modifier
    platform_signal_delta = 0.0
    platform_reasons = []

    if platform == "bilibili":
        if coin_rate > 0.03:
            platform_signal_delta += 0.08
            platform_reasons.append(f"投币率 {coin_rate:.1%} 优秀")
        elif coin_rate > 0.015:
            platform_signal_delta += 0.04
            platform_reasons.append(f"投币率 {coin_rate:.1%} 良好")
        if favorite_rate > 0.05:
            platform_signal_delta += 0.05
            platform_reasons.append(f"收藏率 {favorite_rate:.1%} 优秀")
        elif favorite_rate > 0.03:
            platform_signal_delta += 0.02
            platform_reasons.append(f"收藏率 {favorite_rate:.1%} 良好")

    elif platform == "douyin":
        if completion_rate > 0.4:
            platform_signal_delta += 0.10
            platform_reasons.append(f"完播率 {completion_rate:.0%} 优秀")
        elif completion_rate > 0.25:
            platform_signal_delta += 0.05
            platform_reasons.append(f"完播率 {completion_rate:.0%} 良好")
        if share_rate > 0.02:
            platform_signal_delta += 0.08
            platform_reasons.append(f"转发率 {share_rate:.1%} 高")

    elif platform == "kuaishou":
        if revisit_rate > 0.3:
            platform_signal_delta += 0.12
            platform_reasons.append(f"回访率 {revisit_rate:.0%} 极高（私域粘性强）")
        elif revisit_rate > 0.15:
            platform_signal_delta += 0.06
            platform_reasons.append(f"回访率 {revisit_rate:.0%} 良好")
        if live_viewer_follower_ratio > 0.05:
            platform_signal_delta += 0.08
            platform_reasons.append(f"直播观看/粉丝比 {live_viewer_follower_ratio:.1%} 高")

    platform_signal_delta = min(platform_signal_delta, 0.15)
    modifier_details["platform_signal"] = {
        "delta": round(platform_signal_delta, 3),
        "reason": "; ".join(platform_reasons) if platform_reasons else "无平台特有信号数据",
    }

    # 6. Content longevity modifier
    longevity_delta = LONGEVITY_MODIFIERS.get(platform, 0.0)
    longevity_reasons = {
        "bilibili": "B站内容长尾价值 +10%",
        "douyin": "抖音无长尾效应",
        "kuaishou": "快手轻微长尾（私域回放）+3%",
    }
    modifier_details["content_longevity"] = {
        "delta": longevity_delta,
        "reason": longevity_reasons.get(platform, ""),
    }

    # 7. Seasonal modifier
    seasonal_mod = calculate_seasonal_modifier_cn(current_date, niche)
    seasonal_delta = seasonal_mod - 1.0
    month = current_date.month
    event = SEASONAL_MATRIX_CN["key_events"].get(month, "")
    seasonal_reason = f"{month}月季节性修正 ({seasonal_mod}x)"
    if event:
        seasonal_reason += f" — {event}"
    modifier_details["seasonal"] = {"delta": round(seasonal_delta, 3), "reason": seasonal_reason}

    # Sum and cap
    total_delta = sum(d["delta"] for d in modifier_details.values())
    total_modifier = 1.0 + total_delta
    total_modifier = max(0.4, min(2.0, total_modifier))

    return round(total_modifier, 3), modifier_details


def calculate_deal_adjusted_price_cn(
    base_range: dict[str, float],
    platform: str,
    deliverable_type: str,
    usage_rights: str = "organic_only",
    exclusivity: str = "none",
) -> tuple[dict[str, float], dict[str, float | str]]:
    """Apply deal condition multipliers (CN edition)."""
    platform_deliverables = DELIVERABLE_MULTIPLIERS_CN.get(platform, DELIVERABLE_MULTIPLIERS_CN.get("bilibili", {}))
    deliverable_mult = platform_deliverables.get(deliverable_type, 1.0)
    usage_premium = USAGE_RIGHTS_PREMIUMS_CN.get(usage_rights, 0.0)
    exclusivity_premium = EXCLUSIVITY_PREMIUMS_CN.get(exclusivity, 0.0)

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


def generate_package_tiers_cn(
    adjusted_price_mid: float,
    platform: str,
) -> dict[str, dict]:
    """Generate CN package tiers (试水/标准/深度)."""
    packages: dict[str, dict] = {
        "trial": {
            "name": "试水合作",
            "price": round(adjusted_price_mid * 0.75),
            "includes": ["1条植入视频"],
            "duration": "一次性",
            "note": "适合品牌方首次合作试水",
        },
        "standard": {
            "name": "标准合作",
            "price": round(adjusted_price_mid * 2.0),
            "includes": ["3条植入视频", "1条动态/Story"],
            "duration": "2个月",
            "savings_vs_individual": "25%",
        },
        "deep": {
            "name": "深度合作",
            "price": round(adjusted_price_mid * 3.8),
            "includes": ["6条植入视频", "2条动态/Story", "品牌社交媒体转发权30天"],
            "duration": "6个月",
            "savings_vs_individual": "30%",
        },
    }

    if platform in ("douyin", "kuaishou"):
        packages["deep_with_livestream"] = {
            "name": "深度合作+直播带货",
            "price": round(adjusted_price_mid * 5.0),
            "includes": [
                "6条植入视频",
                "2场直播带货（含坑位）",
                "品牌广告素材使用权30天",
            ],
            "duration": "6个月",
            "savings_vs_individual": "35%",
            "note": "直播带货部分另附佣金协议",
        }

    return packages


def lookup_brand_cn(brand_name: str) -> dict | None:
    """Look up known CN brand info.

    Tries the JSON brand DB (``data/brand_db_cn.json``) first, then falls
    back to the hardcoded ``KNOWN_BRAND_PATTERNS_CN`` dictionary.
    """
    if not brand_name:
        return None

    name_lower = brand_name.lower().strip()

    # --- Try JSON brand DB first ---
    try:
        from pathlib import Path
        import json as _json

        db_path = Path(__file__).parent.parent / "data" / "brand_db_cn.json"
        if db_path.exists():
            with open(db_path, encoding="utf-8") as f:
                db = _json.load(f)
            for b in db.get("brands", []):
                if (
                    name_lower in (b.get("name", "")).lower()
                    or name_lower in (b.get("name_en", "")).lower()
                ):
                    return {
                        "brand_name": b["name"],
                        "category": b.get("category", ""),
                        "sub_category": b.get("sub_category", ""),
                        "budget_tier": b.get("budget_tier", ""),
                        "negotiation_flexibility": b.get("negotiation_flexibility", ""),
                        "typical_cpm_cny": [b.get("cpm_low", 0), b.get("cpm_high", 0)],
                        "payment_reliability": b.get("payment_reliability", ""),
                        "known_issues": b.get("notes", ""),
                        "platforms": {
                            "bilibili": b.get("bilibili", False),
                            "douyin": b.get("douyin", False),
                            "kuaishou": b.get("kuaishou", False),
                        },
                    }
    except Exception:
        pass

    # --- Fall back to hardcoded patterns ---
    key = name_lower
    # Try exact match first
    if key in KNOWN_BRAND_PATTERNS_CN:
        return KNOWN_BRAND_PATTERNS_CN[key]
    # Try matching by Chinese name or pinyin
    for brand_key, info in KNOWN_BRAND_PATTERNS_CN.items():
        parts = brand_key.split("_")
        if key in parts or key == brand_key:
            return info
    return None


def detect_contract_red_flags_cn(
    usage_rights: str,
    exclusivity: str,
    usage_premium_applied: float,
    exclusivity_premium_applied: float,
    has_livestream: bool = False,
) -> list[dict]:
    """Detect contract red flags for CN deals."""
    flags = []

    if "perpetual" in usage_rights and usage_premium_applied < 0.3:
        flags.append(CONTRACT_RED_FLAGS_CN["perpetual_rights_no_premium"])

    if "ad_boost" in usage_rights:
        flags.append(CONTRACT_RED_FLAGS_CN["ad_boost_rights_hidden"])

    if "full_exclusivity" in exclusivity and exclusivity_premium_applied < 0.3:
        flags.append(CONTRACT_RED_FLAGS_CN["full_exclusivity_no_premium"])

    if usage_rights == "perpetual_all_media":
        flags.append(CONTRACT_RED_FLAGS_CN["content_ownership_transfer"])

    if has_livestream:
        flags.append(CONTRACT_RED_FLAGS_CN["livestream_no_refund_clause"])

    return flags


def route_complexity_cn(
    brand_name: str | None,
    exclusivity: str,
    usage_rights: str,
    niche: str,
    is_first_brand_deal: bool = False,
    has_livestream: bool = False,
    num_platforms: int = 1,
) -> str:
    """Determine pipeline complexity for CN edition."""
    HIGH_VARIANCE_NICHES_CN = {
        "finance_investing", "health_fitness", "education_knowledge",
        "automotive", "fashion_ootd",
    }

    score = 0
    if brand_name:
        score += 2
    if exclusivity != "none":
        score += 2
    if usage_rights != "organic_only":
        score += 2
    if has_livestream:
        score += 3
    if num_platforms > 1:
        score += 2
    if niche in HIGH_VARIANCE_NICHES_CN:
        score += 1
    if is_first_brand_deal:
        score += 1

    return "full_pipeline" if score >= 3 else "fast_track"


def calculate_confidence_cn(
    has_api_data: bool,
    has_engagement: bool,
    has_city_tier: bool,
    has_growth: bool,
    has_brand_intel: bool,
    cpm_confidence: str = "medium",
    has_historical_deals: bool = False,
    historical_deviation_pct: float | None = None,
) -> float:
    """Calculate confidence score for CN edition."""
    score = 0.3

    if has_api_data:
        score += 0.15
    if has_engagement:
        score += 0.15
    if has_city_tier:
        score += 0.10
    if has_growth:
        score += 0.10
    if has_brand_intel:
        score += 0.10

    # CPM confidence adjustment
    cpm_bonus = {"high": 0.10, "medium": 0.05, "low": 0.0}
    score += cpm_bonus.get(cpm_confidence, 0.0)

    # Historical deal consistency
    if has_historical_deals and historical_deviation_pct is not None:
        if historical_deviation_pct < 20:
            score += 0.10
        elif historical_deviation_pct < 40:
            score += 0.05
        # > 40% actually reduces confidence
        else:
            score -= 0.05

    return round(min(1.0, max(0.0, score)), 2)
