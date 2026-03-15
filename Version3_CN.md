# KnowYourRate 国内版迁移方案 v2.0 — B站 / 抖音 / 快手

## 修订说明

本版本（v2.0）基于 v1.0 方案进行了以下系统性优化：

1. **修正因子共线性问题**：互动率与粉丝播放比存在统计相关性，v1.0 中两者独立计算会导致双重溢价/惩罚。v2.0 引入正交化处理，消除重复计价。
2. **直播带货模型细化**：区分专场直播与混场直播、纯佣金与坑位费+佣金模式，新增 GMV 保底条款建议。
3. **数据质量前置检查**：在 Agent A 之前增加数据预处理层（Data Validator），提前识别异常数据并降级处理。
4. **置信度体系升级**：引入"样本偏差修正"和"数据新鲜度衰减"机制。
5. **品牌库独立为外部数据文件**：便于持续维护和扩展，不再嵌入主方案。
6. **新增回测框架**：定义验证标准的量化回测方法。
7. **跨平台定价增加内容时长维度**：不同时长内容的跨平台适配成本差异显著。
8. **合同红线增加数据安全和肖像权条款**：已在 v1.0 基础上补充完善。
9. **新增"纯佣金模式"系统性处理逻辑**。
10. **新增小红书预研规格**：为 Phase 2 平台扩展提供详细技术规格。

---

## 项目概述

KnowYourRate 是一个帮助创作者计算品牌合作公平报价的多Agent AI系统。本方案将海外版（YouTube/TikTok）的架构和逻辑迁移到国内市场，覆盖 B站（哔哩哔哩）、抖音、快手三大平台。

**核心设计原则**：同框架、异参数、新逻辑。架构（Data Validator + 4 Agent + Router + Orchestrator）复用海外版骨架，但数据层（CPM表、修正因子、品牌库）、业务逻辑（直播带货、平台撮合系统、广告法合规）和输出层（中文报告、人民币计价）全部针对国内市场重写。

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
| 直播带货 | 较少见 | 核心变现方式之一，定价逻辑完全不同 |
| 税务 | 相对简单（1099） | 劳务报酬/个体户/公司三种模式，税率差异极大 |
| 合规 | FTC disclosure | 广告法合规+平台规则+行业特殊限制 |

---

## 一、整体架构

### 架构总览

v2.0 在 v1.0 的基础上新增了 **Data Validator（数据验证层）** 作为前置处理：

```
用户输入（频道链接 + 合作条件）
        │
   ┌────▼─────────┐
   │ Data Validator│ ← 【新增】数据质量前置检查
   │ (数据验证层)   │    异常检测 / 缺失标记 / 降级策略
   └────┬─────────┘
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

### Data Validator（数据验证层）【新增】

```python
def validate_input_data(user_input):
    """
    在任何Agent执行之前，先对用户输入进行质量检查。
    
    返回：
    - cleaned_data: 清洗后的数据
    - quality_report: 数据质量报告
    - degradation_level: 降级等级 ("full" / "partial" / "minimal")
    """
    quality_report = {
        "warnings": [],
        "errors": [],
        "missing_fields": [],
        "anomalies": [],
    }

    # === 1. 必填字段检查 ===
    required = ["platform", "followers"]
    for field in required:
        if field not in user_input or user_input[field] is None:
            quality_report["errors"].append(f"缺少必填字段: {field}")
    
    # === 2. 数值合理性检查 ===
    if user_input.get("followers", 0) < 500:
        quality_report["warnings"].append("粉丝数低于500，商业报价意义有限")
    
    if user_input.get("avg_views"):
        vf = user_input["avg_views"] / max(user_input.get("followers", 1), 1)
        if vf > 5.0:
            quality_report["anomalies"].append(
                f"粉丝播放比异常高({vf:.1f})，可能是病毒视频拉高均值，建议使用中位数播放量"
            )
        if vf < 0.01:
            quality_report["anomalies"].append(
                f"粉丝播放比极低({vf:.3f})，疑似大量僵尸粉"
            )
    
    if user_input.get("engagement_rate"):
        er = user_input["engagement_rate"]
        if er > 30:
            quality_report["anomalies"].append(
                f"互动率 {er}% 异常高，可能是计算口径问题或刷量"
            )
        if er < 0.1:
            quality_report["anomalies"].append(
                f"互动率 {er}% 极低，数据可能有误"
            )
    
    # === 3. 历史成交价一致性预检 ===
    if user_input.get("historical_deals"):
        prices = [d["price"] for d in user_input["historical_deals"]]
        if len(prices) >= 2:
            max_p, min_p = max(prices), min(prices)
            if min_p > 0 and max_p / min_p > 5:
                quality_report["warnings"].append(
                    f"历史成交价波动过大(最高{max_p} vs 最低{min_p})，"
                    f"可能包含不同类型的合作，请确认"
                )
    
    # === 4. 平台与垂类组合验证 ===
    platform = user_input.get("platform", "")
    niche = user_input.get("niche", "")
    if platform == "kuaishou" and niche == "anime_acg":
        quality_report["warnings"].append(
            "快手ACG/二次元类达人极少，CPM数据置信度很低"
        )
    
    # === 5. 确定降级等级 ===
    if quality_report["errors"]:
        degradation = "minimal"  # 只能给粗略估算
    elif len(quality_report["anomalies"]) >= 2 or len(quality_report["missing_fields"]) >= 3:
        degradation = "partial"  # 部分Agent降级运行
    else:
        degradation = "full"     # 全量分析

    return {
        "cleaned_data": user_input,  # 未来可加入自动修正逻辑
        "quality_report": quality_report,
        "degradation_level": degradation,
    }
```

### 路由器

```python
def route_request_cn(user_input, data_quality):
    """
    v2.0 改进：路由器同时考虑 合作复杂度 和 数据质量。
    数据质量差时，即使合作条件复杂，也可能降级到快速通道（因为完整分析的输入不足）。
    """
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
        complexity_score += 2

    # 注意：是否走官方平台（星图/花火）不计入复杂度
    # 它只影响报告展示（是否展示双价格），不影响分析深度

    # 【v2.0 新增】数据质量降级
    if data_quality["degradation_level"] == "minimal":
        return "fast_track"  # 数据太差，强制快速通道
    
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
    "health_supplements",    # 【新增】保健品（合规风险+高利润导致价格波动大）
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
    "median_views_last_30": 42000,
    "engagement_rate": 6.8,
    "niche": "tech_review",
    "top_audience_city_tier": "一线城市为主",
    "audience_city_distribution": {
      "tier_1": 35,
      "new_tier_1": 25,
      "tier_2": 20,
      "tier_3_below": 20
    },
    "audience_age_distribution": {
      "under_18": 5,
      "18_24": 35,
      "25_34": 40,
      "35_44": 15,
      "45_plus": 5
    },
    "channel_age_months": 30,
    "upload_frequency": "weekly",
    "platform_level": "LV5",
    "has_mcn": false,
    "mcn_name": null,
    "monthly_growth_rate": 3.5,
    "content_avg_duration_sec": 600
  },
  "historical_deals": [
    {"brand": "某3C品牌", "price": 5000, "type": "integrated_mention", "date": "2025-01", "platform": "bilibili"},
    {"brand": "某APP", "price": 8000, "type": "dedicated_video", "date": "2025-03", "platform": "bilibili"}
  ]
}
```

> **设计说明（v2.0 增强）**：
> 1. 新增 `median_views_last_30`（中位数播放量）—— 平均值容易被单条爆款拉高，中位数更能反映稳定表现。**当中位数与平均值偏差 > 50% 时，应使用中位数作为主要计算基准。**
> 2. 新增 `audience_age_distribution`（受众年龄分布）—— 18-34岁是品牌最看重的消费主力人群。
> 3. 新增 `content_avg_duration_sec`（平均内容时长）—— 影响跨平台适配成本和交付物乘数。
> 4. 历史成交价增加 `platform` 字段 —— 同一创作者在不同平台的报价可能差异很大。
> 5. 历史成交价是最强的定价锚点。当历史成交价与CPM计算结果偏差 > 40% 时，应标记 `data_conflict` 并降低置信度。

### 核心指标：粉丝播放比

```python
def calculate_core_metrics(channel_data, platform):
    """
    粉丝播放比 = avg_views / followers
    这是国内衡量达人商业价值的核心指标。
    
    v2.0 改进：
    - 当中位数播放量可用且与均值偏差>50%时，使用中位数
    - 增加"有效播放量"概念（抖音需扣除<3秒划过）
    """
    avg_views = channel_data["avg_views_last_30"]
    median_views = channel_data.get("median_views_last_30")
    
    # 选择更稳健的播放量基准
    if median_views and avg_views > 0:
        deviation = abs(avg_views - median_views) / avg_views
        if deviation > 0.5:
            effective_views = median_views  # 均值被爆款扭曲，用中位数
            view_basis = "median"
        else:
            effective_views = avg_views
            view_basis = "mean"
    else:
        effective_views = avg_views
        view_basis = "mean"
    
    # 抖音有效播放量修正（抖音播放量含大量<3秒划过）
    if platform == "douyin":
        effective_views = effective_views * 0.75  # 约25%为无效曝光
    
    vf_ratio = effective_views / max(channel_data["followers"], 1)

    VF_RATIO_BENCHMARKS = {
        "bilibili":  {"excellent": 0.5, "good": 0.25, "poor": 0.1},
        "douyin":    {"excellent": 0.3, "good": 0.15, "poor": 0.05},
        "kuaishou":  {"excellent": 0.35, "good": 0.2, "poor": 0.08},
    }
    bench = VF_RATIO_BENCHMARKS[platform]

    if vf_ratio >= bench["excellent"]:
        vf_modifier = 1.2
    elif vf_ratio >= bench["good"]:
        vf_modifier = 1.0 + 0.2 * (vf_ratio - bench["good"]) / (bench["excellent"] - bench["good"])
    elif vf_ratio >= bench["poor"]:
        vf_modifier = 0.7 + 0.3 * (vf_ratio - bench["poor"]) / (bench["good"] - bench["poor"])
    else:
        vf_modifier = 0.5
        # 触发 data_quality_flag: "low_vf_ratio_possible_fake_followers"

    return {
        "vf_ratio": vf_ratio,
        "vf_modifier": vf_modifier,
        "effective_views": effective_views,
        "view_basis": view_basis,
    }
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
#
# v2.0 新增：last_calibrated 字段，记录最后校准时间
# v2.0 新增：sample_size 字段，记录该数据点的样本量（0=推算）

NICHE_CPM_TABLE_CN = {
    "bilibili": {
        "finance_investing":    {"low": 40, "mid": 70,  "high": 120, "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1",
                                 "note": "B站财经区品牌预算高但供给少，头部溢价明显"},
        "technology":           {"low": 30, "mid": 50,  "high": 80,  "confidence": "high",
                                 "sample_size": 40, "last_calibrated": "2025-Q1",
                                 "note": "B站科技区商业化最成熟的分区之一，数据充足"},
        "gaming":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "high",
                                 "sample_size": 50, "last_calibrated": "2025-Q1",
                                 "note": "游戏是B站最大广告主品类，数据可靠"},
        "anime_acg":            {"low": 12, "mid": 25,  "high": 45,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1",
                                 "note": "二次元品牌广告主相对少但客单价高"},
        "beauty_skincare":      {"low": 20, "mid": 40,  "high": 65,  "confidence": "medium",
                                 "sample_size": 20, "last_calibrated": "2025-Q1"},
        "food_cooking":         {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium",
                                 "sample_size": 18, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 25, "mid": 45,  "high": 75,  "confidence": "high",
                                 "sample_size": 30, "last_calibrated": "2025-Q1",
                                 "note": "知识区商业价值仅次于科技区"},
        "health_fitness":       {"low": 20, "mid": 35,  "high": 55,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 35, "mid": 60,  "high": 100, "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1",
                                 "note": "车企预算充裕，头部UP主报价可达6位数"},
        "digital_3c":           {"low": 25, "mid": 45,  "high": 70,  "confidence": "high",
                                 "sample_size": 35, "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 18, "mid": 35,  "high": 55,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 15, "mid": 30,  "high": 50,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "travel":               {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "music_dance":          {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",
                                 "sample_size": 3,  "last_calibrated": "2025-Q1"},
        "entertainment_funny":  {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
    },
    "douyin": {
        "finance_investing":    {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1"},
        "technology":           {"low": 20, "mid": 38,  "high": 60,  "confidence": "medium",
                                 "sample_size": 18, "last_calibrated": "2025-Q1"},
        "gaming":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium",
                                 "sample_size": 20, "last_calibrated": "2025-Q1"},
        "beauty_skincare":      {"low": 25, "mid": 45,  "high": 70,  "confidence": "high",
                                 "sample_size": 50, "last_calibrated": "2025-Q1",
                                 "note": "抖音美妆是最成熟的商业化赛道，数据充足"},
        "food_cooking":         {"low": 12, "mid": 25,  "high": 40,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 20, "mid": 35,  "high": 60,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "health_fitness":       {"low": 15, "mid": 30,  "high": 50,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 20, "mid": 40,  "high": 65,  "confidence": "high",
                                 "sample_size": 35, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 30, "mid": 55,  "high": 90,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1"},
        "digital_3c":           {"low": 18, "mid": 35,  "high": 55,  "confidence": "medium",
                                 "sample_size": 18, "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 15, "mid": 28,  "high": 45,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 18, "mid": 32,  "high": 50,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "travel":               {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "music_dance":          {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "entertainment_funny":  {"low": 3,  "mid": 8,   "high": 15,  "confidence": "medium",
                                 "sample_size": 20, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "livestream_ecommerce": {"low": 5,  "mid": 12,  "high": 25,  "confidence": "low",
                                 "sample_size": 8,  "last_calibrated": "2025-Q1",
                                 "note": "带货类达人更看坑位费+佣金，CPM参考价值有限"},
    },
    "kuaishou": {
        "finance_investing":    {"low": 15, "mid": 30,  "high": 55,  "confidence": "low",
                                 "sample_size": 3,  "last_calibrated": "2025-Q1",
                                 "note": "快手财经类达人较少，数据有限"},
        "technology":           {"low": 10, "mid": 22,  "high": 40,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "gaming":               {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "beauty_skincare":      {"low": 12, "mid": 25,  "high": 42,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "food_cooking":         {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1"},
        "lifestyle_vlog":       {"low": 6,  "mid": 14,  "high": 25,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "education_knowledge":  {"low": 12, "mid": 22,  "high": 40,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "health_fitness":       {"low": 10, "mid": 20,  "high": 35,  "confidence": "low",
                                 "sample_size": 3,  "last_calibrated": "2025-Q1"},
        "fashion_ootd":         {"low": 10, "mid": 22,  "high": 38,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "automotive":           {"low": 18, "mid": 35,  "high": 60,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "digital_3c":           {"low": 10, "mid": 22,  "high": 38,  "confidence": "low",
                                 "sample_size": 5,  "last_calibrated": "2025-Q1"},
        "home_decoration":      {"low": 8,  "mid": 18,  "high": 30,  "confidence": "medium",
                                 "sample_size": 8,  "last_calibrated": "2025-Q1"},
        "parenting_family":     {"low": 12, "mid": 22,  "high": 38,  "confidence": "medium",
                                 "sample_size": 10, "last_calibrated": "2025-Q1"},
        "travel":               {"low": 8,  "mid": 18,  "high": 30,  "confidence": "low",
                                 "sample_size": 3,  "last_calibrated": "2025-Q1"},
        "agriculture_rural":    {"low": 5,  "mid": 12,  "high": 22,  "confidence": "medium",
                                 "sample_size": 12, "last_calibrated": "2025-Q1",
                                 "note": "快手特色赛道，带货转化率可能是最高的"},
        "entertainment_funny":  {"low": 3,  "mid": 6,   "high": 12,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
        "pets_animals":         {"low": 5,  "mid": 12,  "high": 22,  "confidence": "low",
                                 "sample_size": 3,  "last_calibrated": "2025-Q1"},
        "livestream_ecommerce": {"low": 3,  "mid": 8,   "high": 18,  "confidence": "medium",
                                 "sample_size": 15, "last_calibrated": "2025-Q1"},
    }
}

# CPM数据校准机制（v2.0 增强）
CPM_CALIBRATION = {
    "method": "用户反馈回收 + 数据新鲜度衰减",
    "freshness_decay": {
        "description": "CPM数据的可靠性随时间衰减",
        "decay_function": """
        freshness_factor = max(0.5, 1.0 - (months_since_calibration - 3) * 0.05)
        # 3个月内无衰减，之后每月衰减5%，最低0.5
        # 示例：校准后6个月 → freshness_factor = 0.85
        """,
        "impact": "freshness_factor 直接乘入 cpm_table_confidence 分数",
    },
    "process": """
    1. 用户使用系统获得报价建议
    2. 实际成交后，可选择性反馈真实成交价
    3. 系统收集足够样本（每个 平台×垂类×层级 至少10个）后更新CPM表
    4. 校准频率：每季度一次，大促后（双11/618）额外校准
    5. 【v2.0 新增】当某个组合的样本量<5时，使用贝叶斯先验（邻近垂类的CPM加权）
    """,
    "bayesian_prior": """
    当 sample_size < 5 时：
    posterior_cpm = (prior_cpm × prior_weight + observed_cpm × sample_size) / (prior_weight + sample_size)
    
    prior_cpm = 该平台所有垂类CPM的中位数
    prior_weight = 3（等效于3个样本的权重）
    """,
}
```

### 互动率标准化定义

```python
ENGAGEMENT_RATE_DEFINITIONS = {
    "bilibili": {
        "formula": "(点赞 + 投币 + 收藏 + 弹幕 + 评论) / 播放量 × 100%",
        "components": ["like", "coin", "favorite", "danmaku", "comment"],
        "niche_averages": {
            "technology":           5.0,
            "gaming":               6.0,
            "anime_acg":            7.0,
            "beauty_skincare":      4.5,
            "food_cooking":         5.5,
            "lifestyle_vlog":       4.0,
            "education_knowledge":  4.5,
            "finance_investing":    3.5,
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
            "livestream_ecommerce": 2.0,
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
            "agriculture_rural":    6.0,
            "travel":               3.5,
            "fashion_ootd":         3.5,
            "health_fitness":       3.5,
            "livestream_ecommerce": 2.5,
        },
        "note": "快手老铁文化下互动率偏高，尤其是评论区活跃度"
    }
}
```

### 修正因子系统（v2.0 正交化处理）

```python
def calculate_all_modifiers_cn(channel_data, platform, niche, current_date):
    """
    修正因子采用加法累积 + 封顶机制，避免乘法累积导致结果爆炸。
    
    v2.0 关键改进：修正因子正交化
    ----------------------------------
    问题：v1.0 中互动率修正和粉丝播放比修正存在共线性。
    高粉丝播放比的达人，互动率往往也高（因为分母相关）。
    两者独立计算会导致"优秀达人"被双重溢价，"差达人"被双重惩罚。
    
    解决方案：
    1. 计算粉丝播放比修正（反映内容触达效率）
    2. 计算互动率修正时，使用"相对于该粉丝播放比水平的预期互动率"作为基准
       而非直接使用垂类平均互动率
    3. 这样互动率修正只捕捉"超出/低于预期的互动质量"，
       而非重复计算"内容好→播放多→互动也多"
    
    总修正因子 = 1.0 + sum(各修正增量)
    封顶范围：总修正因子 ∈ [0.4, 2.0]
    """
    modifier_deltas = {}

    # ===== 1. 粉丝播放比修正（先算这个，作为互动率正交化的基础）=====
    core_metrics = calculate_core_metrics(channel_data, platform)
    vf_modifier = core_metrics["vf_modifier"]
    modifier_deltas["vf_ratio"] = vf_modifier - 1.0

    # ===== 2. 互动率修正（正交化处理）=====
    niche_avg_er = ENGAGEMENT_RATE_DEFINITIONS[platform]["niche_averages"].get(niche, 4.0)
    
    # 正交化：根据粉丝播放比水平调整互动率基准
    # 粉丝播放比高的达人，预期互动率也会偏高
    vf_ratio = core_metrics["vf_ratio"]
    VF_BENCH = {
        "bilibili":  0.3,
        "douyin":    0.15,
        "kuaishou":  0.2,
    }
    vf_deviation = (vf_ratio - VF_BENCH[platform]) / max(VF_BENCH[platform], 0.01)
    # vf_deviation > 0 说明播放比高于平均，互动率基准应上调
    adjusted_niche_avg_er = niche_avg_er * (1 + vf_deviation * 0.3)
    # 限制调整幅度
    adjusted_niche_avg_er = max(niche_avg_er * 0.6, min(niche_avg_er * 1.5, adjusted_niche_avg_er))
    
    ratio = channel_data["engagement_rate"] / adjusted_niche_avg_er

    if ratio < 0.5:
        modifier_deltas["engagement"] = -0.25  # v2.0：降低极端惩罚，因为部分已被vf_ratio捕捉
    elif ratio < 1.0:
        modifier_deltas["engagement"] = -0.12 + 0.12 * (ratio - 0.5) / 0.5
    elif ratio < 2.0:
        modifier_deltas["engagement"] = 0.0 + 0.20 * (ratio - 1.0) / 1.0
    else:
        modifier_deltas["engagement"] = 0.20  # v2.0：降低上限，避免与vf_ratio双重溢价

    # ===== 3. 受众城市线级修正 =====
    city_dist = channel_data.get("audience_city_distribution", None)
    if city_dist:
        city_value = (
            city_dist.get("tier_1", 0) * 1.0 +
            city_dist.get("new_tier_1", 0) * 0.8 +
            city_dist.get("tier_2", 0) * 0.5 +
            city_dist.get("tier_3_below", 0) * 0.2
        ) / 100

        if platform == "kuaishou":
            brand_targets_sinking_market = channel_data.get("brand_targets_sinking", False)
            if brand_targets_sinking_market:
                city_value = 1.0 - city_value + 0.2
                modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
                modifier_deltas["city_tier_note"] = "快手下沉市场优势：品牌目标与受众匹配"
            else:
                modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
        else:
            modifier_deltas["city_tier"] = (city_value - 0.5) * 0.4
    else:
        modifier_deltas["city_tier"] = 0.0

    # ===== 4. 受众年龄修正【v2.0 新增】=====
    age_dist = channel_data.get("audience_age_distribution", None)
    if age_dist:
        # 18-34岁是品牌最看重的核心消费人群
        core_audience_pct = age_dist.get("18_24", 0) + age_dist.get("25_34", 0)
        if core_audience_pct > 70:
            modifier_deltas["audience_age"] = 0.10
        elif core_audience_pct > 50:
            modifier_deltas["audience_age"] = 0.05
        elif core_audience_pct < 30:
            modifier_deltas["audience_age"] = -0.10
        else:
            modifier_deltas["audience_age"] = 0.0
        
        # 未成年人比例高时额外警告
        if age_dist.get("under_18", 0) > 30:
            modifier_deltas["audience_age_warning"] = "未成年人受众占比>30%，部分品类（酒类、金融、游戏）不可合作"
    else:
        modifier_deltas["audience_age"] = 0.0

    # ===== 5. 增长动量修正 =====
    growth_rate = channel_data.get("monthly_growth_rate", 0)
    if growth_rate > 10:
        modifier_deltas["growth"] = 0.15
    elif growth_rate > 3:
        modifier_deltas["growth"] = 0.05 + 0.10 * (growth_rate - 3) / 7
    elif growth_rate >= 0:
        modifier_deltas["growth"] = 0.0
    else:
        modifier_deltas["growth"] = max(-0.15, growth_rate * 0.015)

    # ===== 6. 平台特有信号修正 =====
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
        revisit_rate = channel_data.get("revisit_rate", 0)
        live_to_follower = channel_data.get("live_viewer_follower_ratio", 0)
        if revisit_rate > 0.3:
            platform_signal_delta += 0.12
        elif revisit_rate > 0.15:
            platform_signal_delta += 0.06
        if live_to_follower > 0.05:
            platform_signal_delta += 0.08

    modifier_deltas["platform_signal"] = min(platform_signal_delta, 0.15)

    # ===== 7. 内容长尾效应修正 =====
    LONGEVITY_MODIFIERS = {
        "bilibili":  0.10,
        "douyin":    0.0,
        "kuaishou":  0.03,
    }
    modifier_deltas["content_longevity"] = LONGEVITY_MODIFIERS[platform]

    # ===== 8. 季节性修正 =====
    modifier_deltas["seasonal"] = calculate_seasonal_modifier_cn(current_date, niche) - 1.0

    # ===== 9. 频道稳定性修正【v2.0 新增】=====
    # 使用中位数与均值的偏差来衡量内容表现的稳定性
    # 品牌更偏好稳定的创作者（风险可控）
    avg_v = channel_data.get("avg_views_last_30", 0)
    med_v = channel_data.get("median_views_last_30", 0)
    if avg_v > 0 and med_v > 0:
        stability = med_v / avg_v  # 越接近1越稳定
        if stability > 0.85:
            modifier_deltas["stability"] = 0.05  # 非常稳定
        elif stability > 0.6:
            modifier_deltas["stability"] = 0.0
        else:
            modifier_deltas["stability"] = -0.08  # 波动大
    else:
        modifier_deltas["stability"] = 0.0

    # ===== 合计并封顶 =====
    total_delta = sum(v for k, v in modifier_deltas.items() if isinstance(v, (int, float)))
    total_modifier = 1.0 + total_delta
    total_modifier = max(0.4, min(2.0, total_modifier))

    return {
        "modifier_details": modifier_deltas,
        "total_modifier": round(total_modifier, 3),
        "orthogonalization_applied": True,  # v2.0 标记
    }
```

### 季节性乘数完整矩阵

```python
SEASONAL_MATRIX_CN = {
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
    },
    # 【v2.0 新增】春节浮动处理
    "chinese_new_year_handling": """
    春节日期每年不同（通常在1月下旬-2月中旬），需要动态调整：
    - 春节前2周：年货节旺季，ecommerce_all 额外 +0.15
    - 春节期间（7天假期）：品牌投放基本停止，实际承接需求极少
    - 春节后1周：恢复正常
    
    实现方式：在 calculate_seasonal_modifier_cn 中引入 chinese_new_year_date 参数，
    动态调整1-2月的乘数。
    """
}

def calculate_seasonal_modifier_cn(current_date, niche):
    month = current_date.month
    for group_name, niches in SEASONAL_MATRIX_CN["category_groups"].items():
        if niche in niches:
            return SEASONAL_MATRIX_CN["monthly_multipliers"][group_name][month - 1]
    return 1.0
```

### 频道层级分类

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

---

## 三、Agent B — 市场情报 Agent

### 交付物类型定价乘数表

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
        "livestream_sales_pit": 0.0,    # 直播带货坑位费（单独计算，见下方独立模块）
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

### 直播带货定价模型（v2.0 重构）

```python
# v2.0 重构说明：
# 1. 区分专场直播和混场直播（价格差异2-5倍）
# 2. 增加"纯佣金模式"的系统性处理
# 3. GMV保底条款建议
# 4. 退货率按品类细化

# === 直播形式分类 ===
LIVESTREAM_TYPES = {
    "exclusive_session": {
        "name": "专场直播",
        "description": "整场直播只推一个品牌/产品线",
        "pit_fee_multiplier": 3.0,  # 相对混场坑位费的倍数
        "typical_duration": "2-4小时",
        "note": "品牌独占达人流量，坑位费最高但转化率也最好",
    },
    "mixed_session": {
        "name": "混场直播",
        "description": "一场直播推多个品牌的商品",
        "pit_fee_multiplier": 1.0,  # 基准
        "typical_duration": "4-8小时（单品展示15-30分钟）",
        "note": "最常见的合作形式",
    },
    "short_mention": {
        "name": "直播口播",
        "description": "直播中简短提及品牌（不带购物车）",
        "pit_fee_multiplier": 0.3,
        "typical_duration": "3-5分钟",
        "note": "品牌曝光为主，非带货导向",
    },
}

# === 坑位费交叉表（混场直播基准）===
LIVESTREAM_PIT_FEE_TABLE = {
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

# === 佣金率表 ===
COMMISSION_RATE_TABLE = {
    "beauty_skincare":    {"rate": "20%-40%", "avg": 0.30, "note": "客单价<100效果最佳"},
    "food":               {"rate": "15%-30%", "avg": 0.22, "note": "复购率高是优势"},
    "fashion":            {"rate": "20%-35%", "avg": 0.28, "note": "退货率高（30-50%），实际佣金需打折"},
    "digital_3c":         {"rate": "5%-15%",  "avg": 0.10, "note": "客单价高但转化率低"},
    "home_goods":         {"rate": "15%-25%", "avg": 0.20, "note": "家居决策周期长，效果延迟"},
    "health_supplements": {"rate": "25%-50%", "avg": 0.35, "note": "高利润品类，佣金空间大"},
}

# === 纯佣金模式处理逻辑【v2.0 新增】===
COMMISSION_ONLY_MODEL = {
    "description": """
    纯佣金模式（零坑位费）意味着达人承担了全部风险。
    系统应该：
    1. 计算达人的期望收益 = 预估GMV × 佣金率
    2. 与"坑位费+佣金"模式下达人的预期总收入对比
    3. 如果纯佣金模式下期望收益 < 坑位费模式收入的70%，建议达人拒绝纯佣金
    4. 明确提示：品牌要求纯佣金 = 品牌不愿意为达人的流量买单 = 品牌认为达人的商业价值有限
    """,
    "acceptable_scenarios": [
        "品牌产品客单价高(>¥300)且转化率有历史数据支撑",
        "达人自己也想试水该品类（作为测试数据积累）",
        "品牌承诺提供独家优惠价/赠品（提升转化率）",
    ],
    "warning_scenarios": [
        "品牌产品无历史销售数据",
        "品牌不提供样品或运费补贴",
        "品牌要求达人承担退货成本",
    ],
    "gmv_guarantee_suggestion": """
    如果达人接受纯佣金，强烈建议加入GMV保底条款：
    - 品牌保证提供足够的库存
    - 品牌不得在直播期间调价
    - 如果实际GMV低于预估的50%，品牌补偿差额的部分佣金
    """,
}

# === 直播带货ROI预估 ===
LIVESTREAM_ROI_MODEL = {
    "conversion_rate_by_tier": {
        "超头部": {"low": 0.05, "mid": 0.10, "high": 0.15},
        "头部":   {"low": 0.03, "mid": 0.06, "high": 0.10},
        "中腰部": {"low": 0.02, "mid": 0.04, "high": 0.06},
        "小达人": {"low": 0.01, "mid": 0.02, "high": 0.04},
    },
    "refund_rate_by_category": {
        "fashion":          {"rate": 0.40, "range": "30%-50%", "note": "服装是退货重灾区"},
        "beauty_skincare":  {"rate": 0.15, "range": "10%-20%"},
        "food":             {"rate": 0.08, "range": "5%-10%", "note": "生鲜/冷链较高"},
        "digital_3c":       {"rate": 0.12, "range": "8%-15%"},
        "home_goods":       {"rate": 0.20, "range": "15%-25%"},
        "health_supplements":{"rate": 0.10, "range": "8%-12%"},
    },
    "effective_roi_formula": """
    实际ROI = (GMV × (1 - 退货率) × 利润率 - 坑位费 - GMV × (1-退货率) × 佣金率) / (坑位费 + GMV × (1-退货率) × 佣金率)
    
    示例：某美妆品客单价¥89，达人GMV ¥50,000
    退货率15%，利润率60%
    坑位费 ¥15,000 + 佣金25%
    
    有效销售额 = 50000 × (1-0.15) = ¥42,500
    品牌利润   = 42,500 × 0.60 = ¥25,500
    佣金支出   = 42,500 × 0.25 = ¥10,625
    总投入     = 15,000 + 10,625 = ¥25,625
    净利润     = 25,500 - 25,625 = -¥125（亏损！）
    ROI        = -125 / 25,625 = -0.5%
    
    → 品牌需要仔细计算ROI，而非只看GMV数字
    → 达人在谈判时如果能帮品牌算清楚ROI，反而能增加信任和合作机会
    """,
}
```

### 使用权/排他性溢价

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
    "category_30d":           0.20,
    "category_90d":           0.40,
    "category_6m":            0.65,
    "category_12m":           0.90,
    "full_exclusivity_30d":   0.40,
    "full_exclusivity_90d":   0.80,
    "competitor_brand_30d":   0.25,
    "competitor_brand_90d":   0.50,
    "platform_exclusivity":   0.30,
}

# 总报价计算公式
# 总报价 = 基础价 × 交付物乘数 × (1 + 使用权溢价 + 排他性溢价)
```

### 平台官方撮合系统

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

### 打包方案生成逻辑

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

    # 【v2.0 新增】年框合作
    packages["annual_framework"] = {
        "name": "年框合作",
        "price": adjusted_price_mid * 8.0,
        "includes": [
            "12条视频（每月1条，灵活安排）",
            "品牌社交媒体转发权全年",
            "品类排他90天"
        ],
        "duration": "12个月",
        "savings_vs_individual": "40%",
        "note": "年框对达人意味着稳定收入，对品牌意味着最优单价。适合已有成功合作经验的品牌。"
    }

    return packages
```

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
   论证思路：如果互动率高于垂类平均，量化额外互动数 = (互动率差值/100) × 平均播放量

2.【受众质量】
   引用数据：creator_profile.audience_city_tier 和 audience_age_distribution
   论证思路：
   - 一线城市用户获客成本¥50-¥200，通过该达人触达的CPM仅¥XX
   - 18-34岁核心消费人群占比XX%，高于行业均值
   - B站特有：引用 coin_rate，论证投币代表强购买意向信号

3.【粉丝播放比】
   引用数据：creator_profile.vf_ratio
   论证思路：如果粉丝播放比优秀，说明实际触达有效性远高于账面数字

4.【内容稳定性】（v2.0 新增）
   引用数据：creator_profile.median_views vs avg_views
   论证思路：如果中位数接近均值，说明内容表现稳定，品牌风险低

5.【增长溢价】
   引用数据：creator_profile.growth_trend 和 monthly_growth_rate
   论证思路：按当前增长率，N个月后报价将上涨约X%，现在合作性价比最高

6.【使用权价值】
   引用数据：deal_conditions.usage_rights
   论证思路：信息流投放权的替代成本（品牌自行拍摄广告素材约¥5,000-¥50,000）

7.【内容长尾】（仅B站）
   论证思路：B站内容长尾效应6-12个月，等效CPM远低于账面

8.【季节性时机】
   引用数据：seasonal_modifier
   论证思路：旺季档期紧张，理应溢价

请输出JSON格式：
{
  "suggested_price": 具体数字(CNY),
  "arguments": [
    {"point": "论据标题", "data_reference": "引用的具体数据", "reasoning": "推理逻辑", "impact_pct": "+X%"}
  ],
  "preemptive_rebuttals": ["对可能反驳的预判"],
  "confidence_in_own_estimate": 0.0-1.0
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

请严格基于以下数据进行论证：

1.【市场供给】
   引用数据：creator_profile.tier 和 niche
   论证思路：该平台该垂类该层级达人数量充足，品牌有替代选择

2.【ROI反算】
   引用数据：base_price_range.mid 和 creator_profile.avg_views
   论证思路：品牌CPA目标¥50 → 需要的转化数 → 以行业转化率反算合理报价

3.【播放量波动风险】
   引用数据：creator_profile.avg_views vs median_views（v2.0 新增）
   论证思路：
   - 如果均值>>中位数，说明依赖爆款，品牌承担下行风险
   - 抖音算法波动可能导致某条视频仅为平均的20-30%
   - 建议保底播放量条款

4.【可比基准】
   引用数据：market_context.comparable_deals / 星图花火建议价
   论证思路：同层级达人在官方平台的平均报价作为锚点

5.【长期合作折扣】
   论证思路：季度/年度框架可使单次费率下调30-50%

6.【直播带货实际ROI】（如涉及）
   引用数据：LIVESTREAM_ROI_MODEL + 退货率
   论证思路：GMV ≠ 利润，计算退货、佣金、坑位费后的实际ROI

7.【隐性成本】
   论证思路：brief制作、内容审核、沟通成本也应计入品牌总投入

8.【受众重合度风险】（v2.0 新增）
   论证思路：如果品牌同时投放多个同垂类达人，受众重合度可能导致CPM虚高

请输出JSON格式：
{
  "suggested_price": 具体数字(CNY),
  "arguments": [
    {"point": "论据标题", "data_reference": "引用的具体数据", "reasoning": "推理逻辑", "impact_pct": "-X%"}
  ],
  "counter_arguments": ["对看多方可能论据的反驳"],
  "confidence_in_own_estimate": 0.0-1.0
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

2.【共识区域】识别双方在哪些点上实际达成了共识

3.【最终报价区间】综合双方论据，给出三档报价：
   - walk_away（底线价）：低于此价达人应拒绝合作
   - fair_market（公平市场价）：综合双方论据的中间值
   - anchor_price（锚定价）：达人开口报价，通常比 fair_market 高 25-35%

4.【走平台/私下双报价】（如适用）
   - 走平台报价 = fair_market / (1 - 平台抽成率)
   - 私下合作报价 = fair_market

5.【置信度评分】0-1 之间，考虑：
   - 数据完整度
   - CPM基准表的置信度
   - 历史成交价一致性
   - 辩论收敛性（Bull和Bear差距>100%则大幅降低）

6.【高不确定性标记】如果 Bull 和 Bear 差距超过 80%，标记为高不确定性，
   建议达人"先要求品牌给出预算范围，再基于此谈判"

7.【价格锚定策略建议】（v2.0 新增）
   基于Bull/Bear差距和市场数据，建议达人选择：
   - "高开策略"：当数据强势且有历史成交支撑时，锚定价上浮30%
   - "市场价策略"：当数据一般或首次合作时，直接报fair_market
   - "竞争策略"：当品牌有多个备选达人时，报fair_market下浮10%吸引合作

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
  "pricing_strategy_recommendation": "高开/市场价/竞争 + 原因",
  "judge_notes": "200字以内的综合分析"
}
```

---

## 五、Agent D — 策略报告

### 合同红线检测规则

```python
CONTRACT_RED_FLAGS_CN = {
    # === 核心红线（🚫 强烈建议拒绝或要求修改）===
    "perpetual_rights_no_premium":
        "永久使用权但未加价 → 🚫 强烈建议拒绝或加价200-300%",
    "ad_boost_rights_hidden":
        "品牌要求拿内容投信息流广告（Dou+/巨量引擎）但合同未明确 → 🚫 必须单独约定并加价",
    "content_ownership_transfer":
        "要求转让内容所有权 → 🚫 改为授权使用，保留所有权",
    "portrait_rights_perpetual":
        "品牌要求永久使用达人肖像/形象 → 🚫 肖像权授权必须有明确期限和范围，永久授权至少加价100%",
    "data_sharing_forced":
        "要求达人提供后台数据截图/账号密码 → 🚫 绝不提供账号密码，数据截图需脱敏",
    "forced_positive_review":
        "合同要求必须给好评/不能提缺点 → 🚫 违反广告法真实性要求",
    
    # === 重要警告（⚠️ 需要特别注意并协商）===
    "unlimited_revisions":
        "无限修改轮次 → ⚠️ 限制为2轮，第3轮起按原价20%收费",
    "full_exclusivity_no_premium":
        "全品类排他但未额外补偿 → ⚠️ 至少加价50-100%",
    "payment_after_publish":
        "发布后才付款 → ⚠️ 要求50%预付，发布后7天内付尾款",
    "payment_net_60_plus":
        "付款周期超过60天 → ⚠️ 缩短至30天或加收账期费用",
    "no_off_platform_clause":
        "禁止在其他平台发类似内容 → ⚠️ 确认排他范围",
    "vague_deliverables":
        "交付物描述模糊（如'若干条视频'）→ ⚠️ 必须明确数量、时长、格式",
    "no_kill_fee":
        "无终止费条款 → ⚠️ 加入终止费（合同金额的25-50%）",
    "livestream_no_refund_clause":
        "直播带货合同无退货成本分担条款 → ⚠️ 明确退货成本由谁承担",
    "no_ad_disclosure":
        "合同未要求标注广告 → ⚠️ 广告法规定必须标注'广告'或'推广'",
    "cross_platform_hidden":
        "合同包含跨平台发布但未额外计价 → ⚠️ 每个平台应单独计价",
    "derivative_works_unlimited":
        "允许品牌对内容进行无限二次创作/改编 → ⚠️ 应限定二创范围并保留审核权",
    "penalty_clause_one_sided":
        "合同只有达人的违约金条款，品牌方无对等约束 → ⚠️ 要求加入品牌方违约条款",
    "no_minimum_guarantee_livestream":
        "直播带货合同无最低保底条款 → ⚠️ 如果品牌要求纯佣金，达人承担全部风险",

    # === v2.0 新增 ===
    "ai_training_rights_hidden":
        "品牌方将达人内容用于AI模型训练但合同未明确 → ⚠️ 近年AI训练数据争议增多，建议明确排除或单独定价",
    "content_modification_no_approval":
        "品牌可修改达人内容且不需要达人审核 → ⚠️ 修改后的内容仍挂达人名字，品质风险极大",
    "backdated_exclusivity":
        "排他条款追溯到合同签署之前的合作 → 🚫 不合理，应仅从合同生效日起算",
    "gmv_guarantee_on_creator":
        "合同要求达人对GMV负责（如未达标需退款） → 🚫 达人不应为销售结果兜底",
}
```

### 报告结构中的税务模块

```python
TAX_ESTIMATION_CN = {
    "劳务报酬（个人直接收款）": {
        "description": "最常见的达人收入方式，按劳务报酬所得纳税",
        "tax_brackets": [
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

### 报告展示结构与谈判话术模板

**报告应包含以下模块（按顺序）：**

1. **一句话结论**（用户一眼看到答案）
2. **报价建议表**（锚定价/推荐价/底线价 + 走平台双报价）
3. **定价依据摘要**（可向品牌方展示的数据点）
4. **打包方案**（试水/标准/深度/年框，抖音快手追加直播带货选项）
5. **合同条款红线提醒**
6. **谈判话术模板**（4个场景，见下方）
7. **平台选择建议**（跨平台合作时）
8. **税务提醒**（到手金额对比表）
9. **时机建议**
10. **数据质量声明与置信度**（v2.0 新增：透明披露数据来源和可信度）

**谈判话术模板：**

场景A — 品牌/MCN主动找你：
> "感谢您的合作邀请！基于我的频道数据——互动率X%高于{垂类}平均、受众画像、增长趋势——我的{内容类型}标准报价是¥{锚定价}。如果有兴趣探讨长期合作，我也准备了套餐方案，性价比更高。"

场景B — 你主动联系品牌：
> "您好！我是{平台}{垂类}领域的创作者{名字}，注意到{品牌名}最近在{垂类}加大了投放力度。我的频道拥有{粉丝数}粉丝，互动率{X%}，是行业平均的{X倍}。很乐意以¥{推荐价}的费率为您定制一条{内容类型}。"

场景C — 品牌说报价太高：
> "理解预算考量。同层级达人在{平台}{垂类}的平均CPM是¥{X}-¥{Y}，基于我{Z}的平均播放量，市场公平价约¥{推荐价}。如果预算有限，我的入门套餐¥{入门价}也很适合试水合作。"

场景D — 品牌要求走私下不走平台：
> "我建议我们还是走{花火/星图/磁力聚星}。虽然会有X%平台服务费，但可以确保双方权益：合同保障、数据追踪、内容合规。走平台报价¥{平台报价}；私下合作报价¥{私下报价}，需另签合同。"

---

## 六、数据获取

```python
# === B站数据 ===
bilibili_data_sources = {
    "public_api_no_auth": {
        "user_info": {
            "endpoint": "api.bilibili.com/x/space/wbi/acc/info",
            "returns": "粉丝数、等级、头像、简介",
            "limit": "无需cookie，但需要wbi签名（anti-spam）",
            "reliability": "medium（需定期更新签名算法）",
        },
    },
    "public_api_need_cookie": {
        "video_list": {
            "endpoint": "api.bilibili.com/x/space/wbi/arc/search",
            "returns": "视频列表（标题、播放量、发布时间）",
            "limit": "需要cookie",
        },
        "video_stat": {
            "endpoint": "api.bilibili.com/x/web-interface/view",
            "returns": "单个视频的详细数据（播放/点赞/投币/收藏/弹幕数）",
            "limit": "需要cookie才能获取完整数据",
        },
    },
    "not_available": {
        "audience_demographics": "受众年龄/性别/地域分布 → 仅创作者后台可见",
        "watch_time": "平均观看时长/完播率 → 仅创作者后台可见",
        "revenue_data": "收入数据 → 仅创作者本人可见",
    },
    "recommended_approach": """
    1. 优先用公开API获取：粉丝数、视频列表、各视频播放/互动数据
    2. 计算得出：平均播放量、中位数播放量、互动率、投币率、收藏率、发布频率、增长趋势
    3. 用户手动补充：受众地域分布、年龄分布（从创作者后台截图或选择估算）
    4. 完全不可获取时：基于垂类和粉丝量级做默认估算，并在置信度中体现
    """,
    "third_party_alternatives": ["新榜B站版", "火烧云数据", "飞瓜B站版"],
}

# === 抖音数据 ===
douyin_data_sources = {
    "official_api": {
        "note": "抖音开放平台API主要面向企业号和服务商",
        "xingtu_public": "星图平台可查看入驻达人的公开报价和基础数据",
    },
    "data_acquisition_strategy": """
    1. 星图平台公开数据作为校准锚点
    2. 用户手动输入基础数据
    3. 用户选择性提供完播率、分享率
    4. 第三方API：蝉妈妈/飞瓜/新抖（付费）
    """,
    "xingtu_calibration": """
    当用户提供了星图建议价时，系统应将星图价格作为额外锚点。
    如果系统计算结果与星图建议价偏差 > 50%，应：
    1. 触发 data_conflict 标记
    2. 报告中同时展示两个参考价
    3. 解释差异原因
    """,
}

# === 快手数据 ===
kuaishou_data_sources = {
    "official_api": {
        "note": "快手开放平台有部分API，主要面向商家和服务商",
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
        "real_estate": "房地产广告不得含有升值承诺",
        "cosmetic_surgery": "医美广告限制多，部分平台禁止投放",
    },
    "minor_protection": {
        "rule": "面向未成年人的内容不得含有商业推广",
        "tip": "如果受众中未成年人比例高，某些品类合作存在合规风险",
    },
    # 【v2.0 新增】
    "ai_generated_content": {
        "rule": "如果使用AI生成的内容作为商业推广素材，需标注'AI生成'",
        "note": "这是新趋势，各平台规则仍在演进中，建议保守处理",
    },
}
```

### 7.2 跨平台合作定价

```python
def calculate_cross_platform_price(single_platform_prices, platforms, content_type, content_duration_sec=None):
    """
    v2.0 改进：加入内容时长维度
    长视频(>5min)跨平台适配成本远高于短视频(<60s)
    """
    # 基础适配成本
    ADAPTATION_COSTS_BASE = {
        ("bilibili", "douyin"):      0.25,
        ("bilibili", "kuaishou"):    0.25,
        ("douyin", "bilibili"):      0.08,
        ("douyin", "kuaishou"):      0.05,
        ("kuaishou", "douyin"):      0.05,
        ("kuaishou", "bilibili"):    0.10,
        ("any", "xiaohongshu"):      0.35,
        ("any", "weibo"):            0.12,
        ("any", "wechat_video"):     0.10,
    }

    # 时长修正：长视频重剪成本更高
    def duration_multiplier(duration_sec):
        if duration_sec is None:
            return 1.0
        if duration_sec < 60:
            return 0.7   # 短视频适配容易
        elif duration_sec < 300:
            return 1.0   # 中等时长，标准成本
        else:
            return 1.4   # 长视频重剪成本高

    dur_mult = duration_multiplier(content_duration_sec)

    # 规模折扣
    VOLUME_DISCOUNTS = {
        2: 0.92,
        3: 0.85,
        4: 0.80,
    }

    total_base = sum(single_platform_prices.values())
    
    primary_platform = max(single_platform_prices, key=single_platform_prices.get)
    adaptation_total = 0
    for p in platforms:
        if p != primary_platform:
            key = (primary_platform, p)
            rate = ADAPTATION_COSTS_BASE.get(key, ADAPTATION_COSTS_BASE.get(("any", p), 0.15))
            adaptation_total += single_platform_prices[primary_platform] * rate * dur_mult

    n = min(len(platforms), 4)
    discount = VOLUME_DISCOUNTS.get(n, 0.80)

    final_price = (total_base + adaptation_total) * discount

    return {
        "total_price": round(final_price),
        "breakdown": {
            "base_sum": total_base,
            "adaptation_cost": round(adaptation_total),
            "duration_multiplier": dur_mult,
            "volume_discount": f"{(1-discount)*100:.0f}%",
        },
        "per_platform": {p: round(single_platform_prices[p] * discount) for p in platforms},
    }
```

### 7.3 MCN机构抽成参考

```python
MCN_FEE_REFERENCE = {
    "typical_split": {
        "新人达人（<10万粉）": "MCN 50-70% : 达人 30-50%",
        "成长期达人（10-50万粉）": "MCN 40-60% : 达人 40-60%",
        "头部达人（50万粉+）": "MCN 20-40% : 达人 60-80%",
        "超头部/自有团队": "MCN 10-20% : 达人 80-90%",
    },
    "note": "如果达人签了MCN，系统建议报价应考虑MCN抽成，确保达人实际到手金额合理",
    "display_tip": "向用户展示：品牌支付总额 → 平台抽成 → MCN抽成 → 税费 → 达人实际到手",
    # 【v2.0 新增】
    "mcn_value_assessment": """
    MCN并非纯粹的成本。好的MCN带来：
    - 品牌资源对接（达人自己接不到的单）
    - 内容策划和拍摄支持
    - 合同和法律保障
    - 数据分析工具
    
    系统应提示：如果MCN能帮达人接到高于自行报价50%以上的单子，
    即使抽成40%，达人实际到手可能仍高于自行接单。
    """,
}
```

### 7.4 竞品对标分析

```python
COMPETITOR_LANDSCAPE_CN = {
    "existing_tools": {
        "蝉妈妈": {
            "coverage": "抖音为主，快手部分覆盖",
            "pricing_feature": "有达人报价参考功能",
            "strengths": "数据量大、抖音生态深耕",
            "weaknesses": "报价建议较粗糙，无谈判策略",
            "pricing": "¥几百-几千/月",
        },
        "新榜": {
            "coverage": "全平台覆盖",
            "pricing_feature": "有商业报价估算",
            "strengths": "覆盖面广、品牌信任度高",
            "weaknesses": "报价估算基于简单模型，无对抗辩论",
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
            "weaknesses": "仅覆盖入驻达人，建议价往往偏低",
        },
    },
    "our_differentiation": {
        "1_multi_agent_debate": "对抗辩论机制 — 给出Bull/Bear双视角+裁判综合",
        "2_contract_risk_detection": "合同红线检测+广告法合规",
        "3_negotiation_strategy": "谈判话术+打包方案生成",
        "4_cross_platform": "跨平台统一定价框架",
        "5_confidence_scoring": "置信度评分+数据质量标记",
        "6_livestream_roi": "【v2.0新增】直播带货ROI反算+纯佣金模式分析",
        "7_tax_comparison": "【v2.0新增】三种税务场景到手金额对比",
    }
}
```

### 7.5 平台扩展路线图

```python
PLATFORM_EXPANSION_ROADMAP = {
    "phase_1_mvp": {
        "platforms": ["bilibili", "douyin", "kuaishou"],
        "rationale": "国内三大短视频/中视频平台",
    },
    "phase_2_expansion": {
        "xiaohongshu": {
            "priority": "高",
            "rationale": "小红书是国内最重要的种草平台",
            "key_differences": [
                "以图文笔记为主，短视频为辅",
                "CPM通常按'笔记'而非'视频'计价",
                "蒲公英平台（官方撮合）抽成约10%",
                "互动率计算：(点赞+收藏+评论) / 曝光量",
                "收藏率是最强商业价值信号",
            ],
            "estimated_effort": "新增CPM表+交付物乘数表，约2-3天",
            # 【v2.0 新增】预研规格
            "pre_research_spec": {
                "cpm_ranges": {
                    "beauty_skincare": {"low": 30, "mid": 55, "high": 90},
                    "fashion_ootd": {"low": 25, "mid": 50, "high": 85},
                    "food_cooking": {"low": 15, "mid": 30, "high": 50},
                    "home_decoration": {"low": 20, "mid": 40, "high": 65},
                    "parenting_family": {"low": 20, "mid": 38, "high": 60},
                    "travel": {"low": 15, "mid": 30, "high": 55},
                },
                "deliverable_types": {
                    "image_note": 1.0,
                    "video_note": 1.3,
                    "collection_note": 0.6,
                    "live_mention": 0.3,
                },
                "engagement_formula": "(点赞+收藏+评论)/曝光量×100%",
                "key_metric": "收藏率（>5%为优秀）",
            },
        },
        "wechat_video_channel": {
            "priority": "中",
            "rationale": "微信视频号增长快，但商业化体系尚不成熟",
            "estimated_effort": "约3-5天",
        },
        "weibo": {
            "priority": "低",
            "rationale": "微博增长放缓",
            "estimated_effort": "约2天",
        },
    },
}
```

---

## 八、置信度评分体系（v2.0 增强）

```python
def calculate_final_confidence(agent_outputs, data_quality_report):
    """
    v2.0 改进：
    1. 引入数据新鲜度衰减
    2. 引入样本偏差修正
    3. 引入数据验证层的前置检查结果
    """
    weights = {
        "data_completeness": 0.25,
        "cpm_table_confidence": 0.20,
        "historical_consistency": 0.15,
        "debate_convergence": 0.15,
        "market_data_freshness": 0.10,
        "data_quality_precheck": 0.10,   # 【v2.0 新增】
        "sample_size_adequacy": 0.05,    # 【v2.0 新增】
    }

    scores = {}

    # 数据完整度
    required_fields = ["followers", "avg_views", "engagement_rate", "niche"]
    optional_fields = ["city_tier", "growth_rate", "platform_signals", "audience_age",
                       "median_views", "content_duration"]  # v2.0 新增字段
    filled_required = sum(1 for f in required_fields if agent_outputs.get(f) is not None)
    filled_optional = sum(1 for f in optional_fields if agent_outputs.get(f) is not None)
    scores["data_completeness"] = (filled_required / len(required_fields)) * 0.7 + \
                                   (filled_optional / len(optional_fields)) * 0.3

    # CPM表置信度（含新鲜度衰减）
    cpm_conf = agent_outputs.get("cpm_confidence", "medium")
    base_cpm_score = {"high": 0.9, "medium": 0.6, "low": 0.3}[cpm_conf]
    
    # 新鲜度衰减
    months_since_cal = agent_outputs.get("months_since_calibration", 3)
    freshness_factor = max(0.5, 1.0 - max(0, months_since_cal - 3) * 0.05)
    scores["cpm_table_confidence"] = base_cpm_score * freshness_factor

    # 历史一致性
    if agent_outputs.get("historical_deals"):
        deviation = agent_outputs.get("historical_deviation_pct", 0)
        if deviation < 20:
            scores["historical_consistency"] = 0.9
        elif deviation < 40:
            scores["historical_consistency"] = 0.6
        else:
            scores["historical_consistency"] = 0.3
    else:
        scores["historical_consistency"] = 0.5

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
    scores["market_data_freshness"] = 0.7 * freshness_factor

    # 【v2.0 新增】数据验证层结果
    if data_quality_report:
        n_anomalies = len(data_quality_report.get("anomalies", []))
        n_warnings = len(data_quality_report.get("warnings", []))
        scores["data_quality_precheck"] = max(0.2, 1.0 - n_anomalies * 0.25 - n_warnings * 0.1)
    else:
        scores["data_quality_precheck"] = 0.7

    # 【v2.0 新增】样本量充分度
    sample_size = agent_outputs.get("cpm_sample_size", 10)
    if sample_size >= 20:
        scores["sample_size_adequacy"] = 0.9
    elif sample_size >= 10:
        scores["sample_size_adequacy"] = 0.7
    elif sample_size >= 5:
        scores["sample_size_adequacy"] = 0.5
    else:
        scores["sample_size_adequacy"] = 0.3

    final = sum(scores[k] * weights[k] for k in weights)
    
    return {
        "final_confidence": round(final, 2),
        "component_scores": scores,
        "interpretation": interpret_confidence(final),
    }

def interpret_confidence(score):
    if score >= 0.75:
        return "高置信度：数据充分，建议可直接用于谈判参考"
    elif score >= 0.55:
        return "中等置信度：建议结合其他信息（如星图/花火建议价）综合判断"
    elif score >= 0.35:
        return "低置信度：数据不足，建议仅作粗略参考，先要求品牌给出预算范围"
    else:
        return "极低置信度：关键数据缺失，建议补充数据后重新分析"
```

---

## 九、回测框架【v2.0 新增】

```python
BACKTEST_FRAMEWORK = {
    "description": """
    回测框架用于验证系统报价的准确性。
    通过收集用户的实际成交反馈，计算系统建议价与真实成交价的偏差。
    """,
    "metrics": {
        "MAPE": "平均绝对百分比误差 = mean(|系统建议价 - 实际成交价| / 实际成交价)",
        "hit_rate": "命中率 = 实际成交价落在系统建议区间(walk_away ~ anchor_price)内的比例",
        "directional_accuracy": "方向准确率 = 系统建议高于/低于实际成交的方向是否符合预期",
    },
    "targets": {
        "MAPE": "< 25%（优秀）/ < 35%（合格）/ > 50%（需要校准CPM表）",
        "hit_rate": "> 70%（优秀）/ > 50%（合格）/ < 40%（需要调整区间宽度）",
    },
    "segmented_backtest": """
    按以下维度分别回测，识别薄弱环节：
    - 按平台：B站 / 抖音 / 快手
    - 按垂类：各垂类独立回测
    - 按层级：素人/KOC / 小达人 / 中腰部 / 头部 / 超头部
    - 按合作类型：纯视频 / 直播带货 / 打包方案
    """,
    "feedback_collection": """
    用户反馈数据结构：
    {
        "session_id": "xxx",
        "system_suggestion": {
            "walk_away": 5000,
            "fair_market": 8000,
            "anchor_price": 10500
        },
        "actual_outcome": {
            "deal_closed": true,
            "final_price": 7500,
            "through_platform": true,
            "deal_type": "dedicated_video",
            "brand_initial_offer": 5000,
            "negotiation_rounds": 2
        },
        "user_satisfaction": 4  // 1-5分
    }
    """,
}
```

---

## 十、实施优先级

### Phase 1（MVP）✅ 已完成
- [x] Data Validator 数据验证层
- [x] Agent A 国内版：CPM表（含置信度+样本量标注）、修正因子（含正交化+受众年龄+稳定性）、粉丝播放比、层级分类
- [x] Agent D 基本版：中文报告生成（含税务提醒、走平台/私下双报价）
- [x] 快速通道：Validator → A → D
- [x] 用户输入表单
- [x] 前端展示
- [x] 品牌库：64品牌 JSON DB + 搜索API + 前端品牌搜索组件
- [x] B站自动数据获取（公开API，非WBI）

### Phase 2（核心功能）✅ 已完成
- [x] Agent B：交付物乘数（B站15/抖音13/快手9类型）、使用权溢价（18种）、打包方案（含年框合作）
- [x] Agent C：国内化Bull/Bear/Judge（含结构化数据引用Prompt+价格锚定策略建议）
- [x] 完整通道：Validator → A → B → C → D
- [x] 合同红线检测（22条，含广告法、肖像权、AI训练权、数据安全）
- [x] 季节性完整矩阵（8品类组 × 12月）
- [x] 排他性溢价（10种，含指定竞品排他、平台排他）
- [x] 直播类型分类（专场/混场/口播 + 坑位费乘数）
- [x] ENGAGEMENT_RATE_DEFINITIONS（互动率定义 + 垂类平均值）

### Phase 3（增强，持续迭代）
- [x] B站API对接（使用稳定公开API，非WBI签名）
- [ ] 星图/花火公开报价抓取作为校准锚点
- [ ] 蝉妈妈/飞瓜API对接（如预算允许）
- [x] 品牌库扩充到64个品牌（独立JSON文件维护）
- [ ] 跨平台打包定价工具（`calculate_cross_platform_price`，含内容时长维度）
- [ ] MCN分成计算器（前端组件，数据已有 `MCN_FEE_REFERENCE`）
- [ ] 纯佣金模式独立处理（`COMMISSION_ONLY_MODEL`，需前端UI配合）
- [ ] 直播坑位费自动计算（数据表已有 `LIVESTREAM_PIT_FEE_TABLE`，需前端选择直播类型）
- [ ] 用户反馈→CPM校准闭环
- [ ] 回测框架上线，开始积累数据
- [ ] 置信度评分体系增强（含新鲜度衰减、样本偏差修正）
- [ ] 历史成交价输入 + 校准锚点

### Phase 4（扩展平台）
- [ ] 小红书（已有预研规格）
- [ ] 微信视频号
- [ ] 微博

---

## 十一、验证标准

1. **合理性检验**：输出价格落在层级 typical_range 的 ±30% 内
2. **平台差异性**：同画像达人，B站报价 > 抖音 > 快手（一般规律）
3. **粉丝播放比敏感性**：vf_ratio 从 0.1 变为 0.5 应导致报价上浮 30-60%
4. **直播带货独立性**：直播报价使用独立的坑位费表，且专场 > 混场 > 口播
5. **使用权影响**：信息流投放授权应使报价上浮 30-90%
6. **季节性影响**：11月 vs 3月同一达人报价差异 20-50%
7. **走平台 vs 私下**：走星图报价 > 私下报价（覆盖平台抽成）
8. **垂类敏感性**：同10万粉，汽车类报价 ≈ 娱乐搞笑类的 3-5 倍
9. **广告法合规**：医疗/金融/教育品类自动触发合规提醒
10. **置信度校准**：完整数据→置信度>0.7，缺关键数据→置信度<0.5
11. **历史成交验证**：当有历史成交价时，系统报价偏差应 < 40%
12. **修正因子封顶**：极端输入不应导致报价超出层级范围 3 倍以上
13. **正交化验证**：互动率和粉丝播放比同时极端时，总修正不应超出单独极端的1.5倍（v2.0）
14. **纯佣金预警**：纯佣金模式下如果期望收益<坑位费模式的70%，系统应给出警告（v2.0）
15. **数据验证层有效性**：异常数据（如vf_ratio>5）应被Data Validator正确识别（v2.0）