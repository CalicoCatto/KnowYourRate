[English](./README.md) | [中文](./README_zh.md)

# KnowYourRate

**AI Agent 驱动的创作者品牌合作定价情报引擎**

KnowYourRate 帮助 YouTube 和 TikTok 创作者确定品牌合作的公平报价。不再靠猜测或使用过时的计算器，而是通过 5 个专业 AI Agent 从市场行情、创作者价值、品牌预算、谈判博弈等多维度进行深度分析。

## 痛点

内容创作者在品牌合作中普遍被低估。研究表明，创作者平均被品牌方压价 30-50%。现有工具（如 Social Bluebook）仅基于粉丝数给出静态估价——这种单一维度完全忽略了受众质量、品牌背景和谈判筹码。

## 工作原理

输入你的频道信息和品牌合作细节，5 个 AI Agent 并行分析，2 分钟内生成可执行的定价报告：

```
阶段 1（并行）:
  ├── 市场数据 Agent        → 行业基准与趋势
  ├── 创作者画像 Agent      → 你的独特价值评估
  └── 品牌策略 Agent        → 品牌预算与谈判模式

阶段 2:
  └── 辩论验证 Agent        → 模拟品牌方 vs 创作者谈判

阶段 3:
  └── 策略报告 Agent        → 最终定价报告与策略
```

**输出内容：**
- 报价区间（低 / 中 / 高）及理由说明
- 按内容类型细分报价（专属视频、植入、短视频等）
- 可直接使用的谈判话术
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
│   │   ├── agents/           # 5 个 AI Agent + 编排器
│   │   ├── api/routes/       # REST API 端点
│   │   ├── llm/              # LiteLLM 多模型抽象层
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应模式
│   │   ├── services/         # YouTube API、TikTok、加密服务
│   │   └── utils/            # Prompt 模板
│   └── tests/
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/            # 设置 → 创作者 → 分析 → 报告
│       ├── components/       # 可复用 UI 组件
│       ├── api/              # API 客户端
│       └── store/            # Zustand 状态管理
└── docker-compose.yml        # 一键部署
```

### 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy（异步）、Alembic |
| 前端 | React 18、TypeScript、Vite、Tailwind CSS v4 |
| 数据库 | PostgreSQL 16 |
| 大模型 | LiteLLM（多提供商统一接口） |
| 部署 | Docker Compose |

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
2. **创作者信息** — 选择平台（YouTube / TikTok），输入频道链接或手动填写数据。填写品牌名称和合作类型。
3. **分析** — 实时查看 5 个 Agent 的运行进度。
4. **报告** — 查看定价情报报告。可保存报告或开始新的分析。

## 国际化

应用支持英文和简体中文，可在页面顶部切换语言。AI Agent 生成的报告会使用你选择的语言输出。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DB_PASSWORD` | 是 | PostgreSQL 密码（默认 `changeme`） |
| `DATABASE_URL` | 是 | 完整数据库连接字符串 |
| `ENCRYPTION_SECRET` | 是 | Fernet 密钥，用于加密存储的 API Key |
| `YOUTUBE_API_KEY` | 否 | YouTube Data API v3 密钥，用于自动获取频道数据 |

## 许可证

MIT
