# KnowYourRate

**AI Agent-powered pricing intelligence engine for content creators**

KnowYourRate helps YouTube and TikTok creators determine fair pricing for brand collaborations. Instead of guessing or relying on outdated calculators, creators get multi-dimensional analysis from 5 specialized AI agents that evaluate market rates, creator value, brand budgets, and negotiation dynamics.

## The Problem

Content creators are systematically underpaid in brand deals. Research shows creators are lowballed by 30-50% on average. Existing tools like Social Bluebook only offer static estimates based on follower count — a single dimension that misses audience quality, brand context, and negotiation leverage.

## How It Works

Enter your channel info and the brand deal details. Five AI agents analyze the deal in parallel and produce an actionable pricing report in under 2 minutes:

```
Phase 1 (parallel):
  ├── Market Data Agent        → industry benchmarks & trends
  ├── Creator Profile Agent    → your unique value assessment
  └── Brand Strategy Agent     → brand budget & negotiation patterns

Phase 2:
  └── Debate Agent             → simulates brand vs. creator negotiation

Phase 3:
  └── Report Agent             → final pricing report with strategy
```

**Output includes:**
- Price range (low / mid / high) with reasoning
- Per-content-type breakdown (dedicated video, integration, short, etc.)
- Negotiation talking points you can use directly
- Contract red flags and clause warnings
- Market context and comparable benchmarks

## Supported Platforms

| Platform | Data Source | Status |
|----------|-----------|--------|
| YouTube  | YouTube Data API v3 (auto-fetch) | Available |
| TikTok   | Manual input form | Available |

## Supported LLM Providers

Choose your preferred LLM provider — bring your own API key:

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4-turbo |
| **Anthropic** | Claude Sonnet 4, Claude Haiku 3.5 |
| **Google** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-Reasoner |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An API key from any supported LLM provider

### Deploy

```bash
git clone https://github.com/CalicoCatto/KnowYourRate.git
cd KnowYourRate
cp .env.example .env
# Edit .env to set your ENCRYPTION_SECRET (see below)
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Generate an Encryption Secret

The app encrypts stored API keys at rest. Generate a secret:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into your `.env` file as `ENCRYPTION_SECRET`.

### Local Development (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL (use Docker or a local instance)
docker compose up db -d

# Run the backend
DATABASE_URL="postgresql+asyncpg://kyr:changeme@localhost:5432/knowyourrate" \
ENCRYPTION_SECRET="your-secret-here" \
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at [http://localhost:5173](http://localhost:5173), API proxied to port 8000.

## Architecture

```
KnowYourRate/
├── backend/                  # Python / FastAPI
│   ├── app/
│   │   ├── agents/           # 5 AI agents + orchestrator
│   │   ├── api/routes/       # REST API endpoints
│   │   ├── llm/              # LiteLLM provider abstraction
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # YouTube API, TikTok, encryption
│   │   └── utils/            # Prompt templates
│   └── tests/
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/            # Setup → Creator → Analysis → Report
│       ├── components/       # Reusable UI components
│       ├── api/              # API client
│       └── store/            # Zustand state management
└── docker-compose.yml        # One-click deployment
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4 |
| Database | PostgreSQL 16 |
| LLM | LiteLLM (unified interface for all providers) |
| Deployment | Docker Compose |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
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
2. **Creator** — Choose your platform (YouTube/TikTok), enter your channel URL or stats manually. Add the brand name and deal type.
3. **Analysis** — Watch the 5-agent pipeline run in real-time with live progress updates.
4. **Report** — Review your pricing intelligence report. Save it or start a new analysis.

## Internationalization

The app supports English and Chinese (Simplified). Language can be switched in the header. Agent-generated reports are produced in your selected language.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_PASSWORD` | Yes | PostgreSQL password (default: `changeme`) |
| `DATABASE_URL` | Yes | Full database connection string |
| `ENCRYPTION_SECRET` | Yes | Fernet key for encrypting stored API keys |
| `YOUTUBE_API_KEY` | No | YouTube Data API v3 key for auto channel lookup |

## License

MIT
