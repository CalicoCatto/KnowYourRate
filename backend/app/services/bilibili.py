"""Bilibili (B站) data service.

Fetches public creator data from B站 APIs:
- User info: followers, name, level, avatar
- Video list: recent videos with views, likes, coins, favorites, shares, comments
- Calculated: avg views, engagement rate, coin rate, favorite rate

Private data (city tier distribution, watch time) requires manual input.
"""

import hashlib
import logging
import re
import time
import urllib.parse
import uuid
from functools import reduce

import httpx

logger = logging.getLogger(__name__)

# WBI signing mixin key reorder table (from Bilibili's JS)
_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

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


def _get_mixin_key(img_key: str, sub_key: str) -> str:
    """Derive WBI mixin key from img_key and sub_key."""
    raw = img_key + sub_key
    return reduce(lambda s, i: s + raw[i], _MIXIN_KEY_ENC_TAB, "")[:32]


def _sign_wbi(params: dict, mixin_key: str) -> dict:
    """Add WBI signature (wts + w_rid) to API params."""
    params["wts"] = int(time.time())
    # Filter special characters from values (required by B站 WBI spec)
    filtered = {
        k: "".join(ch for ch in str(v) if ch not in "!'()*")
        for k, v in params.items()
    }
    # Sort and encode
    query = urllib.parse.urlencode(sorted(filtered.items()))
    md5 = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params["w_rid"] = md5
    return params


async def _get_wbi_keys(client: httpx.AsyncClient) -> tuple[str, str]:
    """Fetch WBI signing keys from Bilibili nav API."""
    resp = await client.get("https://api.bilibili.com/x/web-interface/nav", headers=_HEADERS)
    data = resp.json().get("data", {})
    wbi_img = data.get("wbi_img", {})
    img_url = wbi_img.get("img_url", "")
    sub_url = wbi_img.get("sub_url", "")
    # Extract key from URL path: /bfs/wbi/xxx.png -> xxx
    img_key = img_url.rsplit("/", 1)[-1].split(".")[0] if img_url else ""
    sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0] if sub_url else ""
    return img_key, sub_key


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


async def fetch_bilibili_info(uid_or_url: str) -> dict:
    """Fetch Bilibili UP主 info from public APIs.

    Returns a dict matching the CreatorProfile schema with additional
    bilibili-specific fields (coin_rate, favorite_rate, etc.).
    """
    uid = extract_uid(uid_or_url)
    if not uid:
        raise ValueError(
            f"无法识别B站UID。请输入UID数字或空间链接，例如: 12345 或 https://space.bilibili.com/12345"
        )

    # Generate browser-like cookies required by B站 anti-crawling
    cookies = {
        "buvid3": str(uuid.uuid4()) + "infoc",
        "b_nut": str(int(time.time())),
    }

    async with httpx.AsyncClient(timeout=15.0, cookies=cookies) as client:
        # 1. Get WBI signing keys
        img_key, sub_key = await _get_wbi_keys(client)
        mixin_key = _get_mixin_key(img_key, sub_key) if img_key and sub_key else ""

        # 2. Fetch user info
        user_params = {"mid": uid}
        if mixin_key:
            user_params = _sign_wbi(user_params, mixin_key)

        user_resp = await client.get(
            "https://api.bilibili.com/x/space/wbi/acc/info",
            params=user_params,
            headers=_HEADERS,
        )
        user_data = user_resp.json()

        if user_data.get("code") != 0:
            msg = user_data.get("message", "未知错误")
            raise ValueError(f"获取B站用户信息失败: {msg} (UID: {uid})")

        info = user_data["data"]
        name = info.get("name", "")
        followers = info.get("fans", 0)  # Sometimes in this field
        level = info.get("level", 0)
        sign = info.get("sign", "")
        face = info.get("face", "")

        # 3. Fetch follower count from relation/stat API (more reliable)
        stat_resp = await client.get(
            "https://api.bilibili.com/x/relation/stat",
            params={"vmid": uid},
            headers=_HEADERS,
        )
        stat_data = stat_resp.json()
        if stat_data.get("code") == 0:
            followers = stat_data["data"].get("follower", followers)

        # 4. Fetch recent videos (last 30, sorted by newest)
        search_params = {
            "mid": uid,
            "ps": "30",
            "pn": "1",
            "order": "pubdate",
        }
        if mixin_key:
            search_params = _sign_wbi(search_params, mixin_key)

        video_resp = await client.get(
            "https://api.bilibili.com/x/space/wbi/arc/search",
            params=search_params,
            headers=_HEADERS,
        )
        video_data = video_resp.json()

        videos = []
        video_api_code = video_data.get("code")
        if video_api_code == 0:
            vlist = video_data.get("data", {}).get("list", {}).get("vlist", [])
            videos = vlist
        else:
            logger.warning(
                "B站视频列表获取失败 (UID: %s): code=%s, message=%s",
                uid, video_api_code, video_data.get("message", ""),
            )

        # 5. Calculate metrics from videos
        total_views = 0
        total_likes = 0  # Not available in vlist, use video_review (comments)
        total_coins = 0
        total_favorites = 0
        total_comments = 0
        total_danmaku = 0
        video_count = len(videos)

        for v in videos:
            play = v.get("play", 0)
            # Handle hidden play counts (返回 "--")
            if isinstance(play, str):
                play = 0
            total_views += play
            total_comments += v.get("video_review", 0) or 0  # comment count
            total_danmaku += v.get("review", 0) or 0  # actually this might be comments

        # For detailed stats (coins, favorites), fetch top 10 videos individually
        coin_sample_count = 0
        fav_sample_count = 0
        like_sample_count = 0
        sample_views = 0

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
                    coin_sample_count += stat.get("coin", 0)
                    fav_sample_count += stat.get("favorite", 0)
                    like_sample_count += stat.get("like", 0)
            except Exception:
                continue

        # Calculate averages
        avg_views = total_views // video_count if video_count > 0 else 0

        # Engagement rate = (likes + coins + favorites + comments) / views * 100
        if sample_views > 0:
            engagement_rate = round(
                (like_sample_count + coin_sample_count + fav_sample_count) / sample_views * 100,
                2,
            )
            coin_rate = round(coin_sample_count / sample_views * 100, 2)
            favorite_rate = round(fav_sample_count / sample_views * 100, 2)
        else:
            engagement_rate = 0.0
            coin_rate = 0.0
            favorite_rate = 0.0

        # Guess niche from video titles + user sign
        niche_text = sign + " " + " ".join(v.get("title", "") for v in videos[:10])
        content_niche = _guess_niche_cn(niche_text)

        return {
            "platform": "bilibili",
            "platform_id": uid,
            "handle": uid,
            "title": name,
            "display_name": name,
            "subscriber_count": followers,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "content_niche": content_niche,
            "coin_rate": coin_rate,
            "favorite_rate": favorite_rate,
            "level": level,
            "sign": sign,
            "face": face,
            "video_count": video_count,
            "total_views": total_views,
            "sample_video_count": min(10, video_count),
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
