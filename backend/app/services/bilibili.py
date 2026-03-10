"""Bilibili (B站) data service.

B站 has semi-public APIs for basic user info and video stats.
More detailed data (audience demographics, watch time) requires
the creator's own backend access and must be entered manually.
"""


def get_bilibili_form_schema() -> dict:
    """Return JSON schema for manual Bilibili creator data input."""
    return {
        "type": "object",
        "title": "B站创作者数据",
        "description": "请提供B站UP主的基础数据信息。",
        "required": ["handle", "display_name", "follower_count"],
        "properties": {
            "handle": {
                "type": "string",
                "title": "B站UID或用户名",
                "description": "UP主的B站UID或用户名",
            },
            "display_name": {
                "type": "string",
                "title": "UP主昵称",
                "description": "UP主的显示昵称",
            },
            "follower_count": {
                "type": "integer",
                "title": "粉丝数",
                "minimum": 0,
            },
            "avg_views": {
                "type": "integer",
                "title": "近30天平均播放量",
                "minimum": 0,
            },
            "engagement_rate": {
                "type": "number",
                "title": "互动率 (%)",
                "description": "(点赞+投币+收藏+弹幕+评论) / 播放量 × 100%",
                "minimum": 0,
                "maximum": 100,
            },
            "coin_rate": {
                "type": "number",
                "title": "投币率 (%)",
                "description": "投币数 / 播放量 × 100%（可选）",
                "minimum": 0,
                "maximum": 100,
            },
            "favorite_rate": {
                "type": "number",
                "title": "收藏率 (%)",
                "description": "收藏数 / 播放量 × 100%（可选）",
                "minimum": 0,
                "maximum": 100,
            },
            "content_niche": {
                "type": "string",
                "title": "内容分区",
                "enum": [
                    "technology", "gaming", "anime_acg", "beauty_skincare",
                    "food_cooking", "lifestyle_vlog", "education_knowledge",
                    "finance_investing", "automotive", "digital_3c",
                    "entertainment_funny", "music_dance", "pets_animals",
                    "home_decoration", "parenting_family", "travel",
                    "fashion_ootd", "health_fitness",
                ],
            },
            "platform_level": {
                "type": "string",
                "title": "B站等级",
                "description": "如 LV5、LV6",
            },
            "audience_city_tier_1_pct": {
                "type": "number",
                "title": "一线城市受众比例 (%)",
                "minimum": 0,
                "maximum": 100,
            },
            "has_mcn": {
                "type": "boolean",
                "title": "是否签约MCN",
            },
        },
    }
