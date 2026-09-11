# CLAUDE.md — Trade101

Auto-loaded each session in this folder. Full history: `docs/HANDOVER.md`. Backlog: `BACKLOG.md`. Spec/plan: `docs/superpowers/`.

## What this is
**Trade101** — a personal stock-research **and learning** web app for Pranav (student, beginning trader). Type a **company name** (any market) → live chart, indicators explained *in context*, chart patterns, a **sourced AI momentum read**, news + "what it means" inference, ecosystem/peers, and a search History.

**North-star guardrails (never break):**
- The app **describes and teaches; it never gives buy/sell advice** or price targets.
- **Numbers are exact** (deterministic code) — agents receive numbers, never compute/restate them unsourced.
- **Every AI claim is sourced.** If a source is unreachable, say so — never fabricate.
- The goal is to **extract and make sense of data**, not read labels back.

## Status
MVP complete (M0–M5), public on GitHub: https://github.com/pranavlakshminarayan/trade101 (branch `master`). Next = Phase 2 (see `BACKLOG.md`): Ask-Claude chat, Comparison tab, deeper non-US sourcing (Firecrawl), richer patterns, real logo.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI) · services/{marketdata,indicators,patterns,news,company,search}.py
          agents/{orchestrator,analysis,llm}.py · tests/
frontend/ src/{App,api}.jsx · components/{Welcome,Research,PriceChart,Metrics,AiRead,NewsPanel,Ecosystem,History,Logo}.jsx · lib/history.js
```
Endpoints: `/health`, `/search?q=`, `/research/{ticker}?period&interval`, `/analyze/{ticker}` (AI, degrades w/o key), `/patterns/{ticker}`, `/ecosystem/{ticker}`.

## Run (two terminals)
```
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
# frontend (from frontend/)
npm run dev            # PowerShell blocks npm → use npm.cmd run dev, or Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Open http://127.0.0.1:5173. Tests: `cd backend && .venv/Scripts/python.exe -m pytest -q`.

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub). `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth. Named per-agent keys per `.env.example`.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (default `finnhub`; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base `http://127.0.0.1:8000`.
- **Each `/analyze` call spends the user's Claude key — be sparing when testing in the browser.**
- Windows 11, Git Bash available; the `claude` CLI is at `C:\Users\prana\.local\bin\claude.exe`.

## Gotchas
- Kill stray servers on ports 8000/5173 before restart (WinError 10013 = port in use).
- Chart-pattern detection is a heuristic learning aid (returns "none" when nothing clean) — never present it as a signal.
- Layout is a self-balancing JS masonry (measures block heights). Browser back/forward + `#TICKER` shareable links work.
