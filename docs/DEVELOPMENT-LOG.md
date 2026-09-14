# Trade101 — Development Log (phase by phase)

The story of how Trade101 was built, in order: how the idea was broken down and visualised,
what each phase executed, the inputs/suggestions that shaped it, and — honestly — the mistakes
made and how they were corrected.

**This file is updated after every phase completes** (hard rule; see `CLAUDE.md` → Memory
protocol). It is the narrative "how we got here" companion to:
- `CLAUDE.md` — concise current-state reference (auto-loaded each session)
- `BACKLOG.md` — the live feature/bug checklist
- `docs/HANDOVER.md` — the full, detailed technical handover (deep detail lives there)
- `docs/trade101-phase-2-recommendations.md` — the 2026-09-10 product/technical review

Local app while in development: **http://127.0.0.1:5173** (two dev servers — see `CLAUDE.md` →
Run). A shareable/deployed URL is planned *after* the full build (see `BACKLOG.md`).

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
