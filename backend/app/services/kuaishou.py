"""Kuaishou (快手) data service.

Kuaishou's open platform has limited APIs mostly for merchants.
Creator data must be entered manually or via third-party tools.
"""


def get_kuaishou_form_schema() -> dict:
    """Return JSON schema for manual Kuaishou creator data input."""
    return {
        "type": "object",
        "title": "快手主播数据",
        "description": "请提供快手主播的基础数据信息。",
        "required": ["handle", "display_name", "follower_count"],
        "properties": {
            "handle": {
                "type": "string",
                "title": "快手ID",
                "description": "主播的快手ID或用户名",
            },
            "display_name": {
                "type": "string",
                "title": "主播昵称",
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
                "description": "(点赞+评论+转发) / 播放量 × 100%",
                "minimum": 0,
                "maximum": 100,
            },
            "revisit_rate": {
                "type": "number",
                "title": "回访率 (%)",
                "description": "老粉回访比例（可选）",
                "minimum": 0,
                "maximum": 100,
            },
            "live_viewer_follower_ratio": {
                "type": "number",
                "title": "直播观看/粉丝比 (%)",
                "description": "直播间平均观看人数 / 粉丝数（可选）",
                "minimum": 0,
                "maximum": 100,
            },
            "content_niche": {
                "type": "string",
                "title": "内容领域",
                "enum": [
                    "technology", "gaming", "beauty_skincare", "food_cooking",
                    "lifestyle_vlog", "education_knowledge", "finance_investing",
                    "automotive", "digital_3c", "entertainment_funny",
                    "music_dance", "pets_animals", "home_decoration",
                    "parenting_family", "travel", "fashion_ootd",
                    "health_fitness", "agriculture_rural", "livestream_ecommerce",
                ],
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
