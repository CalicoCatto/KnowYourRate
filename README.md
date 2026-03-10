[English](./README.md) | [中文](./README_zh.md)

# KnowYourRate

**Multi-agent pricing intelligence engine for content creators**

KnowYourRate helps content creators determine fair pricing for brand collaborations. Instead of guessing or relying on outdated calculators, creators get multi-dimensional analysis from 4 specialized AI agents that combine deterministic CPM calculations with qualitative LLM reasoning, producing actionable pricing reports with negotiation strategies.

## Editions

KnowYourRate ships in two editions from a single codebase:

| | International | CN (中国版) |
|---|---|---|
| **Platforms** | YouTube, TikTok | B站 (Bilibili), 抖音 (Douyin), 快手 (Kuaishou) |
| **Currency** | USD | CNY (人民币) |
| **Modifier System** | Multiplicative | Additive with cap [0.4, 2.0] |
| **Core Metric** | Engagement rate | VF ratio (粉丝播放比) |
| **Geo Modifiers** | Country-based (US/UK/IN) | City tier (一线/新一线/二线/三线) |
| **Brand Database** | 40+ international brands | 20 CN brands (得物, 蔚来, 米哈游, etc.) |
| **Contract Red Flags** | 8 rules | 15 rules (广告法, 肖像权, 数据安全) |
| **Seasonal Events** | Q4 holiday, Super Bowl | 双11, 618, 春节, 开学季 |
| **CN-Only Features** | — | Tax estimation (3 regimes), platform official pricing (花火/星图/磁力聚星), livestream commerce (坑位费+佣金), MCN commission reference, ad law compliance |

## The Problem

Content creators are systematically underpaid in brand deals. Research shows creators are lowballed by 30-50% on average. Existing tools like Social Bluebook only offer static estimates based on follower count — a single dimension that misses audience quality, brand context, seasonal timing, and negotiation leverage.

## How It Works

Enter your channel info and the brand deal details. The system routes your query through a complexity classifier and runs the appropriate pipeline:

```
User Input → Complexity Router → fast_track or full_pipeline

fast_track (simple queries, ~15s):
  Agent A (Creator Profile + CPM Pricing) → Agent D (Strategy Report)

full_pipeline (complex deals, ~60s):
  Agent A (Creator Profile) → Agent B (Market Intel + Deal Terms)
    → Agent C (Bull vs Bear Debate with Cross-Rebuttal) → Agent D (Report)
```

### Core Design Principle

**Math in code, reasoning in LLM.** All pricing calculations (CPM × views, engagement/geo/growth/seasonal/quality modifiers, deal multipliers) are computed deterministically in Python. LLM is only used for qualitative assessment, brand intelligence, adversarial debate, and report narrative. This ensures consistent, reproducible pricing regardless of which LLM model is used.

### The 4 Agents

| Agent | Role | LLM Usage |
|-------|------|-----------|
| **A — Creator Profile** | Computes base price from CPM tables, applies modifier categories, asks LLM for qualitative adjustment (clamped ±30%) | Qualitative assessment only |
| **B — Market Intel** | Applies deal condition multipliers (deliverable type, usage rights, exclusivity), looks up known brand patterns, generates 3-tier packages, detects contract red flags, asks LLM for market context | Brand intelligence, comparable deals |
| **C — Debate** | 3-round adversarial debate: Bull (creator agent, temp 0.7) vs Bear (brand manager, temp 0.3), cross-rebuttal round (parallel), then Judge (temp 0.4) synthesizes final range (walk_away / fair_market / anchor_price) | Full debate reasoning |
| **D — Report** | Generates narrative report using exact computed prices, package tiers, negotiation scripts for 3 scenarios, and contract red flags | Report writing |

**Output includes:**
- Price range (walk-away / fair market / anchor) with reasoning
- Per-content-type breakdown (dedicated video, integration, short, etc.)
- 3-tier package recommendations (Starter / Standard / Premium)
- Negotiation talking points and scripts for 3 scenarios
- Contract red flags and clause warnings
- Market context and comparable benchmarks
- **CN-only**: Tax estimation (劳务报酬 / 个体工商户 / 公司), platform official pricing reference (花火/星图/磁力聚星 fees), livestream commerce pricing (坑位费 + 佣金), MCN commission reference, ad law compliance

## Supported Platforms

| Platform | Data Source | Edition |
|----------|-----------|---------|
| YouTube  | YouTube Data API v3 (auto-fetch) | International |
| TikTok   | Manual input form | International |
| B站 (Bilibili) | Manual input form (投币率, 收藏率, etc.) | CN |
| 抖音 (Douyin) | Manual input form (完播率, 转发率, 星图建议价) | CN |
| 快手 (Kuaishou) | Manual input form (回访率, 直播观看/粉丝比) | CN |

## Supported LLM Providers

Choose your preferred LLM provider — bring your own API key:

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4-turbo |
| **Anthropic** | Claude Sonnet 4, Claude Haiku 3.5 |
| **Google** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-Reasoner |
| **Moonshot (Kimi)** | Kimi K2.5, Kimi K2 |
| **SiliconFlow** | DeepSeek V3.2, MiniMax M2.5, GLM-4.7, GLM-5, Step 3.5 Flash |

## Quick Start

### Option 1: Windows EXE (Easiest)

No installation needed. Download and double-click.

1. Go to [Releases](https://github.com/CalicoCatto/KnowYourRate/releases)
2. Download:
   - `KnowYourRate-windows-x64.zip` — International edition
   - `KnowYourRate-CN-windows-x64.zip` — CN edition (中国版)
3. Unzip and run the EXE
4. The browser opens automatically at `http://localhost:8000`

Data is stored in a SQLite database (`knowyourrate.db`) in the same folder as the EXE.

### Option 2: Docker Compose

```bash
git clone https://github.com/CalicoCatto/KnowYourRate.git
cd KnowYourRate
cp .env.example .env
# Edit .env to set your ENCRYPTION_SECRET (see below)

# International edition
docker compose up -d

# CN edition
EDITION=cn docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Option 3: Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# International edition (SQLite)
DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000

# CN edition (SQLite)
EDITION=cn DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install

# International edition
npm run dev

# CN edition
VITE_EDITION=cn npm run dev
```

Frontend runs at [http://localhost:5173](http://localhost:5173), API proxied to port 8000.

### Generate an Encryption Secret (Optional)

The app encrypts stored API keys at rest. Generate a secret for production:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into your `.env` file as `ENCRYPTION_SECRET`.

## Architecture

```
KnowYourRate/
├── backend/                  # Python / FastAPI
│   ├── app/
│   │   ├── main.py              # App factory, CORS, static serving, SPA catch-all
│   │   ├── config.py             # Settings (DATABASE_URL, ENCRYPTION_SECRET)
│   │   ├── database.py           # SQLAlchemy async engine + session factory
│   │   ├── edition.py            # Edition detection (EDITION env var)
│   │   ├── agents/               # 4 AI agents + orchestrator
│   │   │   ├── creator_profile.py     # Agent A (international)
│   │   │   ├── creator_profile_cn.py  # Agent A (CN: additive modifiers, VF ratio)
│   │   │   ├── market_data.py         # Agent B (international)
│   │   │   ├── market_data_cn.py      # Agent B (CN: platform pricing, livestream)
│   │   │   ├── debate.py              # Agent C (shared, edition-aware prompts)
│   │   │   ├── report.py              # Agent D (international)
│   │   │   ├── report_cn.py           # Agent D (CN: tax, compliance)
│   │   │   └── orchestrator.py        # Pipeline routing (edition-aware)
│   │   ├── api/routes/           # REST API endpoints
│   │   ├── llm/                  # LiteLLM provider abstraction (6 providers)
│   │   ├── models/               # SQLAlchemy ORM (settings, creator, analysis_run, report)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # YouTube, TikTok, Bilibili, Douyin, Kuaishou, encryption
│   │   └── utils/
│   │       ├── prompts.py            # International prompt templates (7)
│   │       ├── prompts_cn.py         # CN prompt templates (7, Chinese)
│   │       ├── pricing_tables.py     # International CPM tables, modifiers, brand DB
│   │       └── pricing_tables_cn.py  # CN CPM tables, additive modifiers, tax, livestream
│   ├── run.py                    # International EXE entry point
│   ├── run_cn.py                 # CN EXE entry point (sets EDITION=cn)
│   ├── knowyourrate.spec         # International PyInstaller config
│   └── knowyourrate_cn.spec      # CN PyInstaller config
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/                # Setup → Creator → Analysis → Report → History
│       ├── components/           # PlatformSelector, PriceRangeChart, AgentProgress, etc.
│       ├── api/                  # Axios API client + SSE subscription
│       ├── store/                # Zustand state management (3 stores)
│       └── types/index.ts        # Types + edition detection (VITE_EDITION) + label maps
├── .github/workflows/
│   └── build-exe.yml             # Parallel international + CN EXE builds
└── docker-compose.yml            # One-click deployment
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), LiteLLM |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, Zustand, Recharts |
| Database | PostgreSQL 16 or SQLite (auto-detected) |
| LLM | LiteLLM (unified interface for 6 providers) |
| i18n | i18next (English + Chinese) |
| Deployment | Docker Compose, Windows EXE (x2), or local dev |

### Edition System

Both editions share a single codebase. The edition is selected via environment variables:

- **Backend**: `EDITION=cn` loads CN agents, data tables, and prompts via conditional imports in `orchestrator.py`
- **Frontend**: `VITE_EDITION=cn` (build-time) shows CN platforms, deal types, and UI elements
- **EXE builds**: Separate PyInstaller specs produce `KnowYourRate.exe` and `KnowYourRate-CN.exe`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (includes `edition` field) |
| GET | `/api/settings/providers` | List supported LLM providers |
| POST | `/api/settings/provider` | Save provider + API key |
| POST | `/api/settings/provider/test` | Test API key connectivity |
| POST | `/api/creators/lookup` | Fetch creator channel data |
| POST | `/api/analysis/run` | Start analysis pipeline |
| GET | `/api/analysis/{id}/status` | SSE stream of pipeline progress |
| GET | `/api/analysis/{id}/result` | Get completed analysis |
| GET/POST/DELETE | `/api/reports[/{id}]` | Report management |

## User Flow

1. **Setup** — Select an LLM provider and enter your API key. Test the connection.
2. **Creator** — Choose your platform, enter your channel URL or stats manually. Add the brand name, deal type, usage rights, and exclusivity terms. CN users also enter platform-specific metrics (投币率, 完播率, 回访率) and city tier.
3. **Analysis** — Watch the 4-agent pipeline run in real-time with live SSE progress updates. Fast-track queries skip Agents B and C.
4. **Report** — Review your pricing intelligence report with price ranges, negotiation scripts, package tiers, and contract red flags. CN reports also include tax estimation and platform official pricing reference. Reports are auto-saved for later review.

## Internationalization

The app supports English and Chinese (Simplified). Language can be switched in the header. Agent-generated reports are produced in your selected language.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string (PostgreSQL or SQLite) |
| `ENCRYPTION_SECRET` | Yes | Fernet key for encrypting stored API keys |
| `YOUTUBE_API_KEY` | No | YouTube Data API v3 key for auto channel lookup |
| `EDITION` | No | Backend edition: `international` (default) or `cn` |
| `VITE_EDITION` | No | Frontend edition (build-time): `international` (default) or `cn` |
| `DB_PASSWORD` | Docker only | PostgreSQL password (default: `changeme`) |

## Building EXE

```bash
# International edition
cd frontend && npm run build
cd ../backend && pip install -e ".[build]" && pyinstaller knowyourrate.spec --noconfirm

# CN edition
cd frontend && VITE_EDITION=cn npm run build
cd ../backend && pip install -e ".[build]" && pyinstaller knowyourrate_cn.spec --noconfirm
```

Both EXEs are also built automatically via GitHub Actions on tag push (`v*`).

## License

MIT
