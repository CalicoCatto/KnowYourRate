# KnowYourRate 多Agent定价情报引擎 — Claude Code 实施指令

## 项目背景

KnowYourRate 是一个帮助 YouTube/TikTok 创作者计算品牌合作公平报价的多Agent AI系统。用户输入自己的频道链接和品牌合作条件，系统通过多个Agent协作分析，输出带置信区间的报价范围、谈判策略和合同风险提醒。

请你根据以下详细方案，重构/完善项目的多Agent架构和定价分析逻辑，目标是让价格分析更准确、更实用。

---

## 一、整体架构：4个Agent + 1个路由器 + 1个编排器

### 架构总览

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

### 复杂度路由器（Router）

路由器根据用户输入判断分析复杂度，决定走哪条通道：

```python
# 路由逻辑伪代码
def route_request(user_input):
    complexity_score = 0
    
    # 加分因素（需要深度分析）
    if user_input.has_brand_name:          # 指定了品牌 → 需要品牌侧分析
        complexity_score += 2
    if user_input.deal_includes_exclusivity: # 涉及排他性条款
        complexity_score += 2
    if user_input.deal_includes_usage_rights: # 涉及使用权
        complexity_score += 2
    if user_input.niche in HIGH_VARIANCE_NICHES:  # 高方差垂类（财经、科技等）
        complexity_score += 1
    if user_input.is_first_brand_deal:      # 第一次品牌合作
        complexity_score += 1
    
    if complexity_score >= 3:
        return "full_pipeline"    # 完整4-Agent分析
    else:
        return "fast_track"       # 快速通道：仅Agent A → Agent D
```

**快速通道**：仅运行 Agent A（创作者画像）+ Agent D（报告生成），跳过市场情报和辩论。适用于简单的"我有X粉丝，做一个标准植入，大概该收多少钱"的查询。响应时间目标 < 15秒。

**完整通道**：A+B并行 → C辩论 → D报告。适用于涉及具体品牌、复杂条款、高价值交易的查询。响应时间目标 < 60秒。

---

## 二、Agent A — 创作者画像分析 Agent

### 角色定义

分析目标创作者的频道数据，评估其对品牌方的真实商业价值。这是整个定价系统的基础数据层。

### 输入

```json
{
  "platform": "youtube" | "tiktok",
  "channel_url": "https://youtube.com/@example",
  "channel_data": {  // 如果用户手动输入而非API获取
    "subscribers": 85000,
    "avg_views_last_30": 25000,
    "engagement_rate": 4.2,
    "niche": "tech_review",
    "top_audience_country": "US",
    "channel_age_months": 24,
    "upload_frequency": "weekly"
  }
}
```

### 处理逻辑

Agent A 必须计算以下核心指标：

**1. 基础 CPM 报价计算**

```
base_cpm = get_niche_cpm(niche, platform)

# 垂类 CPM 基准表（必须内置，这是核心数据）
NICHE_CPM_TABLE = {
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
    }
}
```

**2. 基础报价 = CPM × 平均观看量 / 1000**

```python
base_price_low  = niche_cpm["low"]  * avg_views / 1000
base_price_mid  = niche_cpm["mid"]  * avg_views / 1000
base_price_high = niche_cpm["high"] * avg_views / 1000
```

**3. 修正因子系统（核心创新点，必须实现）**

```python
multipliers = {
    # 互动率修正：行业平均互动率约3-5%
    "engagement_modifier": calculate_engagement_modifier(engagement_rate, niche_avg),
    # 规则：
    # - 互动率 < 垂类平均的50% → 乘以 0.7
    # - 互动率在垂类平均的50%-100% → 乘以 0.85-1.0（线性）
    # - 互动率在垂类平均的100%-200% → 乘以 1.0-1.3（线性）
    # - 互动率 > 垂类平均的200% → 乘以 1.3（封顶，防止异常值）
    
    # 受众地域修正
    "geo_modifier": calculate_geo_modifier(top_audience_countries),
    # 规则：
    # - US/UK/CA/AU 为主 → 乘以 1.0-1.2
    # - 西欧为主 → 乘以 0.85-1.0
    # - 东南亚/南亚为主 → 乘以 0.3-0.5
    # - 混合地域 → 按比例加权
    
    # 增长动量修正
    "growth_modifier": calculate_growth_modifier(monthly_growth_rate),
    # 规则：
    # - 月增长率 > 10% → 乘以 1.15（上升期创作者溢价）
    # - 月增长率 3-10% → 乘以 1.05
    # - 月增长率 0-3% → 乘以 1.0
    # - 月增长率 < 0%（流失期） → 乘以 0.9
    
    # 内容质量信号修正
    "quality_modifier": calculate_quality_modifier(avg_watch_time_pct, like_ratio),
    # 规则（仅YouTube，TikTok数据有限）：
    # - 平均观看占比 > 50% → 乘以 1.1
    # - 点赞率(likes/views) > 5% → 乘以 1.05
    
    # 季节性修正
    "seasonal_modifier": calculate_seasonal_modifier(current_month),
    # 规则：
    # - 10月-12月（Q4旺季） → 乘以 1.2-1.5
    # - 1月（新年健康类旺季） → 健身/健康垂类乘以 1.15
    # - 6月-8月（夏季淡季） → 乘以 0.85-0.95
    # - 其他月份 → 乘以 1.0
}

# 最终修正后的基础报价
adjusted_price = base_price * product(multipliers.values())
```

**4. 频道层级分类**

```python
TIER_TABLE = {
    "youtube": {
        "nano":       {"min_subs": 1000,   "max_subs": 10000,  "typical_range": "$50-$500"},
        "micro":      {"min_subs": 10000,  "max_subs": 100000, "typical_range": "$200-$5,000"},
        "mid_tier":   {"min_subs": 100000, "max_subs": 500000, "typical_range": "$1,000-$20,000"},
        "macro":      {"min_subs": 500000, "max_subs": 1000000,"typical_range": "$10,000-$20,000+"},
    },
    "tiktok": {
        "nano":       {"min_followers": 1000,   "max_followers": 10000,  "typical_range": "$50-$300"},
        "micro":      {"min_followers": 10000,  "max_followers": 100000, "typical_range": "$200-$2,000"},
        "mid_tier":   {"min_followers": 100000, "max_followers": 500000, "typical_range": "$1,000-$10,000"},
        "macro":      {"min_followers": 500000, "max_followers": 1000000,"typical_range": "$5,000-$10,000"},
    }
}
```

### 输出格式

```json
{
  "creator_profile": {
    "platform": "youtube",
    "tier": "micro",
    "niche": "technology",
    "niche_display": "科技评测",
    "subscribers": 85000,
    "avg_views": 25000,
    "engagement_rate": 4.2,
    "engagement_vs_niche_avg": "+40%",
    "top_geo": "US 65%, UK 12%, CA 8%",
    "growth_trend": "上升期（月增长率 5.2%）",
    "channel_age": "24个月"
  },
  "base_price_range": {
    "low": 500,
    "mid": 875,
    "high": 1375,
    "currency": "USD"
  },
  "applied_modifiers": {
    "engagement_modifier": {"value": 1.15, "reason": "互动率4.2%，高于科技垂类平均3.0%"},
    "geo_modifier": {"value": 1.1, "reason": "65%美国受众，高商业价值地域"},
    "growth_modifier": {"value": 1.05, "reason": "月增长率5.2%，处于上升期"},
    "seasonal_modifier": {"value": 1.0, "reason": "当前3月，非旺季/淡季"}
  },
  "adjusted_price_range": {
    "low": 664,
    "mid": 1162,
    "high": 1827
  },
  "confidence_score": 0.78,
  "data_quality_flags": ["engagement_rate_from_public_data", "geo_data_estimated"]
}
```

### 模型选择

- 如果有API数据（结构化数据处理）→ 用 Claude Haiku 或 GPT-4o-mini（低成本）
- 如果需要从非结构化输入推断垂类/受众 → 用 Claude Sonnet 或 GPT-4o

---

## 三、Agent B — 市场情报与可比交易 Agent

### 角色定义

收集和分析市场基准数据、同类创作者的历史成交参考、品牌方的赞助模式，为定价提供市场锚点。

### 输入

接收 Agent A 的输出 + 用户提供的合作条件：

```json
{
  "creator_profile": { /* Agent A 的输出 */ },
  "deal_conditions": {
    "brand_name": "NordVPN",           // 可选
    "brand_category": "technology",     // 品牌品类
    "deliverables": ["dedicated_video"],// 交付物类型
    "usage_rights": "organic_only",     // 使用权范围
    "exclusivity": "none",             // 排他性
    "timeline": "30_days",             // 交付时间
    "content_approval": true            // 是否需要品牌审核
  }
}
```

### 处理逻辑

**1. 交付物类型定价乘数**

```python
DELIVERABLE_MULTIPLIERS = {
    "youtube": {
        "dedicated_video":     1.0,     # 整条视频专门介绍品牌（基准）
        "integrated_mention":  0.5,     # 视频中段30-60秒植入
        "pre_roll_mention":    0.35,    # 视频开头15-30秒口播
        "shorts":              0.25,    # YouTube Shorts
        "community_post":      0.1,     # 社区帖子
        "pinned_comment":      0.05,    # 置顶评论
        "livestream_mention":  0.4,     # 直播中口播
    },
    "tiktok": {
        "dedicated_video":     1.0,     # 专门为品牌拍的视频
        "integrated_mention":  0.6,     # 自然融入的提及
        "series_3_posts":      2.5,     # 3条系列视频
        "duet_stitch":         0.4,     # 与品牌账号合拍
        "livestream_mention":  0.5,     # 直播中提及
    }
}
```

**2. 使用权和排他性加价逻辑（关键！这是创作者最容易被坑的地方）**

```python
USAGE_RIGHTS_PREMIUMS = {
    "organic_only":           0.0,    # 仅创作者自己频道发布，无额外费用
    "brand_repost_30d":       0.15,   # 品牌社交媒体转发30天
    "brand_repost_perpetual": 0.40,   # 品牌社交媒体永久转发
    "whitelisting_30d":       0.30,   # 品牌用创作者账号投放广告30天
    "whitelisting_90d":       0.60,   # 90天白名单
    "whitelisting_perpetual": 1.0,    # 永久白名单
    "website_use":            0.20,   # 品牌网站使用
    "email_marketing":        0.15,   # 邮件营销使用
    "paid_ads":               0.50,   # 付费广告素材
    "tv_print":               2.0,    # 电视/印刷广告（最高溢价）
    "perpetual_all_media":    3.0,    # 所有媒介永久使用权
}

EXCLUSIVITY_PREMIUMS = {
    "none":                   0.0,
    "category_30d":           0.25,   # 同品类排他30天
    "category_90d":           0.50,   # 同品类排他90天
    "category_6m":            0.75,   # 同品类排他6个月
    "category_12m":           1.0,    # 同品类排他12个月
    "full_exclusivity_30d":   0.50,   # 全品类排他30天
    "full_exclusivity_90d":   1.0,    # 全品类排他90天
}

# 计算合同条款加价后的总报价
def calculate_deal_adjusted_price(base_range, deal_conditions):
    deliverable_mult = DELIVERABLE_MULTIPLIERS[platform][deliverable_type]
    usage_premium = USAGE_RIGHTS_PREMIUMS[usage_rights]
    exclusivity_premium = EXCLUSIVITY_PREMIUMS[exclusivity]
    
    # 总加价 = 基础价 × 交付物乘数 × (1 + 使用权溢价 + 排他性溢价)
    total_multiplier = deliverable_mult * (1 + usage_premium + exclusivity_premium)
    
    return {
        "low":  base_range["low"]  * total_multiplier,
        "mid":  base_range["mid"]  * total_multiplier,
        "high": base_range["high"] * total_multiplier,
    }
```

**3. 品牌类型情报（如果用户指定了品牌名）**

```python
# 已知品牌的赞助行为模式（内置知识库，持续扩充）
KNOWN_BRAND_PATTERNS = {
    "nordvpn": {
        "category": "technology",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "high",        # 知名大预算赞助商
        "negotiation_flexibility": "medium",
        "typical_cpm_range": [30, 50],
        "common_requirements": ["30s-60s mid-roll", "custom tracking link", "talking points provided"],
        "known_issues": [],
        "payment_reliability": "excellent",
    },
    "skillshare": {
        "category": "education",
        "typical_deal_type": "integrated_mention",
        "budget_tier": "medium",
        "negotiation_flexibility": "low",  # 通常给固定报价
        "typical_cpm_range": [15, 30],
        "common_requirements": ["free trial link", "personal endorsement style"],
        "known_issues": ["frequently offers below-market rates to new creators"],
        "payment_reliability": "good",
    },
    # ... 扩充更多品牌
}

# 如果品牌不在已知列表中，通过LLM推断品牌品类和预算层级
def infer_brand_profile(brand_name, brand_category):
    # 使用 LLM 基于品牌名称和品类推断：
    # - 该品牌所在行业的典型赞助预算水平
    # - 该品类品牌的常见赞助模式
    # - 可能的谈判空间
    pass
```

**4. 打包方案生成**

```python
def generate_package_tiers(adjusted_price_mid, platform, deliverables):
    """
    生成铜/银/金三档打包方案
    研究显示90%+的营销人员使用打包作为谈判策略
    60%报告从未收到对打包方案的反对
    """
    return {
        "starter": {
            "name": "入门合作",
            "price": adjusted_price_mid * 0.8,
            "includes": ["1个植入视频"],
            "duration": "一次性",
        },
        "standard": {
            "name": "标准合作",
            "price": adjusted_price_mid * 2.2,  # 不是3x，给品牌感觉性价比
            "includes": ["3个植入视频", "1条Stories/社区帖子"],
            "duration": "3个月",
            "savings_vs_individual": "27%",  # 显示节省比例增加吸引力
        },
        "premium": {
            "name": "深度合作",
            "price": adjusted_price_mid * 4.0,
            "includes": ["6个植入视频", "3条Stories", "品牌社交转发权30天"],
            "duration": "6个月",
            "savings_vs_individual": "33%",
        }
    }
```

### 输出格式

```json
{
  "deal_adjusted_price_range": {
    "low": 830,
    "mid": 1453,
    "high": 2284
  },
  "price_breakdown": {
    "base_creator_value": {"low": 664, "mid": 1162, "high": 1827},
    "deliverable_multiplier": 1.0,
    "usage_rights_premium": "+0%（仅有机发布）",
    "exclusivity_premium": "+0%（无排他）",
    "seasonal_note": "Q4旺季（10-12月）可额外加价20-50%"
  },
  "brand_intelligence": {
    "brand_name": "NordVPN",
    "budget_tier": "高预算赞助商",
    "negotiation_tip": "NordVPN通常给出中高水平报价，有一定谈判空间。建议以报告中的'high'价格起步谈判。",
    "payment_reliability": "付款可靠"
  },
  "comparable_deals_context": "同垂类同规模创作者（科技类8-10万粉）的植入报价通常在$800-$2,000区间",
  "package_tiers": { /* 三档打包方案 */ },
  "confidence_score": 0.72,
  "data_quality_flags": ["brand_data_from_knowledge_base", "comparable_deals_estimated"]
}
```

### 模型选择

- 结构化计算部分 → 代码直接执行，无需LLM
- 品牌情报推断 + 可比交易分析 → Claude Sonnet 或 GPT-4o

---

## 四、Agent C — 对抗性辩论 Agent（看多 vs 看空）

### 角色定义

这是系统的核心创新。模拟"创作者经纪人"（看多/Bull）和"品牌采购经理"（看空/Bear）两个角色对定价进行辩论，由裁判综合出最终报价。研究显示此模式可将估值准确性提升8.3%。

### 架构

```
Agent A 输出 + Agent B 输出
        │
   ┌────▼────┐
   │  辩论控制器 │
   └────┬────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
Bull Agent  Bear Agent    ← 第1轮：各自独立分析
   │         │
   └────┬────┘
        │
   ┌────▼────┐
   │  交叉反驳  │           ← 第2轮：看到对方论点后反驳
   └────┬────┘
        │
   ┌────▼────┐
   │  裁判综合  │           ← 综合双方论点，输出最终报价
   └────┬────┘
        │
        ▼
   最终定价区间 + 置信度
```

### Bull Agent（看多方 — 创作者经纪人视角）Prompt

```
你是一位经验丰富的创作者经纪人，你的职责是为创作者争取最高合理报价。

你会收到一份创作者画像分析和市场情报数据。请从以下角度论证创作者应该获得更高报价：

1.【互动价值】如果创作者的互动率高于垂类平均，强调互动率比粉丝数更重要——一个高互动的小频道比一个低互动的大频道对品牌更有价值。量化这个差异。

2.【受众质量】如果受众以高商业价值地域（美/英/加/澳）为主，强调这些受众的购买力和转化潜力。引用地域溢价数据。

3.【增长溢价】如果创作者处于上升期，论证品牌现在合作是"买入低估资产"，3-6个月后同等合作会更贵。

4.【使用权价值】如果品牌要求超出有机发布的使用权，详细计算每项附加权利的合理加价。特别警惕永久使用权被低估。

5.【季节性时机】如果接近Q4旺季或垂类旺季，论证当前市场需求支撑更高价格。

6.【稀缺性论证】如果创作者在利基市场有独特定位，论证替代选择有限，品牌的议价能力受限。

请输出：
- 你建议的报价（给出具体数字）
- 3-5个关键论据（每个有数据支撑）
- 对可能的反驳的预判

格式要求：JSON，字段为 suggested_price, arguments[], preemptive_rebuttals[]
```

### Bear Agent（看空方 — 品牌采购经理视角）Prompt

```
你是一位精明的品牌营销采购经理，你的职责是评估创作者的真实市场价值，避免品牌方过度支付。

你会收到一份创作者画像分析和市场情报数据。请从以下角度论证报价应该更保守：

1.【市场供给】同垂类同规模的创作者不止一个，强调品牌有替代选择。如果不是极度稀缺的利基，竞争压低了价格。

2.【实际ROI】从品牌CPA/ROAS视角反算。如果品牌的目标获客成本是$50，创作者能带来多少转化？报价是否在ROI框架内合理？

3.【算法风险】平台算法变化可能导致实际触达低于历史平均。强调"平均观看量"不等于"保证观看量"，品牌承担了不确定性。

4.【可比基准】引用同层级创作者的市场均价作为锚点。如果报价显著高于市场中位数，需要额外理由。

5.【长期合作折扣】如果品牌愿意承诺长期合作（3-6个月），论证单次费率应该给折扣（行业惯例是长期合约降低40-60%单次成本）。

6.【隐性成本】提醒关注内容审核轮次、修改成本、品牌方的时间投入等隐性成本。

请输出：
- 你建议的报价（给出具体数字）
- 3-5个关键论据（每个有数据支撑）
- 对看多方可能论据的反驳

格式要求：JSON，字段为 suggested_price, arguments[], counter_arguments[]
```

### 裁判 Agent Prompt

```
你是一位中立的定价分析专家。你刚才旁听了"创作者经纪人"（看多方）和"品牌采购经理"（看空方）关于一位创作者品牌合作报价的辩论。

请你：

1. 评估双方论据的强度，指出哪些论据有数据支撑、哪些是推测性的
2. 识别双方的共识区域（如果有的话）
3. 综合得出最终报价区间：
   - 底价（walk-away price）：低于这个价不值得合作
   - 推荐报价（fair market rate）：双方都合理的价格
   - 理想报价（anchor price）：开口报价，用于谈判锚定
4. 给出置信度评分（0-1），并解释影响置信度的主要因素
5. 如果看多方和看空方的报价差距超过100%，标记为"高不确定性"并解释原因

输出格式：
{
  "final_price_range": {
    "walk_away": 数字,      // 底价
    "fair_market": 数字,    // 公平市场价
    "anchor_price": 数字    // 开口锚定价（比fair_market高约30%）
  },
  "confidence": 0.0-1.0,
  "uncertainty_flag": true/false,
  "key_factors": ["factor1", "factor2", ...],
  "bull_strongest_argument": "...",
  "bear_strongest_argument": "...",
  "consensus_areas": ["area1", "area2", ...],
  "judge_notes": "综合分析说明"
}
```

### 关键实现要点

1. **2轮辩论最优**：第1轮独立分析，第2轮交叉反驳。超过2轮收益递减且token成本翻倍。
2. **异构Agent**：Bull用较高temperature（0.7-0.8），Bear用较低temperature（0.3-0.4），裁判用中等temperature（0.5）。这可以防止同质化收敛。
3. **不强制共识**：如果Bull和Bear差距很大（>100%），保留宽区间，这本身就是有价值的信息——说明该交易有高度不确定性，创作者需要更多信息才能决策。
4. **模型选择**：Bull和Bear用Claude Sonnet，裁判用Claude Opus或GPT-4o（需要最强的综合判断能力）。

---

## 五、Agent D — 策略报告生成 Agent

### 角色定义

将所有Agent的输出汇总为一份用户友好的定价策略报告，包含报价建议、谈判话术、合同红线提醒。

### 输入

接收Agent A + B + C的全部输出。

### 输出报告结构

```markdown
# 📊 你的品牌合作定价报告

## 1. 报价建议

| 策略 | 金额 | 说明 |
|------|------|------|
| 🎯 开口报价（锚定价） | $X,XXX | 用于谈判起步，预留30%谈判空间 |
| ✅ 推荐成交价 | $X,XXX | 基于市场数据的公平价格 |
| 🚫 底线价格 | $X,XXX | 低于此价不建议接受 |

> 置信度：⭐⭐⭐⭐☆（78%）
> 基于：[使用了哪些数据来源]

## 2. 定价依据（用于谈判中向品牌展示）

- "我的互动率是4.2%，高于科技类创作者平均水平40%"
- "我的受众65%位于美国，属于高商业价值地域"
- "过去6个月我的频道月增长率为5.2%，处于上升期"

## 3. 打包方案（推荐展示给品牌方）

### 🥉 入门合作 — $X,XXX
- 1个植入视频
- 适合：初次合作试水

### 🥈 标准合作 — $X,XXX（推荐）
- 3个植入视频 + 1条社区帖子  
- 比单次购买节省 27%
- 适合：3个月持续曝光

### 🥇 深度合作 — $X,XXX
- 6个植入视频 + 3条Stories + 品牌社交转发权30天
- 比单次购买节省 33%
- 适合：产品发布/大型campaign

## 4. 合同条款红线提醒 ⚠️

[根据用户输入的合作条件，检测以下风险项]

- ✅ / ⚠️ / 🚫 使用权范围：[具体分析]
- ✅ / ⚠️ / 🚫 排他性条款：[具体分析]
- ✅ / ⚠️ / 🚫 付款条件：[具体分析]
- ✅ / ⚠️ / 🚫 修改轮次：[具体分析]
- ✅ / ⚠️ / 🚫 内容审核权：[具体分析]

### 红线检测规则：
CONTRACT_RED_FLAGS = {
    "perpetual_rights_no_premium": "永久使用权但未加价 → 🚫 强烈建议拒绝或加价200-300%",
    "unlimited_revisions": "无限修改轮次 → ⚠️ 建议限制为2-3轮",
    "full_exclusivity_no_premium": "全品类排他但未额外补偿 → 🚫 至少要求加价50-100%",
    "payment_net_90_plus": "付款周期超过90天 → ⚠️ 要求50%预付或缩短至Net 30",
    "unilateral_termination": "品牌可单方面终止合同 → ⚠️ 要求加入终止费条款",
    "vague_deliverables": "交付物描述模糊 → ⚠️ 要求明确具体数量和格式",
    "content_ownership_transfer": "要求转让内容所有权 → 🚫 改为授权使用，保留所有权",
    "no_kill_fee": "无终止费条款 → ⚠️ 要求加入（通常为合同金额的25-50%）",
}

## 5. 谈判话术模板

### 场景A：品牌主动找你（你有优势）
"感谢您的合作邀约！基于我的频道数据——[互动率]、[受众画像]、[增长趋势]——
我为这类合作的标准费率是 $[锚定价]。这包括[具体交付物]。
如果您有兴趣探索长期合作，我也准备了更有竞争力的套餐方案。"

### 场景B：你主动pitch品牌（品牌有优势）
"我注意到[品牌名]最近在[垂类]领域加大了投放。我的频道在[垂类]
拥有[受众规模]的高度参与受众，互动率达到[X%]，是行业平均的[X倍]。
我很乐意以[推荐成交价]的费率创作一条专门的[内容类型]。"

### 场景C：品牌说报价太高时
"我理解预算考量。让我分享一下这个费率的依据：
同类创作者在[垂类]的市场CPM是$[X]-$[Y]，基于我的平均观看量[Z]，
计算得出的市场公平价是$[推荐价]。
不过，我确实有一个更灵活的入门套餐：$[入门价]，包含[内容]。"

## 6. 时机建议 📅

- 当前季节性影响：[Q几，对定价的影响]
- 建议：[如果接近旺季，提醒现在可以报更高价 / 如果淡季，建议灵活处理]
- 下一个定价窗口：[下一个旺季的时间和垂类相关性]
```

### 模型选择

- 报告生成 → Claude Sonnet（需要好的中文写作能力和格式化能力）
- 如果用户选择英文输出 → GPT-4o 或 Claude Sonnet 均可

---

## 六、全局状态管理与数据流

### Orchestrator 编排器设计

```python
class PricingOrchestrator:
    """
    全局状态管理器，协调所有Agent的执行
    建议用 LangGraph 实现（支持循环、条件分支、并行执行）
    """
    
    def __init__(self):
        self.state = {
            "user_input": None,
            "route": None,           # "fast_track" or "full_pipeline"
            "agent_a_output": None,
            "agent_b_output": None,
            "agent_c_output": None,
            "agent_d_output": None,
            "final_report": None,
            "total_tokens_used": 0,
            "total_cost_usd": 0,
            "execution_time_ms": 0,
        }
    
    async def run(self, user_input):
        self.state["user_input"] = user_input
        
        # Step 1: 路由
        self.state["route"] = self.router.classify(user_input)
        
        if self.state["route"] == "fast_track":
            # 快速通道：A → D
            self.state["agent_a_output"] = await self.agent_a.run(user_input)
            self.state["agent_d_output"] = await self.agent_d.run(
                agent_a=self.state["agent_a_output"],
                agent_b=None,  # 跳过
                agent_c=None,  # 跳过
            )
        else:
            # 完整通道：A||B → C → D
            # A和B并行执行！
            agent_a_task = self.agent_a.run(user_input)
            agent_b_task = self.agent_b.run(user_input)
            
            self.state["agent_a_output"], self.state["agent_b_output"] = \
                await asyncio.gather(agent_a_task, agent_b_task)
            
            # C 依赖 A+B
            self.state["agent_c_output"] = await self.agent_c.run(
                agent_a=self.state["agent_a_output"],
                agent_b=self.state["agent_b_output"],
            )
            
            # D 汇总所有
            self.state["agent_d_output"] = await self.agent_d.run(
                agent_a=self.state["agent_a_output"],
                agent_b=self.state["agent_b_output"],
                agent_c=self.state["agent_c_output"],
            )
        
        return self.state["agent_d_output"]
```

### 成本控制

```python
# 分层模型路由 — 这是控制成本的核心策略
MODEL_ROUTING = {
    "agent_a_structured":   "claude-haiku",     # 结构化数据处理用小模型
    "agent_a_inference":    "claude-sonnet",     # 垂类推断用中等模型
    "agent_b_structured":   "code_execution",   # 纯计算部分不调LLM
    "agent_b_brand_intel":  "claude-sonnet",     # 品牌情报推断
    "agent_c_bull":         "claude-sonnet",     # 辩论方
    "agent_c_bear":         "claude-sonnet",     # 辩论方
    "agent_c_judge":        "claude-opus",       # 裁判需要最强模型
    "agent_d_report":       "claude-sonnet",     # 报告生成
}

# 预估单次完整分析的token消耗和成本
COST_ESTIMATE = {
    "fast_track": {
        "total_tokens": "~3,000-5,000",
        "estimated_cost": "$0.01-$0.03",
        "latency": "5-15秒",
    },
    "full_pipeline": {
        "total_tokens": "~15,000-25,000",
        "estimated_cost": "$0.08-$0.20",
        "latency": "30-60秒",
    }
}
```

---

## 七、数据层设计

### 内置数据（必须硬编码到系统中）

1. **垂类CPM基准表**（见Agent A部分的 NICHE_CPM_TABLE）
2. **交付物类型乘数表**（见Agent B部分的 DELIVERABLE_MULTIPLIERS）
3. **使用权/排他性溢价表**（见Agent B部分）
4. **季节性乘数**（Q1-Q4，按垂类细分）
5. **已知品牌赞助行为库**（初始50+品牌，持续扩充）
6. **合同红线检测规则**（见Agent D部分的 CONTRACT_RED_FLAGS）
7. **层级分类表**（见Agent A部分的 TIER_TABLE）

### API数据（如可获取）

```python
# YouTube Data API v3 — 免费，10,000单位/天
youtube_data = {
    "subscriber_count": "channels.list(part=statistics)",
    "video_views": "videos.list(part=statistics)",
    "engagement": "计算：(likes + comments) / views",
    "upload_frequency": "计算：最近30天的视频数",
    "video_duration": "videos.list(part=contentDetails)",
    "tags_description": "videos.list(part=snippet)  # 用于垂类推断",
}

# TikTok — 公开数据有限，建议让用户手动输入
tiktok_data = {
    "follower_count": "用户输入或公开页面爬取",
    "avg_views": "用户输入",
    "engagement_rate": "用户输入或从最近视频计算",
}
```

### 用户自助输入（作为API数据的降级方案）

当API不可用时，提供用户自助输入表单：

```
必填：
- 平台（YouTube / TikTok）
- 粉丝/订阅数
- 最近10条视频的平均观看量
- 内容垂类（下拉选择）
- 主要受众地域（下拉选择）

选填（提高分析精度）：
- 互动率（如果知道的话）
- 频道创建时间
- 最近3个月的粉丝增长数
- 品牌名称
- 合作类型（专门视频/植入/口播等）
- 使用权要求
- 排他性要求
- 付款条件
```

---

## 八、实施优先级

### Phase 1（MVP，3-5天）
- [ ] 实现 Agent A（创作者画像分析）的完整逻辑，包括CPM表和所有修正因子
- [ ] 实现 Agent D（报告生成）的基本版本
- [ ] 实现快速通道：A → D
- [ ] 用户输入表单（手动输入模式）
- [ ] 前端展示定价报告

### Phase 2（核心功能，5-8天）
- [ ] 实现 Agent B（市场情报），包括交付物乘数、使用权/排他性加价、打包方案
- [ ] 实现 Agent C（对抗辩论），包括Bull/Bear/Judge三角色
- [ ] 实现完整通道：A||B → C → D
- [ ] 实现复杂度路由器
- [ ] 合同红线检测功能
- [ ] 谈判话术生成

### Phase 3（增强，持续迭代）
- [ ] 接入 YouTube Data API v3，自动获取频道数据
- [ ] 扩充已知品牌赞助行为库（目标100+品牌）
- [ ] 用户反馈循环：让用户报告实际成交价，持续校准CPM表
- [ ] 添加更多垂类的细分CPM数据
- [ ] 多语言支持（英文/中文报告切换）

---

## 九、验证标准

一个好的定价分析应该满足：

1. **合理性检验**：输出价格应落在 TIER_TABLE 对应层级的 typical_range 内（±30%容差）
2. **修正因子敏感性**：改变互动率（从2%到8%）应导致报价变化20-60%，而非无变化或10倍变化
3. **排他性/使用权影响**：添加"永久全媒体使用权+12个月全品类排他"应使报价至少翻3倍
4. **季节性影响**：同一创作者在Q4 vs 夏季的报价应有15-40%差异
5. **垂类敏感性**：同样50K粉丝，财经类报价应该是娱乐类的2-4倍
6. **置信度校准**：数据越完整，置信度越高；缺少关键数据（如互动率、受众地域）应降低置信度

---

请根据以上方案重构项目的多Agent系统。核心原则是：
- **计算能用代码的就用代码**（CPM计算、修正因子、乘数等），不要把简单数学交给LLM
- **LLM只用在需要推理和判断的地方**（垂类推断、品牌情报分析、辩论、报告撰写）
- **内置数据表是定价准确性的基石**，必须完整实现所有CPM表、乘数表和红线规则
- **置信度不是摆设**——每个Agent都要输出置信度，最终报告的置信度是加权综合












