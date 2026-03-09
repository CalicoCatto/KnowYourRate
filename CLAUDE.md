# KnowYourRate - Development Guide

## Project Overview

Multi-agent pricing intelligence engine for content creators. 5 AI agents analyze brand collaboration deals and produce pricing reports with negotiation strategies.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / PostgreSQL / LiteLLM
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS v4 / Zustand
- **Deployment**: Docker Compose

## Key Commands

```bash
# Start all services
docker compose up -d

# Backend only (dev)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend only (dev)
cd frontend && npm run dev

# Run backend tests
cd backend && pytest

# Frontend build check
cd frontend && npm run build

# Database (standalone)
docker compose up db -d
```

## Project Structure

```
backend/app/
├── agents/          # 5 agents + orchestrator (core business logic)
│   ├── base.py          # Abstract BaseAgent
│   ├── orchestrator.py  # Pipeline: Phase1(parallel) → Phase2 → Phase3
│   ├── market_data.py   # Agent 1: market rate benchmarks
│   ├── creator_profile.py # Agent 2: creator value assessment
│   ├── brand_strategy.py  # Agent 3: brand budget analysis
│   ├── debate.py        # Agent 4: dual-persona negotiation
│   └── report.py        # Agent 5: final pricing report
├── api/routes/      # REST endpoints (health, settings, creators, analysis, reports)
├── llm/             # LiteLLM wrapper + provider registry
├── models/          # SQLAlchemy ORM (settings, creator, analysis_run, report)
├── schemas/         # Pydantic request/response schemas
├── services/        # YouTube API, TikTok, Fernet encryption
└── utils/prompts.py # All agent prompt templates

frontend/src/
├── pages/           # SetupPage → CreatorPage → AnalysisPage → ReportPage
├── components/      # Layout, AgentProgress, PriceRangeChart, etc.
├── api/client.ts    # Axios API client + SSE helpers
├── store/           # Zustand settings store
└── types/index.ts   # All TypeScript interfaces
```

## Architecture Decisions

- **LLM abstraction**: LiteLLM provides unified interface across OpenAI/Anthropic/Gemini/DeepSeek. Provider config in `llm/registry.py`.
- **Agent pipeline**: Orchestrator runs agents 1-3 in parallel (`asyncio.gather`), then agent 4, then agent 5. Each agent returns a dict parsed from LLM JSON output.
- **SSE progress**: Analysis endpoint streams agent status via Server-Sent Events (no WebSocket).
- **API key encryption**: Fernet symmetric encryption using `ENCRYPTION_SECRET` env var. Keys encrypted at rest in PostgreSQL `settings` table.
- **TikTok data**: Manual input form (no API — official API requires academic credentials).
- **YouTube data**: YouTube Data API v3 via `python-youtube` library. Optional — users can enter stats manually.
- **Database**: All agent outputs stored as JSONB columns on `analysis_runs` table for simplicity.
- **No auth**: Single-user local tool. No user accounts.
- **i18n**: Frontend uses react-i18next (EN/ZH). Agent reports use language instruction in prompts.

## Code Conventions

- Backend: Python type hints, async/await, Pydantic models for all API boundaries
- Frontend: TypeScript strict mode, functional components, Tailwind utility classes
- Agents return JSON dicts via `LLMClient.chat_json()` — handle `raw_response` fallback key for parse failures
- All prompt templates live in `utils/prompts.py` — agents use `self.build_prompt()` to fill placeholders
- Database models use UUID primary keys, JSONB for flexible structured data

## Environment Variables

- `DATABASE_URL` — PostgreSQL async connection string
- `ENCRYPTION_SECRET` — Fernet key for API key encryption
- `YOUTUBE_API_KEY` — Optional, for auto channel lookup
