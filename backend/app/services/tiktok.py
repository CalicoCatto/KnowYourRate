def get_tiktok_form_schema() -> dict:
    """
    Return a JSON schema describing the manual input form fields needed
    for TikTok creator data.

    This is a placeholder for future TikTok API integration. For now,
    the frontend should present these fields for the user to fill in manually.
    """
    return {
        "type": "object",
        "title": "TikTok Creator Data",
        "description": "Please provide the following information about the TikTok creator.",
        "required": ["handle", "display_name", "follower_count"],
        "properties": {
            "handle": {
                "type": "string",
                "title": "TikTok Handle",
                "description": "The creator's TikTok @username",
                "pattern": r"^@?[\w.]+$",
            },
            "display_name": {
                "type": "string",
                "title": "Display Name",
                "description": "The creator's display name on TikTok",
            },
            "follower_count": {
                "type": "integer",
                "title": "Follower Count",
                "description": "Total number of followers",
                "minimum": 0,
            },
            "avg_views": {
                "type": "integer",
                "title": "Average Views per Video",
                "description": "Approximate average views per video",
                "minimum": 0,
            },
            "engagement_rate": {
                "type": "number",
                "title": "Engagement Rate (%)",
                "description": "Average engagement rate as a percentage",
                "minimum": 0,
                "maximum": 100,
            },
            "content_niche": {
                "type": "string",
                "title": "Content Niche",
                "description": "Primary content category",
                "enum": [
                    "gaming",
                    "tech",
                    "beauty",
                    "fashion",
                    "food",
                    "fitness",
                    "education",
                    "entertainment",
                    "music",
                    "travel",
                    "finance",
                    "lifestyle",
                    "general",
                ],
            },
        },
    }
