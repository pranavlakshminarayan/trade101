# Trade Craft — Development Log (phase by phase)

> Brand **Trade Craft** (renamed from "Trade101" on 2026-09-15; repo/folder/package stay
> `trade101`). This log keeps the old name in the early phases where it was accurate at the time.

The story of how the app was built, in order: how the idea was broken down and visualised,
what each phase executed, the inputs/suggestions that shaped it, and — honestly — the mistakes
made and how they were corrected.

**This file is updated after every phase completes** (hard rule; see `CLAUDE.md` → Memory
protocol). It is the narrative "how we got here" companion to:
- `CLAUDE.md` — concise current-state reference (auto-loaded each session)
- `BACKLOG.md` — the live feature/bug checklist
- `docs/HANDOVER.md` — the full, detailed technical handover (deep detail lives there)
- `docs/DEPLOY.md` — how to deploy the single-service app (shareable URL)
- `docs/trade101-phase-2-recommendations.md` — the 2026-09-10 product/technical review

**Order of the log:** Phase 0 → 1 → 1 flaw pass → 1.5 → 2 → Rebrand → 3.

Local app in development: **http://127.0.0.1:5173** (Vite dev) or **http://127.0.0.1:8000** (the
backend now also serves the production build). A hosted shareable URL is deploy-ready
(`docs/DEPLOY.md`); going live is the user's one host-signup step. The pre-share endpoint-guard
fix is done in code — the only remaining gate on actually *sharing* the resulting URL is the
user setting `TRADE101_ACCESS_TOKEN` on the host once deployed.

---

## Phase 0 — Idea, breakdown, and visualisation

**The idea.** A personal stock-research *and learning* app for a student/beginning trader
(Pranav, trades on Moomoo). Type a company name (any market) → one page assembles a live chart,
indicators explained *in context*, chart patterns, a sourced AI momentum read, news + "what it
means", an ecosystem/peers view, and a search history. Cleaner than Zerodha, calmer than Moomoo
(which "has too many buttons").

**How we broke it down before writing code.** Rather than jump to code, the idea was first
*visualised* to make sure we understood what we were building:
1. Explored feasibility by first integrating **Yahoo Finance into Claude as an MCP connector**
   (a separate `yfinance-mcp` project) — proving we could pull real, exact market data.
2. Ran a **Wall-Street-style AAPL September-event study** on that data and published an
   interactive dashboard — this validated the "extract data and make sense of it, never advise"
   posture that became Trade101's north star.
3. **Brainstormed the app as live HTML mockups (v1→v5)** using the brainstorming skill + a
   visual-companion server, iterating the layout and brand before committing to a stack.

**Decisions locked from the visualisation phase:**
- **Hybrid architecture** — deterministic services for exact numbers (prices, indicators),
  Claude agents for judgment (analysis), coordinated by an orchestrator. Reason: *numbers must
  never be hallucinated; reasoning must be sourced.*
- **Stack:** FastAPI (Python) + React (Vite) + Lightweight-Charts.
- **Markets:** US + China, Japan, Korea, HK, Singapore, India, Europe; search by company name.
- **Brand Trade101**, dark fintech palette derived from a data-cube logo concept.
- Spec → `docs/superpowers/specs/`, plan → `docs/superpowers/plans/`, backlog → `BACKLOG.md`.

**North-star guardrails (never broken since):** describes/teaches, never buy/sell; numbers exact
and deterministic; every AI claim sourced; when a source is unreachable, say so.

**Mistakes / course-corrections in Phase 0:**
- **MCP library gotcha.** First integration used the old `FastMCP` import; on `mcp` 2.x that
  class was renamed. Corrected to `from mcp.server.mcpserver import MCPServer`. *Lesson: pin/
  check library major versions before wiring.*
- **Sales-vs-stock data honesty.** An early AAPL analysis wanted to cross-check stock against
  iPhone unit sales — but Apple stopped reporting units in 2018. Rather than fudge it, we
  switched to iPhone-segment *revenue* from SEC 8-Ks and labelled the limitation. *Lesson that
  set the tone: state the data gap, never paper over it.*

---

## Phase 1 — MVP build (Milestones M0–M5)

Executed the hybrid app end to end. Each milestone was committed.

- **M0 — Scaffold.** Git, `.gitignore` (ignores `.env`, `.venv`, `data`), `.env.example` with
  named per-agent keys, backend/frontend skeletons.
- **M1 — Real-time deterministic core.** `services/marketdata.py` (yfinance, any market via
  exchange suffixes), `services/indicators.py` (RSI/MACD/SMA/EMA/Bollinger — pure pandas, exact,
  unit-tested), `GET /research/{ticker}`. Verified live on NVDA/MSFT/RELIANCE.NS; nothing
  hardcoded to one ticker.
- **M2 — Frontend.** Welcome + Research view, live candlestick+volume chart, real indicators,
  click-to-learn lessons, dark palette.
- **M3 — AI narration.** `services/news.py` (Finnhub news + SEC EDGAR filings, pluggable
  provider), `agents/{llm,analysis,orchestrator}.py`, citation guard, `GET /analyze/{ticker}`
  (separate from `/research` so the chart never blocks on AI; degrades with no key).
- **M4 — Patterns + ecosystem.** `services/patterns.py` (head&shoulders, triple/double
  top&bottom via scipy extrema; labelled + educational), `GET /patterns`; `services/company.py`
  + `GET /ecosystem` (sector, industry, beta, market cap, peers); History tab (localStorage).
- **M5 — Tests + resilience.** 16 passing tests; graceful degradation everywhere; shipped to
  GitHub (public).

**Inputs / suggestions that shaped Phase 1 during the build:**
- Make it truly ticker-agnostic and name-searchable across markets (allianz→ALV.DE,
  samsung→005930.KS) — done, and the "needs a suffix" copy was removed.
- Flowing, content-sized layout → ended as a **self-balancing JS masonry**.
- News as boxed cards; references as descriptive links; candle/line toggle; timeframes
  1Y·1M·10D·5D·1D; auto-refresh; browser back/forward + `#TICKER` shareable links.
- Switched the model default to **Sonnet 5** to cut cost (override via `TRADE101_MODEL`).

**Mistakes / course-corrections in Phase 1:**
- **A security bug was found *and its fix was discarded*.** A live run on 7974.T (Nintendo)
  surfaced that the Finnhub API key was leaking into the browser (raw httpx exception text
  carries the request URL, which contains `token=<key>`). A fix was written and then discarded,
  so Phase 1 shipped with the leak still open. *This is the single biggest process mistake so
  far — a known security issue left in. It was fixed in the Phase 1 flaw pass below, and it is
  why the "fix, don't discard, and re-verify" discipline now matters.*
- **Raw provider errors were shown as user-facing copy** — exception strings (with URLs) landed
  in the UI instead of plain explanations. Corrected in the flaw pass.
- **Non-US coverage over-promised.** Ecosystem/news gaps for non-US tickers showed as blanks
  rather than honest "not available here" messaging. Corrected (messaging) in the flaw pass;
  real non-US data is Phase 2.
- **Deprecation left in:** `datetime.utcnow()` (Python 3.12). Corrected in the flaw pass.

---

## Phase 1 flaw pass — 2026-09-14

A dedicated pass to clear the known flaws before adding features. Full technical detail in
`docs/HANDOVER.md` §4.2.

**Executed:**
- **Fixed the Finnhub key leak (security, top priority).** `services/news.py` no longer returns
  raw exceptions — error paths return fixed, credential-free strings, and a Finnhub 401/403 (the
  non-US case) has its own plain message. Added `services/safe.py::redact_secrets()` as a second
  line of defence, scrubbing `token=`/`apikey=`/`key=` and known key values from anything
  client-bound; `app.py` runs the `/analyze` error `reason` through it.
- **Replaced raw provider errors** with plain, honest explanations.
- **Ecosystem gaps now explained**, not blank: `services/company.py` returns a `coverage` map
  (why beta/peers are missing); the panel renders it.
- **`datetime.utcnow()` → timezone-aware.**
- **Added 4 regression tests** (`tests/test_safe.py`) that plant a fake key and assert it never
  survives into any client-facing string.

**Mistakes / course-corrections in this pass:**
- Briefly added an unused `redact_secrets` import to `news.py` before deciding the friendly
  messages were safe on their own; removed it and applied redaction at the `app.py` boundary
  instead (cleaner separation).
- A shell `cd` during exploration silently moved the working directory and a follow-up command
  failed; corrected by using absolute paths for subsequent commands.

**Left open by design:** non-US news (Finnhub free tier 403s on non-US symbols) — the real fix
is Phase 2 Firecrawl/alternative sourcing. **User action still required: rotate the Finnhub
key**, since the fix can't un-expose a value that may already have been shown on screen.

Tests after this pass: **20 passing** (was 16).

---

## Phase 1.5 — Trust & coherence (in progress, from 2026-09-14)

Chosen to run *before* Phase 2 features, because the review flagged issues that touch the north
star itself (a live NVDA run let unrelated articles colour the AI narrative — a "every claim is
sourced" violation, not a cosmetic bug). Rationale: don't add features until the single-stock
read is demonstrably trustworthy end to end. Source: `docs/trade101-phase-2-recommendations.md`.

**Executed so far (the guardrail slice):**
- **Evidence relevance filter** — new `services/evidence.py`, a *deterministic* classifier
  (company / related-peer / sector / irrelevant) that drops unrelated articles **before** the
  model sees them. It matches on the company name (dropping corporate filler like Inc/Corp/Ltd),
  the ticker (suffix-stripped so `7974.T` matches "Nintendo"/"7974"), sector/industry, and peer
  names. Wired into `agents/orchestrator.py`; only admitted evidence reaches the model, the
  feed, and the references list.
- **Claim-level honesty** — every momentum-evidence point now carries a
  **Fact / Interpretation / Unknown** label (enforced in `agents/analysis.py`), rendered as a
  badge next to the claim in `AiRead.jsx`; the agent must withhold a company-catalyst claim when
  no company-specific news exists. A "N unrelated articles filtered out" line shows the sourcing.
- **Evidence tests** — `tests/test_evidence.py` (6 tests) feed junk/peer/company articles and
  assert the junk is dropped and `has_company_news` is reported honestly.
- **Confirmed keys are backend-only** — no `VITE_`/key refs in `frontend/src`, no frontend
  `.env`.

Tests after the guardrail slice: **26 passing**.

**Remaining in Phase 1.5:** timeframe integrity (one shared as-of label across chart/metrics/
patterns/AI read; indicators computed for the *selected* timeframe, not always daily),
coverage-truthfulness badges, and a visible not-financial-advice notice next to the narrative.

### 2026-09-14 — UX/data fixes pass (three user-reported issues)

Verified live in the browser (US ticker AAPL + non-US 7974.T).

1. **Bigger pattern library, only relevant shapes shown.** `services/patterns.py` gained a
   trendline family alongside the existing reversals: Ascending/Descending/Symmetrical
   Triangle, Rising/Falling Wedge, Ascending/Descending Channel — detected by fitting
   support/resistance lines to recent extrema and classifying by slope + convergence. Only
   shapes actually present are returned (AAPL live showed Head & Shoulders + Inverse H&S +
   Rising Wedge; NVDA/TSLA/Nintendo correctly showed none). New patterns carry `lines` to draw
   two trendlines; `PriceChart.jsx` renders them. Each has a full magnifier explanation of what
   it is and why it reads that way. +2 tests.
2. **Non-US stocks now show the company name and get news.** `marketdata.py` prefers the
   properly-cased `longName` (so "Nintendo Co., Ltd." not "7974.T"), with a Yahoo-search
   fallback; the headline now leads with the name and shows the ticker as a small tag.
   `news.py` falls back to keyless Yahoo Finance news when Finnhub can't serve a symbol (its
   free tier 403s on non-US) — Nintendo went from 0 to 10 headlines, so non-US analysis now has
   real evidence to work from.
3. **State no longer lost on tab-switch (and no wasted API spend).** Added a session result
   cache in `frontend/src/api.js` for research / analyze / ecosystem / patterns. Revisiting a
   stock or returning from another tab restores everything from memory and, critically, never
   re-runs the paid `/analyze` call (verified: 1 call for AAPL, still 1 after History→back).
   The 7-min auto-refresh bypasses the cache with `{ fresh: true }`. This also delivers the
   frontend half of the Phase 1.5 "cache abstraction" item.

**Mistakes / course-corrections in this pass:**
- **Introduced a crash then caught it before it shipped.** While editing `PriceChart.jsx` I left
  a placeholder call to a non-existent `ls_markers(...)` function that would have thrown on
  every pattern render. Spotted it on re-reading the diff and removed it before any browser test.
  *Lesson: re-read the actual diff, not just the intent, after a multi-part edit.*
- **Edited backend files against a server started without `--reload`.** The first backend run
  used plain `uvicorn ... --port 8000` (no reload), so early edits to `news.py`/`marketdata.py`
  silently didn't take effect until I killed and restarted it with `--reload`. *Lesson: always
  run the dev backend with `--reload`.*
- **A stray `cd` in an exploration command** moved the shell's working directory and a following
  command failed; corrected by using absolute paths.

### 2026-09-14 — Prompt caching for the Claude API (cost control)

The user asked to move API usage to prompt caching to avoid burning money. Done in
`agents/llm.py`: the analysis **system prompt is now sent as a `cache_control: ephemeral`
block**. It's byte-identical on every call and the only per-ticker-variable content (the
indicators/news/filings payload) comes *after* it in the user message — a textbook cacheable
prefix. On any call within the 5-minute window Claude serves those system tokens at ~0.1× input
cost instead of full price. `llm.py` also now logs `cache_write`/`cache_read`/`in`/`out` token
counts per call so we can confirm caching from the server log.

**The catch we found and fixed.** Prompt caching only fires above a model-specific minimum
prefix size (Sonnet 5 = 1024 tokens; Opus 5 = 512). Measured with the free `count_tokens` API,
the system prompt was **897 tokens — below Sonnet 5's minimum**, so the cache marker would have
silently done nothing on the default model (no error, just `cache_creation_input_tokens: 0`).
Fixed by adding a genuinely useful, stable worked example of the Fact/Interpretation/Unknown
evidence labeling to the system prompt (improves output quality *and* pushes the prefix to
**1306 tokens**), so caching now actually fires on Sonnet 5. Verified the new count with
`count_tokens` (free); the per-call log will confirm live cache reads on the next real usage.

**Honest scope of the saving.** Caching cuts the *input* cost of the repeated system prompt
across tickers/sessions within the window; it does nothing for output tokens or the per-ticker
payload. The larger money-savers already in place are the frontend session cache (no repeat
`/analyze` calls — the biggest one) and the evidence filter (fewer news tokens sent). The
`effort="high"` setting on the analysis call remains the main *output*-cost lever if further
savings are needed later — left as-is for now to preserve quality.

**Mistakes / course-corrections in this pass:**
- **Nearly shipped a no-op cache.** My first instinct was just to add the `cache_control` marker
  and call it done — which would have looked correct but cached nothing on Sonnet 5, the user's
  default. Measuring the prefix (897 < 1024) before claiming success is what caught it. *Lesson:
  for caching, verify the prefix clears the model's minimum, don't assume the marker is enough.*

---

## Phase 2 — depth _(started 2026-09-14)_

Planned: Ask-Claude chat (done, below); Comparison tab; deeper non-US sourcing
(Firecrawl/alternative — provider slot already pluggable); richer ecosystem graph; the real
data-cube logo; **deploy a shareable/public URL** so the app is checkable from any device. See
`BACKLOG.md` for the full list.

### 2026-09-14 — Ask-Claude chat (first Phase 2 feature)

A conversational tutor over one stock's research bundle. Verified live end to end.

- **Backend.** `orchestrator.gather()` was extracted so the analysis run and the chat share ONE
  deterministic data bundle (exact numbers + relevance-filtered evidence) — reasoning over the
  same sourced data, fetched once. `agents/chat.py` renders that bundle into a cached system
  prompt (same north-star guardrails: exact numbers, cite what you lean on, teach, never
  buy/sell) and runs the conversation in `messages`. `POST /ask/{ticker}` degrades gracefully
  (no key / error → `available:false`) and scrubs secrets from any error. `agents/chat.py` uses
  `effort="medium"` to keep chat cheap.
- **Caching, two layers.** `services/cache.py` (new, TTL 5 min) memoises `gather()` so chat
  turns don't re-fetch and the numbers stay identical across a conversation; that stability is
  also what lets Claude's **prompt cache** hit — the rendered context is byte-identical turn to
  turn. Verified in the server log: chat turn 1 `cache_write=1693, cache_read=0`; turn 2
  `cache_write=0, cache_read=1693` — the whole 1693-token context prefix served from cache at
  ~0.1× cost, with only the 49-token question at full price. This closes the Phase 1.5 cache
  item (frontend session cache + backend TTL cache + Claude prompt caching).
- **Frontend.** `components/AskClaude.jsx` — a chat card in the research masonry with starter
  questions, per-ticker threads kept in module memory (survive tab-switches, like the api
  cache), and a visible "each question is one Claude call · educational only" note. `api.ask()`
  posts the question + history.

**Mistakes / course-corrections in this pass:**
- **Zombie backends held the port and served stale code — the real bug behind a confusing
  404.** `POST /ask` kept returning 404 even though a fresh `import app` showed the route
  registered. Cause: several `uvicorn --reload` backends started across previous turns had
  orphaned worker processes still bound to port 8000 (Windows lets multiple inherit the socket),
  and requests were landing on an old worker without the new route. `taskkill //PID` didn't
  clear them because killing a `--reload` *worker* makes its reloader parent respawn one. Fix:
  list python processes with their command lines, identify the orphaned `multiprocessing.spawn`
  workers (careful NOT to kill the unrelated yfinance-mcp processes), kill exactly those, confirm
  the port was clear, then start a single clean backend. *Lesson: one dev backend at a time —
  verify the port is actually clear before starting another, and diagnose a "route 404s but
  imports fine" as a stale-process problem, not a code problem.*

### 2026-09-14 — Ask-Claude → floating widget + non-US sourcing (free tier)

Two user requests in one pass.

- **Ask-Claude is now a floating chatbot widget** (per a screenshot of a website "Chat with us"
  bot): a bubble pinned bottom-right that opens an overlay panel over the page content, instead
  of a card in the research grid. `AskClaude.jsx` rewritten (launcher + panel with header/close,
  same threads + prompt-cached backend); removed from the masonry `FLOW`, rendered at the
  `Research` root.
- **Non-US sourcing, free/deterministic tier** (user chose free now, paid Firecrawl after
  deploy). The standout gap was beta: non-US listings came back `null` because neither
  yfinance nor Finnhub publishes one. Now `company.py` **computes beta itself** from ~1y of
  daily returns vs the stock's regional index (a suffix→index map: .T→Nikkei 225, .KS→KOSPI,
  .NS→Nifty 50, .HK→Hang Seng, …; US → S&P 500), used only when the provider has none. Verified
  live: 7974.T beta 0.079 vs Nikkei 225 (`betaSource:"computed"`), while AAPL keeps its provider
  beta 1.085. The Ecosystem panel notes when a beta was computed and against which index.
  Non-US peers remain gapped — that's the Firecrawl/Exa job, deferred to post-deploy.

**Mistakes / course-corrections in this pass:**
- **The zombie-backend problem recurred** and again produced stale responses (computed beta
  worked when called directly but the live `/ecosystem` returned `null`). Same root cause as
  above; the accumulation came from repeatedly restarting `uvicorn --reload`. Corrected by
  killing all uvicorn/`multiprocessing.spawn` workers (sparing the MCP processes) and switching
  the throwaway verification backend to run **without** `--reload` (one process, no reloader to
  spawn extras). Documented the whole trap as a Gotcha in `CLAUDE.md`. *Lesson learned twice now:
  treat "works on direct import, stale over HTTP" as a process problem immediately.*

### 2026-09-14 — Comparison tab (Phase 2)

Two stocks side by side, verified live in the browser (Apple vs Microsoft) with **no Claude
spend** — the whole tab is deterministic (`/research` + `/ecosystem` only).

- `components/Compare.jsx` — two search pickers (reuse `/search` disambiguation, take best
  match), color-coded headers (teal A / amber B), a shared timeframe (1Y/1M), and a metrics
  table that reuses `lessons.js` (`METRICS`, `metricValue`, `metricLabel`) so the numbers match
  the research view exactly. Rows: price, change%, RSI, MACD, SMA50/200, Bollinger, volume, beta,
  sector, market cap. "Open full research" chips jump to either stock.
- `components/ComparisonChart.jsx` — both price series rebased to 100 at the window start, so the
  chart compares **% moves** rather than absolute prices (deliberately teal/amber, not
  green/red, so no "good/bad" is implied).
- Wired `view === 'compare'` in `App.jsx`; activated the previously-dead "Comparison" tab in
  `Research.jsx` and the Welcome rail (removed its "soon" tag). Slot A seeds from the stock you
  came from.
- Guardrail held: the header and a footer note both say it **describes differences, never which
  to buy** — no "winner", no recommendation.

**Mistakes / course-corrections in this pass:** none material. (Minor: the `#TICKER` hash router
treats any hash as a ticker, so `#compare` isn't a deep link to the tab — expected; navigation is
via the tab/rail. Not worth a router rework now.)

### 2026-09-14 — Comparison search parity + a latent NaN crash

Feedback: the Comparison pickers took the first search match blindly, so "Samsung"
→ "Failed to fetch". Fixed two things:

- **Full search/disambiguation in the Comparison tab.** `Compare.jsx` now runs the same resolve
  flow as the main search bar: type a name → if ambiguous, a "Did you mean…" candidate list
  drops under that slot's input (symbol · name · exchange), and you pick — instead of guessing
  the first hit. `useSlot` now takes an already-resolved symbol; the search/pick lives in the
  component (per-slot `cands`/`busy` state). Verified live: "samsung" lists 005930.KS (Korea),
  SSNLF (OTC), SMSN.IL (London), Frankfurt, etc.
- **Latent `/research` crash on some non-US symbols (found via Samsung).** `/research/005930.KS`
  returned **500**: `ValueError: Out of range float values are not JSON compliant: nan` — a bad
  holiday/partial OHLC bar produced a NaN that FastAPI can't serialize (indicators were already
  NaN-safe; the raw `ohlcv` list was not). Fixed at the source in `marketdata.get`:
  `dropna(subset=OHLC)` + `Volume.fillna(0)`, so every consumer (research/patterns/analyze)
  is protected. 005930.KS now 200; AAPL/7974.T unaffected. 29 tests still pass.

**Mistakes / course-corrections in this pass:**
- **Shipped the Comparison tab with a blind first-match picker** — it looked fine in my Apple-vs-
  Microsoft test (both resolve cleanly as the top hit) but broke on the first genuinely ambiguous
  non-US name the user tried. *Lesson: test a new picker with an ambiguous/non-US query, not just
  two clean US tickers — the happy path hid both the UX gap and the NaN crash.*

### 2026-09-14 — Real logo + ecosystem node graph (rest of Phase 2)

- **Real data-cube logo.** Replaced the flat placeholder `Logo.jsx` with a hand-crafted
  isometric cube: three shaded faces, an ascending teal bar-chart clipped to the right face, and
  a green up-candlestick on the left — the brand's "data cube" spec, as pure scalable SVG (no
  OpenRouter/image-gen key or cost). Verified in the header + Welcome.
- **Ecosystem node graph.** Peers were a flat chip row; now `Ecosystem.jsx` renders `EcoGraph` —
  a radial SVG graph with the company at the centre and up to 8 peers on a ring, connected by
  edges, each node clickable to research it. Falls back to the existing coverage explanation when
  peers are unavailable (non-US). A fuller *sourced* supply-chain graph (typed edges,
  public/private) remains future work.

With these, Phase 2's build items are essentially done except the two the user deferred to
**after full deployment**: the paid Firecrawl/Exa non-US provider, and deploying a shareable URL.

**Mistakes / course-corrections in this pass:** none material. (Chose to verify the logo on the
free Welcome page and *not* open a research view just to see the ecosystem graph, since that
fires a paid `/analyze` — the graph is deterministic SVG, so it's trusted to the user's next
research view. Noting it so a reviewer knows the graph wasn't screenshot-verified here.)

---

## Rebrand + dark theme — 2026-09-15

- **Renamed Trade101 → Trade Craft** across the UI (headers, Welcome, tab `<title>`, News/Ecosystem
  copy) and the AI prompts (`analysis.py`, `chat.py`) so the model refers to itself correctly.
  The GitHub repo / folder / package names stay `trade101` (renaming those is out of scope and
  risky) — only the user-facing brand changed.
- **New logo** (`Logo.jsx`): a growth-spiral ribbon (green→teal gradient) ending in an arrowhead,
  an ascending bar chart in the loop, and small $/€/¥ currency nodes — per the brand spec, as
  transparent-background SVG so it sits on the dark header. (This replaced the Phase-2 isometric
  data-cube mark.)
- **Deeper palette**: `styles.css` `:root` moved to a deep navy (`--bg:#070E1A`, navy surfaces)
  with soft cream/near-white text (`--ink:#F4F1E9`) and slightly brightened teal/green accents so
  they pop on the darker ground. Verified on the Welcome page.

---

## Phase 3 — surface & scale _(started 2026-09-15)_

### 2026-09-15 — Watchlist (first Phase 3 feature)

- `lib/watchlist.js` (localStorage, mirrors the History pattern) + a `components/Watchlist.jsx`
  view and a ☆/★ **Watch** toggle on the research header. The watchlist view pulls a fresh quote
  per tracked name via `/research` (deterministic, **no Claude spend**) and lists ticker · name ·
  price · change with a remove button. Framed as a *study/tracking* list — "information, not trade
  prompts", no positions/P&L/signals — per the learning north star. New app view `watchlist`; tab
  added across Research/Compare/History/Welcome (also fixed History's Comparison tab, which used to
  go home). Verified live with seeded AAPL/MSFT/7974.T (quotes loaded; test data cleared after).

**Mistakes / course-corrections in this pass:** none material.

### 2026-09-15 — Single-service deploy setup (pivot from desktop packaging)

The user asked to "start desktop packaging," but on discussion the actual goal was a **shareable
link**. Clarified the distinction: a desktop app is a downloadable installer (Electron/Tauri),
whereas a shareable link is a **web deploy** — different channels. The web deploy is far more
efficient for a link and sidesteps bundling the Python backend, so we pivoted to it (desktop
packaging parked). Env check had shown Node 24 but **no Rust** (Tauri) and no PyInstaller, which
also pointed away from desktop.

Done:
- **Made the app single-service.** `app.py` now mounts `frontend/dist` (built React) via
  `StaticFiles(html=True)` *after* all API routes, so one origin serves both the API and the UI.
  `api.js` switches its base URL on `import.meta.env.DEV` — dev still hits `:8000`, the built app
  uses same-origin (relative), so no CORS in prod. Verified locally at `:8000`: `/health` + API
  routes work, `/` serves the Trade Craft app, `/assets/*` load. `npm run build` succeeds.
- **Deploy config:** multi-stage `Dockerfile` (node build → python runtime), `.dockerignore`,
  and `docs/DEPLOY.md` with exact Render steps. Any Dockerfile host works.
- **Repo set PRIVATE** (`gh repo edit --visibility private`), per the user.
- The final "go live" step (host signup + connect repo → live URL) is the user's — it needs
  their account; I can't create it. Once they have the URL, add it to the repo About/README.

**Pre-share reminder (user's explicit request):** the URL is personal-use only for now because
`/analyze` and `/ask` spend the owner's Claude key with no auth/rate-limit — a public visitor
could run up the bill. **Remind the user at the END of Phase 3 to fix this** (password/token gate
+ rate-limit/cap) before sharing. Tracked in `BACKLOG.md` → Pre-share checklist and `CLAUDE.md`.

**Mistakes / course-corrections in this pass:** none material. (Good catch on the user's part
that "desktop packaging" and "shareable link" were being conflated — surfacing that before
building an Electron app saved a lot of wasted work.)

### 2026-09-15 — No-Docker deploy option (Render native runtime)

User asked for a free alternative to Docker. Since `app.py` already serves the built frontend
itself, single-service deploy was never actually Docker-dependent — Docker was just *one way*
to build the image. Render's build environment ships Node **and** Python, so a plain Python web
service can run the frontend build as its build step, no Dockerfile at all.

- Added `render.yaml` (Render Blueprint): `runtime: python`, `buildCommand` runs
  `npm install && npm run build` then `pip install -r requirements.txt`, `startCommand` runs
  uvicorn on Render's `$PORT`, `healthCheckPath: /health`, free plan, env vars for the two keys.
- `docs/DEPLOY.md` restructured: **Option A (no Docker, recommended)** using the Blueprint,
  **Option B (Docker)** kept for hosts that want a container. No app-code changes either way.
- Verified locally: fresh `rm -rf frontend/dist && npm install && npm run build` (exactly what
  the Blueprint's buildCommand does) succeeds, and the running backend still serves the rebuilt
  `dist/` at `:8000`.

**Mistakes / course-corrections in this pass:** none material.

### 2026-09-15 — More markets: currency display fix

Picked up the "more markets fully supported" backlog item. Rather than guess at scope, first
read `services/company.py`, `services/news.py`, `services/marketdata.py`, and `services/search.py`
end to end to see what was actually tuned vs. gapped per exchange. Findings: search is already
market-agnostic (Yahoo search, keyless); the beta suffix→index map already covers all seven
target markets plus several European exchanges; the real, concrete, fixable gap found was in the
**frontend**, not the backend — `Research.jsx`, `Watchlist.jsx`, and `Compare.jsx` each carried
their own copy of a `sym()` helper that only recognized `USD`/`INR`, so every other target-market
currency (JPY, KRW, HKD, SGD, CNY, EUR, GBP) silently rendered as a bare number with no unit.

Fixed with one shared `frontend/src/lib/currency.js::currencySymbol()` (covers the seven target
markets + common others, falls back to the currency code itself rather than blank for anything
unmapped) and swapped all three components onto it. Verified live in the browser on 7974.T
(Nintendo, JPY): Research now shows "¥8118" (was a bare "8118"); the Comparison tab shows the
same for the same symbol. Backend test suite re-run clean (29 passed) since no backend logic
changed.

**Non-US peers (Ecosystem tab) remain gapped** — confirmed there's no good *free* substitute for
Finnhub's US-only peers endpoint (yfinance exposes no peers data), so this stays parked behind
the already-deferred paid Firecrawl/Exa tier rather than being hacked around with a curated
static list, which would risk violating the "every AI claim is sourced / never fabricate"
north star for what would effectively be guessed peer data.

**Mistakes / course-corrections in this pass:** none material. (Deliberately read the four
relevant services fully before writing any code, rather than guessing where "more markets" work
was needed — this is what surfaced the currency bug, which wasn't in the backlog or handover
notes at all.)

### 2026-09-15 — Pre-share endpoint guard (the user's "remind me at end of Phase 3" item)

Rather than wait until Phase 3 fully wraps, raised this proactively once "more markets" work
was underway and picked it up on request. The gap, documented since §13/§16 of
`docs/HANDOVER.md`: `/analyze` and `/ask` spend the owner's Claude key with no auth or
rate-limit at all, so the moment a deploy URL is shared, anyone who has it (or anyone they
forward it to) can trigger unlimited paid calls.

Built both layers `docs/DEPLOY.md` had already sketched as the fix, together (defense in
depth, same pattern as the earlier key-leak fix): new `backend/services/access.py`, wired as a
FastAPI `Depends()` on `/analyze` and `/ask` only (every deterministic endpoint — chart,
indicators, patterns, compare, watchlist — stays open, since none of them cost anything).

- **Access token** (`TRADE101_ACCESS_TOKEN`, optional): if set, both routes require it as the
  `X-Access-Token` header or return 401. Deliberately a single shared secret, not per-user
  accounts — this is a personal app being shared with a few people, not a multi-tenant product.
- **Daily cap** (`TRADE101_DAILY_CAP`, default 50): a process-wide counter over both endpoints
  combined, resetting at UTC midnight, returning 429 once exhausted — a backstop even if the
  token itself leaks or gets shared onward.
- Both are **no-ops when unset**, so this ships with zero effect on local dev/testing — a
  deliberate choice so the fix could be verified without touching the existing workflow.
- Frontend half: `frontend/src/lib/access.js` captures a one-time `?token=...` URL param into
  `localStorage` and strips it from the visible address bar; `api.js`'s `analyze()`/`ask()` send
  it as the header. The owner shares the link once with the token in it; every visit after that
  (including old `#TICKER` bookmarks) keeps working silently.
- 5 new tests in `tests/test_access.py` (gate no-op when unset, wrong/missing token rejected,
  correct token passes, cap exhausted → 429, `/ask` gated too) using the same `TestClient`
  pattern as the existing endpoint smoke tests. Full suite: 34 passing (was 29).

Verified live: restarted the backend to pick up the change, confirmed `/health` and a
non-gated read still worked, and confirmed via the browser that the running app (no token set
in the local `.env`, matching intent) shows no behavior change at all.

**Mistakes / course-corrections in this pass:** none material. (One deliberate design call
worth recording: chose a single in-memory counter over a "real" rate-limiter library or
per-IP/per-user tracking — this is one free-tier process for one owner's personal app, and a
more elaborate system would be solving a problem this project doesn't have. If Trade Craft ever
becomes genuinely multi-tenant, this is the piece to revisit first.)

### 2026-09-15 — UI/UX, non-US news, and accessibility fixes (user-reported, one batch)

The user reported a punch list from actually using the app: metric text was nearly invisible,
the browser's own Back button didn't behave like a normal site, news felt US-only, the Feed/
What-it-means toggle looked unstyled, and the theme should go darker. Also asked to run "the
last part of Phase 3" in the same pass.

- **Invisible metric values.** `styles.css`'s `.metric`/`.metric .v` never set an explicit text
  color; since `.metric` is a `<button>`, it fell back to the browser's own default form-control
  color instead of inheriting the page's cream `--ink` — invisible against a dark card. Fixed
  with explicit colors plus `color-scheme: dark` on `:root` as a root-cause guard against the
  same class of bug recurring on a future unstyled control.
- **Browser Back/Forward didn't walk through tabs.** Read `App.jsx`'s router closely: it only
  ever pushed a history entry from `doResearch()` (ticker searches); clicking Comparison/
  Watchlist/History called `setView()` directly with zero history entry, so physical Back had
  nothing to return to from those tabs. Rewrote the router (`routeHash`/`parseRoute`/
  `goToView`) so every navigation — search or tab switch — pushes one entry, preserving the
  existing `#TICKER` shareable-link shape and adding `#/compare`/`#/watchlist`/`#/history` for
  tabs. Verified live with the browser's actual Back/Forward (not just clicking in-app links):
  Back from Watchlist → previous Research ticker; Forward → Watchlist again, correctly.
- **News broadened beyond Yahoo/SEC.** Added a keyless Google News RSS fallback
  (`services/news.py::_google_news`) in the chain: Finnhub → Google News → Yahoo. Searches by
  company name (passed through from `orchestrator._gather`'s `quote["name"]`) rather than the
  bare ticker, since ticker-only search reads as noise for most non-US symbols on Google News.
  Verified live on 7974.T (Nintendo): the feed now shows MarketWatch, BeInCrypto, Britannica,
  nintendo.com, and Anime News Network — genuinely diverse real-world coverage, not just
  Yahoo's own curated feed. 3 new tests in `tests/test_news.py`.
- **Feed / What-it-means toggle restyled.** Discovered `.newstabs`/`.ntab` had **no CSS rules
  at all** — they were rendering as completely unstyled default HTML buttons, which is exactly
  what the user's screenshot showed. Built a proper segmented-pill toggle matching the existing
  chart-toggle visual language (teal gradient active state).
- **Theme retinted near-black with a navy tint**, per explicit request (was a lighter deep
  navy from the 2026-09-15 rebrand). Since every component already consumed `--bg`/`--surface`/
  etc. as CSS variables rather than hardcoded hex, this was a `:root` token change, not a
  component-by-component rewrite — confirms the variable-based theming from the rebrand pass
  was the right call.
- **Accessibility — the "last part of Phase 3" this pass tackled.** While reviewing the theme
  change, found 10 tab-navigation links (Research/Compare/Watchlist/History's own
  "Comparison · Watchlist · History" links) were `<a>` tags with **no `href`** — the DOM spec
  doesn't make these focusable or Enter-activatable at all, so a keyboard or screen-reader user
  simply could not reach them. Converted all 10 to real `<button>`s (native keyboard support,
  no ARIA workaround needed) with `aria-current="page"` on the active tab; added a global
  `:focus-visible` ring; and fixed one input (`.cmp-pick`) that removed its focus outline with
  no replacement at all. Verified live with actual Tab-key presses and screenshots showing the
  teal focus ring landing on each tab in sequence.

Backend: 37 tests passing (was 34). Frontend: `npm run build` clean both before and after the
accessibility pass.

**Mistakes / course-corrections in this pass:** none in the shipped code, but one recorded
scope decision: the user's ask included "run the last part of Phase 3" alongside the fix list.
Practice lab is a genuinely new, non-trivial feature (a whole simulated trading UI/backend) —
building a rushed version of it in the same turn as five unrelated fixes risked exactly the
"half-finished implementation" this project's own conventions warn against. Treated
accessibility polish as the completable "last part" instead (it's explicitly a remaining Phase
3 item, and much of it naturally overlapped with the contrast/theme work already underway this
pass) and left the practice lab explicitly flagged as needing its own scoping conversation.

### 2026-09-15 — Practice Lab (last remaining Phase 3 feature)

Scoped with the user before writing code, since "an optional simulated practice lab" in the
backlog left real design decisions open. Three quick questions settled it: (1) a **combined**
hypothetical-trade-journal + simulated-portfolio — log a buy/sell with a reasoning note, track
a running cash balance and realized/unrealized P&L, not just a diary of entries; (2) its own
**new top-level tab**, matching how Watchlist/Compare were added; (3) **no AI involvement** —
fully deterministic, zero Claude spend, matching "reflection-focused" and the existing
Watchlist/Compare cost posture.

**Design decision made unprompted, and explained rather than silently applied:** a simulated
portfolio needs ONE cash balance, but trades can be logged against tickers priced in wildly
different currencies (JPY, KRW, EUR, …). Honestly converting between them would need a real FX
rate — a data source this app doesn't have — and fabricating one would violate the north-star
guardrail ("never fabricate"). Rather than build fake FX math, **scoped v1 to USD-priced
tickers only**, with a clear message if someone tries to log a non-USD trade. This is a
real limitation, not hidden — called out in `CLAUDE.md` and here.

**What was built:**
- `lib/practiceLab.js` (localStorage, mirrors `lib/watchlist.js`'s persistence pattern): a
  portfolio object `{ cash, positions, closed }` starting at $100,000. `buy()` always takes the
  ticker's real live price as an argument (never a user-typed number, so the exact-numbers
  guardrail holds even though the trade itself is hypothetical) and computes a running
  average cost basis per position. `sell()` realizes P&L against that average cost, updates
  cash, and appends a closed-trade journal entry carrying the user's own reasoning text.
- `components/PracticeLab.jsx`: portfolio summary (cash / positions value / total value / total
  P&L vs the $100,000 start), a buy form reusing the exact same name→symbol disambiguation
  picker as Compare's search slots, an open-positions list with an inline per-row sell form,
  and a chronological closed-trades journal showing entry → exit price, realized P&L, and the
  reasoning text. New `App.jsx` view `'practice'` (the router already generalized to `#/view`
  hashes in the earlier fix pass this session, so `#/practice` worked with zero router changes).
  Nav link added across Research/Compare/Watchlist/History/Welcome's rail.
- Framed explicitly as "simulated trades only · no real money · a decision journal, not advice"
  — consistent with the Watchlist precedent of never implying positions/signals are real.

**Verified live, end to end, with real numbers:** bought 10 AAPL at the live quoted $330.02 →
cash dropped from $100,000.00 to $96,699.80 (exactly 10 × $330.02); sold 5 at the same live
price → cash rose to $98,349.90 (exactly +5 × $330.02), the position correctly reduced to 5
shares, and the journal recorded "AAPL 5 sh · entry $330.02 → exit $330.02 · $0.00 (0.00%)"
with the typed reasoning text attached. Total portfolio value stayed exactly $100,000.00
throughout (as it should, since price never moved between the buy and sell) — confirming the
math is exact, not approximate.

**Mistakes / course-corrections in this pass:** none in the shipped code. One recorded
near-miss: the initial instinct was to let a "reset" button run with a plain click — added a
`window.confirm()` guard instead once it was clear an accidental click would silently destroy a
user's whole simulated history with no way back; this was caught before shipping, not after.

Frontend: `npm run build` clean (58 modules, was 56). Backend: unaffected (37 tests still
passing) — this is a purely client-side feature with no new endpoints.

With this, **Phase 3 is feature-complete** except non-US peers (deferred to the paid tier) and
desktop packaging (deliberately parked, see §13 of `docs/HANDOVER.md`).

### What's left, now that Phase 3 is feature-complete

Only things that need the user's own action, or are deliberately deferred/parked, remain:
- **Deploy go-live** — needs the user's own host-account signup (Render or similar); code side
  is ready (`docs/DEPLOY.md`).
- **Pre-share step** — the code guard (`services/access.py`) is done; the user still needs to
  set `TRADE101_ACCESS_TOKEN` on the host before ever sharing a live link.
- **Non-US peers** and the **paid Firecrawl/Exa tier** — deliberately deferred until after
  deployment, per the user's earlier call.
- **Desktop packaging** — parked (§13, `docs/HANDOVER.md`); the web deploy already gives the
  shareable link that was the actual goal.
- A broader accessibility pass (modal keyboard-trap review, full contrast audit, mobile layout)
  remains open beyond the 2026-09-15 fixes, but is no longer a Phase 3 blocker.

---

## Audit — critical review, and Waves 0 & 1 (2026-09-16/17)

**The trigger.** With Phase 3 feature-complete, the user asked for an adversarial, no-flattery
review of the whole app — "product critic / systems analyst / solution architect / red-teamer" —
to find the real functional, logical, and executional flaws before treating it as done, plus a
critique (not yet a rebuild) of the UI/UX. Full detail: `docs/AUDIT.md`.

**What the audit found.** Read the entire codebase and reproduced findings by running the code,
not just reading it. Three were worse than "unfinished": (1) market cap rendered with a
hardcoded `$` regardless of the listing's actual currency, so Nintendo's cap read as `$9.36T` —
larger than Apple's real `$4.81T` — a false number breaking the app's own "numbers are exact"
guardrail, on screen, silently; (2) `above_sma50/200` collapsed "the average isn't available" and
"price is below the average" into the same `False`, and that false reached the analysis agent as
exact data; (3) a completed Phase 3 branch (including the pre-share access guard) was sitting
unmerged and unpushed in a stray git worktree — the project's own status docs said the fix was
still outstanding while git said it had been written, i.e. the memory contradicted itself. Also
confirmed, by reproducing them: the "Sony" search bug (typing the company name silently opened
the NYSE ADR because the name equals its own ticker), the news panel depending entirely on the
paid `/analyze` call, the chart being torn down and rebuilt on every keystroke, and a pattern
detector that could return at most one reversal shape from only the last 3 swings.

**Wave 0 (critical fixes, 2026-09-16).** Currency-correct market cap; tri-state SMA flags with
both agent prompts taught to read `null` as unknown (regression test added); a React error
boundary (`ErrorBoundary.jsx`) so a render crash no longer white-screens the whole app; fixed a
`href="#"` news-link bug that mutated the hash router and could bounce the user back to Welcome.
The stranded-branch finding (C3) turned out to have *already* been merged via GitHub PR #2 in a
parallel session between the audit being written and the fix session starting — this session's
`master` was simply one commit behind and needed a routine `git merge`, which surfaced one
conflict in `CLAUDE.md`'s own status text (resolved in favor of the newer, accurate "shipped"
wording, with the audit doc linked in).

**Wave 1 (the four flaws the user named, 2026-09-17).** Search: `App.jsx` no longer auto-picks
on a name/ticker collision (`looksLikeTicker()` — only a genuinely ticker-shaped, unambiguous
query skips the picker), and `services/search.py` now scores/ranks candidates by listing quality
(OTC/CDR/preferred/secondary-dealer lines demoted and badged) instead of passing Yahoo's raw,
unranked order straight through. News: a new free `GET /news/{ticker}` endpoint decouples the
Feed tab from the paid `/analyze` call entirely — headlines now render immediately regardless of
Claude-key/error/daily-cap state, sharing one cached data bundle with `/analyze` so nothing is
fetched twice. Chart: `PriceChart.jsx` rewritten from one effect that destroyed and rebuilt the
whole chart on any prop change into three independent effects (chart lifecycle / price data /
pattern overlay), so the chart survives re-renders and only re-fits its view on a genuinely new
dataset — zoom/pan now survive the 7-min auto-refresh. Patterns: `services/patterns.py`
rewritten to scan the whole series (not just the last 3 swings) built from High/Low (not Close),
with real per-match confidence instead of a fixed string, found **11 distinct patterns on a real
NVDA/1Y series** where the old code could return at most 2. Also de-personalized the Welcome
greeting and moved the SEC EDGAR contact email out of committed source into an env var. 12 new
backend tests added across the four areas; every fix was verified against the live app, not just
unit tests, using the browser tooling — including screenshotting the picker's new OTC/CDR badges
and the pattern overlay markers landing precisely on the candle wicks.

**Mistakes / course-corrections in this pass** (an honest accounting, not a highlight reel):
- Added a new `orchestrator.news(ticker)` function that **shadowed the already-imported
  `services.news` module** at module scope inside `orchestrator.py` — every call inside
  `_gather()` to `news.get_news(...)` would have broken at runtime the moment that function was
  defined, a real bug in the shipped-looking code, not just a test artifact. Caught immediately
  by the new endpoint's own test suite (`AttributeError: <function news> has no attribute
  'get_news'`) before it ever reached the running app; fixed by renaming the function to
  `news_bundle`. The lesson, already true of Python in general: never name a module-level
  function the same as an imported module it needs to keep using.
- Discovered mid-session that the app the user had been running locally — before and during this
  session — was being served from a **stray leftover git worktree**
  (`.claude/worktrees/execution-review-final-tasks-1f86c4`, on an unrelated branch), not from
  this repo. Both the frontend (Vite) and one backend process were launched from that worktree's
  own copy of the code, meaning none of this session's fixes (or, potentially, other recent work)
  were visible in the browser the user was actually looking at until it was found and killed.
  Caught by checking `above_sma200` against the live server and getting the pre-fix answer back
  after the fix had already landed and been tested — i.e. by not trusting "the change is
  committed" as proof the running app reflects it, and checking the live behavior directly
  instead. Lesson carried forward: after any restart, verify the *served* behavior, not just that
  a process is listening on the expected port.
- Windows left a **genuinely orphaned listening socket on port 8000** after a forced process
  kill — `netstat`/`Get-NetTCPConnection` kept reporting a PID as bound, but no process-listing
  tool (`Get-Process`, `taskkill`) could find that PID to kill it, and it didn't clear after 40+
  seconds of waiting. Did not attempt a Winsock-level fix (out of scope for an app-level session,
  and system-network changes are off-limits regardless). Worked around it with a fallback port
  (8001) and a local-only `VITE_API_BASE` override in `frontend/.env.local` (gitignored) rather
  than hardcoding the workaround into committed source. Documented in `CLAUDE.md` → Gotchas in
  case it recurs.

Frontend: `npm run build` clean throughout. Backend: 48/48 tests passing (was 37 at the start of
Wave 0). **Remaining audit work** (per `docs/AUDIT.md` §10): Wave 2 (cache the analysis result,
an Anthropic client timeout, then deploy) and Wave 3 (chart indicator overlays via a
`lightweight-charts` v5 upgrade, and the UI/UX redesign the user asked to review before it's
built) — neither started yet.

**Addendum, same day: the H6 pattern-detector fix was declared done and verified, and wasn't.**
The user tried it and reported patterns barely worked at all — nothing on any timeframe except
1Y, and even 1Y showed a months-old pattern instead of a recent one. Both were real, and both
were self-inflicted by the rewrite, not pre-existing: (1) the new `_has_real_dip`/`_sim` checks
used fixed 4%/2% tolerances copied from the original module constants — reasonable for a full
year of daily bars, but those constants had never been checked against a 5-day/15-minute or
1-day/5-minute window, where the ENTIRE session might only move 1-6% — so the "must clear a real
2% dip" check rejected every genuine intraday pattern, unconditionally, on every ticker tried
(confirmed empirically: median bar-to-bar move was 0.086% on NVDA 5D/15m vs. 0.774% on AAPL
1Y/1d — an order of magnitude apart, one fixed threshold cannot serve both). (2) the new
full-series scan (the actual H6 fix) can legitimately find a real pattern from eight months ago
alongside one from last week, and the code never sorted the results — the UI picks index 0 as
the default tab, so whichever pattern happened to be *discovered* first (chronologically
earliest, since the scan walks forward through time) won the default slot, not whichever was
most *relevant*. The lesson: "the new tests pass and I verified once against real data" is not
the same as "I checked the fix across the actual range of conditions it needs to handle" — the
verification that shipped with H6 tested exactly one timeframe (1Y) against exactly the
condition the audit's finding described, and never tried the other four timeframes the feature
is supposed to work on. Fixed by deriving tolerances from each series' own volatility
(`patterns.py::_scale()`) instead of a fixed constant, and sorting `detect()`'s output
most-recent-first. 6 regression tests added (2 replacing the informal manual check), verified
live across all 5 timeframes this time, not just one.
