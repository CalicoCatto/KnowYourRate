[English](./README.md) | [中文](./README_zh.md)

# KnowYourRate

**多 Agent AI 驱动的创作者品牌合作定价情报引擎**

KnowYourRate 帮助内容创作者确定品牌合作的公平报价。系统通过 4 个专业 AI Agent 将确定性 CPM 计算与 LLM 定性推理相结合，进行多维度深度分析，输出包含谈判策略的可执行定价报告。

## 版本

KnowYourRate 从同一代码库构建两个版本：

| | 国际版 | 中国版 |
|---|---|---|
| **平台** | YouTube、TikTok | B站、抖音、快手 |
| **货币** | USD | CNY（人民币） |
| **修正因子系统** | 乘法累积 | 加法累积，上限 [0.4, 2.0] |
| **核心指标** | 互动率 | VF 比（粉丝播放比） |
| **地域修正** | 国家维度（US/UK/IN） | 城市等级（一线/新一线/二线/三线） |
| **品牌数据库** | 40+ 国际品牌 | 20 国内品牌（得物、蔚来、米哈游等） |
| **合同红线** | 8 条规则 | 15 条规则（广告法、肖像权、数据安全） |
| **季节性事件** | Q4 节日、超级碗 | 双11、618、春节、开学季 |
| **中国版专有** | — | 税费估算（3 种纳税方式）、平台官方报价（花火/星图/磁力聚星）、直播电商（坑位费+佣金）、MCN 分成参考、广告法合规 |

## 痛点

内容创作者在品牌合作中普遍被低估。研究表明，创作者平均被品牌方压价 30-50%。现有工具（如 Social Bluebook）仅基于粉丝数给出静态估价——这种单一维度完全忽略了受众质量、品牌背景、季节性时机和谈判筹码。

## 工作原理

输入你的频道信息和品牌合作细节，系统通过复杂度分类器路由查询，运行相应的分析管线：

```
用户输入 → 复杂度路由器 → 快速通道 或 完整分析

快速通道（简单查询，约15秒）:
  Agent A（创作者画像 + CPM 定价）→ Agent D（策略报告）

完整分析（复杂交易，约60秒）:
  Agent A（创作者画像）→ Agent B（市场情报 + 合同条款）
    → Agent C（多空辩论 + 交叉反驳）→ Agent D（策略报告）
```

### 核心设计原则

**计算用代码，推理用 LLM。** 所有定价计算（CPM × 播放量、互动率/地域/增长/季节/质量修正因子、合同条款乘数）均在 Python 中确定性计算。LLM 仅用于定性评估、品牌情报分析、对抗性辩论和报告撰写。这确保了无论使用哪个 LLM 模型，定价结果都是一致、可复现的。

### 4 个 Agent

| Agent | 角色 | LLM 用途 |
|-------|------|----------|
| **A — 创作者画像** | 从 CPM 表计算基础价格，应用修正因子，请求 LLM 做定性调整（限制 ±30%） | 仅定性评估 |
| **B — 市场情报** | 应用合同条款乘数（交付物类型、使用权、排他性），查询已知品牌库，生成三档套餐，检测合同红线，请求 LLM 提供市场上下文 | 品牌情报、可比交易 |
| **C — 对抗辩论** | 三轮对抗辩论：Bull（创作者经纪人，温度 0.7）vs Bear（品牌采购经理，温度 0.3），交叉反驳轮（并行），裁判（温度 0.4）综合裁定最终报价区间（底线价/公平价/锚定价） | 完整辩论推理 |
| **D — 策略报告** | 使用精确计算价格生成叙事报告，包含套餐方案、三种场景谈判话术和合同红线 | 报告撰写 |

**输出内容：**
- 报价区间（底线价 / 公平市场价 / 锚定价）及理由说明
- 按内容类型细分报价（专属视频、植入、短视频等）
- 三档套餐推荐（入门 / 标准 / 深度）
- 三种场景的谈判话术模板
- 合同条款红线与陷阱预警
- 市场背景与同类创作者参考
- **中国版额外输出**：税费估算（劳务报酬 / 个体工商户 / 公司）、平台官方报价参考（花火/星图/磁力聚星手续费）、直播电商定价（坑位费+佣金）、MCN 分成参考、广告法合规提示

## 支持平台

| 平台 | 数据来源 | 版本 |
|------|---------|------|
| YouTube | YouTube Data API v3（自动获取） | 国际版 |
| TikTok | 手动输入表单 | 国际版 |
| B站 (Bilibili) | 手动输入表单（投币率、收藏率等） | 中国版 |
| 抖音 (Douyin) | 手动输入表单（完播率、转发率、星图建议价） | 中国版 |
| 快手 (Kuaishou) | 手动输入表单（回访率、直播观看/粉丝比） | 中国版 |

## 支持的大模型

选择你偏好的大模型提供商，使用自己的 API Key：

| 提供商 | 模型 |
|--------|------|
| **OpenAI** | GPT-4o、GPT-4o-mini、GPT-4-turbo |
| **Anthropic** | Claude Sonnet 4、Claude Haiku 3.5 |
| **Google** | Gemini 2.0 Flash、Gemini 1.5 Pro |
| **DeepSeek** | DeepSeek-Chat、DeepSeek-Reasoner |
| **月之暗面 (Kimi)** | Kimi K2.5、Kimi K2 |
| **SiliconFlow** | DeepSeek V3.2、MiniMax M2.5、GLM-4.7、GLM-5、Step 3.5 Flash |

## 快速开始

### 方式一：Windows EXE（最简单）

无需安装任何环境，下载即用。

1. 前往 [Releases](https://github.com/CalicoCatto/KnowYourRate/releases) 页面
2. 下载：
   - `KnowYourRate-windows-x64.zip` — 国际版
   - `KnowYourRate-CN-windows-x64.zip` — 中国版
3. 解压后双击运行 EXE
4. 浏览器自动打开 `http://localhost:8000`

数据存储在 EXE 同目录下的 SQLite 数据库文件（`knowyourrate.db`）中。

### 方式二：Docker Compose

```bash
git clone https://github.com/CalicoCatto/KnowYourRate.git
cd KnowYourRate
cp .env.example .env
# 编辑 .env 设置 ENCRYPTION_SECRET（见下方说明）

# 国际版
docker compose up -d

# 中国版
EDITION=cn docker compose up -d
```

浏览器打开 [http://localhost:3000](http://localhost:3000) 即可使用。

### 方式三：本地开发

**后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 国际版（SQLite）
DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000

# 中国版（SQLite）
EDITION=cn DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install

# 国际版
npm run dev

# 中国版
VITE_EDITION=cn npm run dev
```

前端运行在 [http://localhost:5173](http://localhost:5173)，API 自动代理到 8000 端口。

### 生成加密密钥（可选）

应用会对存储的 API Key 进行加密。生产环境建议生成专用密钥：

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将输出粘贴到 `.env` 文件的 `ENCRYPTION_SECRET` 字段。

## 架构

```
KnowYourRate/
├── backend/                  # Python / FastAPI
│   ├── app/
│   │   ├── main.py              # 应用工厂、CORS、静态文件、SPA 路由
│   │   ├── config.py             # 配置（DATABASE_URL、ENCRYPTION_SECRET）
│   │   ├── database.py           # SQLAlchemy 异步引擎 + 会话工厂
│   │   ├── edition.py            # 版本检测（EDITION 环境变量）
│   │   ├── agents/               # 4 个 AI Agent + 编排器
│   │   │   ├── creator_profile.py     # Agent A（国际版）
│   │   │   ├── creator_profile_cn.py  # Agent A（中国版：加法修正、VF 比）
│   │   │   ├── market_data.py         # Agent B（国际版）
│   │   │   ├── market_data_cn.py      # Agent B（中国版：平台报价、直播）
│   │   │   ├── debate.py              # Agent C（共享，按版本加载提示词）
│   │   │   ├── report.py              # Agent D（国际版）
│   │   │   ├── report_cn.py           # Agent D（中国版：税费、合规）
│   │   │   └── orchestrator.py        # 管线路由 + 协调（版本感知）
│   │   ├── api/routes/           # REST API 端点
│   │   ├── llm/                  # LiteLLM 多模型抽象层（6 家提供商）
│   │   ├── models/               # SQLAlchemy ORM（settings, creator, analysis_run, report）
│   │   ├── schemas/              # Pydantic 请求/响应模式
│   │   ├── services/             # YouTube、TikTok、B站、抖音、快手、加密服务
│   │   └── utils/
│   │       ├── prompts.py            # 国际版提示词模板（7 个）
│   │       ├── prompts_cn.py         # 中国版提示词模板（7 个，中文）
│   │       ├── pricing_tables.py     # 国际版 CPM 表、乘数、修正因子、品牌库
│   │       └── pricing_tables_cn.py  # 中国版 CPM 表、加法修正、税费、直播
│   ├── run.py                    # 国际版 EXE 入口
│   ├── run_cn.py                 # 中国版 EXE 入口（设置 EDITION=cn）
│   ├── knowyourrate.spec         # 国际版 PyInstaller 配置
│   └── knowyourrate_cn.spec      # 中国版 PyInstaller 配置
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/                # 设置 → 创作者 → 分析 → 报告 → 历史
│       ├── components/           # PlatformSelector、PriceRangeChart 等
│       ├── api/                  # Axios API 客户端 + SSE 订阅
│       ├── store/                # Zustand 状态管理（3 个 Store）
│       └── types/index.ts        # 类型定义 + 版本检测（VITE_EDITION）
├── .github/workflows/
│   └── build-exe.yml             # 国际版 + 中国版 EXE 并行构建
└── docker-compose.yml            # 一键部署
```

### 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy（异步）、LiteLLM |
| 前端 | React 18、TypeScript、Vite、Tailwind CSS v4、Zustand、Recharts |
| 数据库 | PostgreSQL 16 或 SQLite（自动检测） |
| 大模型 | LiteLLM（6 家提供商统一接口） |
| 国际化 | i18next（英文 + 中文） |
| 部署 | Docker Compose、Windows EXE（×2）或本地开发 |

### 版本系统

两个版本共享同一代码库，通过环境变量选择版本：

- **后端**：`EDITION=cn` 通过 `orchestrator.py` 中的条件导入加载中国版 Agent、数据表和提示词
- **前端**：`VITE_EDITION=cn`（构建时）显示中国版平台、合作类型和界面元素
- **EXE 构建**：独立的 PyInstaller 配置分别生成 `KnowYourRate.exe` 和 `KnowYourRate-CN.exe`

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查（包含 `edition` 字段） |
| GET | `/api/settings/providers` | 获取支持的大模型列表 |
| POST | `/api/settings/provider` | 保存大模型配置 + API Key |
| POST | `/api/settings/provider/test` | 测试 API Key 连通性 |
| POST | `/api/creators/lookup` | 获取创作者频道数据 |
| POST | `/api/analysis/run` | 启动分析 Pipeline |
| GET | `/api/analysis/{id}/status` | SSE 实时推送分析进度 |
| GET | `/api/analysis/{id}/result` | 获取分析结果 |
| GET/POST/DELETE | `/api/reports[/{id}]` | 报告管理 |

## 使用流程

1. **设置** — 选择大模型提供商，输入 API Key，测试连接。
2. **创作者信息** — 选择平台，输入频道链接或手动填写数据。填写品牌名称、合作类型、使用权和排他性条款。中国版用户还需填写平台特定指标（投币率、完播率、回访率）和城市等级。
3. **分析** — 实时查看 4 个 Agent 的运行进度（SSE 推送）。快速通道查询跳过 Agent B 和 C。
4. **报告** — 查看定价情报报告，包含报价区间、谈判话术、套餐方案和合同红线。中国版还包含税费估算和平台官方报价参考。报告自动保存，可随时回顾。

## 国际化

应用支持英文和简体中文，可在页面顶部切换语言。AI Agent 生成的报告会使用你选择的语言输出。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 是 | 数据库连接字符串（PostgreSQL 或 SQLite） |
| `ENCRYPTION_SECRET` | 是 | Fernet 密钥，用于加密存储的 API Key |
| `YOUTUBE_API_KEY` | 否 | YouTube Data API v3 密钥，用于自动获取频道数据 |
| `EDITION` | 否 | 后端版本：`international`（默认）或 `cn` |
| `VITE_EDITION` | 否 | 前端版本（构建时）：`international`（默认）或 `cn` |
| `DB_PASSWORD` | Docker | PostgreSQL 密码（默认 `changeme`） |

## 构建 EXE

```bash
# 国际版
cd frontend && npm run build
cd ../backend && pip install -e ".[build]" && pyinstaller knowyourrate.spec --noconfirm

# 中国版
cd frontend && VITE_EDITION=cn npm run build
cd ../backend && pip install -e ".[build]" && pyinstaller knowyourrate_cn.spec --noconfirm
```

两个 EXE 也会通过 GitHub Actions 在推送标签（`v*`）时自动构建。

## 许可证

MIT
