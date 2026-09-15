# CLAUDE.md — Trade Craft

> **Brand: Trade Craft** (renamed from "Trade101" on 2026-09-15). The GitHub repo, local
> folder, and internal package names stay `trade101` — only the user-facing brand + logo changed.
> Theme is deep navy with cream/near-white text (`frontend/src/styles.css` `:root`).
> **Repo is PRIVATE** (set 2026-09-15). Deploy is **single-service** — FastAPI serves the built
> React app (`app.py` mounts `frontend/dist`). Two deploy paths, both free, no code changes
> either way: `render.yaml` (**no Docker** — Render native Python runtime, recommended) or
> `Dockerfile` (for hosts that want a container). See `docs/DEPLOY.md`.
>
> **⚠️ PRE-SHARE BUG (fix before sharing the URL with ANYONE):** `/analyze` and `/ask` spend the
> owner's Claude key with no auth/rate-limit — a public visitor could run up the bill. Fine while
> the URL is private/personal. **User asked to be reminded at the END of Phase 3 to fix this**
> (password/token gate + rate-limit/cap) before distributing. Tracked in `BACKLOG.md` → Pre-share.
> **STATUS 2026-09-16: the fix is WRITTEN but NOT ON `master`** — `services/access.py` (token
> header + UTC daily cap) sits on the unmerged, unpushed branch `claude/trading-idea-phase-3-297572`.
> Merge it before deploying. Target audience confirmed as **private link for the user + a few
> friends**, so the shared-token + cap design is the right level.
>
> **📋 CRITICAL AUDIT (2026-09-16): [`docs/AUDIT.md`](docs/AUDIT.md)** — adversarial end-to-end review
> (functional / logical / executional / UI-UX), 30+ ranked findings with reproductions and a
> wave-by-wave fix order. Read it before planning new work; its Wave 0/1 items are mirrored in
> `BACKLOG.md` and in "Known bugs" below.

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
**Trade Craft** (renamed from "Trade101" 2026-09-15) — a personal stock-research **and learning** web app for Pranav (student, beginning trader). Type a **company name** (any market) → live chart, indicators explained *in context*, chart patterns, a **sourced AI momentum read**, an Ask-Claude chat, news + "what it means" inference, ecosystem/peers, a Comparison tab, a Watchlist, and a search History.

**North-star guardrails (never break):**
- The app **describes and teaches; it never gives buy/sell advice** or price targets.
- **Numbers are exact** (deterministic code) — agents receive numbers, never compute/restate them unsourced.
- **Every AI claim is sourced.** If a source is unreachable, say so — never fabricate.
- The goal is to **extract and make sense of data**, not read labels back.

## Status
MVP complete (M0–M5). Repo: https://github.com/pranavlakshminarayan/trade101 (branch `master`,
**PRIVATE** since 2026-09-15 — do not make public without being asked).

**Phase 1 flaw pass done** (2026-09-14, see `docs/HANDOVER.md` §4.2) — key leak, raw errors,
ecosystem-gap messaging, datetime all fixed; user still needs to rotate the Finnhub key.

**Phase 1.5 — trust and coherence, mostly done** (see `BACKLOG.md`). Done: evidence relevance
filter + claim-level Fact/Interpretation/Unknown labels + evidence tests + keys-backend-only +
prompt caching + a backend TTL cache (`services/cache.py`). Remaining: timeframe integrity,
coverage badges, a not-advice notice by the narrative.

**Phase 2 — essentially complete** (see `BACKLOG.md`). Done: **Ask-Claude chat** (floating
chatbot widget) — `/ask/{ticker}` + `agents/chat.py`, grounded, no advice, prompt-cached;
**non-US sourcing (free tier)** — computed beta vs the regional index (`company.py`) + Yahoo
news fallback + name fix; **Comparison tab** — two stocks side by side (normalized chart +
metrics table), deterministic, no AI call, "describes differences, never which to buy", with the
same name→symbol disambiguation picker as the main search; **ecosystem node graph** (peers as a
radial graph in `Ecosystem.jsx::EcoGraph`); **real logo** — superseded by the 2026-09-15 rebrand
below. Deferred to post-deploy (user's call): the **paid** Firecrawl/Exa provider for deeper
non-US scraping. Full rationale: `docs/trade101-phase-2-recommendations.md`.

**Rebrand — Trade101 → Trade Craft** (2026-09-15). New growth-spiral logo (`Logo.jsx`,
green→teal ribbon + arrow + bar chart + $/€/¥ nodes), deep-navy theme (`styles.css` `:root`),
brand string updated everywhere user-facing incl. the AI prompts. See `docs/HANDOVER.md` §11.

**Phase 3 — partly on `master`, partly stranded** (2026-09-15/16). ⚠️ A commit titled "Complete
Phase 3" (`8d80ef9` on `claude/trading-idea-phase-3-297572`) adds the access guard, Google-News
fallback, `lib/currency.js`, the Practice Lab and accessibility fixes — but it is **unmerged and
unpushed**, so none of it is in `master` or on GitHub. Treat Phase 3 as *incomplete* until that
branch is merged. On `master` today: **Watchlist** — `components/Watchlist.jsx` +
`lib/watchlist.js` (localStorage; ☆ Watch toggle on the research header; a `watchlist` view with
live quotes via `/research`, framed as tracking, not trade prompts). App views are now
`home | compare | watchlist | history`. Also done as part of Phase 3: **single-service deploy is
ready** (two free paths — `render.yaml` no-Docker or `Dockerfile`, see `docs/DEPLOY.md`) and the
**GitHub repo is now private** — but **not yet live** (needs the user's host signup) and **not to
be shared even once live** until the pre-share fix above is done. Desktop packaging was
considered and **parked** in favor of the web deploy (see `docs/HANDOVER.md` §13 — no Rust/
PyInstaller installed, and the actual goal was a shareable link, which packaging doesn't produce).
Remaining Phase 3 (user to prioritise): more markets fully supported, an optional simulated
*practice lab* (kept separate from the main learning flow), and accessibility polish.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI) · services/{marketdata,indicators,patterns,news,company,search,evidence,safe,cache}.py
          agents/{orchestrator,analysis,chat,llm}.py · tests/
frontend/ src/{App,api}.jsx · components/{Welcome,Research,PriceChart,Metrics,AiRead,NewsPanel,Ecosystem,AskClaude,Compare,ComparisonChart,Watchlist,History,Logo}.jsx · lib/{history,watchlist}.js
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
- **Watchlist**: `lib/watchlist.js` (localStorage, mirrors `lib/history.js`) + `components/
  Watchlist.jsx`. ☆/★ toggle on the research header; the view fetches a live quote per tracked
  ticker via `/research` (no Claude spend). Framed as tracking/study, never positions/P&L/signals.
- **Single-service deploy**: `app.py` mounts `frontend/dist` (built React) via `StaticFiles`
  *after* all API routes, so one process/origin serves both — `api.js` uses same-origin in prod
  (`import.meta.env.DEV` switch), `:8000` directly in dev. Two build paths, no app-code
  difference between them: `render.yaml` (Render Blueprint, native Python runtime, **no
  Docker**) or `Dockerfile` + `.dockerignore` (multi-stage, for hosts that want a container).
  Full steps: `docs/DEPLOY.md`.
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
The app is **local-only for now**; a hosted deploy is config-ready (`docs/DEPLOY.md` — Render,
either `render.yaml` no-Docker or `Dockerfile`) but not yet live, since going live needs the
user's own host-account signup. **Even once live, that URL is personal-use only — never suggest
sharing it** until the pre-share fix in the header above is done (`BACKLOG.md` → Pre-share checklist).

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub). `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth. Named per-agent keys per `.env.example`.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (default `finnhub`; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base `http://127.0.0.1:8000`.
- **Each `/analyze` call spends the user's Claude key — be sparing when testing in the browser.**
- Windows 11, Git Bash available; the `claude` CLI is at `C:\Users\prana\.local\bin\claude.exe`.

## Known bugs
**Full ranked list with evidence: [`docs/AUDIT.md`](docs/AUDIT.md) (critical audit, 2026-09-16).**
Mirrored as checkboxes in `BACKLOG.md` → "Audit — Wave 0/1". Open criticals:

- **Phase 3 work is stranded off `master`** — branch `claude/trading-idea-phase-3-297572`
  (`8d80ef9`, 24 files, +1256) holds the pre-share access guard (`services/access.py`), the
  Google-News fallback, `lib/currency.js`, the Practice Lab and accessibility fixes. **Unmerged
  AND unpushed** (worktree-only). Merge + push before anything else.
- **Market cap rendered as USD for every listing** (`Ecosystem.jsx:4` hardcodes `$`) — Nintendo
  displays `$9.36T` (really ¥9.36T ≈ $63B) vs Apple `$4.81T`. Breaks "numbers are exact". ✅ verified
- **`above_sma50/200` returns `false` for *unknown*** (`indicators.py:108`) and that false is sent
  to Claude as exact data — the deterministic layer feeding the model a wrong fact. ✅ verified
- **Search auto-picks on a name/ticker collision** (`App.jsx:56`) — typing "Sony" silently opens the
  NYSE ADR, never offering Tokyo. Ranking also puts ADR/OTC above primary listings. ✅ verified
- **News only reaches the UI via the paid `/analyze` call** (`NewsPanel.jsx:8`) — no key, an AI
  error, or the daily cap means no headlines at all.
- **Chart is destroyed/rebuilt on every parent render** (`Research.jsx:170` passes a fresh array
  literal) — typing in the header search rebuilds it per keystroke; auto-refresh resets zoom.
- **Pattern detector only inspects the last 3 swings** and can return at most one reversal + one
  trendline shape; its double-top branch rejects the textbook case.
- **Not shareable as written** — `Welcome.jsx:26` hardcodes "Pranav"; `news.py:23` sends a personal
  email as the SEC User-Agent.

### Fixed 2026-09-14/15 (Comparison tab — see `docs/HANDOVER.md` §10)
- ~~Comparison pickers took the first search match blindly~~ (e.g. "samsung" → wrong/failed
  symbol) — `Compare.jsx` now has the same name→symbol disambiguation picker as the main search.
- ~~`/research/005930.KS` (and similar) 500'd~~ — `ValueError: nan not JSON compliant` from a bad
  holiday/partial OHLC bar. Fixed at the source: `marketdata.get` now `dropna`s NaN OHLC rows +
  zero-fills NaN volume, protecting every consumer (research/patterns/analyze), not just Compare.

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
