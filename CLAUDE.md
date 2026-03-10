# KnowYourRate - Development Guide

## Project Overview

Multi-agent pricing intelligence engine for content creators. 4 AI agents + structured CPM calculations analyze brand collaboration deals and produce pricing reports with negotiation strategies.

Supports two editions via the `EDITION` environment variable:
- **International** (default): YouTube / TikTok, USD, multiplicative modifiers
- **CN (中国版)**: B站 / 抖音 / 快手, CNY, additive modifiers with cap [0.4, 2.0]

Both editions share the same 4-agent pipeline architecture but use edition-specific data tables, prompts, and agent implementations.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / PostgreSQL or SQLite / LiteLLM
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS v4 / Zustand / Recharts / i18next
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
│   ├── main.py                   # FastAPI app factory, CORS, static serving, SPA catch-all
│   ├── config.py                 # Settings (DATABASE_URL, ENCRYPTION_SECRET, YOUTUBE_API_KEY)
│   ├── database.py               # SQLAlchemy async engine, session factory, get_db() dependency
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
│   ├── api/
│   │   ├── router.py                # API router: /api prefix, includes all route modules
│   │   ├── deps.py                  # FastAPI dependencies: get_db(), get_llm_client()
│   │   └── routes/                  # REST endpoints
│   │       ├── health.py               # GET /health (includes edition field)
│   │       ├── settings.py             # Provider CRUD, YouTube key CRUD, test endpoints
│   │       ├── creators.py             # POST /lookup (YouTube API or manual form schema)
│   │       ├── analysis.py             # POST /run, GET /status (SSE), GET /result
│   │       └── reports.py              # GET/POST/DELETE report management
│   ├── llm/                      # LiteLLM wrapper + provider registry
│   │   ├── provider.py              # LLMClient: chat(), chat_json(), retry, think-tag stripping
│   │   └── registry.py              # SUPPORTED_PROVIDERS config for 6 providers
│   ├── models/                   # SQLAlchemy ORM
│   │   ├── settings.py              # Settings model (provider, encrypted API key, model)
│   │   ├── creator.py               # Creator model (platform, handle, subscribers, raw_data JSON)
│   │   ├── analysis_run.py          # AnalysisRun model (status, agent outputs as JSON columns)
│   │   └── report.py                # Report model (prices as Decimal, full_report + agent_outputs JSON)
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Platform data services + Fernet encryption
│   │   ├── youtube.py               # YouTube API: test_youtube_key(), fetch_channel_info()
│   │   ├── tiktok.py                # TikTok manual form schema
│   │   ├── bilibili.py              # B站 manual form schema (CN)
│   │   ├── douyin.py                # 抖音 manual form schema (CN)
│   │   ├── kuaishou.py              # 快手 manual form schema (CN)
│   │   └── encryption.py            # Fernet: encrypt_value(), decrypt_value()
│   └── utils/
│       ├── prompts.py               # International agent prompt templates (7 templates)
│       ├── prompts_cn.py            # CN agent prompt templates (7 templates, Chinese)
│       ├── pricing_tables.py        # International: CPM tables, multipliers, modifiers, brand DB
│       └── pricing_tables_cn.py     # CN: CPM tables, additive modifiers, brand DB, tax, livestream
├── run.py                    # International EXE entry point (starts uvicorn + opens browser)
├── run_cn.py                 # CN EXE entry point (sets EDITION=cn, imports run.main())
├── knowyourrate.spec         # International PyInstaller build config
├── knowyourrate_cn.spec      # CN PyInstaller build config
└── pyproject.toml            # Dependencies: fastapi, sqlalchemy, litellm, pyyoutube, etc.

frontend/
├── src/
│   ├── main.tsx             # React Router: / → Setup, /creator, /analysis/:runId, /report/:runId, /history, /history/:reportId
│   ├── App.tsx              # Root component
│   ├── i18n.ts              # i18next config (en/zh, browser language detection, localStorage)
│   ├── index.css            # Tailwind CSS v4 imports + custom utilities
│   ├── pages/
│   │   ├── SetupPage.tsx        # Provider selection, API key entry/test, YouTube key config
│   │   ├── CreatorPage.tsx      # Platform selector, channel lookup/manual entry, brand deal form
│   │   ├── AnalysisPage.tsx     # Real-time agent progress via SSE, error display
│   │   ├── ReportPage.tsx       # Price chart, negotiation points, red flags, packages, scripts
│   │   ├── HistoryPage.tsx      # Saved report list with delete
│   │   └── SavedReportPage.tsx  # View saved report (loaded from /reports/:id)
│   ├── components/
│   │   ├── Layout.tsx           # Header (nav, language switcher, dark mode), footer
│   │   ├── PlatformSelector.tsx # Platform button grid (2-col intl, 3-col CN)
│   │   ├── ProviderSelector.tsx # LLM provider button grid with icons
│   │   ├── LanguageSwitcher.tsx # EN/ZH toggle button
│   │   ├── AgentProgress.tsx    # 4-step vertical timeline with status indicators
│   │   ├── PriceRangeChart.tsx  # Recharts bar chart + 3 big price numbers
│   │   ├── NegotiationPoints.tsx # Talking points list with copy button
│   │   ├── ContractRedFlags.tsx # Red flag cards with severity badges (high/medium/low)
│   │   └── DetailedAnalysis.tsx # Collapsible raw agent output viewer
│   ├── api/client.ts        # Axios client + SSE subscription (EventSource)
│   ├── store/
│   │   ├── settingsStore.ts     # Provider, model, language, darkMode (persisted to localStorage)
│   │   ├── creatorStore.ts      # Platform, profile, manual fields, brand/deal, CN-specific fields
│   │   └── analysisStore.ts     # Analysis runs, SSE tracking, auto-save on completion
│   └── types/index.ts       # All TypeScript interfaces, edition detection (VITE_EDITION), label maps
├── public/locales/
│   ├── en/translation.json  # English UI strings
│   └── zh/translation.json  # Chinese UI strings
├── package.json             # React 18, Zustand 5, Recharts, Axios, i18next, Tailwind CSS 4
├── vite.config.ts           # React + Tailwind plugins, @ path alias, /api proxy to :8000
└── tsconfig.app.json        # Strict mode, noUnusedLocals, noUnusedParameters

.github/workflows/
└── build-exe.yml    # GitHub Actions: parallel international + CN EXE builds on tag push (v*)
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
- **Agent B (MarketIntelAgent / MarketIntelCNAgent)**: Applies deal condition multipliers (deliverable type, usage rights, exclusivity), looks up known brand patterns, generates 3-tier packages (Starter/Standard/Premium), detects contract red flags, asks LLM for market context. CN adds platform official pricing (花火/星图/磁力聚星) and livestream commerce support (坑位费 + 佣金).
- **Agent C (DebateAgent)**: Shared between editions. 3-round debate — Round 1: Bull (temp 0.7) + Bear (temp 0.3) argue independently; Round 2: cross-rebuttal (parallel via asyncio.gather); Round 3: Judge (temp 0.4) synthesizes final range (walk_away / fair_market / anchor_price). Judge constrained to ±30% of engine-computed price_mid. Loads edition-specific prompts via `_load_debate_prompts()`.
- **Agent D (ReportAgent / ReportCNAgent)**: Generates narrative report using exact computed prices, package tiers, negotiation scripts for 3 scenarios, and contract red flags. Prices from judge verdict overwrite any LLM-generated prices. CN adds tax estimation (3 regimes), ad law compliance, and MCN commission reference.

### Complexity Routing

Score >= 3 → full_pipeline, otherwise fast_track:
- Brand name present: +2
- Exclusivity != "none": +2
- Usage rights != "organic_only": +2
- High-variance niche (finance, tech, business, automotive): +1
- First brand deal: +1
- **CN-only**: Has livestream: +3, Multiple platforms: +2

### Edition System

The edition system uses a single codebase with conditional imports:

1. **Backend**: `EDITION` env var (`"international"` or `"cn"`), checked via `app.edition.is_cn()`
2. **Frontend**: `VITE_EDITION` build-time env var, checked via `isCN` constant in `types/index.ts`
3. **Orchestrator**: `_load_agents()` dynamically imports the correct Agent classes and routing function
4. **Debate Agent**: `_load_debate_prompts()` loads edition-specific prompt templates at runtime

### Data Tables — International (`utils/pricing_tables.py`)

- **NICHE_CPM_TABLE**: CPM by platform × niche (15 niches × 2 platforms, USD)
- **NICHE_AVG_ENGAGEMENT**: Average engagement rates by platform × niche (2.5%-7.0%)
- **NICHE_DISPLAY_NAMES**: 15 niche key → Chinese label mappings
- **TIER_TABLE**: 2 platforms × 5 tiers (nano/micro/mid_tier/macro/mega) with subscriber thresholds
- **DELIVERABLE_MULTIPLIERS**: Per-platform content type multipliers (YouTube 7 types, TikTok 5 types)
- **USAGE_RIGHTS_PREMIUMS**: 11 types, 0% (organic) to 300% (perpetual all media)
- **EXCLUSIVITY_PREMIUMS**: 7 types, 0% (none) to 100% (full exclusivity 90d)
- **KNOWN_BRAND_PATTERNS**: 40+ brands with budget tier, CPM range, negotiation style, known issues
- **CONTRACT_RED_FLAGS**: 8 structured detection rules with severity (high/medium)
- **SEASONAL_MODIFIERS**: Q1-Q4 by month with niche overrides (0.85-1.50)
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
- **SEASONAL_MATRIX_CN**: 12 months × 8 category groups (双11, 618, 春节, 开学季, etc.)
- **LONGEVITY_MODIFIERS**: Content lifespan by platform (B站 +10%, 抖音 0%, 快手 +3%)
- **LIVESTREAM_PIT_FEE_TABLE**: 4 tiers × 7 categories (坑位费, CNY)
- **COMMISSION_RATE_TABLE**: Commission rates by category (5%-50%)
- **OFFICIAL_PLATFORM_INFO**: 花火 (7%), 星图 (10%), 磁力聚星 (7%) fee rates
- **TAX_BRACKETS_CN**: 3 tax regimes (劳务报酬, 个体工商户, 公司/MCN)
- **MCN_FEE_REFERENCE**: MCN commission reference (4 tiers by follower count)
- **AD_LAW_COMPLIANCE_CHECKS**: 广告法 compliance rules (disclosure, prohibited claims, medical, finance, education)

### Modifier Systems

```
International (multiplicative):
  base_price × engagement_mod × geo_mod × growth_mod × seasonal_mod × quality_mod

CN (additive, capped):
  base_price × (1.0 + Σ deltas), where deltas = [互动率Δ, VF比Δ, 城市Δ, 增长Δ, 季节Δ, 平台信号Δ, 内容寿命Δ]
  total_modifier capped to [0.4, 2.0]
```

### Prompt Templates

International prompts in `utils/prompts.py`, CN prompts in `utils/prompts_cn.py`. Each file contains 7 templates:
- **CREATOR_PROFILE_PROMPT[_CN]**: Agent A qualitative assessment (returns qualitative_adjustment_pct, content_quality_score, etc.)
- **MARKET_INTEL_PROMPT[_CN]**: Agent B market context analysis (returns market_adjustment_pct, brand_intelligence, etc.)
- **DEBATE_BULL_PROMPT[_CN]**: Agent C bull arguments (CN: MCN商务经理 perspective)
- **DEBATE_BEAR_PROMPT[_CN]**: Agent C bear arguments (CN: 品牌KOL投放负责人)
- **DEBATE_CROSS_REBUTTAL_PROMPT[_CN]**: Agent C cross-rebuttal round
- **DEBATE_JUDGE_PROMPT[_CN]**: Agent C judge synthesis (CN: includes dual pricing)
- **REPORT_PROMPT[_CN]**: Agent D final report generation (CN: includes tax estimates)

## Database Models

All models use UUID primary keys, JSONB for flexible structured data (SQLite stores JSONB as TEXT).

- **Settings**: provider, encrypted API key, model name
- **Creator**: platform, platform_id, handle, display_name, subscriber_count, avg_views, engagement_rate, content_niche, raw_data (JSON), fetched_at
- **AnalysisRun**: creator_id (FK), brand_name, deal_type, status (pending/running/completed/failed), current_agent, creator_analysis (JSON), market_data (JSON), debate_result (JSON), final_report (JSON), error_message, started_at, completed_at
- **Report**: analysis_run_id (FK, CASCADE), title, summary, price_low/mid/high (Decimal 12,2), currency (USD/CNY), full_report (JSON), agent_outputs (JSON)

## LLM Provider System

`LLMClient` in `llm/provider.py` wraps litellm.acompletion:
- **chat(messages, temperature, response_format)**: Raw completion with retry (3 attempts, exponential backoff)
- **chat_json(messages, temperature)**: JSON parsing with fallback to `{"raw_response": text}`
- Custom `api_base` for OpenAI-compatible providers (Moonshot, SiliconFlow)
- Temperature skipping for reasoning models (Kimi K2.5) via `skip_temperature_models` in registry
- Automatic `<think>` tag stripping from reasoning model outputs

6 providers in `llm/registry.py`:
1. **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo
2. **Anthropic**: claude-sonnet-4-20250514, claude-haiku-35-20241022, claude-3-5-sonnet-20241022
3. **Google Gemini**: gemini-2.0-flash, gemini-2.0-flash-lite, gemini-1.5-pro, gemini-1.5-flash
4. **DeepSeek**: deepseek-chat, deepseek-reasoner
5. **Moonshot (Kimi)**: kimi-k2.5, kimi-k2-0905-preview (api_base: https://api.moonshot.cn/v1)
6. **SiliconFlow**: DeepSeek V3.2, MiniMax-M2.5, GLM-4.7, GLM-5, Step-3.5-Flash (api_base: https://api.siliconflow.cn/v1)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (includes `edition` field) |
| GET | `/api/settings/providers` | List supported LLM providers |
| POST | `/api/settings/provider` | Save provider + API key (encrypted) |
| GET | `/api/settings/provider` | Get current provider config |
| DELETE | `/api/settings/provider` | Delete provider config |
| POST | `/api/settings/provider/test` | Test API key connectivity |
| GET | `/api/settings/youtube-key` | Check YouTube API key status |
| POST | `/api/settings/youtube-key` | Save YouTube API key |
| POST | `/api/settings/youtube-key/test` | Test YouTube API key |
| DELETE | `/api/settings/youtube-key` | Delete YouTube API key |
| POST | `/api/creators/lookup` | Fetch creator data (YouTube API or form schema via 422) |
| POST | `/api/analysis/run` | Start analysis pipeline (returns run_id) |
| GET | `/api/analysis/{id}/status` | SSE stream of pipeline progress |
| GET | `/api/analysis/{id}/result` | Get completed analysis result |
| GET | `/api/reports` | List all saved reports |
| POST | `/api/reports` | Save report from analysis run |
| GET | `/api/reports/{id}` | Get saved report with agent outputs |
| DELETE | `/api/reports/{id}` | Delete saved report |

## Frontend Architecture

### Routing (`main.tsx`)
- `/` → SetupPage (provider + API key)
- `/creator` → CreatorPage (channel + deal info)
- `/analysis/:runId` → AnalysisPage (real-time progress)
- `/report/:runId` → ReportPage (pricing report)
- `/history` → HistoryPage (saved report list)
- `/history/:reportId` → SavedReportPage

### Zustand Stores
- **settingsStore**: provider, model, hasApiKey, language, darkMode — persisted to localStorage ("kyr-settings")
- **creatorStore**: platform, channelUrl, profile, manual entry fields (including CN-specific: coinRate, favoriteRate, completionRate, shareRate, revisitRate, cityTier, mcnStatus, hasLivestream, numPlatforms), brand/deal conditions — not persisted
- **analysisStore**: tracks multiple runs via SSE, auto-saves report on completion

### Edition-Aware Components
- **PlatformSelector**: 2-column grid (YouTube/TikTok) or 3-column grid (B站/抖音/快手)
- **CreatorPage**: CN shows platform-specific manual fields, city tier, MCN status, livestream toggle, multi-platform count
- **ReportPage**: CN adds tax estimate section and platform official pricing reference; currency formatted as CNY
- **types/index.ts**: Edition-specific label maps for deal types, usage rights, exclusivity, niches

### i18n
- i18next with `public/locales/{en,zh}/translation.json`
- Browser language auto-detection, stored in localStorage
- Agent reports generated in user's selected language

## Deployment Modes

- **Windows EXE (International)**: `KnowYourRate.exe` — bundles international frontend + backend. Built via `knowyourrate.spec`. Auto-opens browser at `http://localhost:8000`.
- **Windows EXE (CN)**: `KnowYourRate-CN.exe` — bundles CN frontend (VITE_EDITION=cn) + backend (EDITION=cn). Built via `knowyourrate_cn.spec`.
- **Docker Compose**: PostgreSQL + backend + frontend as separate containers. Set `EDITION=cn` for CN mode.
- **Local dev**: Backend (uvicorn :8000) + frontend (vite :5173, proxy /api → :8000). Set `EDITION=cn` and `VITE_EDITION=cn` for CN mode.

## Architecture Decisions

- **Edition system**: Single codebase + `EDITION` env var. Conditional imports load edition-specific agents, data tables, and prompts. Avoids code duplication while keeping CN/international logic cleanly separated.
- **Database**: Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite). EXE mode auto-detects `sys.frozen` and uses SQLite at `{exe_dir}/knowyourrate.db`. Configured via `DATABASE_URL`. SQLite uses `check_same_thread=False`.
- **LLM abstraction**: LiteLLM provides unified interface across 6 providers. Moonshot and SiliconFlow use OpenAI-compatible API with custom `api_base` URLs. Kimi K2.5 is a reasoning model that rejects explicit temperature — handled via `skip_temperature_models` in registry. Reasoning model `<think>` tags are auto-stripped in `provider.py`.
- **Complexity routing**: Router scores deal complexity. Score >= 3 = full pipeline (4 agents, ~60s), otherwise fast track (2 agents, ~15s). Reduces unnecessary LLM calls for straightforward pricing.
- **Static file serving**: In EXE/standalone mode, FastAPI serves the built frontend from `frontend_dist/` (bundled via PyInstaller). SPA catch-all route serves `index.html` for client-side routing.
- **SSE progress**: Analysis endpoint streams agent status via Server-Sent Events (no WebSocket). In-memory `_progress_store` dict per run_id. Supports "skipped" status for fast track mode.
- **API key encryption**: Fernet symmetric encryption using `ENCRYPTION_SECRET` env var. Key derivation via SHA256 → base64.
- **Price enforcement**: Judge's final prices overwrite any LLM-generated prices in the report to ensure computed values are used.
- **No auth**: Single-user local tool. No user accounts.
- **CN platform data**: B站/抖音/快手 all use manual form schemas (no public API integration yet). Creators endpoint returns 422 with form schema for these platforms.

## Code Conventions

- Backend: Python type hints, async/await, Pydantic models for all API boundaries
- Frontend: TypeScript strict mode (`noUnusedLocals`, `noUnusedParameters`), functional components, Tailwind utility classes
- Agents return JSON dicts via `LLMClient.chat_json()` — handle `raw_response` fallback key for parse failures
- International prompts in `utils/prompts.py`, CN prompts in `utils/prompts_cn.py`
- International pricing in `utils/pricing_tables.py`, CN pricing in `utils/pricing_tables_cn.py`
- Database models use UUID primary keys, JSONB for flexible structured data (SQLite stores JSONB as TEXT via SQLAlchemy)
- CN agents use `ensure_ascii=False` in JSON serialization for proper Chinese character handling

## Environment Variables

- `DATABASE_URL` — Connection string. PostgreSQL: `postgresql+asyncpg://...`, SQLite: `sqlite+aiosqlite:///path.db`. EXE mode defaults to SQLite automatically.
- `ENCRYPTION_SECRET` — Fernet key for API key encryption. Generate via: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `YOUTUBE_API_KEY` — Optional, for auto channel lookup (international only)
- `EDITION` — Backend edition: `"international"` (default) or `"cn"`. Controls which agents, data tables, and prompts are loaded.
- `VITE_EDITION` — Frontend build-time edition: `"international"` (default) or `"cn"`. Controls which platforms, deal types, and UI elements are shown.
- `DB_PASSWORD` — Docker Compose only. PostgreSQL password (default: `changeme`).
