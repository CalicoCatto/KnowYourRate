[English](./README.md) | [中文](./README_zh.md)

# KnowYourRate

**多 Agent AI 驱动的创作者品牌合作定价情报引擎**

KnowYourRate 帮助 YouTube 和 TikTok 创作者确定品牌合作的公平报价。系统通过 4 个专业 AI Agent 将确定性 CPM 计算与 LLM 定性推理相结合，进行多维度深度分析，输出包含谈判策略的可执行定价报告。

## 痛点

内容创作者在品牌合作中普遍被低估。研究表明，创作者平均被品牌方压价 30-50%。现有工具（如 Social Bluebook）仅基于粉丝数给出静态估价——这种单一维度完全忽略了受众质量、品牌背景、季节性时机和谈判筹码。

## 工作原理

输入你的频道信息和品牌合作细节，系统通过复杂度分类器路由查询，运行相应的分析管线：

```
用户输入 → 复杂度路由器 → 快速通道 或 完整分析

快速通道（简单查询，约15秒）:
  Agent A（创作者画像 + CPM定价）→ Agent D（策略报告）

完整分析（复杂交易，约60秒）:
  Agent A（创作者画像）→ Agent B（市场情报 + 合同条款）
    → Agent C（多空辩论 + 交叉反驳）→ Agent D（策略报告）
```

### 核心设计原则

**计算用代码，推理用 LLM。** 所有定价计算（CPM × 播放量、互动率/地域/增长/季节/质量修正因子、合同条款乘数）均在 Python 中确定性计算。LLM 仅用于定性评估、品牌情报分析、对抗性辩论和报告撰写。这确保了无论使用哪个 LLM 模型，定价结果都是一致、可复现的。

### 4 个 Agent

| Agent | 角色 | LLM 用途 |
|-------|------|----------|
| **A — 创作者画像** | 从 CPM 表计算基础价格，应用 5 类修正因子，请求 LLM 做定性调整（限制 ±30%） | 仅定性评估 |
| **B — 市场情报** | 应用合同条款乘数（交付物类型、使用权、排他性），查询 40+ 已知品牌库，请求 LLM 提供市场上下文 | 品牌情报、可比交易 |
| **C — 对抗辩论** | 三轮对抗辩论：Bull（创作者经纪人，温度 0.7）vs Bear（品牌采购经理，温度 0.3），交叉反驳轮，裁判（温度 0.4）综合裁定 | 完整辩论推理 |
| **D — 策略报告** | 使用精确计算价格生成叙事报告，包含套餐方案、谈判话术和合同红线 | 报告撰写 |

**输出内容：**
- 报价区间（底线价 / 公平市场价 / 锚定价）及理由说明
- 按内容类型细分报价（专属视频、植入、短视频等）
- 三档套餐推荐（入门 / 标准 / 深度）
- 三种场景的谈判话术模板
- 合同条款红线与陷阱预警
- 市场背景与同类创作者参考

## 支持平台

| 平台 | 数据来源 | 状态 |
|------|---------|------|
| YouTube | YouTube Data API v3（自动获取） | 可用 |
| TikTok | 手动输入表单 | 可用 |

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

提供三种运行方式：

### 方式一：Windows EXE（最简单）

无需安装任何环境，下载即用。

1. 前往 [Releases](https://github.com/CalicoCatto/KnowYourRate/releases) 页面
2. 下载 `KnowYourRate-windows-x64.zip`
3. 解压后双击运行 `KnowYourRate.exe`
4. 浏览器自动打开 `http://localhost:8000`

数据存储在 EXE 同目录下的 SQLite 数据库文件（`knowyourrate.db`）中。

### 方式二：Docker Compose

```bash
git clone https://github.com/CalicoCatto/KnowYourRate.git
cd KnowYourRate
cp .env.example .env
# 编辑 .env 设置 ENCRYPTION_SECRET（见下方说明）
docker compose up -d
```

浏览器打开 [http://localhost:3000](http://localhost:3000) 即可使用。

### 方式三：本地开发

**后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 方案 A：使用 SQLite（零配置）
DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000

# 方案 B：使用 PostgreSQL
docker compose up db -d
DATABASE_URL="postgresql+asyncpg://kyr:changeme@localhost:5432/knowyourrate" \
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
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
│   │   ├── agents/           # 4 个 AI Agent + 编排器
│   │   │   ├── creator_profile.py  # Agent A：CPM 计算 + 定性评估
│   │   │   ├── market_data.py      # Agent B：合同条款 + 品牌情报
│   │   │   ├── debate.py           # Agent C：多空对抗辩论
│   │   │   ├── report.py           # Agent D：策略报告生成
│   │   │   └── orchestrator.py     # 管线路由 + 协调
│   │   ├── api/routes/       # REST API 端点
│   │   ├── llm/              # LiteLLM 多模型抽象层
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应模式
│   │   ├── services/         # YouTube API、TikTok、加密服务
│   │   └── utils/
│   │       ├── prompts.py       # 所有 Agent prompt 模板
│   │       └── pricing_tables.py # CPM 表、乘数、修正因子、品牌库
│   └── tests/
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/            # 设置 → 创作者 → 分析 → 报告
│       ├── components/       # 可复用 UI 组件
│       ├── api/              # API 客户端 + SSE 辅助
│       └── store/            # Zustand 状态管理
└── docker-compose.yml        # 一键部署
```

### 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy（异步）、LiteLLM |
| 前端 | React 18、TypeScript、Vite、Tailwind CSS v4、Zustand |
| 数据库 | PostgreSQL 16 或 SQLite（自动检测） |
| 大模型 | LiteLLM（6 家提供商统一接口） |
| 部署 | Docker Compose、Windows EXE 或本地开发 |

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
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
2. **创作者信息** — 选择平台（YouTube / TikTok），输入频道链接或手动填写数据。填写品牌名称、合作类型、使用权和排他性条款。
3. **分析** — 实时查看 4 个 Agent 的运行进度（SSE 推送）。快速通道查询跳过 Agent B 和 C。
4. **报告** — 查看定价情报报告，包含报价区间、谈判话术、套餐方案和合同红线。可保存报告或开始新的分析。

## 国际化

应用支持英文和简体中文，可在页面顶部切换语言。AI Agent 生成的报告会使用你选择的语言输出。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 是 | 数据库连接字符串（PostgreSQL 或 SQLite） |
| `ENCRYPTION_SECRET` | 是 | Fernet 密钥，用于加密存储的 API Key |
| `YOUTUBE_API_KEY` | 否 | YouTube Data API v3 密钥，用于自动获取频道数据 |
| `DB_PASSWORD` | Docker | PostgreSQL 密码（默认 `changeme`） |

## 许可证

MIT
