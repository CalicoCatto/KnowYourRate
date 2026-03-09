# KnowYourRate - Development Guide

## Project Overview

Multi-agent pricing intelligence engine for content creators. 4 AI agents + structured CPM calculations analyze brand collaboration deals and produce pricing reports with negotiation strategies.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / PostgreSQL or SQLite / LiteLLM
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS v4 / Zustand
- **Deployment**: Docker Compose, Windows EXE, or local dev

## Key Commands

```bash
# Start all services (Docker)
docker compose up -d

# Backend only (dev, SQLite)
cd backend && DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" uvicorn app.main:app --reload --port 8000

# Backend only (dev, PostgreSQL)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend only (dev)
cd frontend && npm run dev

# Run backend tests
cd backend && pytest

# Frontend build
cd frontend && npm run build

# Build EXE (requires frontend built first)
cd backend && pip install -e ".[build]" && pyinstaller knowyourrate.spec --noconfirm
```

## Project Structure

```
backend/
├── app/
│   ├── agents/              # 4 agents + orchestrator (core business logic)
│   │   ├── creator_profile.py  # Agent A: CPM calculation + qualitative assessment
│   │   ├── market_data.py      # Agent B: Deal conditions + brand intel (MarketIntelAgent)
│   │   ├── debate.py           # Agent C: Bull/Bear/Judge adversarial debate
│   │   ├── report.py           # Agent D: Strategy report generation
│   │   └── orchestrator.py     # Pipeline routing + coordination
│   ├── api/routes/          # REST endpoints (health, settings, creators, analysis, reports)
│   ├── llm/                 # LiteLLM wrapper + provider registry
│   ├── models/              # SQLAlchemy ORM (settings, creator, analysis_run, report)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # YouTube API, TikTok, Fernet encryption
│   └── utils/
│       ├── prompts.py       # All agent prompt templates
│       └── pricing_tables.py # CPM tables, multipliers, modifiers, brand DB, red flags
├── run.py               # EXE entry point (starts server + opens browser)
└── knowyourrate.spec    # PyInstaller build config

frontend/src/
├── pages/           # SetupPage → CreatorPage → AnalysisPage → ReportPage
├── components/      # Layout, AgentProgress, PriceRangeChart, DetailedAnalysis, etc.
├── api/client.ts    # Axios API client + SSE helpers
├── store/           # Zustand stores (settings, creator, analysis)
└── types/index.ts   # All TypeScript interfaces

.github/workflows/
└── build-exe.yml    # GitHub Actions: build frontend → PyInstaller → Release
```

## Agent Pipeline Architecture

```
User Input → Router (complexity check) → fast_track or full_pipeline

fast_track:    Agent A (creator CPM) → Agent D (report)
full_pipeline: Agent A → Agent B (market intel) → Agent C (debate) → Agent D (report)
```

### Key Design Principle
**Math in code, reasoning in LLM.** Pricing calculations (CPM × views, modifiers, deal multipliers) are computed deterministically in `pricing_tables.py`. LLM is only used for qualitative assessment, brand intelligence, adversarial debate, and report narrative.

### Agent Details

- **Agent A (CreatorProfileAgent)**: Computes base price from CPM table × avg views, applies engagement/geo/growth/seasonal modifiers, then asks LLM for qualitative adjustment (clamped ±30%)
- **Agent B (MarketIntelAgent)**: Applies deal condition multipliers (deliverable type, usage rights, exclusivity), looks up known brand patterns, asks LLM for market context
- **Agent C (DebateAgent)**: 2-round debate — Bull (high temp 0.7) argues for higher price, Bear (low temp 0.3) argues for lower, Judge (temp 0.4) synthesizes final range anchored to computed price
- **Agent D (ReportAgent)**: Generates narrative report using exact computed prices, package tiers, negotiation scripts, and contract red flags

### Data Tables (`utils/pricing_tables.py`)

- **NICHE_CPM_TABLE**: CPM by platform × niche (15 niches × 2 platforms)
- **DELIVERABLE_MULTIPLIERS**: Content type multipliers (dedicated=1.0, integration=0.5, shorts=0.25, etc.)
- **USAGE_RIGHTS_PREMIUMS**: 0% (organic) to 300% (perpetual all media)
- **EXCLUSIVITY_PREMIUMS**: 0% (none) to 100% (full exclusivity 90d)
- **KNOWN_BRAND_PATTERNS**: 15+ brands with budget tier, CPM range, negotiation style
- **CONTRACT_RED_FLAGS**: 8 structured detection rules
- **SEASONAL_MODIFIERS**: Q1-Q4 by month with niche overrides

## Deployment Modes

- **Windows EXE**: PyInstaller bundles backend + frontend into single executable. Uses SQLite. Auto-opens browser. Built via GitHub Actions on tag push.
- **Docker Compose**: PostgreSQL + backend + frontend as separate containers. Production-ready.
- **Local dev**: Backend (uvicorn) + frontend (vite dev server). Supports both SQLite and PostgreSQL via `DATABASE_URL`.

## Architecture Decisions

- **Database**: Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite). EXE mode auto-detects and uses SQLite. Configured via `DATABASE_URL`. SQLite uses `check_same_thread=False`.
- **LLM abstraction**: LiteLLM provides unified interface across OpenAI/Anthropic/Gemini/DeepSeek/Moonshot(Kimi)/SiliconFlow. Provider config in `llm/registry.py`. Moonshot and SiliconFlow use OpenAI-compatible API with custom `api_base` URLs. Kimi K2.5 is a reasoning model that rejects explicit temperature — handled via `skip_temperature_models` in registry. Reasoning model `<think>` tags are auto-stripped in `provider.py`.
- **Complexity routing**: Router scores complexity based on brand name, exclusivity, usage rights, and niche variance. Score >= 3 = full pipeline (4 agents), otherwise fast track (2 agents).
- **Static file serving**: In EXE/standalone mode, FastAPI serves the built frontend from `frontend_dist/`. SPA catch-all route serves `index.html` for client-side routing.
- **SSE progress**: Analysis endpoint streams agent status via Server-Sent Events (no WebSocket). Supports "skipped" status for fast track mode.
- **API key encryption**: Fernet symmetric encryption using `ENCRYPTION_SECRET` env var.
- **EXE packaging**: `run.py` is the entry point. PyInstaller spec bundles `frontend/dist` as `frontend_dist` data. `app.main` detects `sys.frozen` to locate bundled assets.
- **No auth**: Single-user local tool. No user accounts.

## Code Conventions

- Backend: Python type hints, async/await, Pydantic models for all API boundaries
- Frontend: TypeScript strict mode, functional components, Tailwind utility classes
- Agents return JSON dicts via `LLMClient.chat_json()` — handle `raw_response` fallback key for parse failures
- All prompt templates live in `utils/prompts.py` — agents use `self.build_prompt()` to fill placeholders
- Pricing calculations live in `utils/pricing_tables.py` — pure Python, no LLM dependency
- Database models use UUID primary keys, JSONB for flexible structured data (SQLite stores JSONB as TEXT via SQLAlchemy)

## Environment Variables

- `DATABASE_URL` — Connection string. PostgreSQL: `postgresql+asyncpg://...`, SQLite: `sqlite+aiosqlite:///path.db`. EXE mode defaults to SQLite automatically.
- `ENCRYPTION_SECRET` — Fernet key for API key encryption
- `YOUTUBE_API_KEY` — Optional, for auto channel lookup
