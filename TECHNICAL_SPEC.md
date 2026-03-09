# KnowYourRate 技术说明书

## 目录

1. [系统概述](#1-系统概述)
2. [整体架构](#2-整体架构)
3. [定价引擎核心算法](#3-定价引擎核心算法)
4. [多 Agent 分析管线](#4-多-agent-分析管线)
5. [LLM 抽象层](#5-llm-抽象层)
6. [数据层设计](#6-数据层设计)
7. [前端架构](#7-前端架构)
8. [部署架构](#8-部署架构)
9. [安全设计](#9-安全设计)
10. [性能与成本分析](#10-性能与成本分析)

---

## 1. 系统概述

### 1.1 项目定位

KnowYourRate 是一个面向 YouTube/TikTok 内容创作者的品牌合作定价情报引擎。系统通过多 Agent 协作架构，将**确定性定价计算**与**LLM 定性推理**相结合，为创作者提供数据驱动的报价建议、谈判策略和合同风险分析。

### 1.2 核心设计原则

**"计算用代码，推理用 LLM"**（Math in code, reasoning in LLM）

这是整个系统最重要的设计决策。所有可以用公式表达的定价逻辑都在 Python 代码中确定性计算，LLM 仅用于以下无法公式化的任务：

| 类别 | 代码计算（确定性） | LLM 推理（概率性） |
|------|-------------------|-------------------|
| 基础定价 | CPM × 平均播放量 / 1000 | - |
| 修正因子 | 互动率/地域/增长/季节/质量修正 | - |
| 合同条款 | 交付物乘数 × (1 + 使用权 + 排他性) | - |
| 品牌情报 | 已知品牌库查表 | 未知品牌推断、市场上下文 |
| 定性评估 | - | 内容质量信号、受众价值、USP |
| 对抗辩论 | 价格锚定约束 | Bull/Bear 论证、裁判综合 |
| 报告生成 | 价格数字强制覆盖 | 叙事结构、谈判话术 |

**为什么这样设计？**
- **可复现性**：无论使用 GPT-4o、Claude Sonnet 还是 DeepSeek，相同输入产生相同的基础价格
- **可审计性**：每个修正因子的值和原因都有明确记录
- **成本控制**：结构化计算不消耗 token，大幅降低 LLM 调用成本
- **准确性**：LLM 在数学计算上容易出错，但在定性推理上表现优秀——各取所长

### 1.3 技术栈总览

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend                             │
│  React 18 · TypeScript · Vite · Tailwind CSS v4 · Zustand│
├─────────────────────────────────────────────────────────┤
│                    REST API + SSE                        │
├─────────────────────────────────────────────────────────┤
│                     Backend                              │
│  Python 3.11+ · FastAPI · SQLAlchemy (async) · Pydantic  │
├─────────────┬───────────────────────────┬───────────────┤
│ Agent Layer │   Pricing Engine          │  LLM Layer    │
│ 4 Agents +  │   pricing_tables.py       │  LiteLLM +    │
│ Orchestrator│   (纯 Python 计算)        │  6 Providers  │
├─────────────┴───────────────────────────┴───────────────┤
│                    Database                              │
│          PostgreSQL 16 / SQLite (aiosqlite)              │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 整体架构

### 2.1 请求处理流程

```
客户端 POST /api/analysis/run
        │
        ▼
┌──────────────┐    ┌───────────────┐
│ FastAPI Route │───▶│  创建 DB 记录  │ (analysis_run, status=running)
│ analysis.py  │    │  返回 run_id  │
└──────┬───────┘    └───────────────┘
       │
       ▼ (后台 asyncio.Task)
┌──────────────┐
│ Orchestrator │
│              │
│  1. 复杂度路由 ──▶ route_complexity() → "fast_track" | "full_pipeline"
│  2. 执行管线   │
│  3. 保存结果   │
│  4. SSE 推送   │
└──────────────┘
       │
       ▼ (SSE 端点)
客户端 GET /api/analysis/{id}/status
  → event: agent_progress
  → data: {"agent": "creator_profile", "status": "completed"}
```

### 2.2 复杂度路由器

路由器根据用户输入的品牌合作条件评估分析复杂度，决定走快速通道（2 个 Agent）还是完整管线（4 个 Agent）：

```python
def route_complexity(brand_name, exclusivity, usage_rights, niche, is_first_brand_deal):
    score = 0
    if brand_name:                    score += 2  # 指定品牌 → 需要品牌侧分析
    if exclusivity != "none":         score += 2  # 涉及排他性条款
    if usage_rights != "organic_only": score += 2  # 涉及使用权
    if niche in HIGH_VARIANCE_NICHES: score += 1  # 高方差垂类（财经、科技等）
    if is_first_brand_deal:           score += 1  # 第一次品牌合作

    return "full_pipeline" if score >= 3 else "fast_track"
```

**高方差垂类**指的是 CPM 范围跨度大、定价不确定性高的垂类：`finance_investing`、`technology`、`business_saas`、`automotive`。这些垂类的 CPM 高低差可达 3-4 倍，需要更深度的分析。

### 2.3 管线执行模式

**快速通道（Fast Track）**：
```
Agent A (创作者画像 + CPM 定价)
    │
    ▼
Agent D (策略报告)
```
- 适用场景：简单的"我有 X 粉丝，做一个标准植入，大概该收多少钱"查询
- LLM 调用次数：2 次（Agent A 定性 + Agent D 报告）
- 预计耗时：5-15 秒
- 预计 Token：3,000-5,000
- Agents B 和 C 标记为 `skipped`

**完整管线（Full Pipeline）**：
```
Agent A (创作者画像)
    │
    ▼
Agent B (市场情报 + 合同条款)
    │
    ▼
Agent C (3 轮对抗辩论)
    │
    ▼
Agent D (策略报告)
```
- 适用场景：涉及具体品牌、复杂条款、高价值交易
- LLM 调用次数：6 次（A + B + Bull + Bear + 2× CrossRebuttal + Judge + D = 7 次）
- 预计耗时：30-60 秒
- 预计 Token：15,000-25,000

---

## 3. 定价引擎核心算法

定价引擎位于 `backend/app/utils/pricing_tables.py`，是整个系统的数学基础。所有计算均为纯 Python，不依赖任何 LLM。

### 3.1 基础价格计算

**公式**：`base_price = CPM × avg_views / 1000`

其中 CPM（Cost Per Mille，每千次播放成本）来自内置的垂类 CPM 基准表：

```
NICHE_CPM_TABLE[platform][niche] → {"low": int, "mid": int, "high": int}
```

该表覆盖 **2 个平台 × 15 个垂类 = 30 组 CPM 数据**，每组包含 low/mid/high 三档。

**垂类 CPM 示例**（YouTube）：

| 垂类 | Low CPM | Mid CPM | High CPM | 说明 |
|------|---------|---------|----------|------|
| finance_investing | $30 | $50 | $75 | 最高 CPM，受众购买力强 |
| technology | $20 | $35 | $55 | |
| gaming | $5 | $12 | $20 | 受众年轻，购买力较低 |
| entertainment_comedy | $5 | $10 | $18 | 最低 CPM |

**计算示例**：一个科技类 YouTube 频道，平均播放量 25,000：
```
base_price_low  = 20 × 25,000 / 1000 = $500
base_price_mid  = 35 × 25,000 / 1000 = $875
base_price_high = 55 × 25,000 / 1000 = $1,375
```

### 3.2 五维修正因子系统

基础价格经过 5 个独立的修正因子调整，每个因子都有明确的计算规则和原因说明：

```
adjusted_price = base_price × engagement_mod × geo_mod × growth_mod × seasonal_mod × quality_mod
```

#### 3.2.1 互动率修正（Engagement Modifier）

基于创作者互动率与垂类平均互动率的比值：

```python
ratio = engagement_rate / niche_avg_engagement

if ratio < 0.5:   modifier = 0.7     # 远低于平均
elif ratio < 1.0: modifier = 0.85 + (ratio - 0.5) × 0.3  # 低于平均，线性插值
elif ratio ≤ 2.0: modifier = 1.0 + (ratio - 1.0) × 0.3   # 高于平均，线性插值
else:             modifier = 1.3     # 封顶，防止异常值
```

**垂类平均互动率数据**（内置于 `NICHE_AVG_ENGAGEMENT`）：
- YouTube gaming：5.0%（游戏类互动率高是正常的）
- YouTube technology：3.0%
- TikTok entertainment_comedy：7.0%（TikTok 整体互动率高于 YouTube）

**设计考量**：封顶在 1.3× 是为了防止互动率造假或异常数据导致报价失控。同时，比较的是**同垂类的相对水平**而非绝对值——一个互动率 3% 的游戏频道（低于垂类平均 5%）和一个互动率 3% 的科技频道（等于垂类平均 3%）会得到不同的修正。

#### 3.2.2 受众地域修正（Geo Modifier）

基于创作者主要受众所在国家的商业价值：

```python
GEO_TIERS = {
    "US": 1.0,   "UK": 0.95,  "CA": 0.90,  "AU": 0.90,  # Tier 1
    "DE": 0.85,  "FR": 0.80,  "JP": 0.80,  "KR": 0.75,  # Tier 2
    "BR": 0.45,  "MX": 0.40,                              # Tier 3
    "IN": 0.30,  "ID": 0.30,  "VN": 0.30,  "PH": 0.35,  # Tier 4
}
DEFAULT_GEO_MODIFIER = 0.60  # 未知地域
```

**原理**：品牌方根据受众的购买力和广告转化率来评估创作者价值。美国受众的 CPM 是东南亚受众的 3-5 倍，因为前者的广告转化率和客单价远高于后者。

#### 3.2.3 增长动量修正（Growth Modifier）

基于频道的月增长率：

| 月增长率 | 修正系数 | 说明 |
|---------|---------|------|
| > 10% | 1.15× | 快速增长，创作者溢价 |
| 3%-10% | 1.05× | 稳定增长 |
| 0%-3% | 1.00× | 平稳期 |
| < 0% | 0.90× | 下降期，折价 |

**原理**：处于上升期的创作者是"低估资产"——同等合作在 3-6 个月后会更贵。品牌现在锁定合作实际上是在享受折扣。

#### 3.2.4 季节性修正（Seasonal Modifier）

基于当前月份和品牌广告支出周期：

```python
SEASONAL_MODIFIERS = {
    1:  {"default": 0.95, "health_fitness": 1.15},  # 新年健身热潮
    6:  {"default": 0.90, "travel": 1.10},           # 夏季旅行旺季
    7:  {"default": 0.85, "travel": 1.10},
    10: {"default": 1.20},                            # Q4 开始
    11: {"default": 1.35},                            # 黑色星期五
    12: {"default": 1.50},                            # 假日购物季高峰
}
```

**原理**：Q4（10-12月）是品牌广告支出的高峰期（黑五、圣诞、年终预算清算），创作者在此期间有更高的议价能力。某些垂类有自己的旺季：健身类在1月（新年决心）、旅行类在6-7月（暑假）。

#### 3.2.5 内容质量修正（Quality Modifier）

基于可量化的内容质量信号：

```python
if avg_watch_time_pct > 50%: modifier *= 1.1   # 高留存率
if like_ratio > 5%:          modifier *= 1.05  # 高点赞率
```

**原理**：高留存率（平均观看时长占比 > 50%）意味着观众真正在消费内容而非快速划过。这直接影响品牌信息的曝光时长和记忆度。

### 3.3 合同条款定价

Agent B 在 Agent A 的修正后价格基础上，进一步应用合同条款相关的乘数：

```
deal_price = adjusted_price × deliverable_mult × (1 + usage_premium + exclusivity_premium)
```

#### 3.3.1 交付物类型乘数

以"专属视频"为基准（1.0×），其他内容类型按比例折算：

| 交付物（YouTube） | 乘数 | 说明 |
|------------------|------|------|
| dedicated_video | 1.0× | 整条视频专门介绍品牌（基准） |
| integrated_mention | 0.5× | 视频中段 30-60 秒植入 |
| pre_roll_mention | 0.35× | 视频开头 15-30 秒口播 |
| shorts | 0.25× | YouTube Shorts |
| community_post | 0.1× | 社区帖子 |
| pinned_comment | 0.05× | 置顶评论 |
| livestream_mention | 0.4× | 直播中口播 |

#### 3.3.2 使用权溢价

这是创作者最容易被坑的地方。很多品牌在合同中要求额外使用权但不加价：

| 使用权 | 溢价 | 风险等级 |
|--------|------|---------|
| organic_only（仅创作者频道） | 0% | 安全 |
| brand_repost_30d（品牌转发30天） | 15% | 低 |
| whitelisting_30d（白名单投放30天） | 30% | 中 |
| whitelisting_perpetual（永久白名单） | 100% | 高 |
| paid_ads（付费广告素材） | 50% | 中 |
| tv_print（电视/印刷广告） | 200% | 高 |
| perpetual_all_media（永久全媒体） | 300% | 极高 |

#### 3.3.3 排他性溢价

| 排他性 | 溢价 | 说明 |
|--------|------|------|
| none | 0% | 无排他 |
| category_30d | 25% | 同品类排他30天 |
| category_90d | 50% | 同品类排他90天 |
| category_12m | 100% | 同品类排他12个月 |
| full_exclusivity_90d | 100% | 全品类排他90天 |

**计算示例**：
```
基础修正后价格：$1,162（mid）
交付物：植入视频（0.5×）
使用权：品牌社交转发 + 白名单30天（15% + 30% = 45%）
排他性：同品类排他90天（50%）

deal_price = $1,162 × 0.5 × (1 + 0.45 + 0.50)
           = $1,162 × 0.5 × 1.95
           = $1,133
```

### 3.4 已知品牌情报库

系统内置 40+ 个常见品牌赞助商的行为模式数据库（`KNOWN_BRAND_PATTERNS`），每个品牌包含：

```python
{
    "category": "technology",           # 品牌所属品类
    "typical_deal_type": "integrated_mention",  # 典型合作形式
    "budget_tier": "high",              # 预算等级：low/medium/high/very_high
    "negotiation_flexibility": "medium", # 谈判灵活度
    "typical_cpm_range": [30, 50],      # 该品牌的典型 CPM 范围
    "common_requirements": [...],        # 常见要求
    "known_issues": [...],              # 已知问题
    "payment_reliability": "excellent",  # 付款可靠性
}
```

**已收录品牌示例**：NordVPN、SurfShark、Skillshare、Squarespace、Raid Shadow Legends、Audible、BetterHelp、HelloFresh、Shopify、Notion、Samsung、Dyson、Coinbase、Adobe、HubSpot 等。

当用户输入的品牌在库中时，系统直接使用已知数据；不在库中时，由 LLM 根据品牌名称和品类进行推断。

### 3.5 合同红线检测

系统自动检测 8 种常见的合同陷阱：

| 红线规则 | 严重程度 | 触发条件 | 建议 |
|---------|---------|---------|------|
| 永久使用权无加价 | 高 | 永久使用权但溢价 < 30% | 拒绝或要求 200-300% 加价 |
| 无限修改轮次 | 中 | 合同允许无限修改 | 限制为 2-3 轮 |
| 排他性无补偿 | 高 | 全品类排他但溢价 < 30% | 要求至少 50-100% 加价 |
| 超长付款周期 | 中 | 付款超过 Net 90 | 要求 50% 预付或缩短至 Net 30 |
| 单方终止权 | 中 | 品牌可单方面终止 | 加入终止费条款（25-50%） |
| 模糊交付物 | 中 | 交付物描述不明确 | 要求明确数量、格式、截止日期 |
| 内容所有权转让 | 高 | 要求转让内容所有权 | 改为授权使用，保留所有权 |
| 无终止费 | 中 | 合同无终止费条款 | 加入终止费（合同金额25-50%） |

### 3.6 置信度计算

置信度评分基于数据完整性，范围 0.0-1.0：

```python
score = 0.4   # 基础分（有订阅数和播放量）
if has_api_data:    score += 0.15  # 有 API 数据（非手动输入）
if has_engagement:  score += 0.15  # 有互动率
if has_geo:         score += 0.10  # 有受众地域
if has_growth:      score += 0.10  # 有增长率
if has_brand_intel: score += 0.10  # 品牌在已知库中
```

---

## 4. 多 Agent 分析管线

### 4.1 Agent A — 创作者画像分析

**文件**：`backend/app/agents/creator_profile.py`

**职责**：计算创作者的基础商业价值，是整个定价系统的数据基础层。

**处理流程**：

```
输入（频道数据）
    │
    ▼
1. classify_tier() → 频道层级分类（nano/micro/mid_tier/macro/mega）
    │
    ▼
2. calculate_base_price() → CPM × avg_views / 1000
    │
    ▼
3. apply_all_modifiers() → 5 维修正因子
    │
    ▼
4. LLM 定性评估 → 质量/受众/增长/USP/谈判筹码
    │
    ▼
5. 应用定性调整 → clamped ±30%
    │
    ▼
6. 计算展示字段 → niche_display, engagement_vs_niche_avg, growth_trend, channel_age
    │
    ▼
输出（creator_profile + base_price + modifiers + adjusted_price + final_price）
```

**关键设计**：LLM 的定性调整被限制在 -20% 到 +30% 之间（`max(-20, min(30, qual_adj_pct))`），确保 LLM 不会产生偏离基础计算太远的结果。

**输出字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| creator_profile | dict | 频道基础信息 + 4 个展示字段 |
| base_price_range | dict | CPM 计算的原始价格（low/mid/high） |
| applied_modifiers | dict | 5 个修正因子的值和原因 |
| adjusted_price_range | dict | 修正后价格 |
| qualitative_adjustment | dict | LLM 定性调整百分比和原因 |
| final_price_range | dict | 最终价格（供下游 Agent 使用） |
| confidence_score | float | 数据完整性置信度 |
| data_quality_flags | list | 数据质量警告 |

### 4.2 Agent B — 市场情报与合同条款

**文件**：`backend/app/agents/market_data.py`

**职责**：在 Agent A 的基础价格上叠加合同条款（交付物、使用权、排他性），并提供品牌情报和市场上下文。

**处理流程**：

```
输入（Agent A 输出 + 品牌合作条件）
    │
    ▼
1. calculate_deal_adjusted_price() → 交付物 × (1 + 使用权 + 排他性)
    │
    ▼
2. generate_package_tiers() → 三档套餐方案
    │
    ▼
3. lookup_brand() → 已知品牌库查询
    │
    ▼
4. detect_contract_red_flags() → 合同红线检测
    │
    ▼
5. LLM 市场分析 → 可比交易、市场时机、谈判建议
    │
    ▼
6. 应用市场调整 → clamped ±15%
    │
    ▼
输出（deal_price + brand_intel + packages + red_flags + market_context）
```

**三档套餐生成逻辑**：

```python
starter:  price = mid × 0.8   # 入门合作（单次）
standard: price = mid × 2.2   # 标准合作（3个月，比3×单次便宜27%）
premium:  price = mid × 4.0   # 深度合作（6个月，比6×单次便宜33%）
```

**设计考量**：打包方案的定价不是简单的线性倍数。标准方案定价为 2.2× 而非 3×，给品牌方"量大从优"的感知，同时创作者实际获得的总收入更高。研究显示 90%+ 的营销人员使用打包作为谈判策略，60% 报告从未收到反对。

### 4.3 Agent C — 对抗性辩论

**文件**：`backend/app/agents/debate.py`

**职责**：通过 Bull（创作者经纪人）vs Bear（品牌采购经理）的模拟辩论，从对立视角检验定价合理性，最终由 Judge 综合裁定。

**这是系统的核心创新点。** 研究显示，多角色对抗辩论可将估值准确性提升约 8.3%。

**三轮辩论流程**：

```
         Round 1: 独立论证
    ┌──────────┬──────────┐
    │  Bull    │  Bear    │
    │ (temp 0.7)│ (temp 0.3)│
    │ 高温→创造 │ 低温→保守 │
    │ 性论证    │ 性论证    │
    └────┬─────┴────┬─────┘
         │          │
         ▼          ▼
         Round 2: 交叉反驳（asyncio.gather 并行）
    ┌──────────┬──────────┐
    │ Bull 反驳 │ Bear 反驳 │
    │ Bear 论点 │ Bull 论点 │
    └────┬─────┴────┬─────┘
         │          │
         ▼          ▼
         Round 3: 裁判综合
    ┌─────────────────────┐
    │    Judge (temp 0.4)  │
    │  综合原始论证+反驳    │
    │  输出 walk_away /    │
    │  fair_market /       │
    │  anchor_price        │
    └─────────────────────┘
```

**异构 Agent 设计**：

| 角色 | Temperature | 目的 |
|------|------------|------|
| Bull（看多） | 0.7 | 高温产生更有创造性的论证，挖掘被低估的价值点 |
| Bear（看空） | 0.3 | 低温产生更保守、数据驱动的论证 |
| Judge（裁判） | 0.4 | 中低温确保综合判断的稳定性 |

**温度异构的原理**：如果 Bull 和 Bear 使用相同的温度，它们的论证容易趋同——都会找到类似的论据，辩论变得没有意义。通过设置不同温度，确保两方真正从不同角度思考。

**交叉反驳轮（Round 2）**：
- Bull 看到 Bear 的论点后，针对最强的 2-3 个论点进行反驳
- Bear 看到 Bull 的论点后，同样进行反驳
- 两个反驳调用通过 `asyncio.gather()` 并行执行，不增加延迟
- 反驳结果传递给 Judge，使裁判的判断更全面

**价格锚定约束**：Judge 的 `fair_market` 价格被约束在引擎计算的 `price_mid` 的 ±30% 范围内，防止 LLM 辩论产生脱离现实的价格。

**不确定性标记**：如果 Bull 和 Bear 的建议价格差距超过 100%，系统自动标记为"高不确定性"。这本身就是有价值的信息——说明该交易存在重大争议，创作者需要更多信息才能做出决策。

### 4.4 Agent D — 策略报告生成

**文件**：`backend/app/agents/report.py`

**职责**：将所有 Agent 的输出汇总为用户友好的定价策略报告。

**关键约束**：报告中的所有价格数字必须使用引擎计算的精确值，LLM 不得自行生成不同的价格。实现方式是在 LLM 返回后强制覆盖：

```python
result["price_low"] = round(walk_away, 2)
result["price_mid"] = round(fair_market, 2)
result["price_high"] = round(anchor_price, 2)
```

**报告结构**：

1. **Executive Summary** — 2-3 句总结
2. **Price Recommendation** — walk_away / fair_market / anchor_price
3. **Pricing Rationale** — 定价依据
4. **Negotiation Talking Points** — 3-5 个数据支撑的谈判要点
5. **Package Recommendations** — 三档套餐
6. **Contract Red Flags** — 合同风险项
7. **Negotiation Scripts** — 三种场景的谈判话术模板：
   - 品牌主动联系（创作者有优势）
   - 创作者主动 pitch（品牌有优势）
   - 品牌说报价太高（反报价策略）
8. **Timing Advice** — 季节性建议

**多语言支持**：Report Agent 根据用户选择的语言（`self.language`）在 prompt 中注入语言指令，使 LLM 用对应语言生成报告。

---

## 5. LLM 抽象层

### 5.1 LiteLLM 统一接口

**文件**：`backend/app/llm/provider.py`、`backend/app/llm/registry.py`

系统通过 LiteLLM 提供统一的多提供商 LLM 接口，支持 6 家提供商：

| 提供商 | LiteLLM 前缀 | 特殊处理 |
|--------|-------------|---------|
| OpenAI | （无） | 标准 |
| Anthropic | `anthropic/` | 标准 |
| Google Gemini | `gemini/` | 标准 |
| DeepSeek | `deepseek/` | 标准 |
| Moonshot (Kimi) | `openai/` + 自定义 `api_base` | K2.5 跳过 temperature |
| SiliconFlow | `openai/` + 自定义 `api_base` | 标准 |

### 5.2 LLMClient 核心方法

**`chat(messages, temperature)`**：发送聊天请求，返回纯文本。自动处理：
- 推理模型的 `<think>` 标签剥离
- 跳过不支持 temperature 的模型
- 自定义 `api_base` URL

**`chat_json(messages, temperature)`**：发送请求并解析 JSON 响应。处理：
- 自动追加 "Respond with valid JSON only" 指令
- 剥离 markdown 代码围栏
- 解析失败时返回 `{"raw_response": "..."}` 作为降级

**重试机制**：对 `RateLimitError` 和 `APIConnectionError` 采用指数退避重试（最多 3 次）。

### 5.3 特殊模型处理

**Moonshot Kimi K2.5**：这是一个推理模型（reasoning model），会在响应中包含 `<think>...</think>` 推理过程，并且拒绝接受 `temperature != 1` 的参数。系统通过两个机制处理：
1. `skip_temperature_models` 配置跳过 temperature 参数
2. `_strip_think_tags()` 正则剥离 `<think>` 标签

---

## 6. 数据层设计

### 6.1 数据库支持

系统支持双数据库引擎：

| 引擎 | 驱动 | 使用场景 |
|------|------|---------|
| PostgreSQL | asyncpg | Docker 部署、生产环境 |
| SQLite | aiosqlite | Windows EXE、本地开发 |

通过 `DATABASE_URL` 环境变量自动切换。EXE 模式下自动检测 `sys.frozen` 并使用 SQLite。

### 6.2 数据模型

所有模型使用 **UUID 主键** 和 **JSONB 字段**存储灵活的结构化数据：

- **Settings**：LLM 提供商配置（API key 加密存储）
- **Creator**：创作者频道数据
- **AnalysisRun**：分析运行记录（状态、结果 JSONB）
- **Report**：生成的报告

SQLite 下 JSONB 字段自动退化为 TEXT，SQLAlchemy 处理序列化。

### 6.3 API Key 加密

使用 **Fernet 对称加密**保护用户存储的 LLM API key：

```
用户输入 API key → Fernet.encrypt(key) → 存入数据库
需要使用时 → 从数据库读取 → Fernet.decrypt() → 传给 LiteLLM
```

加密密钥通过 `ENCRYPTION_SECRET` 环境变量配置。

---

## 7. 前端架构

### 7.1 页面流程

```
SetupPage → CreatorPage → AnalysisPage → ReportPage
  (配置LLM)   (输入频道+品牌)  (实时进度)     (查看报告)
```

### 7.2 状态管理

使用 **Zustand** 进行全局状态管理，分为三个 store：

- **settingsStore**：LLM 提供商配置状态
- **creatorStore**：创作者数据和品牌信息
- **analysisStore**：分析运行状态和结果

### 7.3 实时进度推送

分析过程通过 **Server-Sent Events (SSE)** 推送 Agent 进度：

```
客户端                          服务端
  │                               │
  │── GET /analysis/{id}/status ──▶│
  │                               │
  │◀── event: agent_progress ─────│  {"agent": "creator_profile", "status": "running"}
  │◀── event: agent_progress ─────│  {"agent": "creator_profile", "status": "completed"}
  │◀── event: agent_progress ─────│  {"agent": "market_intel", "status": "running"}
  │◀── event: agent_progress ─────│  {"agent": "market_intel", "status": "completed"}
  │◀── event: agent_progress ─────│  {"agent": "debate", "status": "running"}
  │◀── event: agent_progress ─────│  {"agent": "debate", "status": "completed"}
  │◀── event: agent_progress ─────│  {"agent": "report", "status": "running"}
  │◀── event: agent_progress ─────│  {"agent": "report", "status": "completed"}
  │◀── event: complete ───────────│
  │                               │
```

快速通道模式下，`market_intel` 和 `debate` 会收到 `"status": "skipped"` 事件。

### 7.4 关键组件

- **AgentProgress**：实时显示各 Agent 的运行状态（running/completed/skipped）
- **PriceRangeChart**：可视化价格区间（walk_away / fair_market / anchor）
- **DetailedAnalysis**：展开式详细分析面板
- **ReportPage**：完整报告展示，含谈判话术、套餐方案、红线检测

---

## 8. 部署架构

### 8.1 Windows EXE 模式

```
PyInstaller 打包：
  backend/ (Python 代码)
  + frontend/dist/ (Vite 构建产物)
  → KnowYourRate.exe（单文件）

运行时：
  KnowYourRate.exe
    → 启动 uvicorn (port 8000)
    → FastAPI 静态文件服务 frontend_dist/
    → 自动打开浏览器 http://localhost:8000
    → SQLite 数据库在同目录
```

通过 GitHub Actions 在 tag push 时自动构建：
1. 安装 Node.js，构建前端
2. 安装 Python 依赖
3. 运行 PyInstaller
4. 上传到 GitHub Release

### 8.2 Docker Compose 模式

```yaml
services:
  db:        PostgreSQL 16
  backend:   Python/FastAPI (port 8000)
  frontend:  Nginx (port 3000) → 代理 API 到 backend
```

### 8.3 本地开发模式

```
终端 1: cd backend && uvicorn app.main:app --reload --port 8000
终端 2: cd frontend && npm run dev  (port 5173, 代理到 8000)
```

---

## 9. 安全设计

### 9.1 API Key 保护

- 用户的 LLM API key 使用 Fernet 对称加密存储
- 加密密钥通过环境变量注入，不硬编码
- API key 仅在调用 LLM 时解密，不在日志中输出

### 9.2 无认证设计

系统定位为**单用户本地工具**，不实现用户认证。这是有意的设计决策——简化部署，降低使用门槛。Windows EXE 用户只需双击运行即可使用。

### 9.3 数据隔离

- 每次分析运行有独立的 UUID，结果存储在 JSONB 字段中
- SQLite 文件保存在本地，不上传到任何云端
- LLM 调用直接发送到用户选择的提供商，系统不做中转

---

## 10. 性能与成本分析

### 10.1 延迟预算

| 管线 | Agent 调用 | LLM 调用次数 | 预计延迟 |
|------|-----------|-------------|---------|
| 快速通道 | A → D | 2 | 5-15 秒 |
| 完整管线 | A → B → C（3轮） → D | 7 | 30-60 秒 |

Agent C 的交叉反驳轮（Round 2）通过 `asyncio.gather()` 并行执行 Bull 和 Bear 的反驳，不额外增加延迟。

### 10.2 Token 消耗估算

| 管线 | 输入 Token | 输出 Token | 总计 |
|------|-----------|-----------|------|
| 快速通道 | ~2,000 | ~1,500 | ~3,500 |
| 完整管线 | ~12,000 | ~8,000 | ~20,000 |

### 10.3 费用估算（以主流模型为例）

| 模型 | 快速通道费用 | 完整管线费用 |
|------|-----------|-----------|
| GPT-4o-mini | ~$0.002 | ~$0.01 |
| GPT-4o | ~$0.02 | ~$0.10 |
| Claude Sonnet 4 | ~$0.02 | ~$0.12 |
| DeepSeek-Chat | ~$0.001 | ~$0.005 |

### 10.4 验证标准

一个好的定价分析应满足以下标准：

1. **合理性**：输出价格落在对应层级的 typical_range 内（±30% 容差）
2. **修正因子敏感性**：互动率从 2% 变为 8% 应导致报价变化 20-60%
3. **合同条款影响**："永久全媒体 + 12个月全品类排他"应使报价至少翻 3 倍
4. **季节性**：同一创作者 Q4 vs 夏季报价应有 15-40% 差异
5. **垂类差异**：同样 50K 粉丝，财经类报价应为娱乐类的 2-4 倍
6. **置信度校准**：数据越完整，置信度越高

---

## 附录 A：数据表完整清单

| 数据表 | 位置 | 条目数 | 用途 |
|--------|------|--------|------|
| NICHE_CPM_TABLE | pricing_tables.py | 30（2平台×15垂类） | CPM 基准 |
| NICHE_AVG_ENGAGEMENT | pricing_tables.py | 30 | 互动率修正基准 |
| NICHE_DISPLAY_NAMES | pricing_tables.py | 15 | 垂类中文显示名 |
| TIER_TABLE | pricing_tables.py | 10（2平台×5层级） | 频道分级 |
| DELIVERABLE_MULTIPLIERS | pricing_tables.py | 12（2平台×6-7类型） | 交付物定价 |
| USAGE_RIGHTS_PREMIUMS | pricing_tables.py | 11 | 使用权溢价 |
| EXCLUSIVITY_PREMIUMS | pricing_tables.py | 7 | 排他性溢价 |
| KNOWN_BRAND_PATTERNS | pricing_tables.py | 40+ | 品牌情报 |
| CONTRACT_RED_FLAGS | pricing_tables.py | 8 | 合同风险 |
| SEASONAL_MODIFIERS | pricing_tables.py | 12（按月） | 季节性调整 |
| GEO_TIERS | pricing_tables.py | 15 | 地域定价 |

## 附录 B：完整 API 端点列表

| 方法 | 端点 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| GET | `/api/health` | - | `{"status": "ok"}` | 健康检查 |
| GET | `/api/settings/providers` | - | 提供商列表 + 模型列表 | 获取可用 LLM |
| POST | `/api/settings/provider` | `{provider, api_key, model}` | 保存确认 | 配置 LLM |
| POST | `/api/settings/provider/test` | `{provider, api_key, model}` | 测试结果 | 测试连通性 |
| POST | `/api/creators/lookup` | `{platform, url}` | 频道数据 | YouTube API 查询 |
| POST | `/api/analysis/run` | `{creator_data, brand_info}` | `{run_id}` | 启动分析 |
| GET | `/api/analysis/{id}/status` | - | SSE 事件流 | 实时进度 |
| GET | `/api/analysis/{id}/result` | - | 完整分析结果 | 获取结果 |
| GET | `/api/reports` | - | 报告列表 | 历史报告 |
| POST | `/api/reports` | 报告数据 | 保存确认 | 保存报告 |
| DELETE | `/api/reports/{id}` | - | 删除确认 | 删除报告 |
