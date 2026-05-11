# SLA Renegotiation Framework

LLM-based SLA renegotiation framework using LangChain + LangGraph multi-agent negotiation.

## Prerequisites

- Python 3.12+
- Node.js 18+
- At least one LLM API key (OpenAI, Anthropic, or Mistral)

## Setup

```bash
cp .env.example .env    # then add your API key(s)
uv sync
uv sync --group dev
```

## Run

```bash
uv run sla-renegotiation
```

## UI

```bash
cp ui/.env.example ui/.env
cd ui && npm install && npm run dev
```
