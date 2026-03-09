# KnowYourRate - Development Guide

## Project Overview

Multi-agent pricing intelligence engine for content creators. 5 AI agents analyze brand collaboration deals and produce pricing reports with negotiation strategies.

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
│   ├── agents/          # 5 agents + orchestrator (core business logic)
│   ├── api/routes/      # REST endpoints (health, settings, creators, analysis, reports)
│   ├── llm/             # LiteLLM wrapper + provider registry
│   ├── models/          # SQLAlchemy ORM (settings, creator, analysis_run, report)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # YouTube API, TikTok, Fernet encryption
│   └── utils/prompts.py # All agent prompt templates
├── run.py               # EXE entry point (starts server + opens browser)
└── knowyourrate.spec    # PyInstaller build config

frontend/src/
├── pages/           # SetupPage → CreatorPage → AnalysisPage → ReportPage
├── components/      # Layout, AgentProgress, PriceRangeChart, etc.
├── api/client.ts    # Axios API client + SSE helpers
├── store/           # Zustand settings store
└── types/index.ts   # All TypeScript interfaces

.github/workflows/
└── build-exe.yml    # GitHub Actions: build frontend → PyInstaller → Release
```

## Deployment Modes

- **Windows EXE**: PyInstaller bundles backend + frontend into single executable. Uses SQLite. Auto-opens browser. Built via GitHub Actions on tag push.
- **Docker Compose**: PostgreSQL + backend + frontend as separate containers. Production-ready.
- **Local dev**: Backend (uvicorn) + frontend (vite dev server). Supports both SQLite and PostgreSQL via `DATABASE_URL`.

## Architecture Decisions

- **Database**: Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite). EXE mode auto-detects and uses SQLite. Configured via `DATABASE_URL`. SQLite uses `check_same_thread=False`.
- **LLM abstraction**: LiteLLM provides unified interface across OpenAI/Anthropic/Gemini/DeepSeek/Moonshot(Kimi)/SiliconFlow. Provider config in `llm/registry.py`. Moonshot and SiliconFlow use OpenAI-compatible API with custom `api_base` URLs. Kimi K2.5 is a reasoning model that rejects explicit temperature — handled via `skip_temperature_models` in registry. Reasoning model `<think>` tags are auto-stripped in `provider.py`.
- **Agent pipeline**: Orchestrator runs agents 1-3 in parallel (`asyncio.gather`), then agent 4, then agent 5. Each agent returns a dict parsed from LLM JSON output.
- **Static file serving**: In EXE/standalone mode, FastAPI serves the built frontend from `frontend_dist/`. SPA catch-all route serves `index.html` for client-side routing.
- **SSE progress**: Analysis endpoint streams agent status via Server-Sent Events (no WebSocket).
- **API key encryption**: Fernet symmetric encryption using `ENCRYPTION_SECRET` env var.
- **EXE packaging**: `run.py` is the entry point. PyInstaller spec bundles `frontend/dist` as `frontend_dist` data. `app.main` detects `sys.frozen` to locate bundled assets.
- **No auth**: Single-user local tool. No user accounts.

## Code Conventions

- Backend: Python type hints, async/await, Pydantic models for all API boundaries
- Frontend: TypeScript strict mode, functional components, Tailwind utility classes
- Agents return JSON dicts via `LLMClient.chat_json()` — handle `raw_response` fallback key for parse failures
- All prompt templates live in `utils/prompts.py` — agents use `self.build_prompt()` to fill placeholders
- Database models use UUID primary keys, JSONB for flexible structured data (SQLite stores JSONB as TEXT via SQLAlchemy)

## Environment Variables

- `DATABASE_URL` — Connection string. PostgreSQL: `postgresql+asyncpg://...`, SQLite: `sqlite+aiosqlite:///path.db`. EXE mode defaults to SQLite automatically.
- `ENCRYPTION_SECRET` — Fernet key for API key encryption
- `YOUTUBE_API_KEY` — Optional, for auto channel lookup
