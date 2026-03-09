[English](./README.md) | [中文](./README_zh.md)

# KnowYourRate

**Multi-agent pricing intelligence engine for content creators**

KnowYourRate helps YouTube and TikTok creators determine fair pricing for brand collaborations. Instead of guessing or relying on outdated calculators, creators get multi-dimensional analysis from 4 specialized AI agents that combine deterministic CPM calculations with qualitative LLM reasoning, producing actionable pricing reports with negotiation strategies.

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
| **A — Creator Profile** | Computes base price from CPM tables, applies 5 modifier categories, asks LLM for qualitative adjustment (clamped ±30%) | Qualitative assessment only |
| **B — Market Intel** | Applies deal condition multipliers (deliverable type, usage rights, exclusivity), looks up 40+ known brand patterns, asks LLM for market context | Brand intelligence, comparable deals |
| **C — Debate** | 3-round adversarial debate: Bull (creator agent, temp 0.7) vs Bear (brand manager, temp 0.3), cross-rebuttal round, then Judge (temp 0.4) synthesizes | Full debate reasoning |
| **D — Report** | Generates narrative report using exact computed prices, package tiers, negotiation scripts, and contract red flags | Report writing |

**Output includes:**
- Price range (walk-away / fair market / anchor) with reasoning
- Per-content-type breakdown (dedicated video, integration, short, etc.)
- 3-tier package recommendations (Starter / Standard / Premium)
- Negotiation talking points and scripts for 3 scenarios
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
| **Moonshot (Kimi)** | Kimi K2.5, Kimi K2 |
| **SiliconFlow** | DeepSeek V3.2, MiniMax M2.5, GLM-4.7, GLM-5, Step 3.5 Flash |

## Quick Start

Three ways to run KnowYourRate:

### Option 1: Windows EXE (Easiest)

No installation needed. Download and double-click.

1. Go to [Releases](https://github.com/CalicoCatto/KnowYourRate/releases)
2. Download `KnowYourRate-windows-x64.zip`
3. Unzip and run `KnowYourRate.exe`
4. The browser opens automatically at `http://localhost:8000`

Data is stored in a SQLite database (`knowyourrate.db`) in the same folder as the EXE.

### Option 2: Docker Compose

```bash
git clone https://github.com/CalicoCatto/KnowYourRate.git
cd KnowYourRate
cp .env.example .env
# Edit .env to set your ENCRYPTION_SECRET (see below)
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Option 3: Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Option A: Use SQLite (zero setup)
DATABASE_URL="sqlite+aiosqlite:///knowyourrate.db" \
uvicorn app.main:app --reload --port 8000

# Option B: Use PostgreSQL
docker compose up db -d
DATABASE_URL="postgresql+asyncpg://kyr:changeme@localhost:5432/knowyourrate" \
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
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
│   │   ├── agents/           # 4 AI agents + orchestrator
│   │   │   ├── creator_profile.py  # Agent A: CPM calculation + qualitative assessment
│   │   │   ├── market_data.py      # Agent B: Deal conditions + brand intel
│   │   │   ├── debate.py           # Agent C: Bull/Bear/Judge adversarial debate
│   │   │   ├── report.py           # Agent D: Strategy report generation
│   │   │   └── orchestrator.py     # Pipeline routing + coordination
│   │   ├── api/routes/       # REST API endpoints
│   │   ├── llm/              # LiteLLM provider abstraction
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # YouTube API, TikTok, encryption
│   │   └── utils/
│   │       ├── prompts.py       # All agent prompt templates
│   │       └── pricing_tables.py # CPM tables, multipliers, modifiers, brand DB
│   └── tests/
├── frontend/                 # React / TypeScript / Vite / Tailwind
│   └── src/
│       ├── pages/            # Setup → Creator → Analysis → Report
│       ├── components/       # Reusable UI components
│       ├── api/              # API client + SSE helpers
│       └── store/            # Zustand state management
└── docker-compose.yml        # One-click deployment
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), LiteLLM |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, Zustand |
| Database | PostgreSQL 16 or SQLite (auto-detected) |
| LLM | LiteLLM (unified interface for 6 providers) |
| Deployment | Docker Compose, Windows EXE, or local dev |

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
2. **Creator** — Choose your platform (YouTube/TikTok), enter your channel URL or stats manually. Add the brand name, deal type, usage rights, and exclusivity terms.
3. **Analysis** — Watch the 4-agent pipeline run in real-time with live SSE progress updates. Fast-track queries skip Agents B and C.
4. **Report** — Review your pricing intelligence report with price ranges, negotiation scripts, package tiers, and contract red flags. Save it or start a new analysis.

## Internationalization

The app supports English and Chinese (Simplified). Language can be switched in the header. Agent-generated reports are produced in your selected language.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string (PostgreSQL or SQLite) |
| `ENCRYPTION_SECRET` | Yes | Fernet key for encrypting stored API keys |
| `YOUTUBE_API_KEY` | No | YouTube Data API v3 key for auto channel lookup |
| `DB_PASSWORD` | Docker only | PostgreSQL password (default: `changeme`) |

## License

MIT
