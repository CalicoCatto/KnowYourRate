"""Douyin (抖音) data service.

Douyin's open platform APIs are primarily for enterprise accounts.
Individual creator data must be entered manually or obtained via
third-party tools (蝉妈妈, 飞瓜, etc.).
"""


def get_douyin_form_schema() -> dict:
    """Return JSON schema for manual Douyin creator data input."""
    return {
        "type": "object",
        "title": "抖音达人数据",
        "description": "请提供抖音达人的基础数据信息。",
        "required": ["handle", "display_name", "follower_count"],
        "properties": {
            "handle": {
                "type": "string",
                "title": "抖音号",
                "description": "达人的抖音号或用户名",
            },
            "display_name": {
                "type": "string",
                "title": "达人昵称",
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
            "completion_rate": {
                "type": "number",
                "title": "完播率 (%)",
                "description": "平均完播率（可选，从创作者后台获取）",
                "minimum": 0,
                "maximum": 100,
            },
            "share_rate": {
                "type": "number",
                "title": "转发率 (%)",
                "description": "转发数 / 播放量 × 100%（可选）",
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
                    "health_fitness", "livestream_ecommerce",
                ],
            },
            "xingtu_suggested_price": {
                "type": "number",
                "title": "星图建议价 (¥)",
                "description": "如果达人入驻了星图，可填写星图系统建议价作为参考",
                "minimum": 0,
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
