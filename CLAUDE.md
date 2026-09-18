# CLAUDE.md — Trade Craft

> **Brand: Trade Craft** (renamed from "Trade101" on 2026-09-15). The GitHub repo, local
> folder, and internal package names stay `trade101` — only the user-facing brand + logo changed.
> Theme is deep navy with cream/near-white text (`frontend/src/styles.css` `:root`).
> **Repo is PRIVATE** (set 2026-09-15). **🔗 LIVE (2026-09-17): https://trade-craft-qdsw.onrender.com**
> — Render free tier, single-service (FastAPI serves the built React app, `app.py` mounts
> `frontend/dist`), deployed via `render.yaml` (no Docker). Free-tier idle-sleep applies (~15 min
> idle → sleeps, ~30-60s cold-start on next hit). See `docs/DEPLOY.md`.
>
> **✅ BYOK — bring-your-own-key (2026-09-17), replaces the old shared-token/daily-cap gate
> entirely.** Every visitor pastes their OWN Anthropic API key into a first-run gate
> (`components/ApiKeyGate.jsx`), saved permanently in THEIR browser and sent as `X-Anthropic-Key`
> on `/analyze`/`/ask` — never the app owner's key, never logged/stored server-side. An open,
> shared link now carries **zero cost risk** to the owner; nothing needs to be set before
> sharing. `TRADE101_ACCESS_TOKEN`/`TRADE101_DAILY_CAP`/`services/access.py` are gone —
> `TRADE101_ANALYSIS_KEY` still works as a local-dev-only fallback (don't set it on a shared
> host). See `docs/DEPLOY.md`.
>
> **📋 CRITICAL AUDIT (2026-09-16): [`docs/AUDIT.md`](docs/AUDIT.md)** — adversarial end-to-end review
> (functional / logical / executional / UI-UX), 30+ ranked findings with reproductions and a
> wave-by-wave fix order. Read it before planning new work; its Wave 0/1 items are mirrored in
> `BACKLOG.md` and in "Known bugs" below.

Auto-loaded each session in this folder. **This file is the project's living memory** — treat
it as more current than your own assumptions, and keep it that way (see Memory protocol
below). Full history: `docs/HANDOVER.md`. Phase-by-phase journey + mistakes:
`docs/DEVELOPMENT-LOG.md`. Backlog: `BACKLOG.md`. Recommendations under review:
`docs/trade101-phase-2-recommendations.md`. Spec/plan: `docs/superpowers/`. User-facing reading
guide (shareable, not dev docs): `docs/guide-reading-a-stock.html` / `docs/reading-a-stock.pdf`.

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
   peers (Ecosystem tab) were gapped here — fixed later, 2026-09-17, via a free Yahoo fallback
   (see Wave 4 in "Known bugs" below).
4. **Pre-share fix, ORIGINAL version** (superseded 2026-09-17 by BYOK — see header callout) —
   at the time, `services/access.py` gated `/analyze` + `/ask` behind an optional shared access
   token and a shared daily cap. This was the user's explicit "remind me at the end of Phase 3"
   item, raised and actioned mid-phase rather than held back.
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
- **`GET /news/{ticker}`** (`orchestrator.news_bundle`) — the SAME relevance-filtered feed
  `/analyze` uses, but with NO Claude call and no access-token/daily-cap gate. `NewsPanel.jsx`
  loads Feed from here independently of the AI state; "What it means" still needs `/analyze`.
  Both share one TTL-cached `gather()` bundle, so hitting `/news` first never forces a second
  fetch when `/analyze` runs afterward for the same ticker.
- `services/search.py::resolve()` **scores and ranks** candidates by listing quality (home/major
  exchange first; OTC/CDR/preferred/secondary-dealer lines demoted, tagged `listingBadge` and
  shown as a badge+tooltip in the picker) — Yahoo's own order regularly put a thin OTC ADR above
  the real company. `App.jsx`'s `looksLikeTicker()` also gates the picker-skip: only a genuinely
  ticker-shaped, unambiguous query auto-picks, so a company name that equals its own ticker (e.g.
  "Sony") no longer silently skips disambiguation.
- `company.py` **computes beta** vs the regional index (suffix→index map: .T→Nikkei, .KS→KOSPI,
  .NS→Nifty, …) when the provider has none — deterministic; response carries `betaSource`
  ("provider"|"computed") + `betaIndex`. `marketCapCurrency` is also on this response —
  `Ecosystem.jsx`/`Compare.jsx` format market cap in the listing's own currency (it's never USD
  by default; formatting it as `$` regardless was producing false comparisons, e.g. a JPY cap
  reading larger than Apple's real USD cap). `betaIndex` is populated for a provider beta too,
  not just a computed one, so the UI always names the actual benchmark ("vs the S&P 500") instead
  of vaguely "the market". `peers` is deduped case-insensitively (Finnhub's own list can repeat
  a symbol). `peerNames` (ticker → full company name, resolved in parallel via yfinance) backs
  the ecosystem graph's hover tooltip only — `peers` itself stays a plain ticker list for
  `services/evidence.py`. **Non-US peers (2026-09-17)**: Finnhub's peers endpoint is US-listed
  only, which left non-US stocks with no ecosystem graph at all (user-reported, RELIANCE.NS) —
  `_peers()` now falls back to Yahoo Finance's keyless public "people also watch" endpoint
  (`_yahoo_related()`) when Finnhub has nothing. This is a DIFFERENT signal (co-viewed by other
  investors, not same-industry competitors) — tracked via `peersSource` ("finnhub"|"yahoo"|None)
  and the frontend labels the Yahoo case differently rather than presenting it as if it were the
  same kind of peer data.
- `company.py::_fundamentals()` (2026-09-17, docs/AUDIT.md M5 — the biggest content gap) — P/E
  (trailing+forward), EPS, revenue growth, profit margin, dividend yield, debt/equity, next
  earnings date, all straight from yfinance's `.info`/`.calendar` (nothing computed/estimated).
  `dividendYield` and `debtToEquity` are already percentage figures in yfinance's own convention
  (unlike `revenueGrowth`/`profitMargins`, which are fractions) — verified empirically. Wired
  into `/ecosystem/{ticker}`'s `fundamentals` field; degrades to a `coverage.fundamentals` note
  (never fabricated) when a listing genuinely has nothing. Rendered in `Ecosystem.jsx`.
- `patterns.py` scans the WHOLE series (every consecutive pair/triple of swings, not just the
  most recent few) for reversal **and** trendline shapes, built from High/Low (not Close — matches
  the actual wicks). Its similar-level/min-dip/flat tolerances are derived PER SERIES from that
  series' own median bar-to-bar volatility (`_scale()`) rather than a fixed percentage — a fixed
  threshold tuned for daily/yearly swings never fired on intraday timeframes. Results are sorted
  most-recent-first. Overlapping matches are deduplicated; confidence is a real "low"/"moderate"
  label from level-fit tightness, not a fixed string. Only shapes actually present are returned,
  drawn via a `lines`/`points` field in `PriceChart.jsx`. **Reference sources for the pattern
  definitions/explanations** (`EXPL` dict) — supplied by the user 2026-09-17 to verify a
  classification against (e.g. wedge vs. channel), and worth checking against for any future
  pattern-definition question: [Fidelity — Identifying Chart Patterns (PDF)](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/learning-center/Idenitfying-Chart-Patterns.pdf),
  [strike.money — Chart Patterns](https://www.strike.money/technical-analysis/chart-patterns).
  No PDFs or reference docs live IN this repo — these are external, not local files.
- `PriceChart.jsx` — on **`lightweight-charts` v5** (upgraded from v4.2 for multi-pane support,
  2026-09-17). Six independent effects: chart lifecycle / price series / SMA+Bollinger overlays
  (price pane) / RSI+MACD (each their own pane, torn down and rebuilt fresh on any toggle change
  rather than patched in place, since panes shift index when one is removed) / pattern overlay /
  crosshair-legend subscription — no single prop change tears the whole chart down, and the view
  only re-fits on a genuinely new dataset (new ticker/timeframe), so zoom/pan survive the 7-min
  auto-refresh. `services/indicators.py::compute_indicator_series()` supplies the full
  time-aligned arrays this needs (the original `compute_indicators()` only ever returns the
  latest snapshot — fine for the Metrics panel, useless for drawing a line) via `/research`'s
  `indicatorSeries` field. `app.py::_fetch_with_lookback` (+ `_LOOKBACK_FETCH` map) fetches MORE
  history than a short display window needs (e.g. "60d" of 15-min bars for a "5D" display) so
  SMA200's 200-bar lookback is satisfied across the WHOLE visible window, not just a trailing
  sliver — then trims back to the original display width before returning. Unrecognized
  period/interval combos pass through unchanged.
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
  Client `timeout=` is also set here (`ANALYSIS_TIMEOUT_S=90`, `CHAT_TIMEOUT_S=45`) — a hung
  request degrades gracefully after that instead of occupying a worker indefinitely.
- `orchestrator.analyze()` caches its finished result per ticker (`ANALYZE_CACHE_TTL=1200s`) —
  separate from `gather()`'s own 5-min cache, so a page reload/new tab/new visitor within 20 min
  reuses the prior read instead of spending the Claude key again. A raised exception is never
  cached (only a value `fn()` actually returns is stored), so a missing key or transient AI
  error is retried on the next request, not stuck for the full TTL.
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
  Each entry can carry a one-line study note (`setNote()`, 2026-09-17, docs/AUDIT.md §9) —
  editable inline, saved on blur, preserved across a plain re-`addWatch` but cleared if the entry
  is actually removed then re-added. A note, never a position/target/signal.
- **Glossary** (2026-09-17, docs/AUDIT.md §9): `lib/glossary.js` (static, stock-independent
  reference terms — indicators, chart patterns, fundamentals figures) + `components/
  Glossary.jsx`, a normal nav tab with a search box filtering term+definition text. Distinct
  from `lessons.js`, which teaches a metric IN CONTEXT of the current stock's own numbers.
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
- **BYOK (bring-your-own-key), 2026-09-17** — replaced the shared-token/daily-cap gate entirely.
  `components/ApiKeyGate.jsx` is a first-run, full-app gate: a visitor pastes their own
  Anthropic API key (the key itself IS the credential — no separate password), optionally a
  display name, both saved permanently in `lib/apiKey.js` (localStorage, THEIR browser only).
  `api.js::authHeaders()` sends the key as `X-Anthropic-Key` on `/analyze`/`/ask` only — every
  deterministic endpoint stays open/free with no key at all. Backend: `app.py` reads the header
  and threads it as `client_key` through `orchestrator.analyze()/ask()` →
  `agents/analysis.py::run()` / `agents/chat.py::answer()` → `agents/llm.py::call()/call_chat()`,
  which uses it as the actual Anthropic API key for that one call (never stored, never logged).
  `TRADE101_ANALYSIS_KEY` (env var) is a LOCAL-DEV-ONLY fallback when no visitor key is supplied —
  must NOT be set on a shared/deployed host, or a keyless visitor silently spends the owner's key.
  A cache HIT (`orchestrator.analyze()`'s existing `ANALYZE_CACHE_TTL`) never needs a key at all —
  one visitor's fresh analysis can be served free to the next visitor asking about the same
  ticker within the TTL. `app.py::_ai_error_reason()` gives a friendly message for the now-most-
  likely failure mode (a visitor's own key being invalid/expired/rate-limited) instead of
  surfacing Anthropic's raw SDK error text.
- **Single-service deploy**: `app.py` mounts `frontend/dist` (built React) via `StaticFiles`
  *after* all API routes, so one process/origin serves both — `api.js` uses same-origin in prod
  (`import.meta.env.DEV` switch), `:8000` directly in dev. Two build paths, no app-code
  difference between them: `render.yaml` (Render Blueprint, native Python runtime, **no
  Docker**) or `Dockerfile` + `.dockerignore` (multi-stage, for hosts that want a container).
  Full steps: `docs/DEPLOY.md`.
Endpoints: `/health`, `/search?q=` (ranked, badged candidates), `/research/{ticker}?period&interval` (now also returns `indicatorSeries` — full SMA/Bollinger/RSI/MACD arrays for charting), `/news/{ticker}` (free, deterministic feed — no key/gate needed), `/analyze/{ticker}` (AI, degrades w/o key), `POST /ask/{ticker}` (Ask-Claude chat), `/patterns/{ticker}` (High/Low-based, full-series scan), `/ecosystem/{ticker}`.

## Run (two terminals)
```
# backend (from backend/) — port 8000/8001 are currently stuck-orphaned on this machine (see
# Gotchas); running on 8002 until a machine restart reclaims one of them. --reload has also
# proven unreliable here (WatchFiles missed several edits) — restart manually after backend
# changes rather than trusting it to pick them up.
.venv/Scripts/python.exe -m uvicorn app:app --port 8002
# frontend (from frontend/) — VITE_API_BASE in frontend/.env.local must match the port above;
# Vite only reads .env.local at startup, so restart this after changing that file.
npm run dev            # PowerShell blocks npm → use npm.cmd run dev, or Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Open http://127.0.0.1:5173. Backend tests: `cd backend && .venv/Scripts/python.exe -m pytest -q`.
Frontend tests (added 2026-09-17, Wave 4 M10): `cd frontend && npm.cmd run test` (Vitest v2 —
pinned below v3 to stay compatible with the project's Vite 5; Vitest 5 requires Vite 6+).

**App-link rule (hard rule):** whenever you run/build the app for the user to check, make sure
both servers are up and **return the local link `http://127.0.0.1:5173`** in the reply — Pranav
checks it on this machine and reports back what works/breaks so we fix issues one by one.
**Live and deployed (2026-09-17): https://trade-craft-qdsw.onrender.com** — Render free tier
(`render.yaml`, no Docker), verified via `/health` and a live page load. Free-tier idle-sleep
applies (sleeps after ~15 min with no traffic, ~30-60s cold-start on the next hit — not a bug).
Safe to share as-is — BYOK (2026-09-17) means every visitor's AI usage is billed to their own
Anthropic key, not the owner's, so there's no pre-share gate to configure.

## Config / conventions
- `.env` in project root (git-ignored). `TRADE101_ANALYSIS_KEY` (Claude — **local-dev-only
  fallback under BYOK, see below**), `TRADE101_NEWS_KEY` (free Finnhub, still shared/required).
  `TRADE101_MODEL` default **claude-sonnet-5** (cost); use `claude-opus-5` for max depth.
- Claude API via the Anthropic SDK; adaptive thinking + `output_config.effort` for non-Haiku models. Models: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` (no date suffixes).
- News provider is pluggable via `TRADE101_NEWS_PROVIDER` (`finnhub` default → Google News →
  Yahoo fallback chain; standalone `yahoo`/`google` also selectable; add `firecrawl` later).
- Servers pinned to `127.0.0.1` (IPv6 `::1` caused issues); API base overridable via
  `VITE_API_BASE` in a **local-only, gitignored** `frontend/.env.local` — **check this file for
  the currently live backend port** (ports 8000 and 8001 have both gotten stuck with an orphaned
  listening socket on this machine — see Gotchas; don't assume the backend is down before
  checking here).
- **BYOK (2026-09-17)**: `/analyze` and `/ask` spend the VISITOR's own Anthropic key (sent as
  `X-Anthropic-Key`), never the app owner's — see the header callout and the architecture bullet
  above for the full mechanism. `TRADE101_ACCESS_TOKEN`/`TRADE101_DAILY_CAP`/`services/access.py`
  no longer exist. `/news` remains free/unlimited (no Claude call at all) regardless.
- `TRADE101_SEC_CONTACT` (optional): email sent as the SEC EDGAR User-Agent (their fair-access
  policy requires a real contact). Falls back to a generic placeholder if unset — filings lookups
  still work, it's just not a real contact then. Never hardcode a personal email in committed
  source for this; put it in the gitignored `.env` instead.
- Windows 11, Git Bash available; the `claude` CLI is at `C:\Users\prana\.local\bin\claude.exe`.
- **Backend currently runs on port 8002** (2026-09-17 — port 8001 also got stuck with an orphaned
  LISTENING socket, same class of issue as the port-8000 incident; see Gotchas). `frontend/
  .env.local`'s `VITE_API_BASE` points at it. If you restart the backend, prefer 8002 unless/until
  a machine restart reclaims 8000/8001 — check `frontend/.env.local` for whichever port is live
  before assuming the backend is down.

## Known bugs
**Full ranked list with evidence: [`docs/AUDIT.md`](docs/AUDIT.md) (critical audit, 2026-09-16).**
Mirrored as checkboxes in `BACKLOG.md` → "Audit — Wave 0/1/2/3/4". **All waves (0 through 4) are
done, including the deploy step** — live at https://trade-craft-qdsw.onrender.com
(2026-09-17). See `docs/AUDIT.md` §10.

### Fixed 2026-09-18 — /analyze and /ecosystem were racing each other for the same flaky resource
**User pushed back hard, correctly, after the previous entry's retry fix**: "if the ecosystem is
displayed correctly, then [AI Momentum Read/What it means] are not working" — an inverse
correlation between the two features on the SAME page load for the SAME ticker (Tencent,
`0700.HK`, again). Reproduced live in the browser with the real key (not curl): on one load,
AI Momentum Read succeeded but the ecosystem peer graph came back as raw ticker codes with
"Fundamentals aren't available"; the pattern flips on other loads. **Root cause, found by reading
the actual call graph**: `agents/orchestrator.py::_gather()` (which `/analyze` runs) calls
`company.get_profile(ticker)` AGAIN, independently, for news-relevance filtering — completely
separate from the call `/ecosystem` makes. The frontend fires both requests within milliseconds
of each other; both missed the 5-min cache before either had stored a result, so BOTH fired their
own full ~11-concurrent-call yfinance blitz (info, calendar, up to 8 peer lookups, beta history)
AT THE SAME TIME for the same ticker — doubling the load on Yahoo's already-flaky crumb-negotiated
`.info` endpoint right when it's most likely to fail, and making the two features effectively
race each other for the same fragile resource. **This is the piece the "add a retry" fix in the
previous entry didn't address** — retrying doesn't help when the contention is self-inflicted by
the app firing the same expensive call twice at once.
- Fixed: `services/cache.py::get_or_set()` gained a per-key `threading.Lock` (double-checked
  locking) — when several callers miss the cache for the same key concurrently, only the FIRST
  one actually runs `fn()`; the rest block briefly and reuse its result instead of each starting
  their own redundant fetch. New `company.get_profile_cached()` wraps `get_profile()` through
  this cache (key `profile:{TICKER}`, 5-min TTL) and is now what BOTH `app.py`'s `/ecosystem`
  route and `orchestrator._gather()` call, instead of each calling the raw `get_profile()`
  independently.
- 3 new tests (`tests/test_cache.py`) — including one that fires 5 concurrent callers at the same
  key and asserts the slow underlying function only actually runs once. 96 backend tests total.
- Verified locally by firing `/ecosystem/0700.HK` and `/analyze/0700.HK` (with a real key)
  CONCURRENTLY, exactly like the frontend does: both returned real, complete data — ecosystem in
  ~7s (reusing the shared cached profile), analyze in ~34s (normal, dominated by the actual Claude
  call, not the data-gathering step). No more empty/failed side on either call.

**Same-day follow-up: the lock fix above shipped a NEW bug — a failed fetch got cached as if it
were real, for the full 5 minutes.** User insisted (correctly) on checking the LIVE site, not
curl-in-isolation: three separate `/ecosystem/0700.HK` calls, 3s apart, all came back with the
byte-identical empty profile — not three independent Yahoo flakes, one cached failure being
replayed to every caller. Root cause: `company.get_profile()` never raises on a failed `.info`
call — it degrades internally to a dict of `None`s (by design, so a genuinely thin listing
degrades gracefully) — so `get_or_set()` was caching that degraded-but-successfully-returned dict
exactly like a real result. Fixed: `cache.get_or_set()` gained an optional `should_cache`
predicate; `get_profile_cached()` passes one (`_looks_like_a_failed_fetch()` — `sector`/
`industry`/`summary` all `None` together, since those three come ONLY from the main ticker's
`.info` call with no fallback) that skips caching a result that looks like a failed attempt, so
the next request gets a genuinely fresh try instead of the poisoned one. 5 new tests
(`tests/test_cache.py` + `tests/test_company.py`). 101 backend tests total. Verified locally by
reproducing the exact live failure pattern (a fake `get_profile` that fails once then succeeds):
confirmed the failure is no longer cached and the second call gets a fresh, successful attempt.
**Worth naming as a pattern for future work**: fixing one concurrency bug (the race) surfaced a
second, adjacent one (poisoning the fix's own cache with a failure) — caching a call that
degrades-instead-of-raising needs its own explicit "was this actually good?" check, not just a
plain TTL.

### Fixed 2026-09-17 — ecosystem graph showed bare tickers instead of names for non-US listings
**User-reported, live on Render**: searching Samsung on the Korean market (`005930.KS`) showed the
peer graph as a ring of raw numeric codes (`000660…`, `005380…`, `035420…`) with the searched
stock itself labeled `005930…` at the center — the resolved company name (`peerNames`, already
fetched via yfinance for exactly this purpose) sat unused in a hover-only `<title>` tooltip. Fine
for a US ticker (`AAPL`/`MSFT` read fine on their own) but useless for most non-US listings, whose
tickers are opaque numeric codes. `EcoGraph` (`Ecosystem.jsx`) now prefers the resolved name for
BOTH the peer nodes and the center node (a new `centerName` prop, threaded from `Research.jsx`'s
`quote.name`), falling back to the ticker only when no name was resolved; the tooltip flips to
show `TICKER — Full Name` so the ticker is still one hover away. Verified live on 005930.KS: the
graph now reads "Samsung" (center), "SK hynix", "SAMSUNG", "NAVER", etc. instead of numeric codes.
57 frontend tests pass, build clean.

**Round 2, same day — the frontend fix wasn't enough on its own.** User then tested Tencent
(`0700.HK`) live and still saw raw peer codes, with only the CENTER node showing "TENCENT"
correctly. Traced to the actual data source: `/ecosystem/0700.HK` was returning `peerNames: {}`
AND `sector`/`industry`/`marketCap`/`summary` all `null` — i.e. yfinance's `.info` call for the
ticker itself was coming back empty on Render, not just for its peers. Verified directly against
yfinance from a different machine: `.info` for `0700.HK`/`9988.HK`/`1810.HK` all succeeded
instantly with full data (173 keys, real `shortName`/`longName`). **Root cause: Yahoo's
`.info`/`.calendar` endpoint needs a crumb/cookie handshake that's genuinely flaky from Render's
shared IP — `.history()` (which powers the chart and quote) doesn't need this handshake and has
never shown this problem, which is why price data always worked while `.info`-dependent fields
(sector, fundamentals, peer names) kept failing intermittently.** Fixed: new
`services/net.py::with_retry()` (one retry, 0.6s backoff, on top of the existing `with_timeout`)
applied to every `.info`/`.calendar` call in `company.py` and `marketdata.py`'s `_quote()`. 5 new
tests (`tests/test_net.py`, including one simulating exactly this bug: first attempt raises,
second succeeds). 93 backend tests total.

### Fixed 2026-09-17 — no timeout anywhere on yfinance calls, hung the UI forever on a slow/thin ticker
**User-reported on the LIVE deployed link** (first bug caught post-deploy): searching "SK hynix"
(a brand-new NASDAQ listing, `SKHY`, alongside the mature `000660.KS` Korean listing) left the
10D chart tab stuck on "Loading 10D…" indefinitely, and the Ecosystem panel showed a confusing
peer graph. Root cause: yfinance's underlying Yahoo requests default to a 30s timeout **per
request**, but a single `/research`/`/ecosystem` call chains several of them sequentially
(`.info`, `.calendar`, beta history ×2, up to 8 peer-name lookups) — a slow or rate-limited
response (more likely from Render's shared datacenter IP than a home IP in local dev, and more
likely for a genuinely thin/brand-new listing Yahoo hasn't fully backfilled yet) could stack into
60s, 90s, or more, and **nothing anywhere — backend or frontend — ever gave up**. Fixed on both
sides:
- **Backend**: new `services/net.py::with_timeout()` — a hard wall-clock deadline via
  `ThreadPoolExecutor.result(timeout=)` around every risky yfinance call (`marketdata.get`'s
  `t.history`/`t.fast_info`/`t.info`; `company.py`'s `t.info`/`.calendar`/beta histories/peer
  lookups). A timeout on a REQUIRED call (`marketdata.get`, used by `/research`/`/patterns`)
  now surfaces as a proper 504 with an honest "Yahoo is responding slowly, try again" message
  instead of a misleading 404 "no data"; a timeout on a degradable field (beta, fundamentals,
  peer names) falls back to `None`/empty, same as any other provider gap.
- **Frontend**: `api.js` had NO timeout on any `fetch()` call at all — new
  `fetchWithTimeout()` (AbortController, 25s for deterministic endpoints, 100s for
  `/analyze`/`/ask` since those legitimately run a real Claude call up to 90s server-side) is
  now used everywhere. Also fixed a latent bug found while doing this: `analyze()` had no
  try/catch around its fetch at all — a network failure or timeout would reject uncaught, and
  Research.jsx's `.then()` (no `.catch()`) meant `aiLoading` would stay stuck `true` forever,
  same "infinite loading" bug class as the chart hang, just for the AI panel.
- 87 backend tests pass throughout (no test changes needed — `TimeoutError` is a subclass of
  `Exception`, so it flows through every existing degrade-gracefully path unchanged). Frontend
  build verified clean.
- **A UI symptom fixed first, found doing a full button-by-button audit right after the timeout
  fix**: `Research.jsx`'s chart placeholder condition was `chartLoading || !chartOhlcv.length` —
  whenever a timeframe fetch came back with nothing, `chartOhlcv` stayed permanently empty even
  after `tfLoading` correctly cleared, so the UI kept showing "Loading 10D…" forever —
  indistinguishable from an actually-stuck fetch. Fixed with a new `tfError` state tracking a
  per-timeframe fetch failure, so a real failure now shows an honest message instead of lying
  that it's still working. **This masked, but did not cause,** the real bug below — initially
  misdiagnosed as "SKHY is a brand-new listing without 60 days of history," which the user
  correctly challenged (the 1Y chart plainly has months of real data) and which turned out to be
  wrong.
- **The actual root cause, found by testing the exact yfinance calls directly**: `_fetch_with_lookback`
  (used by the 10D/5D/1D tabs to fetch extra history so SMA200 has enough lookback — see the SMA
  lookback fix above) assumes a WIDER period request is always a safe superset of a narrower one.
  False for SKHY: `yfinance.Ticker('SKHY').history(period="60d", interval="30m")` returns **zero
  rows**, while `history(period="1mo", interval="30m")` — the narrower, ORIGINAL request the "10D"
  tab actually wants — returns **287 real bars**, verified directly. Something about this specific
  ticker's intraday data window rejects the wider ask outright rather than degrading to fewer
  bars. Fixed: `_fetch_with_lookback` now falls back to the original (period, interval) — no
  lookback extension — when the widened fetch comes back empty, recovering the real data instead
  of reporting no data at all. 1 new backend test
  (`test_lookback_fetch_falls_back_to_original_window_when_wider_fetch_is_empty`). Verified live
  in the browser: all 5 timeframes (1Y/1M/10D/5D/1D) now render real candles + SMA for SKHY,
  where 10D/5D/1D previously showed nothing.
- **Also found and fixed in the same audit — `/ecosystem` was slow even when nothing failed**:
  `company.get_profile()` ran its `info`/`calendar`/beta-history/peer-name yfinance calls
  sequentially — harmless when each is fast, but they stack: AAPL (a completely normal, healthy
  ticker) took ~19s to load in the Comparison tab, easily read as "stuck." Parallelized with
  `ThreadPoolExecutor` — `info` and `peers` fetch concurrently first, then `fundamentals`,
  `peer_names`, and a computed beta (when needed) all run concurrently in a second round.
  Measured: AAPL's `/ecosystem` call dropped from ~19s to ~3.6s. 87 backend tests still pass
  (pure internal refactor, same return shape).
- **Full button-by-button audit performed after these fixes** (user explicitly asked to verify
  every control works, not just the reported bug): SMA/Bollinger/RSI/MACD toggles, all 5
  timeframes, Candles/Line, Patterns + pattern-pill switching, Metrics tap-to-learn, Watch,
  ecosystem peer-node navigation, Watchlist (add/note/persist), Comparison (both slots, picker,
  chart), History, Practice Lab (buy — verified exact cash math), and Glossary search — all
  confirmed working live, screenshots taken at each step. No other bugs found in this pass.
- **Separately observed, not yet fixed**: `services/search.py::resolve()`'s OTC/secondary
  detection doesn't catch every thin/low-quality listing — `SKHY` (a brand-new NASDAQ line,
  `exchange: "NMS"`, not in `_OTC_EXCHANGES`) ranked ABOVE `000660.KS` with no badge, despite
  Yahoo's `.info` having nothing backfilled for it yet (fundamentals/beta/sector all null) while
  the mature Korean listing has full coverage. This is a real ranking-quality gap, not the bug
  that was actually hanging the UI — tracked here for a future pass rather than fixed now.

### Added 2026-09-17 — README rewrite + real screenshots
`README.md` was stale (missing Comparison/Watchlist/Practice Lab/Glossary/Ask TC-Buddy/
fundamentals entirely, still described the old shared-access-token model). Rewrote to match
current features/setup, plus six real screenshots captured from the running app (Research,
Comparison, Watchlist, Glossary, Ask TC-Buddy, Welcome) — `docs/screenshots/*.png`, committed
(repo is private, so this is safe). Captured via a temporary `puppeteer-core` script pointed at
the machine's existing Edge install (not a project dependency — installed with `--no-save` and
uninstalled again after use; nothing added to `package.json`). This is what surfaced the
Comparison-tab crash below.

### Fixed 2026-09-17 — Comparison tab crashed on load (lightweight-charts v4→v5 leftover)
Found while capturing README screenshots (see the BYOK entry below — same session): loading two
stocks in the Comparison tab crashed the whole app (`TypeError: chart.addLineSeries is not a
function`, caught by `ErrorBoundary`). Root cause: `ComparisonChart.jsx` was never updated when
the rest of the app moved to **lightweight-charts v5** for the H5 chart-overlay fix (2026-09-17,
same day) — it still called the removed v4 method `chart.addLineSeries(...)` instead of v5's
`chart.addSeries(LineSeries, ...)`. `PriceChart.jsx` was migrated correctly at the time;
`ComparisonChart.jsx` was missed because Comparison wasn't exercised again until now. Swept the
whole frontend for any other leftover v4 series-creation calls (`addAreaSeries`/
`addCandlestickSeries`/`addHistogramSeries`/`addBarSeries`) — none found, this was the only one.
Verified live: AAPL vs MSFT now renders both normalized lines correctly with no crash.

### Fixed 2026-09-17 — BYOK (bring-your-own-key), replaces the shared-token/daily-cap gate
User is building a genuinely OPEN, publicly-shareable link and didn't want to manage a shared
access token or worry about a stranger spending their Claude key at all — not even bounded by a
cap. Redesigned the pre-share model entirely rather than extending it:
- **The flow**: a first-run, full-app gate (`components/ApiKeyGate.jsx`) — a visitor pastes their
  own Anthropic API key (the key itself IS the credential; there's no separate password) and
  optionally a display name. Both saved PERMANENTLY in that visitor's own browser
  (`lib/apiKey.js`, localStorage) — never asked again on that device, never sent anywhere except
  as the `X-Anthropic-Key` header on `/analyze`/`/ask`, never logged or stored server-side.
- **Backend threading**: `app.py` reads the header and passes it as `client_key` through
  `orchestrator.analyze()/ask()` → `agents/analysis.py::run()` / `agents/chat.py::answer()` →
  `agents/llm.py::call()/call_chat()`, which uses it as the literal Anthropic API key for that
  one call. `TRADE101_ANALYSIS_KEY` (env var) is now a LOCAL-DEV-ONLY fallback — explicitly
  documented not to be set on a shared/deployed host, or a keyless visitor would silently spend
  the owner's key, defeating the entire point.
- **Removed, not deprecated**: `services/access.py` (the old token+cap gate) and `lib/access.js`
  (the frontend half) are deleted outright, along with `tests/test_access.py` — replaced by
  `tests/test_byok.py`. No dead code, no backward-compat shim.
- **Friendlier failures**: the most likely failure mode is now a VISITOR's own key being
  invalid/expired/rate-limited, not a server misconfiguration — `app.py::_ai_error_reason()`
  catches `anthropic.AuthenticationError`/`PermissionDeniedError`/`RateLimitError` specifically
  and gives a plain, actionable message instead of surfacing Anthropic's raw SDK error JSON.
  Verified live with a deliberately invalid key end to end: the key reached the real Anthropic
  API, was genuinely rejected (401), and degraded to a clean "that key was rejected" message.
- **Cache behavior unchanged, and it's a nice property here**: `orchestrator.analyze()`'s
  existing per-ticker TTL cache means a cache HIT never needs any key at all — one visitor's
  fresh analysis can be served free to the next visitor asking about the same ticker within the
  cache window. Only a cache MISS actually spends anyone's key.
- **Personalization, requested alongside this**: the Welcome greeting ("Which stock shall we
  study today?") now appends the visitor's own stored name when they gave one — the per-visitor
  equivalent of the old hardcoded "Pranav" greeting that H7 removed, but this time correct for
  every visitor instead of just the owner.
- 8 new backend tests (`tests/test_byok.py`). `docs/DEPLOY.md`, `render.yaml`, and this file all
  updated to match — see `docs/DEPLOY.md` for the full visitor-facing explanation.
- **Also discussed and decided in the same conversation**: Netlify was considered and rejected
  for hosting — it's a static-site + serverless-functions platform and can't run this app's
  persistent FastAPI process without real rearchitecting. Stick with Render (or Fly.io/Railway).

### Fixed 2026-09-17 — Wave 3 UI/UX redesign + two live feedback rounds — merged to `master` (commit `897514c`)
Direction discussed and narrowed with the user first (see `docs/AUDIT.md` §8/§10 item 12 for the
original sketch), built for live review, iterated across two feedback rounds on real tickers, then
approved and pushed. Full blow-by-blow narrative (including the reverted pattern-window mistake
and the port/caching investigation) is in `docs/HANDOVER.md` (2026-09-17 entry) — this is the
current-state summary. Also renamed the Ask-Claude chat widget to **Ask TC-Buddy** (UI label only)
with a candlestick SVG icon replacing the ✦ glyph, per explicit user request alongside this wave.

- **Layout**: replaced the height-balancing masonry with a **fixed two-zone layout**: spine is
  chart → **metrics** → AI momentum read (metrics moved above the AI read after user feedback —
  the indicators being learned belong right under the chart, not at the bottom); side column is
  always news → ecosystem → references. Panels no longer jump columns mid-load. User deliberately
  kept the two-column space-filling flow (rejected a rigid three-zone grid over dead-space
  concerns) — only the panel→column assignment became deterministic.
- **Icon system**: new `frontend/src/components/Icons.jsx` — SVG components replacing every emoji
  glyph (🔍📎⚖️★☆🕘✚✦▲▼■✕🧪) across Welcome/Research/Watchlist/History/PracticeLab/Metrics/
  AiRead/NewsPanel with the SAME symbols the user had already chosen — only the rendering
  technology changed (themeable via `currentColor`, OS-consistent, unlike emoji).
- **Evidence panel redesign**: the Fact/Interpretation/Unknown list in `AiRead.jsx` is now a
  `.evidence-list` of bordered cards, left-border colored per type, instead of a plain `<ul>`.
- **Pattern color**: violet (`--pattern`, `#B58EF2`) instead of amber, which clashed with the
  palette and doubled up with the watch-star color. Amber is now unambiguously "the watch star."
- **Mobile/accessibility**: `max-width:720px` media query for the Welcome rail (was a fixed 230px
  column eating most of a phone viewport); `.top`/`.tabs` wrap on narrow widths. Dead CSS removed
  (`.row`, `.cockpit`, `.midrow`, `.snap`, `.refs`, `.mkt`, `.phase`, `.eco-peers`).
- **Logo now navigates home** from every view (was a static, unclickable `<div>`) via a new
  `onHome` prop threaded from `App.jsx`'s existing `goHome`.
- **Chart autofit bug**: `fitContent()` was gated behind an `isFirstFit` check that made it only
  ever fire on the chart's very first-ever load — every subsequent timeframe switch left the view
  unfit. Fixed by removing the redundant gate (the "new dataset" key check alone was already the
  correct trigger).
- **Metrics panel showing the wrong timeframe's indicators**: `Metrics` always rendered the base
  1Y/1D `indicators` regardless of the selected chart tab, so a 10D/30m chart with genuinely no
  SMA200 (not enough 30-min bars for 200 of them) still showed the unrelated 1Y SMA200 number.
  `Research.jsx` now derives `indicators` from the SELECTED timeframe's own response.
- **Frontend cache never expired (docs/AUDIT.md M1)**: `api.js`'s `research`/`ecosystem`/
  `patterns`/`news` caches now expire after 5 min (matches the backend's own cache TTL); `analyze`
  (the paid call) deliberately stays session-long.
- **News coverage for thin/foreign listings**: the relevance filter was correctly dropping
  unrelated results, but a 30-day recency cutoff was ALSO silently discarding real coverage that
  was simply older (common for secondary/foreign listings) — `orchestrator._gather` now
  supplements with a second, name-targeted Google News search using a 90-day window when the
  filtered company-news count is low, and states plainly when a listing genuinely has little
  findable coverage rather than showing a silent empty feed. Well-covered tickers (NVDA, AAPL,
  etc.) were unaffected throughout — this is a real data-availability limit for some listings,
  not a fixable code gap.
- **Pattern detection**: full-series scan (unrestricted, on every timeframe including intraday),
  relying on `patterns.detect`'s existing most-recent-first sort. An intermediate attempt to
  restrict intraday scans to a trailing 2-hour window (meant to stop stale swings from showing)
  was reverted the same day — it backfired by also excluding genuinely recent and older-but-real
  patterns the user wanted visible. **Lesson kept for future work: "recent" is ambiguous between
  "prioritize recent" and "restrict to only recent" — confirm which before filtering.**
- **Backend port**: 8001 (like 8000 before it) got a stuck orphaned LISTENING socket with no
  owning process, and separately `uvicorn --reload`'s WatchFiles watcher proved unreliable on
  this machine (missed several edits, serving stale code silently). **Backend now runs on port
  8002, without `--reload`** — restart manually after backend edits. `frontend/.env.local`
  updated to match; check it for the currently live port before assuming the backend is down.
- **Not yet done from the original sketch**: a full type scale / 8pt spacing system, and Practice
  Lab's redesign (explicitly deferred by the user to Wave 4).
- All 71 backend tests pass.

### Fixed 2026-09-17 (SMA lookback, user-reported — same day as H5)
- ~~SMA200 was cut short on 1Y and vanished entirely on 5D/1D~~ — SMA200 needs 200 bars of
  lookback before it produces a single point; the backend fetched ONLY the display window (e.g.
  exactly 5 days for the 5D chart), leaving no room for that lookback, so SMA200 only appeared
  over whatever trailing sliver of the window happened to have 200+ bars behind it. Fixed:
  `app.py::_fetch_with_lookback` + `_LOOKBACK_FETCH` now fetch MORE history than the display
  window needs (e.g. "60d" of 15-min bars for the "5D" tab, verified empirically against
  yfinance — "3mo" is silently REJECTED for 30m/15m/5m intervals, intraday history is capped at
  60 days regardless of which period token asks for it), compute indicators on the full fetch,
  then trim back to the original display width so the visible candles are unchanged — only the
  indicators drawn on them are now fully populated. 3 new tests. Verified live on NVDA: SMA200
  now spans the ENTIRE visible window on every timeframe (1Y/1M/10D/5D/1D), not just a tail
  sliver or nothing at all.

### Fixed 2026-09-17 (Audit Wave 3, first item — H5: chart indicator overlays)
- ~~No indicators were drawn on the chart~~ — SMA/Bollinger/RSI/MACD were computed and explained
  in prose but never plotted. Upgraded `lightweight-charts` **v4.2 → v5** (its multi-pane support
  is the whole reason — v4 has none). Backend: new `indicators.compute_indicator_series()`
  returns full time-aligned arrays (the existing `compute_indicators()` only ever returns the
  LATEST snapshot value, useless for drawing a line across the chart) — wired into `/research`'s
  new `indicatorSeries` field. Frontend: `PriceChart.jsx` overlays SMA50/SMA200 + Bollinger Bands
  on the price pane, puts RSI and MACD each in their own pane below (RSI on a fixed 0-100 scale
  with 30/70 overbought/oversold reference lines), and adds a crosshair-driven OHLC + change% +
  volume legend. All four togglable from the chart header (SMA on by default; Bollinger/RSI/MACD
  off, so the chart isn't busy for a first-time user). 3 new backend tests. Verified live: RSI's
  hovered value (46.89) matches the Metrics panel's snapshot (46.8876) exactly, confirming the
  two views come from the same numbers; crosshair legend confirmed via a real hover event.

### Fixed 2026-09-17 (Audit Wave 2 — cost/reliability)
- ~~No backend cache of the analysis result — every reload spent a fresh paid call~~ (M2) —
  `orchestrator.analyze()` now caches its finished result for 20 min per ticker
  (`ANALYZE_CACHE_TTL`); a raised exception (missing key, AI error) is never cached, so a
  transient failure is retried on the very next request rather than sticking around. Verified
  live: two `/analyze/AMD` calls back to back → one real ~30s Claude call, then a 4ms cache hit;
  server log confirms exactly one `[llm]` line for both requests. 3 new tests.
- ~~No timeout on the Anthropic client — a hung request could occupy a worker indefinitely~~
  (M11) — `agents/llm.py` now sets `timeout=` on client construction: 90s for analysis
  (`ANALYSIS_TIMEOUT_S`, high effort/4000 tokens), 45s for chat (`CHAT_TIMEOUT_S`, medium
  effort/1200 tokens). Both endpoints already catch generic exceptions and degrade to
  `available:false`, so a timeout now surfaces as a normal graceful-degradation message instead
  of hanging the request forever. 3 new tests.

### Fixed 2026-09-16 (Audit Wave 0)
- ~~Phase 3 work stranded off `master`~~ — was already merged to `origin/master` via PR #2 in a
  parallel session by the time this session checked; this session's `master` (one commit behind,
  the audit doc) merged up to match. Verified: `services/access.py`, the Google-News fallback,
  `lib/currency.js`, Practice Lab and accessibility fixes are all on `master` now.
- ~~Market cap rendered as USD for every listing~~ — `company.get_profile` now returns
  `marketCapCurrency`; `Ecosystem.jsx` and `Compare.jsx` format with `currencySymbol()` instead
  of a hardcoded `$`. Verified: 7974.T now reads `¥9.36T`, not `$9.36T`.
- ~~`above_sma50/200` returned `false` for *unknown*~~ — `indicators.py` now emits
  `True|False|None`; `None` when the average itself isn't available. Both agent prompts
  (`analysis.py`, `chat.py`) now explicitly instruct: a `null` figure means not-available, never
  treat it as "below". Regression test in `test_indicators.py`. Verified live.
- ~~News items with no URL rendered `href="#"`~~ (reset the hash route → kicked the user home) —
  `NewsPanel.jsx` now renders those as a non-link block instead.
- ~~No React error boundary~~ — `components/ErrorBoundary.jsx` now wraps `<App/>` in `main.jsx`;
  a render crash shows a recoverable message (remounts the tree) instead of a white screen.

### Fixed 2026-09-17 (Audit Wave 1 — the four flaws the user named)
- ~~Search auto-picked on a name/ticker collision~~ (`App.jsx:56`) — typing "Sony" silently opened
  the NYSE ADR, never offering Tokyo. Fixed with `looksLikeTicker()`: the picker is now skipped
  only when the query is genuinely ticker-shaped (no spaces, no lowercase) AND unambiguous — a
  company NAME that happens to equal its own ticker no longer auto-picks. Same fix in `Compare.jsx`.
  Also: `services/search.py::resolve()` now scores and sorts candidates by listing quality (home/
  major exchange first; OTC/CDR/preferred/secondary-dealer lines demoted and badged `OTC`/`CDR`/
  `Pref`/`Secondary` in the picker with a plain-language tooltip) — previously Yahoo's raw,
  unranked order regularly put a thin OTC ADR above the real company (verified: "nintendo" put
  `NTDOY` OTC above `7974.T` Tokyo). 4 new tests in `tests/test_search.py`. Verified live in the
  browser: "Sony" now opens the picker with `6758.T` ranked above the NYSE ADR.
- ~~News only reached the UI via the paid `/analyze` call~~ — new `GET /news/{ticker}`
  (`agents/orchestrator.py::news_bundle`, no Claude call, not gated by the access guard) returns
  the same relevance-filtered feed `/analyze` uses. `NewsPanel.jsx` now loads Feed from this
  endpoint independently of the AI state; "What it means" still needs `/analyze` for its
  inference, but headlines render immediately regardless of AI availability. Feed is now the
  default tab (was "What it means"). 4 new tests in `tests/test_news_endpoint.py`, incl. one
  proving `/news` and `/analyze` share one cached `gather()` call (no double-fetch). Verified
  live: headlines rendered while the AI panel was still "Scraping & analysing…".
- ~~Chart was destroyed/rebuilt on every parent render~~ — `PriceChart.jsx` rewritten from one
  effect (any prop change → `chart.remove()` + full rebuild) into three independent effects:
  chart creation (mount-once), price series (swap series only when candles↔line actually
  changes, else just `setData`), pattern overlay (fully separate, never touches price data).
  View is now only re-fit on a genuinely different dataset (new ticker/timeframe), not a
  same-shape auto-refresh — zoom/pan now survive the 7-min refresh. `Research.jsx` also
  memoizes `chartOhlcv`/`chartPatterns` so a fresh array identity isn't manufactured on every
  keystroke in the header search. Verified live: typing no longer visibly rebuilds the chart.
- ~~Pattern detector only inspected the last 3 swings, returned at most one reversal + one
  trendline, and its double-top branch rejected the textbook case~~ — `services/patterns.py`
  rewritten: full-series scan (every consecutive pair/triple of swings, not just the tail);
  extrema now from High/Low, not Close (matches the actual wicks); double top/bottom no longer
  requires an unrelated third peak to be higher (that rejected a double top with a *lower* prior
  peak — the normal case at the end of an uptrend); overlapping matches dedup'd (a Head &
  Shoulders claims its peaks so they aren't also reported as a Double Top); confidence is now a
  real "low"/"moderate" label from level-fit tightness, not a fixed string.
  **User caught two real regressions in this first pass, both now fixed (2026-09-17):**
  (a) the 4%/2%/3% tolerance/min-dip/flat constants were tuned for daily-or-longer swings and
  never fired on intraday timeframes (5D/1D returned 0 patterns on every ticker tried) —
  `_scale()` now derives tol/min_dip/flat from the SERIES' OWN median bar-to-bar volatility, so a
  proportionally-clean pattern is found regardless of absolute price scale; also lowered the
  hard `n < 30` bar-count floor to `n < 20` (1M/22 bars was always empty purely on bar count).
  (b) results weren't sorted, so the full-series scan could surface a months-old match ahead of
  an equally-clean recent one (the UI selects index 0 by default) — `detect()` now sorts
  most-recent-first. 6 new regression tests total. Verified live on NVDA across all 5
  timeframes (was 0 patterns on 1M/5D/1D, now finds patterns on every one) and confirmed the
  default-selected pattern is the most recent (Double Bottom near the current date, not a
  Triple Top from January).
- ~~Not shareable as written~~ — `Welcome.jsx` greeting de-personalized; `news.py`'s SEC
  User-Agent contact now reads from `TRADE101_SEC_CONTACT` (falls back to a generic placeholder)
  instead of a hardcoded personal email in committed source — the real email still lives in the
  gitignored local `.env`, which is the correct place for it.

### Fixed 2026-09-17 (Ecosystem panel, user-reported)
- ~~Company summary was cut off mid-word~~ (e.g. "...artificial intelligence solutions an…") —
  `company.py` sliced the summary at a fixed 360-char count with no regard for word boundaries,
  and `Ecosystem.jsx` then unconditionally appended a SECOND "…" even when the text already
  ended cleanly. Fixed: `company._truncate_summary()` cuts at the last word boundary and only
  adds "…" when actually truncated; the frontend no longer appends its own. 4 new tests.
- ~~Beta explanation named "the market" instead of the actual benchmark~~ — a PROVIDER-sourced
  beta (the common case for most US tickers) carried no index name at all, unlike a computed
  one. `company.get_profile` now also names the benchmark for the provider case (reusing the
  same suffix→index map `_computed_beta` uses — S&P 500 for US, Nikkei 225/KOSPI/etc.
  elsewhere); `Ecosystem.jsx::betaNote()` names it throughout ("more volatile than the S&P 500"
  instead of "than the market"). 2 new tests. Verified live on NVDA: beta 2.217 now explicitly
  reads "vs the S&P 500" end to end.
- ~~Ecosystem peer nodes showed only a bare ticker, no way to see the company name without
  already knowing it~~ — `company.get_profile` now also returns `peerNames` (ticker → full name,
  resolved via parallel yfinance lookups — Yahoo's keyless batch-quote endpoint now 401s without
  a session/crumb, so this is one `.info` call per peer run concurrently, ~0.85s for 8 rather than
  8x that sequentially) purely for the ecosystem graph's hover tooltip; `peers` itself is
  untouched (still a plain ticker list — `services/evidence.py` matches news against it
  directly). `EcoGraph` nodes now carry a native SVG `<title>` (hovering "MU" shows "Micron
  Technology, Inc.") and are keyboard-focusable/Enter-activatable with a `:focus-visible` ring
  (click-to-navigate itself already worked correctly). 2 new tests.
- ~~A peer could appear twice in the ecosystem graph~~ (confirmed live: QCOM's Finnhub peers list
  genuinely contained "MRVL" twice) — `company._peers()` now dedupes case-insensitively,
  preserving order. 1 new test.

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
**⚠️ Superseded 2026-09-17 by BYOK — see the header callout at the top of this file.** This
whole approach (shared token + daily cap) was replaced, not extended; `services/access.py` and
`lib/access.js` no longer exist. Kept below as a historical record only.
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
- **A killed process can leave a genuinely orphaned LISTENING socket on Windows** (seen 2026-09-17
  on port 8000): `netstat -ano`/`Get-NetTCPConnection` keep reporting a PID as `LISTEN`-ing the
  port, but `Get-Process`/`taskkill` on that same PID say it doesn't exist — a real kernel-level
  stuck socket, not a stale display. Waited 40+s, didn't clear on its own. Do NOT run `netsh
  winsock reset` or any other system-level network fix for this — that's a prohibited action.
  Workaround: run the backend on a fallback port (`--port 8001`) and point the frontend at it via
  `frontend/.env.local`'s `VITE_API_BASE` (gitignored, local-only — see Config). A machine restart
  should reclaim the original port; this needs no code change once it does.
- **On 8001 too (2026-09-17, first occurrence): found FIVE separate stray processes all launched
  as `uvicorn app:app --port 8001` (no `--reload`)** — from several past sessions never cleanly
  exited. Only one (`Get-NetTCPConnection -LocalPort 8001 -State Listen`) actually owned the
  socket; the rest were dead weight, but backend code edits were silently NOT taking effect
  because that one live process had no `--reload` and was running stale code from before this
  session's changes. `Stop-Process -Force` on all five worked cleanly that time (not a stuck
  kernel socket) — killed all five, confirmed the port was free, relaunched with `--reload`.
- **8001 again (2026-09-17, same session, later): this time it WAS the stuck-orphaned-socket
  problem** (like the port-8000 incident) — `Get-NetTCPConnection -LocalPort 8001` kept reporting
  PID 32592 as `LISTEN`, but `Get-Process -Id 32592` said no such process exists. Also separately
  found `uvicorn --reload`'s WatchFiles watcher was NOT reliably picking up backend file edits on
  this machine — only one reload fired across several subsequent saves, so code changes looked
  "not applied" when the process just hadn't restarted. **Net effect: don't trust `--reload` on
  this machine, and check who actually owns the port before assuming a code fix didn't work.**
  Resolution: moved to **port 8002, without `--reload`** (restart manually after backend edits).
  `frontend/.env.local`'s `VITE_API_BASE` updated to match — **check this file for the currently
  live port** before assuming the backend is down or a fix didn't land. Vite only reads
  `.env.local` at startup, so the frontend dev server needs restarting too after changing it.
- Chart-pattern detection is a heuristic learning aid (returns "none" when nothing clean) — never present it as a signal. Detects on High/Low, not Close (2026-09-17). Scans the WHOLE fetched window on every timeframe, including intraday — a brief attempt to restrict intraday scans to a recent rolling window backfired (it excluded genuine patterns, not just stale ones) and was reverted the same day; recency is handled by `patterns.detect`'s most-recent-first sort, not by hiding data from the scan.
- Layout is a fixed two-zone column split (chart → metrics → AI read spine; news → ecosystem → references side) — no longer a self-balancing masonry (removed 2026-09-17, see "Wave 3 UI/UX redesign" above). Browser back/forward + `#TICKER` shareable links work — and now `#/compare` `#/watchlist` `#/history` too (2026-09-15).
- Any element that doesn't set an explicit `color` can fall back to browser UA defaults instead
  of inheriting the page's `--ink` — this bit the `.metric` buttons once already (2026-09-15).
  `color-scheme: dark` is set on `:root` as a guard, but still set colors explicitly on new
  `<button>`/`<input>` styling rather than relying on inheritance alone.
