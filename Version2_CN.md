# KnowYourRate 国内版迁移方案 — B站 / 抖音 / 快手

## 项目概述

KnowYourRate 是一个帮助创作者计算品牌合作公平报价的多Agent AI系统。本方案将海外版（YouTube/TikTok）的架构和逻辑迁移到国内市场，覆盖 B站（哔哩哔哩）、抖音、快手三大平台。

**核心设计原则**：同框架、异参数、新逻辑。架构（4 Agent + Router + Orchestrator）完全复用海外版，但数据层（CPM表、修正因子、品牌库）、业务逻辑（直播带货、平台撮合系统、广告法合规）和输出层（中文报告、人民币计价）全部针对国内市场重写。

**国内市场与海外市场的核心差异**：

| 维度 | 海外版 | 国内版 |
|------|--------|--------|
| 货币 | USD | CNY（人民币） |
| 平台特性 | YouTube/TikTok 以广告植入为主 | B站有充电/花火，抖音有星图，快手有磁力金牛，变现路径多元 |
| 创作者称谓 | Creator/Influencer | UP主（B站）/ 达人（抖音快手）/ KOL / KOC |
| 品牌合作模式 | 品牌直接联系或经纪公司 | 大量通过平台官方撮合系统（星图/花火/磁力聚星） |
| 核心合同议题 | 使用权(usage rights) | 是否走平台、直播带货坑位、信息流投放授权、广告法合规 |
| 受众地域价值 | 全球分布（US/UK溢价） | 城市线级（一线城市 vs 下沉市场） |
| 数据获取 | YouTube API 比较开放 | 各平台API限制多，依赖蝉妈妈/新榜/飞瓜等第三方 |
| 季节性 | Q4(圣诞)、Super Bowl | 双11、618、春节、开学季、国庆 |

---

## 一、整体架构

架构图与海外版完全一致：编排器 → 路由器 → Agent A/B/C/D。具体架构请参考海外版方案中的架构总览图。
```
用户输入（频道链接 + 合作条件）
        │
   ┌────▼────┐
   │ 编排器   │ ← 管理全局状态，协调Agent执行顺序
   │Orchestrator│
   └────┬────┘
        │
   ┌────▼────┐
   │复杂度路由器│ ← 判断走"快速通道"还是"完整分析"
   │ Router   │
   └────┬────┘
        │
   ┌────┴─────────────┐
   │                   │
   ▼                   ▼
快速通道            完整分析通道
(1-2 Agent)        (全部4 Agent)
   │                   │
   │         ┌─────────┼─────────┐
   │         ▼         ▼         │
   │    Agent A    Agent B       │  ← A和B并行执行
   │   (创作者画像) (市场情报)     │
   │         └────┬────┘         │
   │              ▼              │
   │         Agent C             │  ← C依赖A+B的结果
   │        (对抗辩论)            │
   │              │              │
   │              ▼              │
   │         Agent D             │  ← D汇总所有结果
   │       (策略报告生成)         │
   │              │              │
   └──────────────┴──────────────┘
                  │
                  ▼
           输出定价报告
```


### 路由器

```python
def route_request_cn(user_input):
    complexity_score = 0

    if user_input.has_brand_name:
        complexity_score += 2
    if user_input.deal_includes_exclusivity:
        complexity_score += 2
    if user_input.deal_includes_livestream_sales:
        complexity_score += 3    # 直播带货定价复杂度极高
    if len(user_input.platforms) > 1:
        complexity_score += 2    # 跨平台合作
    if user_input.niche in HIGH_VARIANCE_NICHES_CN:
        complexity_score += 1
    if user_input.is_first_brand_deal:
        complexity_score += 1
    if user_input.deal_includes_usage_rights:
        complexity_score += 2    # 涉及使用权

    # 注意：是否走官方平台（星图/花火）不计入复杂度
    # 它只影响报告展示（是否展示双价格），不影响分析深度

    if complexity_score >= 3:
        return "full_pipeline"
    else:
        return "fast_track"

HIGH_VARIANCE_NICHES_CN = [
    "finance_investing",     # 财经，监管严、价格波动大
    "health_medical",        # 健康医疗，合规成本高
    "education_k12",         # K12教育（双减政策风险）
    "luxury_fashion",        # 奢侈品时尚
    "automotive",            # 汽车（客单价高，品牌预算差异大）
    "real_estate",           # 房地产（区域性强）
]
```

---

## 二、Agent A — 创作者画像分析 Agent

### 输入

```json
{
  "platform": "bilibili" | "douyin" | "kuaishou",
  "channel_url": "https://space.bilibili.com/12345",
  "channel_data": {
    "followers": 180000,
    "avg_views_last_30": 50000,
    "engagement_rate": 6.8,
    "niche": "tech_review",
    "top_audience_city_tier": "一线城市为主",
    "channel_age_months": 30,
    "upload_frequency": "weekly",
    "platform_level": "LV5",
    "has_mcn": false,
    "mcn_name": null
  },
  "historical_deals": [
    {"brand": "某3C品牌", "price": 5000, "type": "integrated_mention", "date": "2025-01"},
    {"brand": "某APP", "price": 8000, "type": "dedicated_video", "date": "2025-03"}
  ]
}
```

> **设计说明**：历史成交价是最强的定价锚点。如果用户提供了1-3个历史成交案例，Agent A 应以此作为基准进行交叉验证，而非仅依赖CPM计算。当历史成交价与CPM计算结果偏差 > 40% 时，应标记"data_conflict"并降低置信度。

### 核心指标：粉丝播放比

```python
def calculate_core_metrics(channel_data, platform):
    """
    粉丝播放比 = avg_views / followers
    这是国内衡量达人商业价值的核心指标：
    - > 0.5：优秀（内容质量高，粉丝活跃度强）
    - 0.2 - 0.5：正常
    - 0.1 - 0.2：偏低（僵尸粉多或内容质量下滑）
    - < 0.1：危险信号（可能有大量僵尸粉/买粉行为）
    
    各平台基准不同：
    - B站：平均约 0.2-0.4（内容型平台，粉丝活跃度高）
    - 抖音：平均约 0.1-0.3（算法推荐为主，粉丝播放波动大）
    - 快手：平均约 0.15-0.35（私域较强，稳定但上限低）
    """
    vf_ratio = channel_data["avg_views"] / channel_data["followers"]

    # 粉丝播放比修正因子
    VF_RATIO_BENCHMARKS = {
        "bilibili":  {"excellent": 0.5, "good": 0.25, "poor": 0.1},
        "douyin":    {"excellent": 0.3, "good": 0.15, "poor": 0.05},
        "kuaishou":  {"excellent": 0.35, "good": 0.2, "poor": 0.08},
    }
    bench = VF_RATIO_BENCHMARKS[platform]

    if vf_ratio >= bench["excellent"]:
        vf_modifier = 1.2    # 封顶
    elif vf_ratio >= bench["good"]:
        # 线性插值 1.0 → 1.2
        vf_modifier = 1.0 + 0.2 * (vf_ratio - bench["good"]) / (bench["excellent"] - bench["good"])
    elif vf_ratio >= bench["poor"]:
        # 线性插值 0.7 → 1.0
        vf_modifier = 0.7 + 0.3 * (vf_ratio - bench["poor"]) / (bench["good"] - bench["poor"])
    else:
        vf_modifier = 0.5    # 严重警告
        # 同时触发 data_quality_flag: "low_vf_ratio_possible_fake_followers"

    return vf_ratio, vf_modifier
```

### 垂类 CPM 基准表

```python
# 数据来源说明：
# - 基于公开的行业报告（克劳锐指数、新榜研究院、蝉妈妈年度报告）
# - 花火/星图平台公开可见的达人报价区间逆推
# - 行业从业者访谈
# - confidence 字段表示该数据点的可靠程度：
#   "high" = 有多个一致数据源支撑
#   "medium" = 有1-2个数据源，行业共识
#   "low" = 主要基于推算和类比
#
# ⚠️ 重要：所有CPM数据应在上线后通过用户反馈的实际成交价持续校准
# 建议：每季度校准一次，特别是双11/618后

NICHE_CPM_TABLE_CN = {
    "bilibili": {
        "finance_investing":    {"low": 40, "mid": 70,  "high": 120, "confidence": "medium",
                                 "note": "B站财经区品牌预算高但供给少，头部溢价明显"},
        "technology":           {"low": 30, "mid": 50,  "high": 80,  "confidence": "high",
                                 "note": "B站科技区商业化最成熟的分区之一，数据充足"},
        "gaming":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "high",
                                 "note": "游戏是B站最大广告主品类，数据可靠"},
        "anime_acg":            {"low": 12, "mid": 25,  "high": 45,  "confidence": "medium",
                                 "note": "二次元品牌广告主相对少但客单价高"},
        "beauty_skincare":      {"low": 20, "mid": 40,  "high": 65,  "confidence": "medium"},
        "food_cooking":         {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium"},
        "lifestyle_vlog":       {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium"},
        "education_knowledge":  {"low": 25, "mid": 45,  "high": 75,  "confidence": "high",
                                 "note": "知识区商业价值仅次于科技区"},
        "health_fitness":       {"low": 20, "mid": 35,  "high": 55,  "confidence": "low"},
        "fashion_ootd":         {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium"},
        "automotive":           {"low": 35, "mid": 60,  "high": 100, "confidence": "medium",
                                 "note": "车企预算充裕，头部UP主报价可达6位数"},
        "digital_3c":           {"low": 25, "mid": 45,  "high": 70,  "confidence": "high"},
        "home_decoration":      {"low": 18, "mid": 35,  "high": 55,  "confidence": "low"},
        "parenting_family":     {"low": 15, "mid": 30,  "high": 50,  "confidence": "low"},
        "travel":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium"},
        "music_dance":          {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low"},
        "entertainment_funny":  {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium"},
        "pets_animals":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "low"},
    },
    "douyin": {
        "finance_investing":    {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium"},
        "technology":           {"low": 20, "mid": 38,  "high": 60,  "confidence": "medium"},
        "gaming":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium"},
        "beauty_skincare":      {"low": 25, "mid": 45,  "high": 70,  "confidence": "high",
                                 "note": "抖音美妆是最成熟的商业化赛道，数据充足"},
        "food_cooking":         {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium"},
        "lifestyle_vlog":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "medium"},
        "education_knowledge":  {"low": 20, "mid": 35,  "high": 60,  "confidence": "medium"},
        "health_fitness":       {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium"},
        "fashion_ootd":         {"low": 20, "mid": 40,  "high": 65,  "confidence": "high"},
        "automotive":           {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium"},
        "digital_3c":           {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium"},
        "home_decoration":      {"low": 15, "mid": 28,  "high": 45,  "confidence": "medium"},
        "parenting_family":     {"low": 18, "mid": 32,  "high": 50,  "confidence": "medium"},
        "travel":               {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium"},
        "music_dance":          {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low"},
        "entertainment_funny":  {"low": 3,  "mid": 8,   "high": 15,  "confidence": "medium"},
        "pets_animals":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low"},
        "livestream_ecommerce": {"low": 5,  "mid": 12,  "high": 25,  "confidence": "low",
                                 "note": "带货类达人更看坑位费+佣金，CPM参考价值有限"},
    },
    "kuaishou": {
        "finance_investing":    {"low": 15, "mid": 30,  "high": 55,  "confidence": "low",
                                 "note": "快手财经类达人较少，数据有限"},
        "technology":           {"low": 10, "mid": 22,  "high": 40,  "confidence": "low"},
        "gaming":               {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium"},
        "beauty_skincare":      {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium"},
        "food_cooking":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium"},
        "lifestyle_vlog":       {"low": 6,  "mid": 14,  "high": 25,  "confidence": "medium"},
        "education_knowledge":  {"low": 12, "mid": 22,  "high": 40,  "confidence": "low"},
        "health_fitness":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "low"},
        "fashion_ootd":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "medium"},
        "automotive":           {"low": 18, "mid": 35,  "high": 60,  "confidence": "low"},
        "digital_3c":           {"low": 10, "mid": 22,  "high": 38,  "confidence": "low"},
        "home_decoration":      {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium"},
        "parenting_family":     {"low": 12, "mid": 22,  "high": 38,  "confidence": "medium"},
        "travel":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low"},
        "agriculture_rural":    {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium",
                                 "note": "快手特色赛道，带货转化率可能是最高的"},
        "entertainment_funny":  {"low": 3,  "mid": 6,   "high": 12,  "confidence": "medium"},
        "pets_animals":         {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low"},
        "livestream_ecommerce": {"low": 3,  "mid": 8,   "high": 18,  "confidence": "medium"},
    }
}

# CPM数据校准机制
CPM_CALIBRATION = {
    "method": "用户反馈回收",
    "process": """
    1. 用户使用系统获得报价建议
    2. 实际成交后，可选择性反馈真实成交价
    3. 系统收集足够样本（每个 平台×垂类×层级 至少10个）后更新CPM表
    4. 校准频率：每季度一次，大促后（双11/618）额外校准
    """,
    "fallback": "当某个 平台×垂类 组合的CPM置信度为'low'时，报告中应明确提示"
}
```

### 互动率标准化定义

```python
# 各平台的互动率计算口径不同，必须标准化
ENGAGEMENT_RATE_DEFINITIONS = {
    "bilibili": {
        "formula": "(点赞 + 投币 + 收藏 + 弹幕 + 评论) / 播放量 × 100%",
        "components": ["like", "coin", "favorite", "danmaku", "comment"],
        "niche_averages": {
            # B站各分区的平均互动率（含所有互动形式）
            "technology":           5.0,
            "gaming":               6.0,
            "anime_acg":            7.0,   # B站ACG互动率最高
            "beauty_skincare":      4.5,
            "food_cooking":         5.5,
            "lifestyle_vlog":       4.0,
            "education_knowledge":  4.5,
            "finance_investing":    3.5,   # 财经类互动率偏低但质量高
            "automotive":           3.0,
            "digital_3c":           4.8,
            "entertainment_funny":  5.5,
            "music_dance":          6.5,
            "pets_animals":         5.0,
            "home_decoration":      4.0,
            "parenting_family":     4.0,
            "travel":               4.0,
            "fashion_ootd":         4.0,
            "health_fitness":       4.0,
        },
        "note": "B站互动率远高于其他平台，因为投币和收藏是独特的强互动信号"
    },
    "douyin": {
        "formula": "(点赞 + 评论 + 转发) / 播放量 × 100%",
        "components": ["like", "comment", "share"],
        "niche_averages": {
            "technology":           3.0,
            "gaming":               4.0,
            "beauty_skincare":      4.5,
            "food_cooking":         4.0,
            "lifestyle_vlog":       3.5,
            "education_knowledge":  3.0,
            "finance_investing":    2.5,
            "automotive":           2.0,
            "digital_3c":           3.0,
            "entertainment_funny":  5.0,
            "music_dance":          5.5,
            "pets_animals":         4.5,
            "home_decoration":      3.5,
            "parenting_family":     4.0,
            "travel":               3.5,
            "fashion_ootd":         4.0,
            "health_fitness":       3.5,
        },
        "note": "抖音的'播放量'包含大量'划过'(< 3秒)的无效曝光，因此互动率的分母被放大"
    },
    "kuaishou": {
        "formula": "(点赞 + 评论 + 转发) / 播放量 × 100%",
        "components": ["like", "comment", "share"],
        "niche_averages": {
            "technology":           3.5,
            "gaming":               4.5,
            "beauty_skincare":      4.0,
            "food_cooking":         5.0,
            "lifestyle_vlog":       4.5,
            "education_knowledge":  3.0,
            "finance_investing":    2.5,
            "automotive":           2.5,
            "digital_3c":           3.5,
            "entertainment_funny":  5.5,
            "music_dance":          5.0,
            "pets_animals":         5.0,
            "home_decoration":      4.0,
            "parenting_family":     5.0,
            "agriculture_rural":    6.0,   # 快手特色，农村类互动率极高
            "travel":               3.5,
            "fashion_ootd":         3.5,
            "health_fitness":       3.5,
        },
        "note": "快手老铁文化下互动率偏高，尤其是评论区活跃度"
    }
}
```

### 修正因子系统

```python
def calculate_all_modifiers_cn(channel_data, platform, niche, current_date):
    """
    修正因子采用加法累积 + 封顶机制，避免乘法累积导致结果爆炸。
    
    总修正因子 = 1.0 + sum(各修正增量)
    封顶范围：总修正因子 ∈ [0.4, 2.0]
    即最终价格最多是基础价的2倍或最低0.4倍
    """
    modifier_deltas = {}

    # ===== 1. 互动率修正 =====
    niche_avg = ENGAGEMENT_RATE_DEFINITIONS[platform]["niche_averages"].get(niche, 4.0)
    ratio = channel_data["engagement_rate"] / niche_avg

    if ratio < 0.5:
        modifier_deltas["engagement"] = -0.3
    elif ratio < 1.0:
        modifier_deltas["engagement"] = -0.15 + 0.15 * (ratio - 0.5) / 0.5  # -0.15 → 0
    elif ratio < 2.0:
        modifier_deltas["engagement"] = 0.0 + 0.25 * (ratio - 1.0) / 1.0    # 0 → +0.25
    else:
        modifier_deltas["engagement"] = 0.25  # 封顶

    # ===== 2. 粉丝播放比修正=====
    _, vf_modifier = calculate_core_metrics(channel_data, platform)
    modifier_deltas["vf_ratio"] = vf_modifier - 1.0  # 转为增量形式

    # ===== 3. 受众城市线级修正=====
    city_dist = channel_data.get("audience_city_distribution", None)
    if city_dist:
        # 加权计算城市价值分
        city_value = (
            city_dist.get("tier_1", 0) * 1.0 +      # 一线 (北上广深)
            city_dist.get("new_tier_1", 0) * 0.8 +   # 新一线 (杭州成都南京等)
            city_dist.get("tier_2", 0) * 0.5 +        # 二线
            city_dist.get("tier_3_below", 0) * 0.2     # 三线及以下
        ) / 100  # 归一化到0-1

        # 快手特殊处理
        if platform == "kuaishou":
            # 快手的下沉市场受众对特定品类（农产品、白牌、实惠型产品）反而是优势
            brand_targets_sinking_market = channel_data.get("brand_targets_sinking", False)
            if brand_targets_sinking_market:
                # 如果品牌目标就是下沉市场，反转城市线级修正
                city_value = 1.0 - city_value + 0.2  # 下沉越多反而越高
                modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
                modifier_deltas["city_tier_note"] = "快手下沉市场优势：品牌目标与受众匹配"
            else:
                modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
        else:
            # B站和抖音：城市越高线价值越高
            modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
            # city_value=0.8 → +0.12; city_value=0.3 → -0.08
    else:
        modifier_deltas["city_tier"] = 0.0  # 无数据时不修正

    # ===== 4. 增长动量修正 =====
    growth_rate = channel_data.get("monthly_growth_rate", 0)
    if growth_rate > 10:
        modifier_deltas["growth"] = 0.15
    elif growth_rate > 3:
        modifier_deltas["growth"] = 0.05 + 0.10 * (growth_rate - 3) / 7
    elif growth_rate >= 0:
        modifier_deltas["growth"] = 0.0
    else:
        modifier_deltas["growth"] = max(-0.15, growth_rate * 0.015)  # 负增长惩罚，封底

    # ===== 5. 平台特有信号修正=====
    platform_signal_delta = 0.0
    if platform == "bilibili":
        coin_rate = channel_data.get("coin_rate", 0)
        favorite_rate = channel_data.get("favorite_rate", 0)
        if coin_rate > 0.03:
            platform_signal_delta += 0.08
        elif coin_rate > 0.015:
            platform_signal_delta += 0.04
        if favorite_rate > 0.05:
            platform_signal_delta += 0.05
        elif favorite_rate > 0.03:
            platform_signal_delta += 0.02

    elif platform == "douyin":
        completion_rate = channel_data.get("completion_rate", 0)
        share_rate = channel_data.get("share_rate", 0)
        if completion_rate > 0.4:
            platform_signal_delta += 0.10
        elif completion_rate > 0.25:
            platform_signal_delta += 0.05
        if share_rate > 0.02:
            platform_signal_delta += 0.08

    elif platform == "kuaishou":
        # 快手私域价值修正
        revisit_rate = channel_data.get("revisit_rate", 0)  # 回访率
        live_to_follower = channel_data.get("live_viewer_follower_ratio", 0)
        if revisit_rate > 0.3:
            platform_signal_delta += 0.12  # 快手私域粘性极高，商业价值大
        elif revisit_rate > 0.15:
            platform_signal_delta += 0.06
        if live_to_follower > 0.05:
            platform_signal_delta += 0.08

    # 子项封顶：平台信号最多 +0.15
    modifier_deltas["platform_signal"] = min(platform_signal_delta, 0.15)

    # ===== 6. 内容长尾效应修正=====
    # B站内容的长尾效应远强于抖音：
    #   一条B站视频可能在发布后3-12个月持续获得播放和搜索流量
    #   而抖音视频的生命周期通常只有48-72小时
    LONGEVITY_MODIFIERS = {
        "bilibili":  0.10,   # B站长尾价值 +10%
        "douyin":    0.0,    # 抖音无长尾
        "kuaishou":  0.03,   # 快手有轻微长尾（私域回放）
    }
    modifier_deltas["content_longevity"] = LONGEVITY_MODIFIERS[platform]

    # ===== 7. 季节性修正 =====
    modifier_deltas["seasonal"] = calculate_seasonal_modifier_cn(current_date, niche) - 1.0

    # ===== 合计并封顶 =====
    total_delta = sum(v for k, v in modifier_deltas.items() if isinstance(v, (int, float)))
    total_modifier = 1.0 + total_delta
    total_modifier = max(0.4, min(2.0, total_modifier))  # 封在 [0.4, 2.0]

    return {
        "modifier_details": modifier_deltas,
        "total_modifier": round(total_modifier, 3),
    }
```

### 季节性乘数完整矩阵

```python
# 完整的月度 × 品类组 季节性乘数表
# 品类组是为了避免18个垂类 × 12个月 = 216个值的组合爆炸
SEASONAL_MATRIX_CN = {
    # 品类组定义
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
    # 月度乘数（1.0 = 无影响）
    "monthly_multipliers": {
        #                  1月    2月    3月    4月    5月    6月    7月    8月    9月    10月   11月   12月
        "ecommerce_all":  [0.90,  0.85,  0.90,  0.95,  1.10,  1.30,  0.90,  0.90,  0.95,  1.20,  1.50,  1.20],
        "education":      [1.00,  1.10,  1.00,  0.95,  1.00,  1.10,  1.10,  1.15,  1.20,  1.05,  1.10,  1.00],
        "gaming_acg":     [1.05,  1.10,  1.00,  1.00,  1.00,  1.05,  1.15,  1.15,  1.00,  1.10,  1.15,  1.10],
        "travel_outdoor": [0.85,  0.90,  0.95,  1.10,  1.15,  1.05,  1.15,  1.10,  1.20,  1.30,  0.95,  0.90],
        "auto_finance":   [1.10,  0.90,  1.00,  1.10,  1.05,  1.00,  0.95,  0.95,  1.10,  1.15,  1.20,  1.10],
        "entertainment":  [1.05,  1.10,  0.95,  0.95,  1.00,  1.00,  1.05,  1.05,  0.95,  1.05,  1.10,  1.05],
        "parenting":      [1.00,  1.05,  1.00,  1.00,  1.05,  1.15,  1.00,  1.10,  1.15,  1.05,  1.15,  1.10],
        "agriculture":    [1.20,  1.10,  0.90,  0.95,  1.00,  1.00,  1.00,  0.95,  1.05,  1.10,  1.20,  1.15],
    },
    # 关键节点说明（用于报告解读）
    "key_events": {
        1:  "元旦/年货节",
        2:  "春节（具体日期按农历浮动）",
        3:  "38女神节（美妆时尚小旺季）",
        5:  "618预热期开始",
        6:  "618大促",
        7:  "暑期（游戏/教育旺季）",
        8:  "开学季",
        9:  "中秋/国庆预热",
        10: "双11预热期开始",
        11: "双11大促（全年最大旺季）",
        12: "双12/年货节",
    }
}

def calculate_seasonal_modifier_cn(current_date, niche):
    month = current_date.month
    # 找到该垂类所属的品类组
    for group_name, niches in SEASONAL_MATRIX_CN["category_groups"].items():
        if niche in niches:
            return SEASONAL_MATRIX_CN["monthly_multipliers"][group_name][month - 1]
    return 1.0  # 未匹配到品类组时返回无修正
```

### 频道层级分类

频道层级分类表详见本方案附录 A。

---

## 三、Agent B — 市场情报 Agent

### 交付物乘数

交付物类型定价乘数表详见本方案附录 B。

### 直播带货坑位费交叉表

```python
# 坑位费不仅和粉丝量级相关，更和品类强相关
# 单位：人民币
LIVESTREAM_PIT_FEE_TABLE = {
    # 格式：[层级][品类] = (low, mid, high)
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

# 佣金率表（按品类）
COMMISSION_RATE_TABLE = {
    "beauty_skincare":    {"rate": "20%-40%", "note": "客单价<100效果最佳"},
    "food":               {"rate": "15%-30%", "note": "复购率高是优势"},
    "fashion":            {"rate": "20%-35%", "note": "退货率高（30-50%），实际佣金需打折"},
    "digital_3c":         {"rate": "5%-15%",  "note": "客单价高但转化率低"},
    "home_goods":         {"rate": "15%-25%", "note": "家居决策周期长，效果延迟"},
    "health_supplements": {"rate": "25%-50%", "note": "高利润品类，佣金空间大"},
}

# 直播带货ROI预估
LIVESTREAM_ROI_MODEL = {
    "conversion_rate_by_tier": {
        "超头部": "5%-15%",
        "头部":   "3%-10%",
        "中腰部": "2%-6%",
        "小达人": "1%-4%",
    },
    "refund_rate_by_category": {
        "fashion":          "30%-50%（服装是退货重灾区）",
        "beauty_skincare":  "10%-20%",
        "food":             "5%-10%（生鲜/冷链较高）",
        "digital_3c":       "8%-15%",
        "home_goods":       "15%-25%",
    },
    "effective_roi_formula": """
    实际ROI = (GMV × (1 - 退货率) × 利润率 - 坑位费) / 坑位费
    
    示例：某美妆品客单价¥89，达人GMV ¥50,000
    退货率15%，利润率60%
    坑位费 ¥15,000 + 佣金25%
    
    实际收入 = 50000 × (1-0.15) × 0.60 - 50000 × (1-0.15) × 0.25 - 15000
             = 25,500 - 10,625 - 15,000
             = -¥125（亏损！）
    
    → 这个案例说明品牌需要仔细计算ROI，而非只看GMV
    """,
}
```

### 使用权/排他性溢价

使用权与排他性溢价表详见本方案附录 C。

### 平台官方撮合系统

平台官方撮合系统信息（花火/星图/磁力聚星）详见本方案附录 D。

### 已知品牌库（20个常见国内品牌）

```python
KNOWN_BRAND_PATTERNS_CN = {
    # ===== 互联网/APP =====
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

    # ===== 美妆个护 =====
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

    # ===== 食品饮料 =====
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

    # ===== 汽车 =====
    "蔚来_nio": {
        "category": "automotive", "budget_tier": "very_high",
        "negotiation_flexibility": "high", "typical_cpm_cny": [50, 100],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["试驾体验", "技术讲解", "不允许竞品对比"],
        "payment_reliability": "优秀",
        "note": "新能源车品牌预算充裕",
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

    # ===== 游戏 =====
    "米哈游_mihoyo": {
        "category": "gaming", "budget_tier": "very_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [25, 55],
        "platforms": ["bilibili"],
        "requirements": ["游戏实况", "角色/活动展示", "严格内容审核"],
        "known_issues": ["审核非常严格", "不允许任何负面评价"],
        "payment_reliability": "优秀",
        "note": "B站游戏区最大品牌客户之一",
    },
    "网易游戏_netease": {
        "category": "gaming", "budget_tier": "high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [20, 45],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["游戏体验", "玩法介绍"],
        "payment_reliability": "优秀",
    },

    # ===== 教育/工具 =====
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

    # ===== 3C数码 =====
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
        "note": "手机品牌是全平台最大广告主品类之一",
    },
    "追觅_dreame": {
        "category": "digital_3c", "budget_tier": "medium_high",
        "negotiation_flexibility": "medium", "typical_cpm_cny": [20, 40],
        "platforms": ["bilibili", "douyin"],
        "requirements": ["产品实测", "清洁效果对比"],
        "payment_reliability": "良好",
    },
}
```

### 打包方案

打包方案生成逻辑详见本方案附录 E。

---

## 四、Agent C — 对抗辩论 Agent

### Bull Agent Prompt（看多方 — 达人经纪人视角）

```
你是一位经验丰富的国内MCN机构商务经理，你的职责是为达人争取最高合理报价。

你将收到以下结构化数据：
- creator_profile: 达人画像（来自Agent A）
- deal_conditions: 合作条件（来自Agent B）
- base_price_range: 基础报价区间
- market_context: 市场情报

请严格基于以下数据进行论证，每个论据必须引用具体数字：

1.【互动价值】
   引用数据：creator_profile.engagement_rate 和 engagement_vs_niche_avg
   论证思路：如果互动率高于垂类平均，量化这意味着每千次播放带来更多互动（具体算：互动率差值 × 平均播放量 = 额外多出的互动数）

2.【受众质量】
   引用数据：creator_profile.audience_city_tier 和/或 audience_age
   论证思路：
   - 一线城市用户获客成本通常是¥50-¥200，而通过该达人触达的CPM仅¥XX
   - B站特有：引用 coin_rate，论证投币代表强购买意向信号

3.【粉丝播放比】
   引用数据：creator_profile.vf_ratio
   论证思路：如果粉丝播放比优秀（如 > 0.3），说明粉丝活跃度高，不是僵尸粉，实际触达有效性远高于账面数字

4.【增长溢价】
   引用数据：creator_profile.growth_trend 和 monthly_growth_rate
   论证思路：按当前增长率，3个月后同一个达人的报价将上涨约 X%，品牌现在合作是性价比最高的时机

5.【使用权价值】
   引用数据：deal_conditions.usage_rights
   论证思路：如果品牌要求信息流投放权，计算替代成本（品牌自行拍摄一条广告素材成本约¥5,000-¥50,000）

6.【内容长尾】（仅B站）
   论证思路：B站内容的长尾效应意味着品牌曝光将持续6-12个月，等效CPM远低于账面数字

7.【季节性时机】
   引用数据：seasonal_modifier
   论证思路：如果当前或即将进入旺季，达人档期紧张，理应溢价

请输出JSON格式：
{
  "suggested_price": 具体数字(CNY),
  "arguments": [
    {"point": "论据标题", "data_reference": "引用的具体数据", "reasoning": "推理逻辑", "impact": "对报价的具体影响(+X%)"}
  ],
  "preemptive_rebuttals": ["对可能反驳的预判"]
}
```

### Bear Agent Prompt（看空方 — 品牌方采购视角）

```
你是一位国内品牌市场部的KOL投放负责人，你的职责是评估达人的真实市场价值，确保品牌方获得合理的ROI。

你将收到以下结构化数据：
- creator_profile: 达人画像（来自Agent A）
- deal_conditions: 合作条件（来自Agent B）
- base_price_range: 基础报价区间
- market_context: 市场情报

请严格基于以下数据进行论证，每个论据必须引用具体数字：

1.【市场供给】
   引用数据：creator_profile.tier 和 niche
   论证思路：{平台}上{垂类}的{层级}达人数量约 X-X 个（参考星图/花火平台数据），品牌有充足的替代选择

2.【ROI反算】
   引用数据：base_price_range.mid 和 creator_profile.avg_views
   论证思路：
   - 品牌CPA目标若为¥50，需要达人带来 报价/50 = X 个转化
   - 以行业平均转化率 0.5%-2% 计算，X万播放能带来 X 个转化
   - 反算合理报价 = 转化数 × CPA目标

3.【播放量波动风险】
   引用数据：creator_profile.avg_views（注意这是"平均"）
   论证思路：
   - 平均播放量不等于保证播放量，品牌承担了下行风险
   - 抖音特别明显：算法波动可能导致某条视频播放量仅为平均值的 20-30%
   - 建议：如果报价高，应讨论保底播放量条款

4.【可比基准】
   引用数据：market_context.comparable_deals
   论证思路：同层级达人在{星图/花火/磁力聚星}上的平均报价为¥X，本次报价是否偏离过大

5.【长期合作折扣】
   论证思路：如果品牌愿意承诺季度/年度框架，单次费率应下调 30-50%，这对达人也有好处（稳定收入、降低获客成本）

6.【直播带货实际ROI】（如涉及）
   引用数据：LIVESTREAM_ROI_MODEL
   论证思路：GMV ≠ 利润，退货率+佣金+坑位费后实际ROI可能为负

7.【隐性成本】
   论证思路：品牌方的时间投入（brief制作、内容审核、沟通成本）也应计入总成本

请输出JSON格式：
{
  "suggested_price": 具体数字(CNY),
  "arguments": [
    {"point": "论据标题", "data_reference": "引用的具体数据", "reasoning": "推理逻辑", "impact": "对报价的具体影响(-X%)"}
  ],
  "counter_arguments": ["对看多方可能论据的反驳"]
}
```

### 裁判 Agent Prompt

```
你是一位中立的KOL商业定价分析专家。你刚才旁听了"达人经纪人"（看多方）和"品牌采购经理"（看空方）关于一位达人品牌合作报价的辩论。

请你完成以下分析：

1.【论据评估】评估双方每个论据的强度（强/中/弱），标准是：
   - 强：有具体数据支撑，逻辑链完整
   - 中：有数据但推理有跳跃，或数据来源有不确定性
   - 弱：主要基于推测或类比，缺乏直接数据

2.【共识区域】识别双方在哪些点上实际达成了共识（即使表述不同）

3.【最终报价区间】综合双方论据，给出三档报价：
   - walk_away（底线价）：低于此价达人应拒绝合作
   - fair_market（公平市场价）：综合双方论据的中间值
   - anchor_price（锚定价）：达人开口报价，通常比 fair_market 高 25-35%

4.【走平台/私下双报价】（如适用）
   - 走平台（星图/花火/磁力聚星）的报价 = fair_market / (1 - 平台抽成率)
   - 私下合作报价 = fair_market

5.【置信度评分】0-1 之间，考虑以下因素：
   - 数据完整度（缺少互动率/受众地域等关键数据时降低）
   - CPM基准表的置信度（如果该 平台×垂类 的CPM置信度为"low"则降低）
   - 历史成交价一致性（如果有历史成交且与计算结果偏差>40%则降低）
   - 辩论收敛性（Bull和Bear差距>100%则大幅降低）

6.【高不确定性标记】如果 Bull 和 Bear 的报价差距超过 80%，标记为高不确定性，
   并明确建议达人"先要求品牌给出预算范围，再基于此谈判"

输出格式：
{
  "final_price_range": {
    "walk_away": 数字,
    "fair_market": 数字,
    "anchor_price": 数字,
    "currency": "CNY"
  },
  "platform_adjusted": {
    "official_platform_brand_pays": 数字,
    "official_platform_creator_gets": 数字,
    "private_deal_price": 数字
  },
  "confidence": 0.0-1.0,
  "uncertainty_flag": true/false,
  "argument_assessment": {
    "bull_strongest": {"point": "...", "strength": "强/中/弱"},
    "bear_strongest": {"point": "...", "strength": "强/中/弱"}
  },
  "consensus_areas": ["area1", "area2"],
  "judge_notes": "200字以内的综合分析"
}
```

---

## 五、Agent D — 策略报告

### 合同红线检测规则

```python
CONTRACT_RED_FLAGS_CN = {
    "perpetual_rights_no_premium":
        "永久使用权但未加价 → 🚫 强烈建议拒绝或加价200-300%",
    "ad_boost_rights_hidden":
        "品牌要求拿内容投信息流广告（Dou+/巨量引擎）但合同未明确 → 🚫 必须单独约定并加价",
    "unlimited_revisions":
        "无限修改轮次 → ⚠️ 限制为2轮，第3轮起按原价20%收费",
    "full_exclusivity_no_premium":
        "全品类排他但未额外补偿 → 🚫 至少加价50-100%",
    "payment_after_publish":
        "发布后才付款 → ⚠️ 要求50%预付，发布后7天内付尾款",
    "payment_net_60_plus":
        "付款周期超过60天 → ⚠️ 缩短至30天或加收账期费用",
    "no_off_platform_clause":
        "禁止在其他平台发类似内容 → ⚠️ 确认排他范围",
    "vague_deliverables":
        "交付物描述模糊（如'若干条视频'）→ ⚠️ 必须明确数量、时长、格式",
    "content_ownership_transfer":
        "要求转让内容所有权 → 🚫 改为授权使用，保留所有权",
    "no_kill_fee":
        "无终止费条款 → ⚠️ 加入终止费（合同金额的25-50%）",
    "livestream_no_refund_clause":
        "直播带货合同无退货成本分担条款 → ⚠️ 明确退货成本由谁承担",
    "forced_positive_review":
        "合同要求必须给好评/不能提缺点 → ⚠️ 违反广告法真实性要求",
    "no_ad_disclosure":
        "合同未要求标注广告 → ⚠️ 广告法规定必须标注'广告'或'推广'",
    "cross_platform_hidden":
        "合同包含跨平台发布但未额外计价 → ⚠️ 每个平台应单独计价",

    # === 新增遗漏条款===
    "portrait_rights_perpetual":
        "品牌要求永久使用达人肖像/形象 → 🚫 肖像权授权必须有明确期限和范围，永久授权至少加价100%",
    "derivative_works_unlimited":
        "允许品牌对内容进行无限二次创作/改编 → ⚠️ 应限定二创范围（如不得用于负面对比、恶搞），并保留审核权",
    "penalty_clause_one_sided":
        "合同只有达人的违约金条款，品牌方无对等约束 → ⚠️ 要求加入品牌方违约条款（如延迟付款违约金）",
    "data_sharing_forced":
        "要求达人提供后台数据截图/账号密码 → 🚫 绝不提供账号密码，数据截图需脱敏",
    "no_minimum_guarantee_livestream":
        "直播带货合同无最低保底条款 → ⚠️ 如果品牌要求纯佣金（零坑位费），达人承担了全部风险",
}
```

### 报告结构中的税务模块

```python
TAX_ESTIMATION_CN = {
    "劳务报酬（个人直接收款）": {
        "description": "最常见的达人收入方式，按劳务报酬所得纳税",
        "tax_brackets": [
            # (收入区间, 预扣率, 速算扣除数)
            ("≤ ¥800",        "免税",     ""),
            ("¥800-¥4,000",   "预扣率20%，扣除¥800后计算", ""),
            ("¥4,000-¥20,000","预扣率20%，扣除20%费用后计算", "实际税率约16%"),
            ("¥20,000-¥50,000","预扣率30%", "速算扣除¥2,000"),
            ("> ¥50,000",     "预扣率40%", "速算扣除¥7,000"),
        ],
        "example": "单笔收入¥10,000 → 应纳税额 = 10000 × (1-20%) × 20% = ¥1,600 → 实际到手¥8,400",
        "annual_settlement": "年度汇算时并入综合所得，可能多退少补",
    },
    "个体工商户/工作室": {
        "description": "年收入>¥30万的达人建议注册，可显著优化税负",
        "advantages": [
            "核定征收情况下综合税率可低至 3%-5%",
            "可以开增值税发票，品牌方更愿意合作",
            "部分支出可抵扣（设备、场地等）",
        ],
        "注册成本": "约¥2,000-¥5,000（含代理记账一年）",
        "风险提示": "近年核定征收政策收紧，部分地区已暂停新申请",
    },
    "公司/MCN": {
        "description": "头部达人或团队化运营时选择",
        "tax_rate": "企业所得税25% + 分红个税20% = 综合约40%（但可通过成本抵扣优化）",
        "advantages": ["品牌方信任度最高", "可签大额框架合同", "风险隔离"],
    },
    "走平台（星图/花火/磁力聚星）": {
        "description": "平台代扣代缴，最省心但不一定最省税",
        "mechanism": "平台按劳务报酬代扣预缴，年终需自行汇算",
        "note": "走平台=品牌付总额，平台先扣服务费，再代扣个税，达人收到的是净额",
    },
    "报告建议": """
    系统应在报告中展示三种场景的到手金额对比：
    | 场景 | 品牌支付 | 平台费 | 税费 | 达人到手 |
    |------|---------|--------|------|---------|
    | 走平台(个人) | ¥XX | ¥XX | ¥XX | ¥XX |
    | 私下(个人)   | ¥XX | ¥0  | ¥XX | ¥XX |
    | 私下(工作室) | ¥XX | ¥0  | ¥XX | ¥XX |
    """
}
```

### 其余报告结构

报告中的谈判话术模板、打包方案展示、时机建议等模块详见本方案附录 G。

---

## 六、数据获取

```python
# === B站数据 ===
bilibili_data_sources = {
    "public_api_no_auth": {
        # 无需任何认证即可调用（但可能被频率限制）
        "user_info": {
            "endpoint": "api.bilibili.com/x/space/wbi/acc/info",
            "returns": "粉丝数、等级、头像、简介",
            "limit": "无需cookie，但需要wbi签名（anti-spam）",
            "reliability": "medium（B站近年加强了反爬，可能需要定期更新签名算法）",
        },
    },
    "public_api_need_cookie": {
        # 需要有效的B站cookie（登录态）
        "video_list": {
            "endpoint": "api.bilibili.com/x/space/wbi/arc/search",
            "returns": "视频列表（标题、播放量、发布时间）",
            "limit": "需要cookie，否则可能返回空或被403",
        },
        "video_stat": {
            "endpoint": "api.bilibili.com/x/web-interface/view",
            "returns": "单个视频的详细数据（播放/点赞/投币/收藏/弹幕数）",
            "limit": "需要cookie才能获取完整数据",
        },
    },
    "not_available": {
        # 无法公开获取的数据
        "audience_demographics": "受众年龄/性别/地域分布 → 仅创作者后台可见，需用户手动输入",
        "watch_time": "平均观看时长/完播率 → 仅创作者后台可见",
        "revenue_data": "收入数据 → 仅创作者本人可见",
    },
    "recommended_approach": """
    1. 优先用公开API获取：粉丝数、视频列表、各视频播放/互动数据
    2. 计算得出：平均播放量、互动率、投币率、收藏率、发布频率、增长趋势
    3. 用户手动补充：受众地域分布、年龄分布（从创作者后台截图或选择估算）
    4. 完全不可获取时：基于垂类和粉丝量级做默认估算，并在置信度中体现
    """,
    "third_party_alternatives": ["新榜B站版", "火烧云数据", "飞瓜B站版"],
}

# === 抖音数据 ===
douyin_data_sources = {
    "official_api": {
        "note": "抖音开放平台API主要面向企业号和服务商，个人达人数据几乎无法通过API获取",
        "xingtu_public": "星图平台可查看入驻达人的公开报价和基础数据（粉丝数、互动率区间），无需登录",
    },
    "data_acquisition_strategy": """
    1. 星图平台公开数据：入驻达人的报价参考（作为校准锚点！）
    2. 用户手动输入：粉丝数、平均播放量、互动率
    3. 用户选择性提供：完播率、分享率（从创作者后台获取）
    4. 第三方API：蝉妈妈/飞瓜/新抖（付费API，如果预算允许）
    """,
    "xingtu_calibration": """
    ⚠️ 关键设计：当用户提供了星图建议价时，系统应将星图价格作为额外锚点。
    如果系统计算结果与星图建议价偏差 > 50%，应：
    1. 触发 data_conflict 标记
    2. 报告中同时展示两个参考价（系统计算 vs 星图建议价）
    3. 解释差异原因（如星图价可能偏低/偏高的常见原因）
    """,
}

# === 快手数据 ===
kuaishou_data_sources = {
    "official_api": {
        "note": "快手开放平台有部分API，但主要面向商家和服务商",
    },
    "data_acquisition_strategy": """
    1. 磁力聚星公开数据（有限）
    2. 用户手动输入为主
    3. 第三方：新快、飞瓜快手版
    """,
}
```

---

## 七、国内版特有模块

### 7.1 广告法合规检测

广告法合规检测规则详见本方案附录 H。

### 7.2 跨平台合作定价

```python
def calculate_cross_platform_price(single_platform_prices, platforms, content_type):
    """
    跨平台定价 ≠ 简单按平台数打折
    而是：各平台独立报价 + 内容适配成本 - 规模折扣
    """
    ADAPTATION_COSTS = {
        # (源平台, 目标平台): 额外工作量比例
        ("bilibili", "douyin"):      0.25,  # 横版长视频 → 竖版短视频，需要重剪
        ("bilibili", "kuaishou"):    0.25,
        ("douyin", "bilibili"):      0.08,  # 竖版可直接发B站动态，适配成本低
        ("douyin", "kuaishou"):      0.05,  # 抖音→快手适配成本最低
        ("kuaishou", "douyin"):      0.05,
        ("kuaishou", "bilibili"):    0.10,
        # 跨格式
        ("any", "xiaohongshu"):      0.35,  # 需要适配小红书的图文+短视频风格
        ("any", "weibo"):            0.12,  # 微博图文适配
        ("any", "wechat_video"):     0.10,  # 微信视频号
    }

    # 规模折扣（总平台数越多，折扣越深，但有底线）
    VOLUME_DISCOUNTS = {
        2: 0.92,   # 2个平台总价打92折
        3: 0.85,   # 3个平台打85折
        4: 0.80,   # 4个平台打80折（封底）
    }

    total_base = sum(single_platform_prices.values())
    
    # 计算适配成本
    primary_platform = max(single_platform_prices, key=single_platform_prices.get)
    adaptation_total = 0
    for p in platforms:
        if p != primary_platform:
            key = (primary_platform, p)
            rate = ADAPTATION_COSTS.get(key, ADAPTATION_COSTS.get(("any", p), 0.15))
            adaptation_total += single_platform_prices[primary_platform] * rate

    # 应用规模折扣
    n = min(len(platforms), 4)
    discount = VOLUME_DISCOUNTS.get(n, 0.80)

    final_price = (total_base + adaptation_total) * discount

    return {
        "total_price": round(final_price),
        "breakdown": {
            "base_sum": total_base,
            "adaptation_cost": round(adaptation_total),
            "volume_discount": f"{(1-discount)*100:.0f}%",
        },
        "per_platform": {p: round(single_platform_prices[p] * discount) for p in platforms},
    }
```

### 7.3 MCN机构抽成参考

MCN机构抽成参考表详见本方案附录 F。

### 7.4 竞品对标分析

```python
COMPETITOR_LANDSCAPE_CN = {
    "existing_tools": {
        "蝉妈妈": {
            "coverage": "抖音为主，快手部分覆盖",
            "pricing_feature": "有达人报价参考功能，基于历史数据",
            "strengths": "数据量大、抖音生态深耕",
            "weaknesses": "报价建议较粗糙（仅区间），无谈判策略",
            "pricing": "付费工具，¥几百-几千/月",
        },
        "新榜": {
            "coverage": "全平台覆盖（微信、抖音、B站、快手等）",
            "pricing_feature": "有商业报价估算，数据维度较全",
            "strengths": "覆盖面广、品牌信任度高",
            "weaknesses": "报价估算基于简单模型，无对抗辩论机制",
            "pricing": "付费",
        },
        "飞瓜数据": {
            "coverage": "抖音+快手",
            "pricing_feature": "有达人对比和报价区间",
            "strengths": "直播带货数据强",
            "weaknesses": "B站覆盖弱",
        },
        "花火/星图/磁力聚星（官方平台）": {
            "coverage": "各自平台",
            "pricing_feature": "有系统建议价",
            "strengths": "官方数据最准",
            "weaknesses": "仅覆盖入驻达人，建议价往往偏低（平台有压价动机）",
        },
    },
    "our_differentiation": {
        "1_multi_agent_debate": "对抗辩论机制是核心差异化 — 市面工具都只给一个数字，我们给出Bull/Bear双视角+裁判综合",
        "2_contract_risk_detection": "合同红线检测+广告法合规 — 竞品都不做",
        "3_negotiation_strategy": "谈判话术+打包方案生成 — 竞品都不做",
        "4_cross_platform": "跨平台统一定价框架 — 竞品各做各平台",
        "5_confidence_scoring": "置信度评分+数据质量标记 — 竞品给一个数字不说可信度",
    }
}
```

### 7.5 平台扩展路线图

```python
PLATFORM_EXPANSION_ROADMAP = {
    "phase_1_mvp": {
        "platforms": ["bilibili", "douyin", "kuaishou"],
        "rationale": "国内三大短视频/中视频平台，覆盖最核心的品牌合作场景",
    },
    "phase_2_expansion": {
        "xiaohongshu": {
            "priority": "高",
            "rationale": "小红书是国内最重要的种草平台，品牌投放预算快速增长",
            "key_differences": [
                "以图文笔记为主，短视频为辅（与其他平台相反）",
                "CPM通常按'笔记'而非'视频'计价",
                "蒲公英平台（官方撮合）抽成约10%",
                "互动率计算：(点赞+收藏+评论) / 曝光量",
                "小红书的'收藏率'是最强的商业价值信号（用户收藏=有购买意向）",
            ],
            "estimated_effort": "新增CPM表+交付物乘数表，约2-3天",
        },
        "wechat_video_channel": {
            "priority": "中",
            "rationale": "微信视频号增长快，但商业化体系尚不成熟",
            "key_differences": [
                "强社交裂变，但品牌合作模式仍在摸索中",
                "暂无成熟的官方撮合平台",
                "CPM数据非常有限，初期置信度会很低",
            ],
            "estimated_effort": "约3-5天（数据获取是最大挑战）",
        },
        "weibo": {
            "priority": "低",
            "rationale": "微博商业化成熟但增长放缓，品牌KOL投放预算在向短视频转移",
            "estimated_effort": "约2天",
        },
    },
}
```

---

## 八、置信度评分体系

```python
def calculate_final_confidence(agent_outputs):
    """
    最终报告置信度 = 各维度置信度的加权平均
    """
    weights = {
        "data_completeness": 0.30,   # 输入数据完整度
        "cpm_table_confidence": 0.20, # CPM基准表的置信度
        "historical_consistency": 0.20,# 与历史成交价的一致性
        "debate_convergence": 0.15,   # 辩论收敛程度
        "market_data_freshness": 0.15, # 市场数据时效性
    }

    scores = {}

    # 数据完整度
    required_fields = ["followers", "avg_views", "engagement_rate", "niche"]
    optional_fields = ["city_tier", "growth_rate", "platform_signals", "audience_age"]
    filled_required = sum(1 for f in required_fields if agent_outputs.get(f) is not None)
    filled_optional = sum(1 for f in optional_fields if agent_outputs.get(f) is not None)
    scores["data_completeness"] = (filled_required / len(required_fields)) * 0.7 + \
                                   (filled_optional / len(optional_fields)) * 0.3

    # CPM表置信度
    cpm_conf = agent_outputs.get("cpm_confidence", "medium")
    scores["cpm_table_confidence"] = {"high": 0.9, "medium": 0.6, "low": 0.3}[cpm_conf]

    # 历史一致性（如果有历史成交价）
    if agent_outputs.get("historical_deals"):
        deviation = agent_outputs.get("historical_deviation_pct", 0)
        if deviation < 20:
            scores["historical_consistency"] = 0.9
        elif deviation < 40:
            scores["historical_consistency"] = 0.6
        else:
            scores["historical_consistency"] = 0.3
    else:
        scores["historical_consistency"] = 0.5  # 无历史数据，中性

    # 辩论收敛
    if agent_outputs.get("debate_results"):
        bull_bear_gap = agent_outputs["debate_gap_pct"]
        if bull_bear_gap < 30:
            scores["debate_convergence"] = 0.9
        elif bull_bear_gap < 60:
            scores["debate_convergence"] = 0.6
        elif bull_bear_gap < 100:
            scores["debate_convergence"] = 0.4
        else:
            scores["debate_convergence"] = 0.2
    else:
        scores["debate_convergence"] = 0.5

    # 市场数据时效性
    scores["market_data_freshness"] = 0.7  # 默认中等（每季度校准后可提升）

    final = sum(scores[k] * weights[k] for k in weights)
    return round(final, 2)
```

---

## 九、实施优先级

### Phase 1（MVP，3-5天）
- [ ] Agent A 国内版：CPM表（含置信度标注）、修正因子（含封顶机制）、粉丝播放比、层级分类
- [ ] Agent D 基本版：中文报告生成（含税务提醒、走平台/私下双报价）
- [ ] 快速通道：A → D
- [ ] 用户输入表单（含历史成交价可选字段）
- [ ] 前端展示

### Phase 2（核心功能，5-8天）
- [ ] Agent B：交付物乘数、使用权溢价、直播带货定价（坑位费交叉表+佣金）、打包方案
- [ ] Agent C：国内化Bull/Bear/Judge（含结构化数据引用Prompt）
- [ ] 完整通道：A||B → C → D
- [ ] 合同红线检测（含广告法、肖像权、数据安全等）
- [ ] 季节性完整矩阵
- [ ] 置信度评分体系

### Phase 3（增强，持续迭代）
- [ ] B站API对接（含wbi签名维护）
- [ ] 星图/花火公开报价抓取作为校准锚点
- [ ] 蝉妈妈/飞瓜API对接（如预算允许）
- [ ] 品牌库扩充到50+
- [ ] 跨平台打包定价工具
- [ ] MCN分成计算器
- [ ] 用户反馈→CPM校准闭环

### Phase 4（扩展平台）
- [ ] 小红书（优先级最高的扩展平台）
- [ ] 微信视频号
- [ ] 微博

---

## 十、验证标准

1. **合理性检验**：输出价格落在层级 typical_range 的 ±30% 内
2. **平台差异性**：同画像达人，B站报价 > 抖音 > 快手（一般规律）
3. **粉丝播放比敏感性**：vf_ratio 从 0.1 变为 0.5 应导致报价上浮 30-60%
4. **直播带货独立性**：直播报价使用独立的坑位费表，非视频报价的简单乘数
5. **使用权影响**：信息流投放授权应使报价上浮 30-90%
6. **季节性影响**：11月 vs 3月同一达人报价差异 20-50%
7. **走平台 vs 私下**：走星图报价 > 私下报价（覆盖平台抽成）
8. **垂类敏感性**：同10万粉，汽车类报价 ≈ 娱乐搞笑类的 3-5 倍
9. **广告法合规**：医疗/金融/教育品类自动触发合规提醒
10. **置信度校准**：完整数据→置信度>0.7，缺关键数据→置信度<0.5
11. **历史成交验证**：当有历史成交价时，系统报价偏差应 < 40%
12. **修正因子封顶**：极端输入（所有修正因子同方向叠加）不应导致报价超出层级范围 3 倍以上


---

## 附录

### 附录 A：频道层级分类表

```python
TIER_TABLE_CN = {
    "bilibili": {
        "素人/KOC":   {"min": 1000,    "max": 10000,   "typical_range": "¥200-¥2,000"},
        "小UP主":     {"min": 10000,   "max": 100000,  "typical_range": "¥1,000-¥15,000"},
        "中腰部UP主": {"min": 100000,  "max": 500000,  "typical_range": "¥5,000-¥80,000"},
        "头部UP主":   {"min": 500000,  "max": 2000000, "typical_range": "¥30,000-¥200,000"},
        "超头部UP主": {"min": 2000000, "max": None,    "typical_range": "¥100,000-¥500,000+"},
    },
    "douyin": {
        "素人/KOC":   {"min": 1000,    "max": 10000,    "typical_range": "¥100-¥800"},
        "小达人":     {"min": 10000,   "max": 100000,   "typical_range": "¥500-¥8,000"},
        "中腰部达人": {"min": 100000,  "max": 1000000,  "typical_range": "¥3,000-¥50,000"},
        "头部达人":   {"min": 1000000, "max": 5000000,  "typical_range": "¥20,000-¥150,000"},
        "超头部达人": {"min": 5000000, "max": None,     "typical_range": "¥80,000-¥500,000+"},
    },
    "kuaishou": {
        "素人/KOC":   {"min": 1000,    "max": 10000,    "typical_range": "¥80-¥500"},
        "小主播":     {"min": 10000,   "max": 100000,   "typical_range": "¥300-¥5,000"},
        "中腰部主播": {"min": 100000,  "max": 1000000,  "typical_range": "¥2,000-¥30,000"},
        "头部主播":   {"min": 1000000, "max": 5000000,  "typical_range": "¥15,000-¥100,000"},
        "超头部主播": {"min": 5000000, "max": None,     "typical_range": "¥50,000-¥300,000+"},
    }
}
```

### 附录 B：交付物类型定价乘数表

```python
DELIVERABLE_MULTIPLIERS_CN = {
    "bilibili": {
        "dedicated_video":     1.0,     # 定制视频/恰饭视频 → 基准
        "integrated_mention":  0.5,     # 视频中段植入
        "pre_roll_mention":    0.3,     # 片头口播
        "end_card_mention":    0.15,    # 片尾感谢/挂链接
        "dynamic_post":        0.1,     # 动态推广帖
        "column_article":      0.2,     # 专栏文章
        "livestream_collab":   0.6,     # 直播合作
        "pinned_comment":      0.03,    # 置顶评论
        "bilibili_story":      0.15,    # B站Story模式短视频
        "charging_video":      0.7,     # 充电专属视频里植入
    },
    "douyin": {
        "dedicated_video":     1.0,     # 定制短视频
        "integrated_mention":  0.5,     # 植入提及
        "series_3_posts":      2.5,     # 3条系列视频
        "series_5_posts":      4.0,     # 5条系列视频
        "livestream_mention":  0.4,     # 直播口播
        "livestream_sales_pit": 0.0,    # 直播带货坑位费（单独计算）
        "challenge_collab":    1.5,     # 参与品牌挑战赛
        "duet_video":          0.35,    # 合拍视频
        "product_showcase":    0.2,     # 商品橱窗挂链
        "search_seo_video":    0.8,     # 搜索SEO型内容
    },
    "kuaishou": {
        "dedicated_video":     1.0,     # 定制短视频
        "integrated_mention":  0.5,     # 植入提及
        "series_3_posts":      2.3,     # 3条系列
        "livestream_mention":  0.4,     # 直播口播
        "livestream_sales_pit": 0.0,    # 直播带货坑位费（单独计算）
        "quickshop_link":      0.15,    # 快手小店挂链
        "private_domain_push": 0.6,     # 粉丝群/私信推送
    }
}
```

### 附录 C：使用权与排他性溢价表

```python
USAGE_RIGHTS_PREMIUMS_CN = {
    "organic_only":             0.0,     # 仅达人自己平台发布
    "brand_repost_social_30d":  0.10,    # 品牌社交媒体转发30天
    "brand_repost_perpetual":   0.30,    # 品牌社交媒体永久转发
    "brand_ecommerce_page":     0.20,    # 品牌电商详情页使用（淘宝/京东/抖音商城）
    "brand_douyin_ad_boost":    0.25,    # 品牌用达人内容在抖音投Dou+或信息流广告
    "brand_ad_boost_30d":       0.35,    # 品牌用达人素材投放广告30天
    "brand_ad_boost_90d":       0.60,    # 90天广告素材使用权
    "brand_ad_boost_perpetual": 0.90,    # 永久广告素材使用权
    "offline_use":              0.40,    # 线下物料（门店、展会海报等）
    "tv_broadcast":             1.5,     # 电视广告
    "cross_platform_repost":    0.15,    # 跨平台搬运
    "secondary_creation_auth":  0.20,    # 允许品牌二次创作/剪辑
    "perpetual_all_media":      2.5,     # 所有媒介永久使用权
}

EXCLUSIVITY_PREMIUMS_CN = {
    "none":                   0.0,
    "category_30d":           0.20,    # 同品类排他30天
    "category_90d":           0.40,    # 同品类排他90天
    "category_6m":            0.65,    # 同品类排他6个月
    "category_12m":           0.90,    # 同品类排他12个月
    "full_exclusivity_30d":   0.40,    # 全品类排他30天
    "full_exclusivity_90d":   0.80,    # 全品类排他90天
    "competitor_brand_30d":   0.25,    # 指定竞品品牌排他30天
    "competitor_brand_90d":   0.50,    # 指定竞品品牌排他90天
    "platform_exclusivity":   0.30,    # 仅在该平台发布（不发其他平台）
}

# 总报价计算公式
# 总报价 = 基础价 × 交付物乘数 × (1 + 使用权溢价 + 排他性溢价)
```

### 附录 D：平台官方撮合系统信息

```python
OFFICIAL_PLATFORM_INFO = {
    "bilibili_huahuo": {
        "name": "B站花火平台",
        "url": "https://huahuo.bilibili.com",
        "platform_fee": "平台抽成约 5%-10%",
        "min_followers": 10000,
        "pricing_reference": "花火平台有官方报价参考，达人可自行调整",
        "advantage": "合同保障、数据透明、品牌信任度高",
        "disadvantage": "平台抽成、响应速度慢、灵活性差",
    },
    "douyin_xingtu": {
        "name": "抖音星图平台",
        "url": "https://www.xingtu.cn",
        "platform_fee": "平台抽成约 5%-15%（不同任务类型不同）",
        "min_followers": 10000,
        "pricing_reference": "星图有系统建议价，基于达人数据自动计算",
        "advantage": "流量加权（走星图的内容可能获得额外推荐）",
        "disadvantage": "抽成较高、内容审核更严格",
        "special_note": "不走星图的商业内容可能被限流",
    },
    "kuaishou_cili": {
        "name": "快手磁力聚星",
        "url": "https://juxing.kuaishou.com",
        "platform_fee": "平台抽成约 5%-10%",
        "min_followers": 5000,
        "pricing_reference": "磁力聚星有建议价",
        "advantage": "数据透明、合同保障",
        "disadvantage": "快手商业化体系相对抖音不够成熟",
    }
}

def calculate_platform_adjusted_price(base_price, platform, through_official):
    if through_official:
        fee_rates = {
            "bilibili_huahuo": 0.07,
            "douyin_xingtu": 0.10,
            "kuaishou_cili": 0.07,
        }
        fee_rate = fee_rates.get(platform, 0.10)
        brand_pays = base_price / (1 - fee_rate)
        creator_gets = base_price
        platform_takes = brand_pays - creator_gets
        return {
            "brand_total": round(brand_pays),
            "creator_receives": round(creator_gets),
            "platform_fee": round(platform_takes),
            "fee_rate": f"{fee_rate*100:.0f}%",
        }
    else:
        return {
            "brand_total": base_price,
            "creator_receives": base_price,
            "platform_fee": 0,
            "note": "私下合作无平台抽成，但需自行处理税务和合同"
        }
```

### 附录 E：打包方案生成逻辑

```python
def generate_package_tiers_cn(adjusted_price_mid, platform, deliverables):
    packages = {
        "trial": {
            "name": "试水合作",
            "price": adjusted_price_mid * 0.75,
            "includes": ["1条植入视频"],
            "duration": "一次性",
            "note": "适合品牌方首次合作试水"
        },
        "standard": {
            "name": "标准合作",
            "price": adjusted_price_mid * 2.0,
            "includes": ["3条植入视频", "1条动态/Story"],
            "duration": "2个月",
            "savings_vs_individual": "25%",
        },
        "deep": {
            "name": "深度合作",
            "price": adjusted_price_mid * 3.8,
            "includes": [
                "6条植入视频",
                "2条动态/Story",
                "品牌社交媒体转发权30天"
            ],
            "duration": "6个月",
            "savings_vs_individual": "30%",
        },
    }

    if platform in ["douyin", "kuaishou"]:
        packages["deep_with_livestream"] = {
            "name": "深度合作+直播带货",
            "price": adjusted_price_mid * 5.0,
            "includes": [
                "6条植入视频",
                "2场直播带货（含坑位）",
                "品牌广告素材使用权30天"
            ],
            "duration": "6个月",
            "savings_vs_individual": "35%",
            "note": "直播带货部分另附佣金协议"
        }

    return packages
```

### 附录 F：MCN机构抽成参考

```python
MCN_FEE_REFERENCE = {
    "typical_split": {
        "新人达人（<10万粉）": "MCN 50-70% : 达人 30-50%",
        "成长期达人（10-50万粉）": "MCN 40-60% : 达人 40-60%",
        "头部达人（50万粉+）": "MCN 20-40% : 达人 60-80%",
        "超头部/自有团队": "MCN 10-20% : 达人 80-90%",
    },
    "note": "如果达人签了MCN，系统建议报价应考虑MCN抽成，确保达人实际到手金额合理",
    "display_tip": "向用户展示：品牌支付总额 → 平台抽成 → MCN抽成 → 达人实际到手",
}
```

### 附录 G：谈判话术模板与报告展示模块

**报告展示结构**

报告应包含以下模块：
1. 报价建议表（锚定价/推荐价/底线价 + 走平台双报价）
2. 定价依据（可向品牌方展示的数据点）
3. 打包方案（试水/标准/深度，抖音快手追加直播带货选项）
4. 合同条款红线提醒
5. 谈判话术模板（4个场景）
6. 平台选择建议（跨平台合作时）
7. 税务提醒
8. 时机建议

**谈判话术模板**

场景A：品牌/MCN主动找你
> "感谢您的合作邀请！基于我的频道数据——互动率X%高于{垂类}平均、受众画像、增长趋势——我的{内容类型}标准报价是¥{锚定价}。如果有兴趣探讨长期合作，我也准备了套餐方案，性价比更高。"

场景B：你主动联系品牌
> "您好！我是{平台}{垂类}领域的创作者{名字}，注意到{品牌名}最近在{垂类}加大了投放力度。我的频道拥有{粉丝数}粉丝，互动率{X%}，是行业平均的{X倍}。很乐意以¥{推荐价}的费率为您定制一条{内容类型}。"

场景C：品牌说报价太高
> "理解预算考量。同层级达人在{平台}{垂类}的平均CPM是¥{X}-¥{Y}，基于我{Z}的平均播放量，市场公平价约¥{推荐价}。如果预算有限，我的入门套餐¥{入门价}也很适合试水合作。"

场景D：品牌要求走私下不走平台
> "我建议我们还是走{花火/星图/磁力聚星}。虽然会有X%平台服务费，但可以确保双方权益：合同保障、数据追踪、内容合规。走平台报价¥{平台报价}；私下合作报价¥{私下报价}，需另签合同。"

### 附录 H：广告法合规检测规则

```python
AD_LAW_COMPLIANCE_CHECKS = {
    "disclosure_requirement": {
        "rule": "商业推广内容必须标注'广告'或'推广'",
        "platforms": {
            "bilibili": "视频标题或简介需注明'推广'或'商业合作'",
            "douyin": "走星图会自动标注，私下合作需达人自行标注",
            "kuaishou": "走磁力聚星会自动标注",
        },
        "penalty": "未标注可能被平台限流或处罚，严重者违反广告法",
    },
    "prohibited_claims": {
        "rule": "不得使用'最佳''第一''国家级'等绝对化用语",
        "tip": "脚本中避免出现绝对化表述，用'之一''领先'等替代",
    },
    "category_restrictions": {
        "medical_health": "医疗、药品、保健品广告需特殊资质，达人需确认品牌方资质",
        "finance": "金融产品推广需持牌机构，达人需确认品牌合规性",
        "education": "教培行业受双减政策影响，K12阶段学科培训不得投放",
        "alcohol": "酒类广告不得出现在面向未成年人的内容中",
        "food_supplements": "保健品不得宣称治疗功效",
    },
    "minor_protection": {
        "rule": "面向未成年人的内容不得含有商业推广（各平台青少年模式限制）",
        "tip": "如果受众中未成年人比例高，某些品牌合作可能存在合规风险",
    },
}
```