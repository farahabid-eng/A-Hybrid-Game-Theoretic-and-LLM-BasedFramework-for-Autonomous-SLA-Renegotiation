# SLA Renegotiation Framework — Agent Guide

## Setup

```bash
uv sync                      # install prod deps
uv sync --group dev          # + dev (pytest, ruff, mypy)
cd ui && npm install         # frontend
```

## Run

```bash
uv run sla-renegotiation     # FastAPI on :8000 (reload on)
cd ui && npm run dev         # Vite on :5173
uv run python examples/run_cli.py  # headless end-to-end (needs API key)
```

## Tests

```bash
uv run pytest                            # all 18 tests
uv run pytest tests/unit/                # unit only
uv run pytest tests/integration/         # integration (TestClient, no real LLM)
```

Tests use mock LLM fixtures — no `.env` API key needed.

## Lint & Typecheck

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
cd ui && npx tsc --noEmit
```

Order: `ruff check → ruff format --check → mypy → tsc --noEmit`

## Architecture

- **Backend**: `src/sla_renegotiation/` — FastAPI + LangChain/LangGraph, entrypoint `main.py`
- **Frontend**: `ui/` — React 19 + Vite + Tailwind v4, routes in `App.tsx`
- **No DB**: in-memory `WorkflowStore` (dict), lost on restart
- **No PostCSS/autoprefixer**: Tailwind v4 via `@tailwindcss/vite` plugin, index.css is `@import "tailwindcss"`
- **Vite proxies**: removed — set `VITE_API_URL=http://localhost:8000` in `ui/.env` instead (both HTTP & WS derive from it)

## Config & LLM

- `.env` (gitignored) loaded by pydantic-settings at import time
- At least one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRALAI_API_KEY` required
- Per-role model config: `CLIENT_MODEL`, `PROVIDER_MODEL`, `PROFILING_MODEL`, `RC_MODEL`
- API key resolved by model name prefix (mistral → mistralai_api_key, gpt/o → openai_api_key, claude → anthropic_api_key) in `llm/factory.py`
- LangChain pinned: `langchain==1.2.17`, `langchain-core>=1.2.26`

## Domain Quirks

- `Violation.metric` is a `@property` derived from `event_type.value.removesuffix("_violation")` — no separate `metric` field
- `BATNA` is a single `float | None` (absolute walk-away for the violated metric), not a dict
- `ZOPA.calculator` normalizes BATNA as `upper = min(upper, batna / agreed_value)` only for the violated metric
- All `datetime` fields are ISO strings on the model (e.g. `Proposal.timestamp`) — not `datetime` objects, avoids JSON serialization errors

## Negotiation Flow

- **WS streaming** is the primary UX path: token-by-token via `negotiation.token` messages in `api/routes/negotiation.py`
- **REST endpoint** (`POST /workflows/{id}/negotiation/round`) uses `WorkflowService.run_negotiation_round()` — blocking, non-streaming
- **LangGraph graph** (`negotiation/graph.py`) exists but is NOT used by the service layer or WS handler — it's standalone
- `NegotiationAgent` uses lazy init: chain built on first `invoke()`/`stream_content()` call
- Agent prompt enforces: 1-2 sentence proposals, no greetings/meta-commentary, no JSON in streaming mode
- **Early agreement detection** in `negotiation/agreement.py`: keyword-based (`"I accept"`, `"Agreed"`, `"acceptable"`) with negation guard — breaks the round loop when detected
- `tone` field on `ClientForm`/`StakeholderProfile` flows through profile JSON in the prompt (not a separate template variable)

## Code Style

- Python: ruff (line-length=100, double quotes), mypy --strict (excludes tests)
- TypeScript: strict mode, noUnusedLocals, noUnusedParameters
- No comments on code unless asked
