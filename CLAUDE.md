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
MVP (M0–M5) + Phases 1.5/2/2.5/3/4 complete. 128 backend tests. Repo: https://github.com/pranavlakshminarayan/trade101.
Roadmap was reordered by an external review (see `docs/trade101-phase-2-recommendations.txt` and `BACKLOG.md`): trust & coherence before features.
**Read `docs/EXECUTION-REPORT.md` first** — it lists what is built, what needs live testing, and known gaps.
Still open: Ask-Claude chat, Firecrawl/non-US sourcing, richer patterns, real logo, a licensed relationship dataset.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI)
          services/  marketdata indicators patterns news company search        (core)
                     evidence cache storage usage                              (trust backbone)
                     fundamentals replay lenses compare watchlist relationships (features)
          agents/{orchestrator,analysis,llm}.py · tests/ (128)
frontend/ src/{App,api}.jsx · lib/{history,theme}.js
          components/ Welcome Research PriceChart Metrics AiRead NewsPanel Ecosystem History Logo
                      AsOf Coverage Lenses StudyMode Replay Journal Fundamentals
                      Compare Watchlist Practice Graph
```
Endpoints: `/health` `/search` `/research/{t}` `/analyze/{t}` `/patterns/{t}` `/ecosystem/{t}`
`/fundamentals/{t}` `/lenses/{t}` `/graph/{t}` `/replay/{t}` `/replay/{t}/reveal`
`/journal` `/watchlist` `/practice` `/compare?tickers=` `/usage` `/history` `/cache`

**The evidence pipeline is the backbone.** One bounded analysis call sits between two
deterministic gates in `services/evidence.py`: `select()` decides what the model may see,
`verify()` drops any claim citing something we did not supply. Do not route new AI features
around it, and do not add agents or keys to improve sourcing — fix the evidence first.

## Run (two terminals)
```
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
# frontend (from frontend/)
npm run dev            # PowerShell blocks npm → use npm.cmd run dev, or Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Open http://127.0.0.1:5173. Tests: `cd backend && .venv/Scripts/python.exe -m pytest -q`.

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub). `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth.
- **One key is a fully supported setup.** The other named keys (`_RESEARCH_`, `_ECOSYSTEM_`, `_ORCHESTRATOR_`) are optional and fall back to `TRADE101_ANALYSIS_KEY`. Per-feature spend is tracked in-app either way — `GET /usage` breaks cost down by purpose, key, model and ticker. Pricing table in `services/usage.py` (published rates, captured 2026-06-24); an unknown model is counted but never priced.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (default `finnhub`; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base `http://127.0.0.1:8000`.
- **Each `/analyze` call spends the user's Claude key — be sparing when testing in the browser.**
- Windows 11, Git Bash available; the `claude` CLI is at `C:\Users\prana\.local\bin\claude.exe`.

## Gotchas
- Kill stray servers on ports 8000/5173 before restart (WinError 10013 = port in use).
- Chart-pattern detection is a heuristic learning aid (returns "none" when nothing clean) — never present it as a signal.
- **Never fabricate an absence.** Empty ≠ nonexistent: "no relationship source configured" and "this company has no suppliers" look identical in a UI and mean opposite things. Every empty list must say which it is.
- Replay's `setup` and `reveal` are separate endpoints on purpose — the future must never reach the browser before the learner commits a read.
- Tests must stay hermetic: stub `news.get_recent_filings` and `fundamentals.get_fundamentals`, or the suite waits on real SEC/Yahoo timeouts.
- Layout is a self-balancing JS masonry (measures block heights). Browser back/forward + `#TICKER` shareable links work.
