# Trade101 — Full Project Handover

A faithful, detailed record of the entire conversation and build that produced Trade101, written so a new chat (or a new person) can pick up with full context. It captures every topic discussed, every decision, every round of feedback, and what was delivered.

- **Repo:** https://github.com/pranavlakshminarayan/trade101 (public)
- **Local:** `C:\Users\prana\Documents\Claude Code\Trading idea`
- **Status (2026-09-12):** MVP complete (Milestones 0–5) and pushed to GitHub.
- **User:** Pranav (student, beginning trader; trades on Moomoo; workspace.sonic@gmail.com). GitHub: pranavlakshminarayan.

---

## 0. The through-line (what the whole chat was about)

The conversation moved through three phases, all in one session:

1. **Integrating Yahoo Finance into Claude** → a local MCP connector.
2. **A Wall-Street-style AAPL September-event study** → a published analysis dashboard.
3. **Building Trade101** → the personal stock research + learning web app (this repo).

The consistent guardrail throughout: **the tool describes/teaches; it never gives buy/sell advice.** Numbers are exact (deterministic code); every AI opinion is source-backed; when a source is unreachable, say so rather than fabricate.

---

## 1. Phase 1 — Yahoo Finance MCP connector

**User asked:** "Can I integrate Yahoo Finance into Claude?" Then: build a Claude Code MCP and integrate Yahoo Finance, to use as a live connector.

**What we built** (in a *separate* folder `C:\Users\prana\Documents\Claude Code\yfinance-mcp`, not this repo):
- `server.py` wrapping the `yfinance` library as MCP tools: `get_quote`, `get_history`, `get_financials`, `compare_tickers`.
- Isolated `.venv`. Key gotcha discovered: installed `mcp` **2.x**, where `FastMCP` was renamed — use `from mcp.server.mcpserver import MCPServer` (NOT the old `FastMCP`). The `.tool()` decorator and `.run()` are unchanged.
- Verified live (pulled real MSFT/AAPL data).
- **Registered** for Claude Code: `claude mcp add -s user yfinance -- <venv python> <server.py>` (user scope → available in all projects). Confirmed `✔ Connected`.
- The `claude` CLI was not on PowerShell PATH; it lives at `C:\Users\prana\.local\bin\claude.exe`.
- Discussed all three "surfaces": (1) Claude Code (done), (2) **Claude Desktop** via a `.mcpb` Desktop Extension (built `dist/yfinance.mcpb`, manifest_version 0.3, points at the venv python), (3) **claude.ai web** via a remote HTTP server (`server.py` made dual-mode: stdio default, `MCP_TRANSPORT=http` serves `streamable_http_app()` via uvicorn) — needs public hosting the user does themselves.

---

## 2. Phase 2 — AAPL September-event study (Wall Street trader)

**User asked:** use the Yahoo Finance integration; act as a Wall Street trader; research AAPL around Apple's September keynote over the last 4 years — drivers before/after the event, trends/stats, average fluctuations, RSI/bullish metrics at each launch, how long it stays in profit and when it dips.

**What we did:**
- Pulled the live AAPL quote through the MCP connector, then ran the heavy study with a Python script on the same `yfinance` engine (avoiding dumping thousands of bars into context).
- Studied the four September keynotes (iPhone 14/15/16/17, 2022–2025): pre-event run-up, event-day reaction, T+1…T+30 returns, RSI(14), SMA50/200, volatility, peak/dip timing.
- Key findings: it's a **"sell-the-news"** event — muted event-day (avg −0.56%), reliable day-after dip (avg −1.43%), recovery building to ~+6.6% peak around session 21, +2.45% by T+30. RSI entering the event averaged ~48.6 (neutral, NOT overbought — myth-busted). Trend (above 200-DMA) mattered more than RSI.
- Built and **published an interactive Artifact dashboard** (trading-desk style, dark, validated palette): https://claude.ai/code/artifact/8123b4b3-88db-495b-80f1-5bfe7530b5bb

**Follow-up asks & additions:**
- **Cross-validate stock vs product sales.** Honest data reality: Yahoo has no unit sales; Apple stopped reporting iPhone units in 2018 — used **iPhone-segment revenue** for the December launch quarter (fiscal Q1) from SEC 8-Ks. Finding: extremes agree (iPhone 14 weak sales + weak stock; iPhone 17 record sales +23% + strong stock), but the middle inverts — the stock trades the *anticipated demand narrative*, not the phone (which reports months later). Added a "Sales vs Stock" panel.
- **September-only analysis.** iPhone-quarter revenue rose every year (steady) while the September stock move swung −12.5% to +10.8% — showing the month's stock is decoupled from actual sales (macro + anticipation). Added a "September in isolation" panel.

---

## 3. Phase 3 — Building Trade101 (this repo)

### 3.1 The idea (user's vision)
A personal stock research **and learning** app. Type a company, get everything assembled: live chart, indicators explained *in context*, chart patterns, AI momentum read (describe, not advise), news + inference, an ecosystem chain, and a history of searches. Zerodha-clean but a notch more pro than Moomoo (which has too many buttons). Chrome-style tabs (Research / Comparison / History). Hands-on learning tool — the point is to **extract data and make sense of it**, not just read labels.

### 3.2 Brainstorm → decisions (via the brainstorming skill + a visual-companion mockup server)
Design was iterated as live HTML mockups (v1→v5). Locked decisions:
- **Architecture: hybrid** — deterministic services for exact numbers (prices, indicators, storage) + specialist **agents** for judgment (research/analysis), coordinated by an orchestrator. Reason: numbers can't be hallucinated; reasoning is sourced. (User confirmed: "a mix of agents and LLM is good… I do not want to hallucinate the numbers.")
- **Agents do judgment; deterministic tools do the mechanical scraping/fetching** (efficient — the LLM never parses raw HTML).
- **Stack: FastAPI (Python) backend + React (Vite) frontend**, Lightweight-Charts for the chart. (Chosen over all-Python/NiceGUI and desktop/Tauri.)
- **Markets:** US, China, Japan, S.Korea, Hong Kong, Singapore, India (+ Europe). Search by **company name**, disambiguate if multiple.
- **Brand: Trade101.** Logo = an isometric data-cube (2×2 panels: blue bar-chart + green candlesticks, "1" and "0" = "10"; teal/olive faceted sides) — described in detail; placeholder SVG in the app for now; real logo is Phase 2 (needs an OpenRouter key). Palette: dark fintech (NOT white), derived from the logo — ground `#0E1A26`, teal `#34A9BE` (interactive), green `#00D68F` (up), red `#F0616D` (down).
- **UI:** Gemini/Claude-style Welcome page → Research view. Standard trader metric symbols (RSI(14), MACD(12,26,9), SMA50/200 — no emoji). Flexible/flowing layout (no rigid boxes). News with a "What it means" inference tab. References box listing every source. "Ask Claude" chat reserved for Phase 2.
- **Phasing:** Phase 1 MVP = single-stock Research view; Phase 2 = richer patterns, ecosystem depth, Ask-Claude chat, more markets/Firecrawl; Phase 3 = Comparison tab, desktop packaging.
- Spec written to `docs/superpowers/specs/2026-09-09-trade101-design.md`; plan to `docs/superpowers/plans/2026-09-09-trade101-implementation-plan.md`; running backlog in `BACKLOG.md`.

### 3.3 Build milestones (each committed)
- **M0 Scaffold** — git, `.gitignore` (ignores `.env`, `.venv`, `.superpowers`, `data`), `.env.example` with named keys, backend/frontend skeletons.
- **M1 Real-time core** — `services/marketdata.py` (yfinance, any ticker/market), `services/indicators.py` (RSI/MACD/SMA/EMA/Bollinger — pure pandas, exact, unit-tested), `GET /research/{ticker}`. Verified live on NVDA/MSFT/RELIANCE.NS + 404 on bad ticker. **Nothing hardcoded to NVDA.**
- **M2 Frontend** — Welcome + Research view, live candlestick+volume chart, real indicators, click-to-learn lessons, dark Trade101 palette. Verified end-to-end.
- **M3 AI narration** — `services/news.py` (Finnhub company news + SEC EDGAR filings, pluggable via `TRADE101_NEWS_PROVIDER`), `agents/llm.py` (Claude API), `agents/analysis.py` (the sense-making engine — synthesizes signals, sourced, no buy/sell), `agents/orchestrator.py`, citation guard, `GET /analyze/{ticker}` (separate from /research so the chart never blocks on AI; degrades gracefully with no key). Frontend AiRead + NewsPanel (Feed / What it means). `.env` loaded via python-dotenv.
- **M4 Patterns + Ecosystem** — `services/patterns.py` (head&shoulders ±, triple/double top&bottom via scipy extrema; labeled points, neckline, rich educational explanations), `GET /patterns` (any timeframe); on-chart amber overlay + selector (one pattern at a time). `services/company.py` + `GET /ecosystem` (sector, industry, beta with a "what beta means" note, market cap, Finnhub peers as clickable chips). History tab (localStorage, 2-line AI takeaway per search, clickable to reopen).
- **M5 Tests + resilience** — 16 passing tests (indicators, patterns, endpoint smoke). Graceful degradation everywhere (bad ticker, no key, source down, AI timeout — chart always renders).

### 3.4 Feedback rounds during the build (user asks → delivered)
- Real-time & ticker-agnostic (confirmed; not NVDA-specific).
- **Name → ticker** search with a disambiguation picker (works for any market — allianz→ALV.DE, samsung→005930.KS, etc.); removed the "needs a suffix" copy.
- **Flexible layout** → ended as a **self-balancing JS masonry**: measures each block's height and sends flow blocks (metrics/news/ecosystem/references) to the shorter column, so both columns stay even and scrolling is minimized. AI read anchors one column.
- **News as boxed cards** (Google-News style, darker contrast); **references as descriptive links** (headline/filing, not repeated "Yahoo").
- **Chart:** Candles ↔ Line toggle; timeframes **1Y · 1M · 10D · 5D · 1D (intraday)**; line color follows direction (green up / red down over the window); auto-refresh every 7 min.
- **Patterns:** one at a time via ▲/▼ selector; richer explanations (meaning + momentum inference + what traders typically do + caveat); apply across all chart tabs.
- **Loading widget** (spinner + "Scraping & analysing…") while the AI runs.
- **Browser back/forward + `#TICKER` shareable links** (History API) — so a link sent to a friend opens on that stock.
- **Model switched to Sonnet** (`claude-sonnet-5`) to cut cost (override via `TRADE101_MODEL`).
- **History tab** completed (list + 2-line inference + reopen + clear).

### 3.5 The finale — GitHub
- Comprehensive README (setup + run for backend & frontend, `.env`, the PowerShell npm execution-policy note).
- Safety-checked: only `.env.example` tracked, no real keys anywhere in history.
- `gh repo create trade101 --public --source=. --push` → live at the repo URL. 12 commits, 42 files, branch `master`.

---

## 4. Current state & how to run

See `README.md`. Two terminals: backend `uvicorn app:app --reload --port 8000` (from `backend/`, via the venv python), frontend `npm run dev` (from `frontend/`). Open `http://127.0.0.1:5173`. Add `TRADE101_ANALYSIS_KEY` (Claude) + `TRADE101_NEWS_KEY` (free Finnhub) to a root `.env` for the AI/news. Tests: `pytest -q` in `backend/`.

**Gotchas learned:**
- PowerShell blocks `npm` ("running scripts disabled") → use `npm.cmd run dev` or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Vite/backend pinned to `127.0.0.1` (IPv6 `::1` binding caused connection issues); API base is `http://127.0.0.1:8000`.
- Kill stray servers holding ports 8000/5173 before restarting (WinError 10013 = port in use).
- Each `/analyze` call spends the user's Claude key — be sparing in testing.

---

## 4.1 Known problems carried out of Phase 1

Found during a live end-to-end run on **7974.T (Nintendo, Tokyo)** on 2026-09-12 — a
deliberately non-US ticker, which is where all four of these surface. They are **still
present in the code**; a fix was written and then discarded, so Phase 2 starts with them open.

**1. The Finnhub API key leaks into the browser. (Security — fix first.)**
`services/news.py` catches provider exceptions and returns `f"News provider error: {e}"`
straight to the client. httpx puts the **full request URL** in its exception text, and that
URL carries `token=<your Finnhub key>`. So on any request that errors, the key is rendered
into the news panel and sits in the `/analyze` JSON payload in the browser. Non-US symbols
hit this on *every* search (see #2), so it is not an edge case.
*Fix:* redact `token=` / `apikey=` / `key=` params and any configured key value from provider
error text before it leaves the backend; same treatment for the EDGAR error path. Assume the
current key is compromised if the app was ever opened where someone could see the screen —
rotate it.

**2. Non-US listings get no news at all.**
Finnhub's free tier returns **403 Forbidden** for company news on non-US symbols. The app
degrades honestly (the AI says it had no headlines and infers nothing — the guardrail works),
but it means the whole news half of the product is US-only right now. This is the free tier's
limit, not a defect, and it is exactly what the Phase 2 "deeper non-US sourcing (Firecrawl)"
item is for.

**3. Ecosystem is thin outside the US.**
For 7974.T, `beta` came back `null` and `peers` came back `[]` — yfinance had no beta for the
symbol and Finnhub's peers endpoint is US-only. Sector, industry, market cap and summary all
populated fine. The panel currently just shows the gaps rather than explaining them.

**4. Raw provider errors are shown as user-facing copy.**
Even setting the key leak aside, what the user sees on a failure is a raw exception string
with a URL in it. It should be a plain sentence explaining what happened and what it means
for the read.

**5. Minor:** `services/news.py` uses `datetime.utcnow()`, deprecated in 3.12 (warning in the
test run). Use a timezone-aware `datetime.now(datetime.UTC)`.

**Not problems, for the record:** pattern detection returning `none` on 7974.T is correct
behaviour (it declines rather than forcing a shape); the unknown-ticker 404, the no-API-key
degrade, and the name→ticker search across markets all worked as designed.

---

## 4.2 Phase 1 flaw pass — 2026-09-14

Cleared four of the five §4.1 items. Approach for the security fix was defense-in-depth:
stop the leak at the source *and* add a scrubber at the API boundary, so a future code path
that forgets can't re-open the hole.

- **Key leak (§4.1 #1) — fixed.** `services/news.py` no longer does `return [], f"...{e}"`;
  both the Finnhub and EDGAR error paths now return fixed, credential-free strings, and a
  Finnhub 401/403 (the non-US case) returns its own plain message without ever formatting the
  response. New `services/safe.py::redact_secrets()` masks `token=`/`apikey=`/`key=` params and
  any configured key value; `app.py` runs the `/analyze` generic-exception `reason` through it.
  New `tests/test_safe.py` (4 tests) asserts a planted key never survives into a note or reason.
  **Still on the user: rotate the Finnhub key** — the fix stops future leaks but can't un-expose
  a value already shown on screen.
- **Raw errors as copy (§4.1 #4) — fixed** by the same friendly-message change.
- **Ecosystem gaps (§4.1 #3) — fixed (explanation, not new data).** `services/company.py` now
  returns a `coverage` map keyed `beta`/`peers` with a plain reason when each is missing (non-US
  vs generic); `frontend/.../Ecosystem.jsx` renders the peers explanation instead of hiding the
  block. Real non-US beta/peers data is still a data-source problem for later.
- **`datetime.utcnow()` (§4.1 #5) — fixed**, timezone-aware now; the deprecation warning is gone
  from the test run.
- **Non-US news (§4.1 #2) — still open by design.** Message is friendlier; the actual fix is the
  Phase 2 Firecrawl/alternative sourcing (provider slot already pluggable).

Tests: 20 passing (was 16). Next planned work is **Phase 1.5 — trust and coherence**
(see `BACKLOG.md` and `docs/trade101-phase-2-recommendations.md`) ahead of Phase 2 features.

---

## 4.3 Phase 1.5 — trust & coherence (in progress, from 2026-09-14)

User chose to do Phase 1.5 before Phase 2 features. Started with the guardrail item, because
"unrelated articles leaking into the AI narrative" is really a violation of the north star
("every AI claim is sourced" / "make sense of data, not read labels"), not a cosmetic bug.

**Evidence pipeline — done.** New `services/evidence.py` is a *deterministic* relevance filter
(the review was explicit that this is a data-validation job, not a reason to add AI calls). It
tokenises the company name (dropping corporate filler like Inc/Corp/Ltd), the ticker (base,
suffix-stripped so `7974.T` matches "Nintendo"/"7974"), sector/industry, and peer names, then
classifies each article as company / related / sector / irrelevant and drops the irrelevant
ones. `orchestrator.analyze` now also fetches the company profile (for sector/peers), filters
the news through this before `analysis.run`, and only the admitted items reach the model, the
feed, and the references list. A `sourcing` report ({kept, dropped, has_company_news, counts})
rides along in the `/analyze` response.

**Claim-level honesty — done.** `analysis.py` SYSTEM now requires a Fact/Interpretation/Unknown
`type` on every evidence point and forbids a company-catalyst claim when `has_company_news` is
false; `_citation_guard` normalises the type and still drops unsourced points. `AiRead.jsx`
renders a coloured badge per claim plus a "N unrelated articles filtered out" line.

**Also done:** `tests/test_evidence.py` (6 tests, incl. the "feed it junk, assert it's dropped"
cases the review asked for); confirmed no API key reaches the frontend (no `VITE_`/key refs,
no frontend `.env`).

Tests now 26 passing.

**Remaining Phase 1.5:** timeframe integrity (shared as-of label; indicators computed for the
selected timeframe, not always daily), coverage-truthfulness badges (extend the `coverage` map
`company.get_profile` already returns), a cache abstraction (in-memory/SQLite), and a visible
not-financial-advice notice next to the narrative.

---

## 5. What's next — Phase 2 (from `BACKLOG.md`)
- **Ask Claude** chat over the research bundle (seam reserved).
- **Comparison tab** (two stocks side by side).
- Deeper non-US sourcing (**Firecrawl** or alternative) — the news provider is already pluggable (`TRADE101_NEWS_PROVIDER`).
- Richer pattern library + step-by-step teaching replay; the real data-cube **logo**; desktop packaging; broader premium sourcing (Exa, etc.).
- North-star reminder: **extract and make sense of data; teach understanding; never advise.**
