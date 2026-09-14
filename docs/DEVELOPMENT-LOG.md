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

---

## Phase 2 — depth _(not started)_

Planned: Ask-Claude chat over the research bundle; Comparison tab; deeper non-US sourcing
(Firecrawl/alternative — provider slot already pluggable); richer pattern library + teaching
replay; the real data-cube logo; **deploy a shareable/public URL** so the app is checkable from
any device. See `BACKLOG.md` for the full list.

**Mistakes / course-corrections:** _(to be recorded when Phase 2 begins.)_
