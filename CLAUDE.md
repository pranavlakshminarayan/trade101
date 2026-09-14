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

**Phase 1.5 — trust and coherence, mostly done** (see `BACKLOG.md`). Done: evidence relevance
filter + claim-level Fact/Interpretation/Unknown labels + evidence tests + keys-backend-only +
prompt caching + a backend TTL cache (`services/cache.py`). Remaining: timeframe integrity,
coverage badges, a not-advice notice by the narrative.

**Phase 2 — in progress** (see `BACKLOG.md`). Done: **Ask-Claude chat** (floating chatbot
widget) — `/ask/{ticker}` + `agents/chat.py`, grounded, no advice, prompt-cached; **non-US
sourcing (free tier)** — computed beta vs the regional index (`company.py`) + Yahoo news
fallback + name fix; **Comparison tab** — two stocks side by side (normalized chart + metrics
table), deterministic, no AI call, "describes differences, never which to buy". **real data-cube logo** (`Logo.jsx`, hand-crafted SVG); **ecosystem node graph** (peers as a
radial graph in `Ecosystem.jsx::EcoGraph`). Deferred to post-deploy (user's call): the **paid**
Firecrawl/Exa provider for deeper non-US scraping, and **deploying a shareable URL**. That
leaves Phase 2 essentially complete bar the two deferred items. Full rationale:
`docs/trade101-phase-2-recommendations.md`.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI) · services/{marketdata,indicators,patterns,news,company,search,evidence,safe,cache}.py
          agents/{orchestrator,analysis,chat,llm}.py · tests/
frontend/ src/{App,api}.jsx · components/{Welcome,Research,PriceChart,Metrics,AiRead,NewsPanel,Ecosystem,AskClaude,Compare,ComparisonChart,History,Logo}.jsx · lib/history.js
```
- `services/evidence.py` — deterministic relevance filter; drops unrelated news before the AI
  sees it (Phase 1.5 guardrail). `services/safe.py` — `redact_secrets` for anything client-bound.
- `/analyze` now fetches the company profile too (for relevance filtering) and returns
  `news.sourcing` (kept/dropped counts) + per-evidence Fact/Interpretation/Unknown labels.
- News is Finnhub → **Yahoo Finance fallback** (keyless, global) so non-US listings get a feed.
- `company.py` **computes beta** vs the regional index (suffix→index map: .T→Nikkei, .KS→KOSPI,
  .NS→Nifty, …) when the provider has none — deterministic; response carries `betaSource`
  ("provider"|"computed") + `betaIndex`. Non-US peers are still gapped (Firecrawl is post-deploy).
- `patterns.py` detects reversals **and** trendline shapes (triangles/wedges/channels), drawn
  via a `lines` field in `PriceChart.jsx`. Only shapes actually present are returned.
- `frontend/src/api.js` holds a **session result cache** (research/analyze/ecosystem/patterns) —
  tab-switching restores from memory; `/analyze` runs at most once per ticker per session.
- **Comparison tab**: `components/Compare.jsx` (App `view === 'compare'`, tabs in Research/Welcome)
  loads two stocks via `/research` + `/ecosystem` (no `/analyze` → no Claude spend);
  `ComparisonChart.jsx` plots both rebased to 100 (% moves). Metrics table reuses `lessons.js`
  (`METRICS`, `metricValue`). Each slot has the **same name→symbol disambiguation picker as the
  main search** (type a name → pick from candidates). Guardrail: describes differences, never
  "which is better".
- `marketdata.get` drops NaN OHLC rows + zero-fills NaN volume — a bad partial bar (seen on
  005930.KS) otherwise produces a NaN that FastAPI can't JSON-serialize (500 on `/research`).
- `agents/llm.py` sends the analysis **system prompt as a `cache_control: ephemeral` block**
  (prompt caching) — served at ~0.1× input cost within the 5-min window. Requires the prefix to
  clear the model minimum (Sonnet 5 = 1024 tok, Opus 5 = 512); ours is ~1306 tok so it fires.
  `llm.py` logs `cache_write`/`cache_read`/`in`/`out` per call — check the server log to confirm.
- **Ask-Claude chat**: `POST /ask/{ticker}` → `orchestrator.ask` → `agents/chat.py`. Same
  guardrails as analysis; the ticker's data bundle is rendered into a cached system prompt so
  multi-turn chat reuses it (chat turn 2+ reads the whole prefix from cache). `agents/chat.py`
  uses `effort="medium"` (cheaper). `orchestrator.gather()` is the shared deterministic bundle,
  memoised by `services/cache.py` (TTL 5 min) so chat turns don't re-fetch and numbers stay
  stable across a conversation. Frontend: `components/AskClaude.jsx` is a **floating chatbot
  widget** (bubble pinned bottom-right → opens an overlay panel over the content), rendered at
  the `Research` root (not in the masonry); per-ticker threads kept in module memory.
Endpoints: `/health`, `/search?q=`, `/research/{ticker}?period&interval`, `/analyze/{ticker}` (AI, degrades w/o key), `POST /ask/{ticker}` (Ask-Claude chat), `/patterns/{ticker}`, `/ecosystem/{ticker}`.

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
- _(none open right now — non-US news was fixed 2026-09-14 via the Yahoo fallback below.)_

### Fixed 2026-09-14 (UX/data fixes — see `docs/DEVELOPMENT-LOG.md` 2026-09-14 entry)
- ~~Non-US listings get no news~~ — `services/news.py` now falls back to keyless Yahoo Finance
  news when Finnhub can't serve a symbol; non-US listings get a real feed.
- ~~Non-US stocks displayed as the ticker ID~~ — `marketdata.py` prefers `longName` (+ a Yahoo
  search fallback); the frontend headline leads with the company name, ticker shown as a tag.
- ~~Only a couple of patterns ever appeared~~ — `services/patterns.py` now also detects
  triangles/wedges/channels (trendline family) and returns only the shapes actually present.
- ~~Switching tabs reloaded everything and re-spent the Claude key~~ — `frontend/src/api.js`
  now has a session result cache (research/analyze/ecosystem/patterns); `/analyze` runs once per
  ticker per session. Auto-refresh bypasses it with `{ fresh: true }`.

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
- **`uvicorn --reload` leaves zombie workers on Windows.** Each restart can orphan a worker that
  keeps port 8000 bound and serves *stale* code (symptom: a new route 404s / a code change
  doesn't take, but `import app` shows it fine). Killing a `--reload` worker makes its reloader
  respawn one. Fix: `Get-CimInstance Win32_Process | ? CommandLine -match 'uvicorn|multiprocessing.spawn'`
  (exclude the yfinance-mcp / Claude Extensions python), kill those, confirm the port is clear,
  then start ONE backend. For a throwaway verification instance, run without `--reload`.
- Chart-pattern detection is a heuristic learning aid (returns "none" when nothing clean) — never present it as a signal.
- Layout is a self-balancing JS masonry (measures block heights). Browser back/forward + `#TICKER` shareable links work.
