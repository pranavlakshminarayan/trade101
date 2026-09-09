# Trade101

A personal stock-research **and learning** app. It pulls live market data, indicators, news, and company context for any ticker, teaches the metrics *in the context of the stock you're viewing*, and reads momentum with sourced evidence.

**It never tells you to buy or sell.** It's a data-analytics + learning tool: numbers are exact (deterministic code), and every AI opinion is source-backed.

## Status
Milestone 1 — real-time deterministic core (backend). See `docs/superpowers/`:
- `specs/2026-09-09-trade101-design.md` — design
- `plans/2026-09-09-trade101-implementation-plan.md` — build plan

## Run the backend
```bash
cd backend
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
```
Then:
- `GET http://localhost:8000/health`
- `GET http://localhost:8000/research/NVDA` (works for any ticker; non-US needs a suffix, e.g. `RELIANCE.NS`, `005930.KS`)

## Test
```bash
cd backend
.venv/Scripts/python.exe -m pytest -q
```

## Config
Copy `.env.example` to `.env`. Claude API keys are only needed from Milestone 3 (AI narration); Milestones 0–2 run with no keys.
