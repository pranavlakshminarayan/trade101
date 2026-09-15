# CLAUDE.md — Trade Craft

> **Brand: Trade Craft** (renamed from "Trade101" on 2026-09-15). The GitHub repo, local
> folder, and internal package names stay `trade101` — only the user-facing brand + logo changed.
> Theme is deep navy with cream/near-white text (`frontend/src/styles.css` `:root`).
> **Repo is PRIVATE** (set 2026-09-15). Deploy is **single-service** — FastAPI serves the built
> React app (`app.py` mounts `frontend/dist`). Two deploy paths, both free, no code changes
> either way: `render.yaml` (**no Docker** — Render native Python runtime, recommended) or
> `Dockerfile` (for hosts that want a container). See `docs/DEPLOY.md`.
>
> **✅ PRE-SHARE FIX — code done 2026-09-15, merged to `master` 2026-09-16 (PR #2).** `/analyze`
> and `/ask` are now gated by `services/access.py`: an optional shared access token
> (`TRADE101_ACCESS_TOKEN`, header `X-Access-Token`) + a shared daily cap (`TRADE101_DAILY_CAP`,
> default 50/day across both endpoints). Both are **no-ops until set** — local dev is unaffected.
> **Remaining user action before sharing a live URL:** set `TRADE101_ACCESS_TOKEN` (and
> optionally tune the cap) as env vars on the host, then share the link as
> `https://yourapp/?token=<value>` once — the frontend saves it to `localStorage` and strips it
> from the visible URL. See `docs/DEPLOY.md`.
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
**Trade Craft** (renamed from "Trade101" 2026-09-15) — a personal stock-research **and learning** web app for Pranav (student, beginning trader). Type a **company name** (any market) → live chart, indicators explained *in context*, chart patterns, a **sourced AI momentum read**, an Ask-Claude chat, news + "what it means" inference, ecosystem/peers, a Comparison tab, a Watchlist, a search History, and a Practice Lab (simulated trade journal).

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

**Phase 3 — feature-complete, merged to `master` 2026-09-16 (PR #2)** (started 2026-09-15, done
2026-09-15 — a same-day arc; the merge itself lagged a day, see `docs/AUDIT.md` §7 finding C3 for
that incident). App views are now `home | compare | watchlist | history | practice`. What
shipped, in order:

1. **Watchlist** — `components/Watchlist.jsx` + `lib/watchlist.js` (localStorage; ☆ Watch
   toggle on the research header; live quotes via `/research`, framed as tracking, not trade
   prompts).
2. **Single-service deploy** ready (two free paths — `render.yaml` no-Docker or `Dockerfile`,
   see `docs/DEPLOY.md`) and the **GitHub repo made private**. Desktop packaging was considered
   and **parked** in favor of the web deploy (`docs/HANDOVER.md` §13 — the actual goal was a
   shareable link, which packaging doesn't produce).
3. **More markets**: fixed a currency-display gap (non-US currencies showed no symbol at all —
   see Known bugs) and broadened non-US news with a keyless Google News RSS fallback. Non-US
   peers (Ecosystem tab) remain gapped, deferred to the paid Firecrawl/Exa tier post-deploy.
4. **Pre-share fix** (see header callout) — `services/access.py` gates `/analyze` + `/ask`
   behind an optional access token and a shared daily cap. This was the user's explicit
   "remind me at the end of Phase 3" item, raised and actioned mid-phase rather than held back.
5. **UI/UX + accessibility fixes** (see Known bugs for full detail): fixed the
   invisible-metric-value contrast bug, made browser Back/Forward walk through tab switches
   (not just searches), restyled the Feed/What-it-means toggle (was completely unstyled),
   retinted the whole theme to near-black navy, and fixed 10 nav-tab links that were
   keyboard/screen-reader-unreachable (`<a>` with no `href` → real `<button>`s) plus one input
   that removed its focus outline with no replacement.
6. **Practice Lab** — `components/PracticeLab.jsx` + `lib/practiceLab.js`: a simulated
   portfolio (starts at $100,000 practice cash, USD-only for v1 — no fake FX conversion) that
   doubles as a trade journal. Log a hypothetical buy at the real live price (never
   user-typed) with a reasoning note; sell later to realize P&L against average cost and close
   the journal entry. New top-level tab across every view. Zero Claude spend. Verified live
   end-to-end: bought 10 AAPL @ $330.02 (cash −$3300.20 exactly), sold 5 (cash +$1650.10
   exactly, $0 realized P&L since price was unchanged, journal entry recorded correctly).

**Everything on the Phase 3 list has shipped** except non-US peers (deferred to the paid tier)
and desktop packaging (deliberately parked, not planned). What remains is the user's own
deploy step (host signup) and setting the access token before ever sharing the link — not code.

## Architecture
Hybrid: deterministic **services** for exact data + Claude **agents** for judgment, behind a FastAPI API; **React/Vite** frontend.
```
backend/  app.py (FastAPI) · services/{marketdata,indicators,patterns,news,company,search,evidence,safe,cache,access}.py
          agents/{orchestrator,analysis,chat,llm}.py · tests/
frontend/ src/{App,api}.jsx · components/{Welcome,Research,PriceChart,Metrics,AiRead,NewsPanel,Ecosystem,AskClaude,Compare,ComparisonChart,Watchlist,History,PracticeLab,Logo}.jsx · lib/{history,watchlist,practiceLab,currency,access}.js
```
- `services/evidence.py` — deterministic relevance filter; drops unrelated news before the AI
  sees it (Phase 1.5 guardrail). `services/safe.py` — `redact_secrets` for anything client-bound.
- `/analyze` now fetches the company profile too (for relevance filtering) and returns
  `news.sourcing` (kept/dropped counts) + per-evidence Fact/Interpretation/Unknown labels.
- News is Finnhub → **Google News RSS** (keyless, global, searches by company name) →
  **Yahoo Finance fallback** so non-US listings get real, diverse coverage, not just Yahoo's.
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
- **Practice Lab**: `lib/practiceLab.js` (localStorage) + `components/PracticeLab.jsx`. A
  simulated $100,000 USD-only portfolio + trade journal — deliberately separate from the main
  learning flow. Buy/sell always use the real live `/research` price (never a typed number);
  sell realizes P&L against the position's average cost and appends a journal entry with the
  user's own reasoning. Zero Claude spend, same deterministic pattern as Watchlist/Compare.
  Scope limit: USD only for v1 — a single cash pool can't honestly mix currencies without real
  FX data, which this app doesn't have and won't fake.
- **Currency display**: `frontend/src/lib/currency.js::currencySymbol()` is the single source of
  truth for the $/¥/₹/₩/€/£/etc. symbol shown next to a price — used by Research/Watchlist/
  Compare so a market never renders a bare, unlabeled number.
- **Router**: `App.jsx`'s `routeHash`/`parseRoute`/`goToView` push one browser-history entry per
  navigation (search OR tab switch), so Back/Forward walks through both like a normal site.
  Ticker searches keep `#TICKER`; tab views get `#/compare`, `#/watchlist`, `#/history`.
- **Pre-share access guard**: `services/access.py::guard_paid_endpoint` is a FastAPI dependency
  on `/analyze` and `/ask` only (every deterministic endpoint stays open/free). Checks an
  optional `TRADE101_ACCESS_TOKEN` against the `X-Access-Token` header (401 if set and wrong/
  missing; a no-op if unset) and a process-wide daily counter (`TRADE101_DAILY_CAP`, default 50,
  resets at UTC midnight; 429 once exhausted). Frontend half: `lib/access.js` captures a
  `?token=` URL param into `localStorage` once and sends it as that header on `/analyze`/`/ask`
  only. Deliberately a single-process in-memory counter, not distributed — right-sized for one
  free-tier instance, not a multi-tenant product.
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
user's own host-account signup. The pre-share code fix is done (see header callout), but **still
treat any deploy URL as personal-use only until the user has actually set `TRADE101_ACCESS_TOKEN`
on the host** — the gate is a no-op until that env var is set.

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub). `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth. Named per-agent keys per `.env.example`.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (`finnhub` default → Google News →
  Yahoo fallback chain; standalone `yahoo`/`google` also selectable; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base `http://127.0.0.1:8000`.
- **Each `/analyze` call spends the user's Claude key — be sparing when testing in the browser.**
- `TRADE101_ACCESS_TOKEN` / `TRADE101_DAILY_CAP` (both optional, unset = no-op): the pre-share
  guard on `/analyze` + `/ask`. See `services/access.py` and `docs/DEPLOY.md`.
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

### Fixed 2026-09-15 (UI/UX + news + accessibility, user-reported)
- ~~RSI/MACD/SMA/etc. metric values were nearly invisible~~ — `.metric`/`.metric .v` in
  `styles.css` never set an explicit text color, so a `<button>` (native form control) fell
  back to the browser's own default text color instead of inheriting the page's cream `--ink`.
  Fixed with an explicit color plus `color-scheme: dark` on `:root` (the root-cause guard so
  this class of bug can't recur on a future unstyled button/input).
- ~~Browser Back/Forward only walked through ticker searches, not tab switches~~ — `App.jsx`'s
  router only ever pushed a history entry for `doResearch()`; clicking Comparison/Watchlist/
  History called `setView()` directly with no history entry at all, so the physical Back button
  had nothing meaningful to return to from those tabs. Rewrote the router (`routeHash`/
  `parseRoute`/`goToView`) so every navigation — search or tab switch — pushes one entry;
  `#TICKER` links are unchanged, tab views get their own `#/compare`, `#/watchlist`, `#/history`.
  Verified live: Back from Watchlist correctly returns to the previous Research ticker, Forward
  returns to Watchlist.
- ~~News was Yahoo Finance + SEC EDGAR only, i.e. effectively US-centric~~ — added a keyless
  Google News RSS fallback (`services/news.py::_google_news`, searches by company name for
  much better relevance than the bare ticker) ahead of the Yahoo fallback. Verified live on
  7974.T (Nintendo): feed now includes MarketWatch, BeInCrypto, Britannica, nintendo.com,
  Anime News Network — real, diverse, dated coverage, not just Yahoo's own feed.
- ~~The Feed / What-it-means toggle looked like raw unstyled HTML buttons~~ — `.newstabs`/
  `.ntab` had **no CSS rules at all**. Added a proper segmented-pill toggle matching the
  existing chart-toggle visual language.
- **Theme retinted near-black with a navy tint** (was a lighter deep navy) per explicit request
  — `--bg`/`--bg2`/`--surface`/`--surface2`/`--hair` all darkened in `styles.css :root`; every
  component consumes these as CSS vars, so the whole app retints from one place.
- ~~10 tab-navigation links were keyboard/screen-reader-unreachable~~ — Research/Compare/
  Watchlist/History's "Comparison · Watchlist · History" links were `<a>` tags with no `href`,
  which the DOM doesn't treat as focusable or clickable-by-Enter at all. Converted all 10 to
  real `<button>`s (native keyboard support, no extra ARIA needed) with `aria-current="page"`
  on the active tab. Also added a global `:focus-visible` ring and fixed one input
  (`.cmp-pick`) that removed its focus outline with no replacement.

### Fixed 2026-09-15 (pre-share endpoint guard — see BACKLOG.md → Pre-share checklist)
- ~~`/analyze` and `/ask` had no auth or rate-limit~~ — new `services/access.py`, wired as a
  FastAPI dependency on both routes: an optional shared access token
  (`TRADE101_ACCESS_TOKEN` → `X-Access-Token` header, 401 if wrong/missing when set) plus a
  process-wide daily cap (`TRADE101_DAILY_CAP`, default 50, 429 once exhausted). Both are
  no-ops when unset, so local dev/testing is unaffected. Frontend `lib/access.js` captures a
  one-time `?token=` URL param into `localStorage`. 5 new tests in `tests/test_access.py`
  (34 passing overall, was 29). **Remaining user action:** actually set `TRADE101_ACCESS_TOKEN`
  as a host env var once deployed — the code is ready but inert until that value exists.

### Fixed 2026-09-15 (Phase 3 — more markets support)
- ~~Non-US currencies showed as a bare number, no symbol~~ — `Research.jsx`, `Watchlist.jsx`,
  and `Compare.jsx` each had their own tiny `sym()` helper that only recognized USD/INR;
  every other target-market currency (JPY, KRW, HKD, SGD, CNY, EUR, GBP, …) silently showed
  no unit at all. Replaced all three with a shared `frontend/src/lib/currency.js::currencySymbol()`
  covering the target markets + common others, falling back to the currency code itself
  (never blank) for anything not in the map. Verified live on 7974.T (Nintendo, JPY) in both
  Research and Comparison — now shows ¥8118 instead of a bare 8118.

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
- Layout is a self-balancing JS masonry (measures block heights). Browser back/forward + `#TICKER` shareable links work — and now `#/compare` `#/watchlist` `#/history` too (2026-09-15).
- Any element that doesn't set an explicit `color` can fall back to browser UA defaults instead
  of inheriting the page's `--ink` — this bit the `.metric` buttons once already (2026-09-15).
  `color-scheme: dark` is set on `:root` as a guard, but still set colors explicitly on new
  `<button>`/`<input>` styling rather than relying on inheritance alone.
