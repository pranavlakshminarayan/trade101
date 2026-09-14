# CLAUDE.md — Trade101

Auto-loaded each session in this folder. **This file is the project's living memory** — treat
it as more current than your own assumptions, and keep it that way (see Memory protocol
below). Full history: `docs/HANDOVER.md`. Phase-by-phase journey + mistakes:
`docs/DEVELOPMENT-LOG.md`. Backlog: `BACKLOG.md`. Recommendations under review:
`docs/trade101-phase-2-recommendations.md`. Spec/plan: `docs/superpowers/`.

## Memory protocol (hard rule — do this without being asked)

This file, `BACKLOG.md`, and `docs/HANDOVER.md` together are the only continuity this project
has across sessions and context resets. Keep them current as part of finishing the work, not
as a separate favor to the user:

- **Before ending a turn that changed status, architecture, endpoints, config/env vars, the
  run/setup steps, or the known-bugs list** — update the matching section of *this file* in
  the same turn.
- **Bug found or fixed** → update "Known bugs" here immediately, and mirror the checkbox in
  `BACKLOG.md`. A bug that's fixed gets removed from both, not just checked off.
- **Milestone/phase status changes** (a phase starts, finishes, or gets reprioritized) →
  update "Status" here and the phase headings in `BACKLOG.md`.
- **A decision, incident, or long narrative worth preserving in detail** → append a dated
  entry to `docs/HANDOVER.md` rather than bloating this file. This file stays a concise,
  current-state reference; `docs/HANDOVER.md` is where the "why" and the full story live.
- **Phase-by-phase development tracking** → `docs/DEVELOPMENT-LOG.md` records the journey
  phase by phase (idea → visualisation → Phase 1 → 1.5 → …). **Hard rule: update it whenever a
  phase completes** — what was executed, the inputs/suggestions that shaped it, and, honestly,
  the **mistakes made and how they were corrected** in that phase (every phase section must have
  a "Mistakes / course-corrections" note; "none" is only acceptable if truly none). Do this as
  part of finishing the phase, without being asked.
- **New standalone doc created** (a recommendations file, a design note) → link it from here
  and from `BACKLOG.md` in the same turn it's created — an unlinked doc is as good as lost.
- If you ever find this file, `BACKLOG.md`, and `docs/HANDOVER.md` disagreeing about current
  state, treat that as a bug in the memory itself: fix the discrepancy as part of the task,
  don't just note it and move on.

## What this is
**Trade101** — a personal stock-research **and learning** web app for Pranav (student, beginning trader). Type a **company name** (any market) → live chart, indicators explained *in context*, chart patterns, a **sourced AI momentum read**, news + "what it means" inference, ecosystem/peers, and a search History.

**North-star guardrails (never break):**
- The app **describes and teaches; it never gives buy/sell advice** or price targets.
- **Numbers are exact** (deterministic code) — agents receive numbers, never compute/restate them unsourced.
- **Every AI claim is sourced.** If a source is unreachable, say so — never fabricate.
- The goal is to **extract and make sense of data**, not read labels back.

## Status
MVP complete (M0–M5), public on GitHub: https://github.com/pranavlakshminarayan/trade101 (branch `master`).

**Phase 1 flaw pass done** (2026-09-14, see `docs/HANDOVER.md` §4.2) — key leak, raw errors,
ecosystem-gap messaging, datetime all fixed; user still needs to rotate the Finnhub key.

**Phase 1.5 — trust and coherence, in progress** (see `BACKLOG.md`). Done: evidence relevance
filter (`services/evidence.py`) + claim-level Fact/Interpretation/Unknown labels + evidence
tests + keys-backend-only confirmed. Remaining: timeframe integrity (shared as-of label +
timeframe-correct indicators), coverage badges, a cache layer, and a not-advice notice by the
narrative. Then Phase 2 proper (Ask-Claude chat, Comparison tab, Firecrawl non-US sourcing,
richer patterns, real logo). Full rationale: `docs/trade101-phase-2-recommendations.md`.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI) · services/{marketdata,indicators,patterns,news,company,search,evidence,safe}.py
          agents/{orchestrator,analysis,llm}.py · tests/
frontend/ src/{App,api}.jsx · components/{Welcome,Research,PriceChart,Metrics,AiRead,NewsPanel,Ecosystem,History,Logo}.jsx · lib/history.js
```
- `services/evidence.py` — deterministic relevance filter; drops unrelated news before the AI
  sees it (Phase 1.5 guardrail). `services/safe.py` — `redact_secrets` for anything client-bound.
- `/analyze` now fetches the company profile too (for relevance filtering) and returns
  `news.sourcing` (kept/dropped counts) + per-evidence Fact/Interpretation/Unknown labels.
Endpoints: `/health`, `/search?q=`, `/research/{ticker}?period&interval`, `/analyze/{ticker}` (AI, degrades w/o key), `/patterns/{ticker}`, `/ecosystem/{ticker}`.

## Run (two terminals)
```
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
# frontend (from frontend/)
npm run dev            # PowerShell blocks npm → use npm.cmd run dev, or Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Open http://127.0.0.1:5173. Tests: `cd backend && .venv/Scripts/python.exe -m pytest -q`.

**App-link rule (hard rule):** whenever you run/build the app for the user to check, make sure
both servers are up and **return the local link `http://127.0.0.1:5173`** in the reply — Pranav
checks it on this machine and reports back what works/breaks so we fix issues one by one.
The app is **local-only during development**; a shareable/deployed URL is a Phase 2 task (see
`BACKLOG.md`), to be created after the full execution.

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub). `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth. Named per-agent keys per `.env.example`.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (default `finnhub`; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base `http://127.0.0.1:8000`.
- **Each `/analyze` call spends the user's Claude key — be sparing when testing in the browser.**
- Windows 11, Git Bash available; the `claude` CLI is at `C:\Users\prana\.local\bin\claude.exe`.

## Known bugs
- **Non-US listings get no news** — Finnhub free tier 403s on non-US symbols. Now degrades with
  a plain message ("not available on the current news plan"); the AI still infers nothing rather
  than fabricating. The real fix is Phase 2 Firecrawl/alternative non-US sourcing.

### Fixed 2026-09-14 (Phase 1 flaw pass — see `docs/HANDOVER.md` §4.2)
- ~~Finnhub key leaked to the browser~~ — `services/news.py` no longer returns raw exceptions;
  errors are hardcoded friendly strings, plus `services/safe.py::redact_secrets` scrubs any
  key/URL that could ride an exception into `/analyze`. Regression tests in `tests/test_safe.py`.
  **Action still on the user: rotate the Finnhub key** if the app was ever shown where the old
  leaked value could have been seen.
- ~~Raw provider errors shown as user-facing copy~~ — replaced with plain explanations.
- ~~Ecosystem thin outside the US shows blank~~ — `services/company.py` now returns a `coverage`
  map explaining why beta/peers are missing; the Ecosystem panel renders the explanation.
- ~~`datetime.utcnow()` deprecated~~ — now timezone-aware (`datetime.now(timezone.utc)`).

## Gotchas
- Kill stray servers on ports 8000/5173 before restart (WinError 10013 = port in use).
- Chart-pattern detection is a heuristic learning aid (returns "none" when nothing clean) — never present it as a signal.
- Layout is a self-balancing JS masonry (measures block heights). Browser back/forward + `#TICKER` shareable links work.
