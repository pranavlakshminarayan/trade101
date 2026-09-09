# Trade101 — Implementation Plan

**Date:** 2026-09-09 · Derived from `specs/2026-09-09-trade101-design.md`
**Rule:** every milestone ends in something you can *run and test*. We build the real-time, ticker-agnostic core first; AI narration sits on top of it.

---

## Milestone 0 — Scaffold (no features yet)
**Goal:** a clean, runnable skeleton.
- `git init`; add `.gitignore` (`.env`, `.superpowers/`, `data/`, `node_modules/`, `__pycache__/`).
- `backend/` — FastAPI app, venv, deps (`fastapi`, `uvicorn`, `yfinance`, `pandas`, `pandas-ta`, `scipy`, `httpx`, `anthropic`). A `GET /health` route.
- `frontend/` — Vite + React skeleton, one page that pings `/health`.
- `.env.example` documenting every key name (`Trade101-Orchestrator`, `-Research`, `-Analysis`, `-Ecosystem`, `Trade101-News`, `Trade101-Scrape`).
- **Verify:** backend serves `/health`; frontend loads and shows "connected".

## Milestone 1 — Real-time deterministic core (THE foundation, no AI)
**Goal:** live, exact data for *any* ticker.
- `services/marketdata.py` — yfinance quote + OHLCV + financials (pluggable provider interface).
- `services/indicators.py` — RSI(14), MACD, SMA/EMA 50/200, Bollinger, volume. **Unit-tested vs known fixtures.**
- `GET /research/{ticker}` → returns a **real** bundle (price, OHLCV, indicators) for whatever ticker is passed.
- **Verify:** `GET /research/NVDA` and `GET /research/<any US ticker>` return correct live numbers; indicator tests pass. *(This is your "real-time, not NVDA-hardcoded" guarantee, proven.)*

## Milestone 2 — Frontend research view (renders the real data)
**Goal:** see the live data in the Trade101 UI.
- Welcome page (search → route to research) + Research view shell (dark palette, tabs).
- **Live chart** via Lightweight-Charts fed by the OHLCV; auto-refresh interval; "delayed ~15m" label.
- Metrics row (standard symbols) + click-to-learn panel (static lesson text for now) + Esc to close.
- **Verify:** type a ticker on Welcome → research view draws the real chart + real indicators.

## Milestone 3 — The agents (AI narration, grounded)
**Goal:** momentum read + news + "What it means", all sourced.
- `services/news.py` + **Research agent** (Claude API) using a scrape/news provider (Firecrawl / Bright Data / Exa — pick one) — returns sourced items.
- **Analysis agent** — takes exact numbers + news → momentum read (confidence, no buy/sell), contextual metric lessons, news **"What it means"** inference.
- **Citation guard** — reject any numeric claim without a source; tests for it.
- Wire `Ask Claude` seam (endpoint stub, UI button — full chat is Phase 2).
- **Verify:** research view shows a sourced momentum read + Feed/"What it means"; guard test passes; if the API fails, chart + indicators still render.

## Milestone 4 — Patterns, ecosystem, references, history
- `services/patterns.py` — triple-top/bottom + head-and-shoulders via extrema; return draw-points.
- `Patterns` button → slide-out panel + magnifier overlay on the chart.
- **Ecosystem agent** — supply chain + index membership + beta; index learning.
- References box (aggregate all sources) + `services/storage.py` (SQLite) saving history with a 2-line summary.
- **Verify:** magnifier draws the detected pattern; ecosystem + references populate; history persists across restarts.

## Milestone 5 — Resilience, tests, the true test
- Error handling: unknown ticker, source down/rate-limited, AI timeout (graceful degrade).
- Fill out tests (indicators, patterns, citation guard, `/research` smoke).
- **Your true test:** you name a surprise stock; we run it live end-to-end.

---

## Notes
- **Claude API keys** (named per component) needed from Milestone 3 on.
- **News/scrape provider** chosen at Milestone 3 (Firecrawl / Bright Data / Exa).
- Logo (OpenRouter) is independent — drop in whenever.
- Phases 2–3 (other markets, Comparison, History UI, Ask-Claude chat, richer patterns, desktop packaging) follow after this MVP runs.
