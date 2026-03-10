# KnowYourRate - Development Guide

## Project Overview

Multi-agent pricing intelligence engine for content creators. 4 AI agents + structured CPM calculations analyze brand collaboration deals and produce pricing reports with negotiation strategies.

Supports two editions via the `EDITION` environment variable:
- **International** (default): YouTube / TikTok, USD, multiplicative modifiers
- **CN (中国版)**: B站 / 抖音 / 快手, CNY, additive modifiers with cap [0.4, 2.0]

Both editions share the same 4-agent pipeline architecture but use edition-specific data tables, prompts, and agent implementations.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / PostgreSQL or SQLite / LiteLLM
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS v4 / Zustand
- **Deployment**: Docker Compose, Windows EXE (international + CN), or local dev

## Key Commands

```bash
# Start all services (Docker)
docker compose up -d

# Backend only (dev, SQLite, international)
cd backend && DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" uvicorn app.main:app --reload --port 8000

# Backend only (dev, SQLite, CN edition)
cd backend && EDITION=cn DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" uvicorn app.main:app --reload --port 8000

# Backend only (dev, PostgreSQL)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend only (dev, international)
cd frontend && npm run dev

# Frontend only (dev, CN edition)
cd frontend && VITE_EDITION=cn npm run dev

# Run backend tests
cd backend && pytest

# Frontend build (international)
cd frontend && npm run build

# Frontend build (CN edition)
cd frontend && VITE_EDITION=cn npm run build

# Build EXE — international (requires frontend built first)
cd backend && pip install -e ".[build]" && pyinstaller knowyourrate.spec --noconfirm

# Build EXE — CN edition (requires CN frontend built first)
cd backend && pip install -e ".[build]" && pyinstaller knowyourrate_cn.spec --noconfirm
```

## Project Structure

```
backend/
├── app/
│   ├── edition.py                # Edition detection (EDITION env var → is_cn())
│   ├── agents/                   # 4 agents + orchestrator (core business logic)
│   │   ├── base.py                  # BaseAgent ABC with build_prompt() helper
│   │   ├── creator_profile.py       # Agent A (international): CPM calc + qualitative assessment
│   │   ├── creator_profile_cn.py    # Agent A (CN): Additive modifiers + VF ratio + platform signals
│   │   ├── market_data.py           # Agent B (international): Deal conditions + brand intel
│   │   ├── market_data_cn.py        # Agent B (CN): CN brands + platform pricing + livestream
│   │   ├── debate.py                # Agent C: Bull/Bear/Judge debate (shared, loads edition prompts)
│   │   ├── report.py                # Agent D (international): Strategy report (USD)
│   │   ├── report_cn.py             # Agent D (CN): Strategy report (CNY + tax + compliance)
│   │   └── orchestrator.py          # Pipeline routing + coordination (edition-aware)
│   ├── api/routes/               # REST endpoints (health, settings, creators, analysis, reports)
│   ├── llm/                      # LiteLLM wrapper + provider registry
│   │   ├── provider.py              # LLMClient with chat(), chat_json(), retry, think-tag stripping
│   │   └── registry.py              # SUPPORTED_PROVIDERS config for 6 providers
│   ├── models/                   # SQLAlchemy ORM (settings, creator, analysis_run, report)
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Platform data services + Fernet encryption
│   │   ├── youtube.py               # YouTube API integration
│   │   ├── tiktok.py                # TikTok manual form schema
│   │   ├── bilibili.py              # B站 manual form schema (CN)
│   │   ├── douyin.py                # 抖音 manual form schema (CN)
│   │   ├── kuaishou.py              # 快手 manual form schema (CN)
│   │   └── encryption.py            # Fernet API key encryption
│   └── utils/
│       ├── prompts.py               # International agent prompt templates (7 templates)
│       ├── prompts_cn.py            # CN agent prompt templates (7 templates, Chinese)
│       ├── pricing_tables.py        # International: CPM tables, multipliers, modifiers, brand DB
│       └── pricing_tables_cn.py     # CN: CPM tables, additive modifiers, brand DB, tax, livestream
├── run.py                    # International EXE entry point
├── run_cn.py                 # CN EXE entry point (sets EDITION=cn)
├── knowyourrate.spec         # International PyInstaller build config
└── knowyourrate_cn.spec      # CN PyInstaller build config

frontend/src/
├── pages/           # SetupPage → CreatorPage → AnalysisPage → ReportPage
├── components/      # Layout, AgentProgress, PriceRangeChart, PlatformSelector, etc.
├── api/client.ts    # Axios API client + SSE helpers
├── store/           # Zustand stores (settings, creator, analysis)
└── types/index.ts   # All TypeScript interfaces + edition detection (VITE_EDITION)

.github/workflows/
└── build-exe.yml    # GitHub Actions: parallel international + CN EXE builds
```

## Agent Pipeline Architecture

```
User Input → Router (complexity check) → fast_track or full_pipeline

fast_track:    Agent A (creator CPM) → Agent D (report)
full_pipeline: Agent A → Agent B (market intel) → Agent C (debate) → Agent D (report)
```

### Key Design Principle
**Math in code, reasoning in LLM.** Pricing calculations (CPM × views, modifiers, deal multipliers) are computed deterministically in `pricing_tables.py` / `pricing_tables_cn.py`. LLM is only used for qualitative assessment, brand intelligence, adversarial debate, and report narrative.

### Agent Details

- **Agent A (CreatorProfileAgent / CreatorProfileCNAgent)**: Computes base price from CPM table × avg views, applies modifiers, then asks LLM for qualitative adjustment (clamped ±30%). International uses multiplicative modifiers; CN uses additive modifiers capped [0.4, 2.0] with VF ratio and platform-specific signals.
- **Agent B (MarketIntelAgent / MarketIntelCNAgent)**: Applies deal condition multipliers (deliverable type, usage rights, exclusivity), looks up known brand patterns, asks LLM for market context. CN adds platform official pricing (花火/星图/磁力聚星) and livestream commerce support.
- **Agent C (DebateAgent)**: Shared between editions. 3-round debate — Round 1: Bull (temp 0.7) + Bear (temp 0.3) argue independently; Round 2: cross-rebuttal (parallel via asyncio.gather); Round 3: Judge (temp 0.4) synthesizes final range. Loads edition-specific prompts via `_load_debate_prompts()`.
- **Agent D (ReportAgent / ReportCNAgent)**: Generates narrative report using exact computed prices, package tiers, negotiation scripts, and contract red flags. CN adds tax estimation (3 regimes), ad law compliance, and MCN commission reference.

### Edition System

The edition system uses a single codebase with conditional imports:

1. **Backend**: `EDITION` env var (`"international"` or `"cn"`), checked via `app.edition.is_cn()`
2. **Frontend**: `VITE_EDITION` build-time env var, checked via `isCN` constant in `types/index.ts`
3. **Orchestrator**: `_load_agents()` dynamically imports the correct Agent classes and routing function
4. **Debate Agent**: `_load_debate_prompts()` loads edition-specific prompt templates at runtime

### Data Tables — International (`utils/pricing_tables.py`)

- **NICHE_CPM_TABLE**: CPM by platform × niche (15 niches × 2 platforms, USD)
- **NICHE_AVG_ENGAGEMENT**: Average engagement rates by platform × niche
- **DELIVERABLE_MULTIPLIERS**: Content type multipliers (dedicated=1.0, integration=0.5, etc.)
- **USAGE_RIGHTS_PREMIUMS**: 0% (organic) to 300% (perpetual all media)
- **EXCLUSIVITY_PREMIUMS**: 0% (none) to 100% (full exclusivity 90d)
- **KNOWN_BRAND_PATTERNS**: 40+ brands with budget tier, CPM range, negotiation style
- **CONTRACT_RED_FLAGS**: 8 structured detection rules
- **SEASONAL_MODIFIERS**: Q1-Q4 by month with niche overrides
- **GEO_TIERS**: Country-based price modifiers (US=1.0 to IN/VN=0.3)

### Data Tables — CN (`utils/pricing_tables_cn.py`)

- **NICHE_CPM_TABLE_CN**: 3 platforms × 18 niches (CNY, with confidence level)
- **NICHE_AVG_ENGAGEMENT_CN**: Platform-specific engagement benchmarks (B站 includes 投币/收藏)
- **VF_RATIO_BENCHMARKS**: Followers-to-views ratio benchmarks per platform (core CN metric)
- **DELIVERABLE_MULTIPLIERS_CN**: Per-platform multipliers (B站 10 types, 抖音 10 types, 快手 7 types)
- **USAGE_RIGHTS_PREMIUMS_CN**: 13 types including 信息流投放, 电商详情页, 线下物料
- **EXCLUSIVITY_PREMIUMS_CN**: 9 types including 指定竞品排他, 平台排他
- **KNOWN_BRAND_PATTERNS_CN**: 20 CN brands (得物, 拼多多, 完美日记, 蔚来, 米哈游, etc.)
- **CONTRACT_RED_FLAGS_CN**: 15 rules (广告法, 肖像权, 数据安全, 直播退货分担, etc.)
- **SEASONAL_MATRIX_CN**: 12 months × 8 category groups (双11, 618, 春节, etc.)
- **LONGEVITY_MODIFIERS**: Content lifespan by platform (B站 +10%, 抖音 0%, 快手 +3%)
- **LIVESTREAM_PIT_FEE_TABLE**: 4 tiers × 7 categories (坑位费, CNY)
- **COMMISSION_RATE_TABLE**: Commission rates by category
- **OFFICIAL_PLATFORM_INFO**: 花火 (7%), 星图 (10%), 磁力聚星 (7%) fee rates
- **TAX_BRACKETS_CN**: 3 tax regimes (劳务报酬, 个体工商户, 公司/MCN)
- **MCN_FEE_REFERENCE**: MCN commission reference (4 tiers)
- **AD_LAW_COMPLIANCE_CHECKS**: 广告法 compliance rules

### CN Modifier System (Additive, not Multiplicative)

```
International: base_price × engagement_mod × geo_mod × growth_mod × seasonal_mod × quality_mod
CN:            base_price × (1.0 + Σ deltas), where deltas = [互动率Δ, VF比Δ, 城市Δ, 增长Δ, 季节Δ, 平台信号Δ, 内容寿命Δ]
               total_modifier capped to [0.4, 2.0]
```

### Prompt Templates

International prompts in `utils/prompts.py`, CN prompts in `utils/prompts_cn.py`. Each file contains 7 templates:
- **CREATOR_PROFILE_PROMPT[_CN]**: Agent A qualitative assessment
- **MARKET_INTEL_PROMPT[_CN]**: Agent B market context analysis
- **DEBATE_BULL_PROMPT[_CN]**: Agent C bull arguments (CN: MCN商务经理 perspective)
- **DEBATE_BEAR_PROMPT[_CN]**: Agent C bear arguments (CN: 品牌KOL投放负责人)
- **DEBATE_CROSS_REBUTTAL_PROMPT[_CN]**: Agent C cross-rebuttal round
- **DEBATE_JUDGE_PROMPT[_CN]**: Agent C judge synthesis (CN: includes dual pricing)
- **REPORT_PROMPT[_CN]**: Agent D final report generation (CN: includes tax estimates)

## Deployment Modes

- **Windows EXE (International)**: `KnowYourRate.exe` — bundles international frontend + backend. Built via `knowyourrate.spec`.
- **Windows EXE (CN)**: `KnowYourRate-CN.exe` — bundles CN frontend (VITE_EDITION=cn) + backend (EDITION=cn). Built via `knowyourrate_cn.spec`.
- **Docker Compose**: PostgreSQL + backend + frontend as separate containers. Set `EDITION=cn` for CN mode.
- **Local dev**: Backend (uvicorn) + frontend (vite dev server). Set `EDITION=cn` and `VITE_EDITION=cn` for CN mode.

## Architecture Decisions

- **Edition system**: Single codebase + `EDITION` env var. Conditional imports load edition-specific agents, data tables, and prompts. Avoids code duplication while keeping CN/international logic cleanly separated.
- **Database**: Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite). EXE mode auto-detects and uses SQLite. Configured via `DATABASE_URL`. SQLite uses `check_same_thread=False`.
- **LLM abstraction**: LiteLLM provides unified interface across OpenAI/Anthropic/Gemini/DeepSeek/Moonshot(Kimi)/SiliconFlow. Provider config in `llm/registry.py`. Moonshot and SiliconFlow use OpenAI-compatible API with custom `api_base` URLs. Kimi K2.5 is a reasoning model that rejects explicit temperature — handled via `skip_temperature_models` in registry. Reasoning model `<think>` tags are auto-stripped in `provider.py`.
- **Complexity routing**: Router scores complexity based on brand name, exclusivity, usage rights, niche variance, and first-brand-deal flag. CN adds livestream (+3) and cross-platform (+2) factors. Score >= 3 = full pipeline (4 agents), otherwise fast track (2 agents).
- **Static file serving**: In EXE/standalone mode, FastAPI serves the built frontend from `frontend_dist/`. SPA catch-all route serves `index.html` for client-side routing.
- **SSE progress**: Analysis endpoint streams agent status via Server-Sent Events (no WebSocket). Supports "skipped" status for fast track mode.
- **API key encryption**: Fernet symmetric encryption using `ENCRYPTION_SECRET` env var.
- **EXE packaging**: `run.py` / `run_cn.py` is the entry point. PyInstaller spec bundles `frontend/dist` as `frontend_dist` data. `app.main` detects `sys.frozen` to locate bundled assets.
- **No auth**: Single-user local tool. No user accounts.
- **CN platform data**: B站/抖音/快手 all use manual form schemas (no public API integration yet). Form schemas return platform-specific fields (投币率, 完播率, 回访率, etc.).

## Code Conventions

- Backend: Python type hints, async/await, Pydantic models for all API boundaries
- Frontend: TypeScript strict mode, functional components, Tailwind utility classes
- Agents return JSON dicts via `LLMClient.chat_json()` — handle `raw_response` fallback key for parse failures
- International prompts live in `utils/prompts.py`, CN prompts in `utils/prompts_cn.py`
- International pricing in `utils/pricing_tables.py`, CN pricing in `utils/pricing_tables_cn.py`
- Database models use UUID primary keys, JSONB for flexible structured data (SQLite stores JSONB as TEXT via SQLAlchemy)
- CN agents use `ensure_ascii=False` in JSON serialization for proper Chinese character handling

## Environment Variables

- `DATABASE_URL` — Connection string. PostgreSQL: `postgresql+asyncpg://...`, SQLite: `sqlite+aiosqlite:///path.db`. EXE mode defaults to SQLite automatically.
- `ENCRYPTION_SECRET` — Fernet key for API key encryption
- `YOUTUBE_API_KEY` — Optional, for auto channel lookup (international only)
- `EDITION` — Backend edition: `"international"` (default) or `"cn"`. Controls which agents, data tables, and prompts are loaded.
- `VITE_EDITION` — Frontend build-time edition: `"international"` (default) or `"cn"`. Controls which platforms, deal types, and UI elements are shown.
