"""Bilibili (B站) data service.

Fetches public creator data from B站 APIs:
- User info (card API): name, level, sign, avatar, archive count
- Follower count (relation/stat API)
- Video list (medialist API): recent videos with play counts + bvids
- Video details (view API): likes, coins, favorites per video

Uses stable public APIs that don't require WBI signing or login cookies.
Private data (city tier distribution, watch time) requires manual input.
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Referer": "https://www.bilibili.com/",
}

# Niche keyword mapping for B站 content categories
_NICHE_KEYWORDS_CN = {
    "technology": ["科技", "数码", "评测", "电脑", "手机", "软件", "编程"],
    "gaming": ["游戏", "电竞", "主机", "手游", "网游", "steam"],
    "anime_acg": ["动画", "番剧", "漫画", "二次元", "虚拟", "vtuber", "鬼畜"],
    "beauty_skincare": ["美妆", "护肤", "化妆", "彩妆", "口红"],
    "food_cooking": ["美食", "做菜", "烹饪", "吃播", "料理", "厨房"],
    "lifestyle_vlog": ["生活", "vlog", "日常", "记录"],
    "education_knowledge": ["知识", "科普", "学习", "教育", "考试", "英语"],
    "finance_investing": ["财经", "理财", "投资", "股票", "基金", "经济"],
    "automotive": ["汽车", "车评", "驾驶", "新能源", "摩托"],
    "digital_3c": ["数码", "3C", "耳机", "相机", "镜头"],
    "entertainment_funny": ["搞笑", "娱乐", "综艺", "影视", "电影", "解说"],
    "music_dance": ["音乐", "翻唱", "舞蹈", "乐器", "编曲"],
    "pets_animals": ["宠物", "猫", "狗", "萌宠"],
    "home_decoration": ["家居", "装修", "收纳", "家装"],
    "parenting_family": ["育儿", "亲子", "母婴", "宝宝"],
    "travel": ["旅行", "旅游", "出行", "风景"],
    "fashion_ootd": ["穿搭", "时尚", "潮流", "服饰"],
    "health_fitness": ["健身", "运动", "减肥", "瑜伽", "跑步"],
}


def extract_uid(url_or_uid: str) -> str | None:
    """Extract Bilibili UID from URL or direct input.

    Supports:
      - https://space.bilibili.com/12345
      - https://www.bilibili.com/space/12345
      - https://b23.tv/xxx (short URL - not resolved, returns None)
      - UID: 12345
      - 12345
    """
    text = url_or_uid.strip()

    # Direct numeric UID
    if text.isdigit():
        return text

    # "UID: 12345" or "uid:12345"
    match = re.search(r"uid[:\s]*(\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1)

    # space.bilibili.com/12345 or bilibili.com/space/12345
    match = re.search(r"bilibili\.com/(?:space/)?(\d+)", text)
    if match:
        return match.group(1)

    return None


async def _init_session(client: httpx.AsyncClient) -> None:
    """Visit bilibili.com to obtain anti-crawling cookies.

    Some B站 APIs (like medialist) need cookies from the main site.
    The card and relation/stat APIs work without cookies.
    """
    try:
        await client.get("https://www.bilibili.com/", headers=_HEADERS)
        # Get proper buvid3/buvid4 from SPI endpoint
        spi_resp = await client.get(
            "https://api.bilibili.com/x/frontend/finger/spi",
            headers=_HEADERS,
        )
        spi_data = spi_resp.json()
        if spi_data.get("code") == 0:
            b3 = spi_data["data"].get("b_3", "")
            b4 = spi_data["data"].get("b_4", "")
            if b3:
                client.cookies.set("buvid3", b3, domain=".bilibili.com")
            if b4:
                client.cookies.set("buvid4", b4, domain=".bilibili.com")
    except Exception as e:
        logger.warning("B站 session init failed: %s", e)


async def fetch_bilibili_info(uid_or_url: str) -> dict:
    """Fetch Bilibili UP主 info from public APIs.

    Strategy uses stable, non-WBI APIs:
    1. /x/web-interface/card — user info (no auth needed)
    2. /x/relation/stat — follower count (no auth needed)
    3. /x/v2/medialist/resource/list — video list with play counts (needs cookies)
    4. /x/web-interface/view — per-video detailed stats (no auth needed)
    """
    uid = extract_uid(uid_or_url)
    if not uid:
        raise ValueError(
            "无法识别B站UID。请输入UID数字或空间链接，例如: 12345 或 https://space.bilibili.com/12345"
        )

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        # 0. Init session for cookie-dependent APIs
        await _init_session(client)

        # 1. Fetch user info via card API (stable, no WBI needed)
        card_resp = await client.get(
            "https://api.bilibili.com/x/web-interface/card",
            params={"mid": uid, "photo": "false"},
            headers=_HEADERS,
        )
        card_data = card_resp.json()

        if card_data.get("code") != 0:
            msg = card_data.get("message", "未知错误")
            raise ValueError(f"获取B站用户信息失败: {msg} (UID: {uid})")

        card = card_data["data"]["card"]
        name = card.get("name", "")
        level = card.get("level_info", {}).get("current_level", 0)
        sign = card.get("sign", "")
        face = card.get("face", "")
        fans = card.get("fans", 0)
        archive_count = card_data["data"].get("archive_count", 0)
        like_num = card_data["data"].get("like_num", 0)

        # 2. Fetch follower count from relation/stat API (more accurate)
        try:
            stat_resp = await client.get(
                "https://api.bilibili.com/x/relation/stat",
                params={"vmid": uid},
                headers=_HEADERS,
            )
            stat_data = stat_resp.json()
            if stat_data.get("code") == 0:
                fans = stat_data["data"].get("follower", fans)
        except Exception:
            pass

        # 3. Fetch recent videos via medialist API (needs cookies)
        videos = []
        try:
            ml_resp = await client.get(
                "https://api.bilibili.com/x/v2/medialist/resource/list",
                params={
                    "type": 1,
                    "biz_id": uid,
                    "oid": uid,
                    "otype": 2,
                    "ps": 20,
                    "direction": "false",
                    "desc": "true",
                    "sort_field": 1,
                    "tid": 0,
                    "with_current": "true",
                },
                headers={**_HEADERS, "Referer": f"https://space.bilibili.com/{uid}"},
            )
            ml_data = ml_resp.json()
            if ml_data.get("code") == 0:
                media_list = ml_data.get("data", {}).get("media_list") or []
                for item in media_list:
                    cnt = item.get("cnt_info", {})
                    play = cnt.get("play", 0)
                    if isinstance(play, str):
                        play = 0
                    videos.append({
                        "bvid": item.get("bv_id", ""),
                        "title": item.get("title", ""),
                        "play": play,
                    })
            else:
                logger.warning(
                    "B站视频列表获取失败 (UID: %s): code=%s, msg=%s",
                    uid, ml_data.get("code"), ml_data.get("message", ""),
                )
        except Exception as e:
            logger.warning("B站视频列表请求异常 (UID: %s): %s", uid, e)

        video_count = len(videos)

        # 4. Calculate total views from medialist
        total_views = sum(v["play"] for v in videos)
        avg_views = total_views // video_count if video_count > 0 else 0

        # 5. Fetch detailed stats for up to 10 videos (coins, favorites, likes)
        coin_total = 0
        fav_total = 0
        like_total = 0
        sample_views = 0
        sample_count = 0

        for v in videos[:10]:
            bvid = v.get("bvid", "")
            if not bvid:
                continue
            try:
                detail_resp = await client.get(
                    "https://api.bilibili.com/x/web-interface/view",
                    params={"bvid": bvid},
                    headers=_HEADERS,
                )
                detail = detail_resp.json()
                if detail.get("code") == 0:
                    stat = detail["data"].get("stat", {})
                    views = stat.get("view", 0)
                    if isinstance(views, str):
                        views = 0
                    sample_views += views
                    coin_total += stat.get("coin", 0)
                    fav_total += stat.get("favorite", 0)
                    like_total += stat.get("like", 0)
                    sample_count += 1
            except Exception:
                continue

        # 6. Calculate rates
        if sample_views > 0:
            engagement_rate = round(
                (like_total + coin_total + fav_total) / sample_views * 100, 2
            )
            coin_rate = round(coin_total / sample_views * 100, 2)
            favorite_rate = round(fav_total / sample_views * 100, 2)
        else:
            engagement_rate = 0.0
            coin_rate = 0.0
            favorite_rate = 0.0

        # 7. Guess niche from video titles + user sign
        niche_text = sign + " " + " ".join(v.get("title", "") for v in videos[:10])
        content_niche = _guess_niche_cn(niche_text)

        return {
            "platform": "bilibili",
            "platform_id": uid,
            "handle": uid,
            "title": name,
            "display_name": name,
            "subscriber_count": fans,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "content_niche": content_niche,
            "coin_rate": coin_rate,
            "favorite_rate": favorite_rate,
            "level": level,
            "sign": sign,
            "face": face,
            "video_count": video_count,
            "archive_count": archive_count,
            "like_num": like_num,
            "total_views": total_views,
            "sample_video_count": sample_count,
        }


def _guess_niche_cn(text: str) -> str:
    """Guess content niche from Chinese text (titles, description)."""
    text_lower = text.lower()
    best_niche = "lifestyle_vlog"
    best_score = 0
    for niche, keywords in _NICHE_KEYWORDS_CN.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_niche = niche
    return best_niche


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
