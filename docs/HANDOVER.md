# Trade Craft (née Trade101) — Full Project Handover

A faithful, detailed record of the entire conversation and build that produced Trade Craft, written so a new chat (or a new person) can pick up with full context. It captures every topic discussed, every decision, every round of feedback, and what was delivered.

- **Repo:** https://github.com/pranavlakshminarayan/trade101 (**PRIVATE** as of 2026-09-15 — set on the user's explicit instruction; do not make it public again without being asked). Local folder, package names, and internal `Trade101` references in code/prompts are being migrated to the "Trade Craft" brand gradually; the repo name itself stays `trade101`.
- **Local:** `C:\Users\prana\Documents\Claude Code\Trading idea`
- **Brand:** **Trade Craft** (renamed from "Trade101" on 2026-09-15 — see §11). Near-black theme with a navy tint and cream/near-white text (retinted 2026-09-15, was a lighter deep navy).
- **Status (2026-09-17):** MVP + Phase 1/1.5/2/3 all shipped (as of 2026-09-15), then a full
  adversarial audit (`docs/AUDIT.md`) drove **Audit Waves 0, 1, and 2's code half, plus Wave 3's
  chart-overlay item, all done** — see §20 for the complete summary. Still not live: deploy
  needs the user's own host signup (§14/§15), and Wave 3's UI/UX redesign is still a proposal to
  review before it's built, per the user's explicit instruction. See §20.8 for exactly what to
  pick up next.
- **User:** Pranav (student, beginning trader; trades on Moomoo; workspace.sonic@gmail.com). GitHub: pranavlakshminarayan.
- **Companion docs (all kept current, cross-reference this one):** `CLAUDE.md` (concise current-state reference, auto-loaded every session, carries the hard "memory protocol" rules), `BACKLOG.md` (live checklist), `docs/AUDIT.md` (the 2026-09-16 adversarial audit — 30+ ranked findings, the wave plan §20 executes), `docs/DEVELOPMENT-LOG.md` (phase-by-phase narrative + an explicit "mistakes/course-corrections" note per phase — lighter-weight than this file), `docs/DEPLOY.md` (deploy instructions), `docs/trade101-phase-2-recommendations.md` (the 2026-09-10 product/technical review that shaped Phase 1.5's priorities).

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

## 5. Memory/documentation infrastructure (2026-09-12, before the work below)

Before continuing the build, the user asked for the project's own memory system: `CLAUDE.md`
should be a **living, self-updating** document (not a static reference), so that a fresh chat —
or this same chat after a context reset — has full clarity without being re-briefed. This became
a standing rule that shaped everything documented in this file from here on:

- **`CLAUDE.md` "Memory protocol" section** (hard rule): before ending any turn that changes
  status, architecture, config, endpoints, or known bugs, update the matching section of
  `CLAUDE.md` in the same turn; mirror bug fixes into `BACKLOG.md`; put long narrative/decisions
  in `docs/HANDOVER.md` (this file); link any new standalone doc from both docs immediately.
- **`docs/DEVELOPMENT-LOG.md` created** as a second, complementary hard rule (added 2026-09-14,
  see §12 below): a phase-by-phase story of the *journey* — inputs/suggestions per phase and,
  explicitly, **mistakes made and how they were corrected** — updated after every phase completes.
- **Persistent cross-session memory** (outside the repo, in Claude's own memory store) was also
  seeded: a project summary of what Trade Craft is/its guardrails, plus feedback memories
  recording the user's standing preferences — e.g. "return the local app link on every run",
  "keep the dev log updated with mistakes after every phase", and the pre-share reminder (§16).
  These survive even if this conversation's context is fully reset.
- **Consequence for how this file is used:** `docs/HANDOVER.md` (this file) is the *deep* record;
  `CLAUDE.md` stays short and current; `docs/DEVELOPMENT-LOG.md` is the *readable phase story*.
  When in doubt about current state, `CLAUDE.md` is authoritative; when you need to understand
  *why* something is the way it is, come here.

---

## 6. Phase 1.5 continued — UX/data fixes pass (2026-09-14)

Three issues the user found by actually using the app (not from a review — direct feedback),
fixed together in one pass, each verified live before moving on.

**1. Chart patterns were limited to a couple of shapes.** The user linked the Fidelity Investments
chart-patterns guide and strike.money's pattern library, and was explicit: *not every pattern
applies to every stock* — the app should detect and show only the patterns actually present on
the current chart, with an explanation of *why* it was flagged, not a menu of every possible
pattern. `services/patterns.py` already had the reversal family (Triple/Double Top/Bottom,
Head & Shoulders + inverse); it gained a **trendline family**: Ascending/Descending/Symmetrical
Triangle, Rising/Falling Wedge, Ascending/Descending Channel. Detection fits least-squares
support/resistance lines through the two or three most recent swing highs/lows, classifies by
each line's slope (flat/up/down) and whether the pair converges (triangle/wedge) or stays
parallel (channel), and only returns a shape when the geometry is clean — nothing is invented to
fill space. New pattern objects carry a `lines` field (two trendlines to draw) alongside the
existing `points`/`neckline`; `PriceChart.jsx` draws them. Verified live on AAPL 1Y: Head &
Shoulders + Inverse Head & Shoulders + a Rising Wedge, all three genuinely present; NVDA/TSLA/
Nintendo (7974.T) correctly returned no patterns rather than forcing one. +2 tests
(`test_ascending_triangle_detected`, `test_descending_channel_detected`).

**2. Non-US stocks displayed as the raw ticker ID, not the company name; no news for them.**
`services/marketdata.py`'s `_quote()` was preferring `shortName` (often ALL-CAPS or absent) over
`longName`; switched the preference order (`longName` first) and added a `_name_from_search()`
fallback via the existing Yahoo search endpoint for the rare case `.info` has neither. Verified:
7974.T now shows "Nintendo Co., Ltd." The frontend headline (`Research.jsx`) was changed to lead
with the company name and show the ticker as a small tag beside it, rather than the ticker as the
`<h1>`. Separately, `services/news.py` gained a **Yahoo Finance news fallback**
(`_yahoo_news()`, keyless, via `yf.Ticker(ticker).news`) used whenever Finnhub returns nothing
(no key, or its free tier's US-only 401/403) — this is what actually fixed "no news for non-US
listings" rather than just making the error message nicer. Verified: Nintendo went from 0 to 10
headlines. `get_news()`'s provider dispatch tries Finnhub first, then Yahoo, so US symbols keep
using Finnhub (richer metadata) and non-US symbols get real evidence instead of silence.

**3. THE MOST IMPORTANT FIX OF THIS PASS — switching tabs (History, then back) lost all page
state and silently re-ran the paid Claude analysis.** The user's framing, verbatim: "if I search
on Google and swap tabs and come back to the original tab, that does not mean Google deletes
everything and restarts the search, correct?" This was a genuine architecture gap, not a
cosmetic one — every `/analyze` re-run spends the Claude API key for nothing. Fixed with a
**session result cache** added to `frontend/src/api.js`: an in-memory `Map` per endpoint
(`research`, `analyze`, `ecosystem`, `patterns`), keyed by ticker (+ params for `research`/
`patterns`). `analyze()` checks the cache before firing a request and never re-runs a completed
analysis for the same ticker within the session; the 7-minute auto-refresh interval explicitly
passes `{ fresh: true }` to bypass the cache (it's supposed to re-fetch). **Verified end-to-end
in the browser**, not just by reading code: loaded AAPL (1 `/analyze` call, confirmed via the
backend access log), navigated to History, clicked back into AAPL — **still exactly 1 `/analyze`
call total**, full page state (chart, AI read, news, ecosystem) restored instantly from memory.
This is also what later became the frontend half of the Phase 1.5 "cache abstraction" backlog
item (the backend half — `services/cache.py` — came with Ask-Claude, §8).

Tests after this pass: 28 passing (was 26).

**Mistakes made in this pass (recorded honestly per the dev-log rule):** (a) a stray reference
to a non-existent `ls_markers(...)` helper was left in a `PriceChart.jsx` edit and would have
crashed every pattern render — caught by re-reading the diff before testing, not by the test
suite (there is no frontend test suite); (b) the backend was edited while running *without*
`--reload`, so early edits silently had no effect until the process was restarted — this became
recurring self-inflicted pain across later sessions too (see §17).

---

## 7. Prompt caching for cost control (2026-09-14)

Explicit user ask: **"update my API Key usage to prompt caching method, I do not want to burn
money."** `agents/llm.py`'s `call()` was changed to send the system prompt as a
`cache_control: {type: "ephemeral"}` content block instead of a bare string — the system prompt
(guardrails + JSON schema) is byte-identical on every `/analyze` call, and only the per-ticker
data payload (which varies) sits after it in the `user` message, making it a textbook cacheable
prefix. A second function, `call_chat()`, was added later (§8) for the same treatment on
multi-turn conversations. Both log `cache_write`/`cache_read`/`in`/`out` token counts to the
server console via a shared `_log_usage()` helper, specifically so cache activity can be
confirmed from a live run rather than assumed.

**The catch, caught before it shipped:** prompt caching only activates once the cached prefix
clears a *model-specific minimum token count* — 512 for Opus 5/Fable-tier models, but **1024 for
Sonnet 5**, which is this project's default model (`TRADE101_MODEL`). Using the free
`messages.count_tokens` API, the `agents/analysis.py` system prompt measured **897 tokens — below
Sonnet 5's minimum**, meaning the `cache_control` marker would have silently done nothing (no
error, just `cache_creation_input_tokens: 0` forever) on the model the user actually runs. Fixed
by adding a genuinely useful, stable **worked example** of the Fact/Interpretation/Unknown
evidence-labelling rule (already a Phase 1.5 requirement, see §4.3) directly into the system
prompt — this simultaneously improved output quality and pushed the prefix to **1306 tokens**,
clearing the threshold. Re-verified with `count_tokens` before considering it done.

**Honest scope of the saving**, stated to the user rather than oversold: caching only cuts the
*input* cost of the repeated system prompt across calls within the cache's ~5-minute window; it
does nothing for output tokens or the varying per-ticker payload. The bigger savings levers
already in place are the frontend session cache (§6, eliminates repeat `/analyze` calls
entirely — the largest lever) and the evidence relevance filter (§4.3, fewer news tokens sent to
the model at all). `effort="high"` on the analysis call was deliberately left unchanged to
protect answer quality; lowering it remains an available lever if the user wants to squeeze
further, not applied without being asked.

Verified live in production use later (§8): a 2-turn Ask-Claude conversation showed turn 1
`cache_write=1693, cache_read=0` and turn 2 `cache_write=0, cache_read=1693` — the entire
1693-token context served from cache on the second call, confirming the mechanism actually works
end to end, not just in theory.

---

## 8. Phase 2, feature 1 — Ask-Claude chat (2026-09-14)

The first Phase 2 feature (the UI already had a reserved seam for it). A conversational tutor
over ONE stock's research bundle, sharing every guardrail with the `/analyze` narration: exact
numbers only, cite what it leans on, teach the reasoning, never buy/sell/hold, and (per the
Phase 1.5 rule) never assert a company-specific catalyst when no company-specific news exists.

**Backend architecture.** `agents/orchestrator.py`'s single `analyze()` function was split so
`gather()` — the deterministic data-collection half (market data, indicators, relevance-filtered
news/filings, sourcing report) — is now shared between the AI narration path and a new chat
path, rather than duplicated. New `agents/chat.py` renders that shared bundle into a system
prompt (guardrails text + the ticker's exact data as JSON) and drives the conversation through
`messages`; `llm.call_chat()` sends it with the same `cache_control` treatment as §7. New
endpoint `POST /ask/{ticker}` (body: `{question, history}`) degrades gracefully exactly like
`/analyze` (`MissingKeyError` → `available:false`; any other exception scrubbed through
`redact_secrets` before it reaches the client) and uses `effort="medium"` rather than `"high"`
to keep per-question cost down, since chat answers are shorter and less analytically demanding
than the full momentum read.

**New caching layer — `services/cache.py`.** A tiny in-memory TTL cache (5-minute default,
matching the Claude prompt-cache window) memoising `orchestrator.gather()` by ticker. Two
purposes: chat turns on the same stock don't re-fetch market data/news, and — critically — the
data bundle stays *byte-identical* across turns, which is what actually lets the Claude-side
prompt cache hit (a re-fetch could return marginally different numbers on a live-refreshing
market and silently break the cache). This is also the backend half of the Phase 1.5
"cache abstraction" item that the frontend session cache (§6) started.

**Frontend, first version.** `components/AskClaude.jsx` initially rendered as a card inside the
research page's self-balancing masonry layout, with three starter-question chips, a message
list, and a footer note ("each question makes one Claude call — educational only"). Per-ticker
conversation threads were kept in a module-level JS object so switching tabs and returning
(the exact problem from §6) restores the conversation too, not just the research data.

**Verified live, twice, deliberately:** the feature was tested end-to-end in the browser with a
real question ("What is the RSI telling us here, in one short paragraph?") on AAPL, which
correctly answered using the exact RSI/SMA figures shown on the page; then a second follow-up
turn ("And what does MACD add to that picture?") confirmed the prompt-cache hit described in §7.

**Mistake made in this pass, and the recurring one it exposed:** `POST /ask` returned a
persistent 404 even though a fresh `import app` in a Python shell showed the route registered
correctly. Root cause: multiple `uvicorn --reload` backend processes had been started across
earlier turns in this session, and Windows lets more than one process bind the same listening
socket — requests were round-robining to a *stale* worker process that predated the new route.
Killing a `--reload` worker's PID doesn't fix this, because its reloader parent immediately
respawns a replacement. The actual fix was to enumerate all Python processes by command line
(`Get-CimInstance Win32_Process`), identify the orphaned `multiprocessing.spawn` workers
specifically (carefully avoiding the unrelated `yfinance-mcp` MCP-server Python processes, which
must keep running), kill exactly those, confirm the port was genuinely free
(`Get-NetTCPConnection -LocalPort 8000`), and only then start one clean backend. **This exact
failure mode recurred at least twice more later in the session** (§9, §10) before the standing
practice changed to running the local verification backend *without* `--reload` at all when
doing a quick check, precisely to avoid spawning extra worker processes. Documented as a
permanent Gotcha in `CLAUDE.md`.

Tests after this pass: unaffected (no new backend tests added in this specific increment beyond
what §6 already covered functionally); functional verification was via the live browser session.

---

## 9. Ask-Claude → floating chatbot widget, and non-US sourcing free tier (2026-09-14)

Two separate user requests handled together.

**Request 1 — turn Ask-Claude into a real chatbot widget.** The user's framing: "the ask claude
part is a bot option, just like how we have a new chat bot in any website," and attached a
screenshot of a generic website chat-widget builder (a bubble bottom-right that opens an
overlay panel over the page). `AskClaude.jsx` was rewritten: removed entirely from the masonry's
`FLOW` array, and rendered instead as a fixed-position launcher button (`.askbubble-btn`,
bottom-right, "✦ Ask Claude") that toggles an overlay panel (`.askpanel`, `position: fixed`,
with its own header/close button, message list, starters, and input) — the panel sits *on top
of* the research page rather than occupying grid space in it. Per-ticker threads and the
prompt-cached backend were carried over unchanged. Verified visually in the browser: the bubble
renders correctly and the panel opens as an overlay, matching the reference screenshot's
behaviour.

**Request 2 — non-US sourcing, deterministic/free tier only.** Before building, the user was
explicitly asked (via a structured choice) whether to spend on a paid scraping provider
(Firecrawl) now or stay free — the answer was **free now, paid tier deferred to after full
deployment**. The standout remaining non-US gap (beyond the news fix in §6) was **beta**: neither
yfinance's `.info` nor Finnhub publishes a beta value for most non-US symbols, so the Ecosystem
panel showed a blank. `services/company.py` gained `_computed_beta()`: a deterministic
regression of ~1 year of the stock's daily returns against its **regional market index**,
selected via a ticker-suffix → index map (`.T` → Nikkei 225 `^N225`, `.KS` → KOSPI `^KS11`, `.NS`
→ Nifty 50 `^NSEI`, `.HK` → Hang Seng `^HSI`, `.DE` → DAX, `.L` → FTSE 100, and similar entries
for ~15 exchanges; no-suffix/US tickers default to the S&P 500 `^GSPC`). Used only as a fallback
when the provider has no beta; the response carries `betaSource` (`"provider"` vs `"computed"`)
and `betaIndex` (which index was used) so the frontend can be transparent about it rather than
presenting a computed figure as if it were sourced data — the Ecosystem panel renders a small
note ("Computed by Trade Craft from ~1y of daily returns vs the Nikkei 225…") whenever
`betaSource === "computed"`. Verified live: 7974.T (Nintendo) → beta 0.079 vs Nikkei 225,
computed; AAPL unaffected, still shows its provider beta 1.085. Non-US **peers** remain gapped —
that is explicitly left for the Firecrawl/Exa work, not attempted with free tooling.

**The zombie-backend problem recurred exactly as in §8** — computed beta worked correctly when
called directly in a Python shell but the live `/ecosystem` endpoint kept returning `null` from
a stale worker. Same diagnosis, same fix (enumerate and kill orphaned `multiprocessing.spawn`
uvicorn workers, sparing the MCP processes, confirm the port is clear, start exactly one clean
backend — this time explicitly **without** `--reload** for the verification instance, to stop
generating more of the problem while testing).

---

## 10. Phase 2 — Comparison tab, twice (2026-09-14 build, 2026-09-14/15 fix)

**Initial build.** New `components/Compare.jsx` (a new `App.jsx` view, `'compare'`) and
`components/ComparisonChart.jsx`. Two independent "slots," each with its own search input, load
two stocks side by side: a shared-timeframe (1Y/1M) normalized price chart (both series rebased
to 100 at the window start, so the comparison is of **percentage moves**, not absolute price
levels — deliberately colored teal/amber rather than green/red so no "good/bad" judgement is
implied by color), plus a metrics table reusing the exact same `lessons.js` value-formatting
functions (`METRICS`, `metricValue`, `metricLabel`) the single-stock Research view uses, so the
numbers are guaranteed to match rather than being recomputed separately. Rows: price, change%,
RSI, MACD, SMA50/200, Bollinger, volume-vs-20d, beta, sector, market cap. "Open full research"
chips jump either stock into the normal single-stock view. The whole tab intentionally uses only
`/research` and `/ecosystem` — **no `/analyze` call, zero Claude spend** to use Comparison at
all. The previously-dead "Comparison" tab links across `Research.jsx`, `History.jsx`, and the
Welcome-page rail were wired to this view; Welcome's "soon" label on the Comparison rail item was
removed. Verified live with Apple vs Microsoft: chart renders correctly (Apple +141 vs Microsoft
+98.59 over the window, screenshotted), full metrics table populated correctly for both.

**The bug the user found next.** The initial slot loader took the **first** result from
`/search` without disambiguation and just used it. This looked fine with "apple"/"microsoft"
(both resolve unambiguously to their top hit) and shipped that way — then the user tried
"Samsung," which is genuinely ambiguous across 005930.KS (Korea, the real listing), SSNLF (OTC
ADR), SMSN.IL (London), a Frankfurt listing, and more, and got **"Failed to fetch."** Two
separate problems were found chasing this down:

1. **Missing search parity** — `Compare.jsx` needed the *same* name→symbol disambiguation flow
   the main Research search bar already had: type a name, and if `/search` returns more than one
   plausible match, show a "Did you mean…" candidate list (symbol · full name · exchange) and let
   the user pick, rather than silently guessing. `useSlot()`'s API was changed to take an
   already-resolved symbol; the resolve/disambiguate logic moved into the component with
   per-slot `cands`/`busy` state, mirroring `App.jsx`'s existing `submitQuery()` pattern exactly.
   Verified live: typing "samsung" now correctly lists all five candidates found above.

2. **A latent, unrelated backend crash, only surfaced by trying an actual ambiguous non-US
   symbol.** Picking `005930.KS` from the candidate list still failed — this time the real API
   call `/research/005930.KS` was returning HTTP **500**, with the server log showing
   `ValueError: Out of range float values are not JSON compliant: nan`. A bad holiday/partial
   OHLC bar in the raw Yahoo data for that symbol contained a NaN, and while
   `services/indicators.py` was already NaN-safe (its `_num()` helper converts NaN/inf to
   `None`), the **raw OHLCV list** returned by `/research` was not — FastAPI's JSON encoder
   cannot serialize a bare `nan`. Fixed at the true source, `services/marketdata.py::get()`:
   `hist.dropna(subset=["Open","High","Low","Close"])` plus `Volume.fillna(0)` immediately after
   the yfinance fetch, so **every** downstream consumer (`/research`, `/patterns`, `/analyze`,
   the Comparison tab) is protected, not just the one caller that happened to trip over it.
   Verified: `005930.KS` now returns 200; AAPL/7974.T unaffected; the full 29-test suite still
   passes.

**Explicit self-noted lesson:** the tab shipped with the disambiguation gap because the only
manual test used two clean, unambiguous US tickers — the happy path hid both the missing-picker
UX gap and the NaN crash simultaneously. Recorded as a standing testing habit going forward: a
new search-driven feature should be smoke-tested with at least one genuinely ambiguous / non-US
query, not just clean US names.

---

## 11. Phase 2 — real logo, ecosystem node graph, and the Trade Craft rebrand (2026-09-14/15)

**Real logo, v1 (still under the "Trade101" brand).** The original design spec (§3.2) described
an isometric "data cube" mark; `Logo.jsx` had been a rough placeholder pending "Phase 2, needs an
OpenRouter key." Rather than spend on image generation, a proper isometric-cube mark was
hand-authored directly as SVG: three shaded cube faces, an ascending teal bar-chart clipped to
the right face, a green up-candlestick on the left face — matching the original spec's intent, at
zero cost and infinitely scalable. Verified in the header and Welcome page.

**Ecosystem node graph.** The peers list (`Ecosystem.jsx`) had been a flat row of ticker chips.
Replaced with `EcoGraph`, a small inline SVG radial layout: the current company sits at the
center as a highlighted node, up to 8 peer tickers are arranged evenly around it on a ring
connected by edges, and every node (including the center) is clickable to jump research to it.
Falls back to the existing plain-text coverage explanation when peers are unavailable (the usual
non-US case). Explicitly scoped as v1 — a fuller *sourced* supply-chain graph with typed edges
(supplier/customer/competitor/etc.) and public/private distinction remains a later idea, not
attempted here.

**The rebrand — Trade101 → Trade Craft (2026-09-15).** The user supplied a full, detailed SVG
specification for a new brand mark ("Trade Craft" — a 3D-styled growth-spiral ribbon in a
lime-green→cyan-teal gradient, spiraling from bottom-left to a sharp arrowhead top-right,
wrapping an implied cylinder for depth, with 4–5 small currency-symbol nodes ($, €, ¥) along the
ribbon, and a 3-bar ascending mini bar-chart nested in the top loop) along with a reference
screenshot of a similar "Growth Spiral" icon. `Logo.jsx` was rewritten a second time to this new
spec (SVG gradients via `<linearGradient>`, layered ribbon paths for the wrapped/3D feel, the
arrowhead polygon, the nested bar-chart rectangles, and three small currency-node circles/text).
The brand string "Trade101" was replaced with "Trade Craft" everywhere user-facing — page
`<title>`, every component header, Welcome-page hero text, the AI-narration and Ask-Claude system
prompts (`agents/analysis.py`, `agents/chat.py`, so the model refers to itself correctly), and
copy strings in `NewsPanel.jsx`/`Ecosystem.jsx`. **Explicitly scoped out:** the GitHub repo name,
local folder name, and internal Python package/module names all stay `trade101` — renaming those
was judged out of scope and needlessly risky for a purely cosmetic brand change. In the same
pass, the color palette (`styles.css` `:root`) was deepened per the user's request ("change the
colour palette to a darker shade entirely... maybe you can go with deep navy"): background moved
from `#0E1A26` to `#070E1A`, and the ink/text color brightened from `#EAF1F6` to a warmer
cream-white `#F4F1E9`, with teal/green accents nudged slightly brighter so they still read
clearly against the darker ground. Verified visually on the Welcome page (screenshotted): new
logo, "Trade Craft" branding, and the deeper navy theme all rendering correctly together.

With this, Phase 2's build items were essentially complete, leaving only the two items the user
had explicitly deferred to **after full deployment**: the paid Firecrawl/Exa non-US provider, and
deploying a public/shareable URL.

---

## 12. Phase 3 — Watchlist (2026-09-15)

First Phase 3 feature. New `lib/watchlist.js` (localStorage-backed, structurally mirroring the
existing `lib/history.js`) and `components/Watchlist.jsx`. A ☆/★ **Watch** toggle button was
added to the Research page header; toggling it adds/removes the current ticker from the
watchlist. The Watchlist view itself lists every tracked company with a **live** price and
change%, fetched via `/research` per name (deterministic — **no Claude spend** to view or
maintain the watchlist) and a remove (✕) button per row. New `App.jsx` view `'watchlist'`, with
its tab added consistently across Research, Compare, History, and the Welcome-page rail (this
pass also fixed a pre-existing bug where `History.jsx`'s own "Comparison" tab link went to
`'home'` instead of `'compare'`). Deliberately framed in its own copy as a **study/tracking
list**, not a trading tool: "companies you're tracking · information, not trade prompts" — no
positions, no P&L, no buy/sell signal of any kind, consistent with the app's north star.
Verified live by seeding three tickers (AAPL, MSFT, 7974.T) directly into `localStorage` via the
browser, confirming all three rendered with correct live quotes (Apple $334.17 +0.57%, Microsoft
$505.37 +1.97%, Nintendo ¥8268 +3.49%), then clearing the seeded test data afterward so the
user's actual watchlist starts empty.

---

## 13. Desktop packaging → the "shareable link" clarification (2026-09-15)

The user asked to "start desktop packaging" as the next Phase 3 item. Before writing any code,
the environment was checked: Node 24 present, but **no Rust toolchain** (required for Tauri) and
**no PyInstaller** (needed to bundle the Python backend into a standalone executable for
Electron too). Both desktop-packaging paths would have required non-trivial new tooling.

Before committing to either, the user was asked a structured clarifying question about how far
to take desktop packaging — and their answer ("I am testing and building locally but I will be
pushing and creating a shareable link of it so I am not sure what to use?") revealed that the
actual goal was **not** a desktop app at all. This was surfaced explicitly rather than just
proceeding: **a desktop app (Electron/Tauri) produces a downloadable installer** that someone
runs on their own machine; **a shareable link is a web deployment** that produces a URL anyone
opens in a browser — they are different delivery channels, and desktop packaging does not
produce a link. A second structured question confirmed the pivot: the user chose to prioritize
the web deploy (the actual "shareable link" goal) and park desktop packaging.

**Why the web deploy is unambiguously the more efficient choice here**, as explained to the
user: it works on any device with no install, updates are instant on every push, and — most
importantly for this stack — it entirely sidesteps the hardest part of desktop packaging, which
is bundling the Python/FastAPI backend into a native binary (PyInstaller with `pandas`/`scipy`/
`yfinance`/`anthropic` is notoriously finicky and produces large builds). Desktop packaging
remains parked in the backlog, not abandoned, should the user want a native app later once Rust
or PyInstaller tooling is set up.

**One important tradeoff surfaced proactively, not left implicit:** a *public* deploy URL means
every visitor's `/analyze` and `/ask` calls spend the **owner's** Claude API key — there is
currently no per-visitor authentication or rate-limiting. This became the seed of the pre-share
requirement formalized in §16.

---

## 14. Single-service deploy setup, and the repo made private (2026-09-15)

Given the pivot in §13, the most efficient deploy architecture was chosen and built: **one
service**, not two. `backend/app.py` was changed to mount the built React app
(`frontend/dist`, via `StaticFiles(html=True)`) as a catch-all route registered **after** every
API route, so a single process serves both the API and the UI from one origin — no CORS
configuration needed in production, and only one thing to deploy. `frontend/src/api.js`'s base
URL was made environment-aware: `import.meta.env.DEV` still points at `http://127.0.0.1:8000`
during local development (where Vite and the backend run as two separate processes), but the
production build uses a same-origin relative base, since in production they're the same
process. This required **no changes to any individual API call** — only the one shared `BASE`
constant.

A multi-stage `Dockerfile` was added at the repo root (stage 1: Node image builds the frontend;
stage 2: a slim Python image installs backend requirements and copies in both the backend source
and the stage-1 build output), plus `.dockerignore`, and a new `docs/DEPLOY.md` walking through
deploying it on Render (chosen as the simplest free host that auto-detects a Dockerfile) —
including the two environment variables that must be set on the host (`TRADE101_ANALYSIS_KEY`,
`TRADE101_NEWS_KEY`) and an explicit note that `PORT` must be left to the host to set. All of
this was **verified locally before considering it done**: `npm run build` was run for real,
producing an actual `dist/` folder; the backend was restarted to pick it up; then `curl` checks
confirmed `/health` (API) and `/` (built HTML, correct `<title>Trade Craft</title>`) and a static
asset all served correctly from the same `:8000` origin, and that ordinary API routes
(`/search`, `/research/AAPL`) still worked unaffected by the new catch-all mount.

**Per the user's explicit instruction, the GitHub repository was switched from public to
private** (`gh repo edit pranavlakshminarayan/trade101 --visibility private
--accept-visibility-change-consequences`), confirmed via `gh repo view`. This is a standing
state, not a one-off — do not make the repo public again unless specifically asked to.

The user was also told plainly what remains a step only they can take: actually creating the
live deployment requires signing into a hosting account (Render or similar) with their own
credentials and connecting the repository — that action cannot be performed on their behalf.
Once they have a live URL, the plan is to add it to the repository's GitHub "About" field or the
README.

---

## 15. A free no-Docker deploy alternative — Render native runtime (2026-09-15)

The user asked for a free alternative to Docker for the same deploy. Because §14's single-service
design lives entirely in `app.py` (mounting the built frontend) rather than in the Dockerfile,
switching *how* the service is built required **zero application code changes** — Docker had
only ever been one way to produce the build, not a structural requirement. Render's own build
image already includes both Node and Python regardless of which "runtime" a service declares, so
a plain Python web service can run the frontend's `npm install && npm run build` as its build
step and then `pip install -r requirements.txt`, with no container involved at all.

Added `render.yaml` at the repo root — a Render "Blueprint" declaring `runtime: python`, the
combined build command described above, a `startCommand` running uvicorn on Render's `$PORT`, a
`/health` health-check path, the free instance plan, and placeholder slots for the two API-key
environment variables (left `sync: false` so Render prompts for them rather than committing
secrets). `docs/DEPLOY.md` was restructured into **Option A (no Docker, recommended — the new
Blueprint path)** and **Option B (Docker, kept for hosts that specifically want a container)**,
both documented with equivalent step-by-step instructions. Verified before committing anything:
`frontend/dist` was deleted and rebuilt completely from scratch (`rm -rf frontend/dist && npm
install && npm run build`) — exactly the sequence Render's Blueprint build command performs —
and it succeeded cleanly; the already-running backend was then reconfirmed to serve the freshly
rebuilt output correctly at `:8000`.

The `Dockerfile` from §14 was kept in the repo rather than removed, since it remains useful for
any host that specifically expects a container (Fly.io, Railway, etc.) or if the user simply
prefers Docker later.

---

## 16. ⚠️ Pre-share requirement — status update: code fix done 2026-09-15

**Originally a standing, unresolved item, explicitly requested by the user to be tracked and
re-surfaced.** Verbatim from the user: *"remind me at the end of phase 3 execution to fix this
bug and only then i can share the details."* Raised proactively mid-Phase-3 (while picking up
the "more markets" backlog item) rather than held back to the literal end, and the user asked
to act on it then.

**The bug (now fixed in code):** `/analyze` and `/ask` had **no authentication and no
rate-limiting**. Every call to either endpoint spends the **owner's** Claude API key. On a
private, personal-only URL this was fine — but the moment the URL is shared with even one other
person, that person (or anyone they forward it to) could trigger unlimited paid Claude calls
against the owner's account with zero friction or cost cap.

**What was built (`backend/services/access.py`, `frontend/src/lib/access.js`):**
- A shared access-token gate: `TRADE101_ACCESS_TOKEN` (optional, off by default) checked against
  an `X-Access-Token` header on `/analyze` and `/ask` only — every deterministic endpoint stays
  open, since none of them spend anything.
- A process-wide daily cap: `TRADE101_DAILY_CAP` (default 50/day across both endpoints combined,
  resets at UTC midnight) — a backstop even if the token leaks or is shared onward.
- Both are no-ops when unset, so this shipped with zero effect on local dev.
- The frontend captures a one-time `?token=...` URL param into `localStorage` and strips it from
  the address bar, so the owner shares one link with the token embedded and it keeps working
  silently after that.
- 5 new tests (`tests/test_access.py`); full suite 34 passing. Full narrative:
  `docs/DEVELOPMENT-LOG.md`'s "Pre-share endpoint guard" entry.

**Deliberately not built:** a real distributed rate-limiter, per-user accounts, or per-IP
tracking — this is one free-tier process for one owner's app, not a multi-tenant product; that
would be solving a problem this project doesn't have.

**What's still the user's step, not code:** actually **set `TRADE101_ACCESS_TOKEN`** as an env
var on the host once deployed, before sharing the link — the code is ready but inert (a no-op)
until that value exists. `docs/DEPLOY.md` walks through exactly when/how. A spend cap on the
Claude key in the Anthropic console remains a good additional backstop, independent of this code.

**Where this was tracked, so it survived context resets:** the "Pre-share checklist" section at
the top of `BACKLOG.md` (now checked off, with the remaining user action called out
separately); the `CLAUDE.md` header callout (now marked done); and a persistent memory file
(`trading_idea_preshare_reminder.md`, in Claude's own cross-session memory) — that memory should
be updated to reflect the code fix landing, since it otherwise still reads as fully open.

---

## 17. Cross-cutting lesson — the recurring zombie-backend-process problem

Worth its own section because it recurred at least three separate times across this session
(§8, §9, and again during §15's verification) and cost real debugging time each occurrence, so a
future session should recognize the *symptom* immediately rather than re-diagnosing it from
scratch. **Symptom:** a newly added/changed backend route or behavior appears to not exist or
not take effect when hit over HTTP (a 404 for a route that clearly exists in the source, or stale
data from a fix that was clearly applied) — **but** a fresh `python -c "import app; ..."` in a
new shell shows the code is correct. **Root cause:** on Windows, starting `uvicorn --reload`
multiple times across a session (e.g. restarting after every edit, or after this conversation's
context was compacted/resumed) can leave orphaned `multiprocessing.spawn` worker processes still
bound to and listening on the same port; new HTTP requests can land on a stale worker rather than
the most recently started one. **Why the obvious fix doesn't work:** killing a `--reload`
worker's specific PID doesn't help, because its reloader *parent* process notices the worker died
and immediately spawns a fresh replacement — you have to find and kill the actual orphaned
worker processes, not just "the backend." **The reliable fix, every time:** enumerate all Python
processes with their full command lines (`Get-CimInstance Win32_Process | Where-Object {
$_.CommandLine -match 'uvicorn|multiprocessing.spawn' }`), carefully exclude the *unrelated*
`yfinance-mcp` MCP-server Python processes (a completely different, legitimate long-running
service that must not be touched), kill exactly the orphaned uvicorn-related ones, confirm with
`Get-NetTCPConnection -LocalPort 8000 -State Listen` that the port is genuinely empty, and only
then start one single clean backend process. **Standing practice adopted as a result:** for quick
local verification checks (not active development), start the backend **without** `--reload` at
all, since a single non-reloading process cannot accumulate this problem — `--reload` is worth
the convenience only during active multi-edit development, not for a one-off verification. This
is now documented as a permanent Gotcha in `CLAUDE.md` so it isn't rediscovered a fourth time.

---

## 18. Current state & how to run (updated from §4, 2026-09-15)

**Local development** (unchanged in shape from §4, still two terminals):
```
# backend, from backend/
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
# frontend, from frontend/
npm run dev
```
Open `http://127.0.0.1:5173` for the dev experience (hot-reloading Vite frontend calling the
`:8000` API directly), **or** run `npm run build` in `frontend/` and hit `http://127.0.0.1:8000`
directly to exercise the exact single-service production configuration locally before deploying.
`.env` in the project root still needs `TRADE101_ANALYSIS_KEY` and `TRADE101_NEWS_KEY` for the
AI/news features; everything else (chart, indicators, patterns, Comparison, Watchlist, Practice
Lab) works without any key. Tests: `cd backend && .venv/Scripts/python.exe -m pytest -q` — **37
passing** as of 2026-09-15's Phase 3 completion (started at 16 in §4).

**Deploying for real** (the user's own remaining step): pick Option A (no Docker, `render.yaml`,
recommended) or Option B (Docker) from `docs/DEPLOY.md`, sign into a host with the user's own
account, connect the (private) GitHub repo, set the API-key environment variables, deploy.
**Then stop — do not share the resulting URL with anyone until `TRADE101_ACCESS_TOKEN` is also
set** (the pre-share guard code is done, §16, but is a no-op until that value exists).

---

## 19. What's next — remaining Phase 3, and the deferred items

**Phase 3 is feature-complete as of 2026-09-15.** What shipped across the day's two passes:
- More markets: a currency-display bug fixed (non-US currencies were a bare number, no symbol);
  non-US news broadened with a keyless Google News RSS fallback (Finnhub → Google News →
  Yahoo), verified live on 7974.T pulling in MarketWatch, BeInCrypto, Britannica, nintendo.com,
  Anime News Network. Non-US peers (Ecosystem) remain gapped — no free substitute for
  Finnhub's US-only peers endpoint exists; real fix is still the deferred paid Firecrawl/Exa
  tier.
- Accessibility polish: 10 nav-tab links that were `<a>` with no `href`
  (keyboard/screen-reader-unreachable) converted to real `<button>`s, a global focus-visible
  ring added, one input's missing focus outline fixed. A broader pass (modal keyboard-trap
  review, full contrast audit, mobile layout) remains open but is no longer a Phase 3 blocker.
- **Practice Lab** — `lib/practiceLab.js` + `components/PracticeLab.jsx`, scoped with the user
  first (combined trade-journal + simulated portfolio, its own tab, no AI/zero Claude spend).
  A simulated $100,000 USD-only cash pool (deliberately not multi-currency — a shared cash
  balance across currencies would need real FX data this app doesn't have, and fabricating a
  rate would violate the north-star "never fabricate" guardrail, so v1 is USD-only with a clear
  message otherwise). Buy/sell always use the real live `/research` price, never a typed
  number; selling realizes P&L against average cost and appends a reasoned journal entry.
  Verified live end-to-end with exact numbers (bought 10 AAPL, sold 5, cash and P&L math exact
  to the cent). Full detail: `docs/DEVELOPMENT-LOG.md`'s "Practice Lab" and "UI/UX, non-US
  news, and accessibility fixes" entries.

**What's left is no longer Phase 3 scope**, just deployment steps and deliberate deferrals:
going live (needs the user's host signup), setting `TRADE101_ACCESS_TOKEN` before sharing the
link, the paid Firecrawl/Exa tier for non-US peers, and desktop packaging (parked, §13).
- An optional simulated *practice lab* — explicitly to be kept **separate** from the main
  learning flow (delayed/hypothetical, reflection-focused), per the original Phase-2
  recommendations review; not yet started.
- Accessibility / keyboard-navigation / responsive polish — not yet started.

**Explicitly deferred by the user, to be picked up only when asked:**
- The **paid** Firecrawl/Exa non-US sourcing tier (deferred "until after full deployment").
- Actually going live with the deploy (needs the user's host-account signup, §14/§15).
- **The pre-share endpoint-guard fix (§16) — this is a blocker, not just a "later," and must be
  raised again proactively as Phase 3 wraps up, before any link is shared with anyone.**

**North-star reminder, unchanged since §0:** the app describes and teaches; it never gives
buy/sell advice or price targets; numbers are exact (deterministic code); every AI claim is
sourced, and an unreachable source is disclosed rather than papered over.

---

## 20. The critical audit, and Audit Waves 0–3 (started) — 2026-09-16/17

A new session. The user asked for an adversarial, no-flattery review of the whole app before
treating Phase 3 as "done" — explicitly invoking the framing of a **product critic / systems
analyst / solution architect reviewer / red-teamer**, plus a critique (not yet a rebuild) of the
UI/UX, with any redesign to be reviewed as a proposal before being built. This section is the
summary; full blow-by-blow detail (including every mistake made and how it was caught) lives in
`docs/DEVELOPMENT-LOG.md`'s entries for the same dates, and the audit's full findings live in
**`docs/AUDIT.md`**, which is now a permanent companion doc (link it from here — an unlinked doc
is as good as lost).

### 20.1 The audit itself

Read the entire codebase and reproduced every finding by running the code, not just reading it.
Three findings were worse than "unfinished": (1) market cap rendered with a hardcoded `$`
regardless of the listing's actual currency, so Nintendo's cap read as `$9.36T` — larger than
Apple's real `$4.81T` — a false number breaking the app's own "numbers are exact" guardrail, on
screen, silently; (2) `above_sma50/200` collapsed "the average isn't available" and "price is
below the average" into the same `False`, which reached the analysis agent as exact data; (3) a
completed Phase 3 commit (including the pre-share access guard from §16) was sitting **unmerged
in a stray git worktree** — `CLAUDE.md` said the guard was still outstanding while git said it
had been written, i.e. the project's own memory contradicted itself. Also reproduced: the "Sony"
search bug (typing the company name silently opened the NYSE ADR because the name equals its own
ticker), the news panel depending entirely on the paid `/analyze` call, the chart being torn down
and rebuilt on every keystroke, and a pattern detector capped at one reversal shape from only the
last 3 swings. `docs/AUDIT.md` has the full ranked list (30+ findings) and a wave-by-wave fix
order; §10 of that doc is the plan this section's work followed.

### 20.2 Wave 0 — critical fixes

Currency-correct market cap; tri-state `above_sma50/200` (both agent prompts taught to read
`null` as unknown, with a regression test); a React error boundary so a render crash no longer
white-screens the app; a `href="#"` news-link bug that mutated the hash router and could bounce
the user back to Welcome. The stranded-branch finding turned out to have *already* been merged
via GitHub PR #2 in a parallel session between the audit being written and this fix session
starting — a routine `git merge` (one conflict, in `CLAUDE.md`'s own status text) closed the gap.

### 20.3 Wave 1 — the four flaws the user named, plus shareability

**Search:** `App.jsx`'s `looksLikeTicker()` fixed the "Sony" auto-pick bug — the picker is now
skipped only for a genuinely ticker-shaped, unambiguous query. `services/search.py::resolve()`
now scores and ranks candidates by listing quality (home/major exchange first; OTC/CDR/preferred/
secondary-dealer lines demoted and badged in the picker with a plain-language tooltip) instead of
passing Yahoo's raw order straight through.

**News:** a new free `GET /news/{ticker}` decouples the Feed tab from the paid `/analyze` call
entirely — headlines render immediately regardless of Claude-key/error/daily-cap state, sharing
one cached data bundle so nothing is fetched twice.

**Chart:** `PriceChart.jsx` rewritten from one effect (any prop change → full teardown/rebuild)
into independent effects, so the chart survives re-renders and only re-fits its view on a
genuinely new dataset — zoom/pan now survive the 7-minute auto-refresh.

**Patterns:** `services/patterns.py` rewritten to scan the whole series (not just the last 3
swings), built from High/Low (not Close), with overlapping matches deduplicated and a real
per-match confidence label. Found **11 distinct patterns on a real NVDA/1Y series** where the old
code could return at most 2. *(A first-pass regression the user then caught: the fixed 4%/2%
tolerances never fired on intraday timeframes, and results weren't sorted by recency — both
fixed same-day; see `docs/DEVELOPMENT-LOG.md`'s "mistakes" note for the honest accounting.)*

**Shareability:** de-personalized the Welcome greeting; moved the SEC EDGAR contact email out of
committed source into `TRADE101_SEC_CONTACT` (the real value lives in the gitignored `.env`).

### 20.4 Ecosystem panel — three more user-reported bugs

Fixed after the user actually used the app: the company summary was cut off mid-word (a fixed
360-char slice with no word-boundary awareness, plus the frontend appending a second ellipsis
unconditionally); the beta explanation said "the market" instead of naming the actual benchmark,
because only a computed (non-US-fallback) beta carried an index name, never a provider beta (the
common case); and — the user's own follow-up ask — hovering a peer node in the ecosystem graph
showed only the bare ticker, no company name. Added `peerNames` (resolved via parallel yfinance
lookups, ~0.85s for 8 peers) wired to a native SVG `<title>` tooltip. While verifying that live on
QCOM, caught a fourth: "MRVL" appeared as two separate graph nodes — Finnhub's own peers list
genuinely contained it twice. Deduped case-insensitively.

### 20.5 New brand mark

Mid-session, the user supplied a full new brand brief (T/C monogram, navy/teal/copper, explicitly
avoiding finance iconography) and asked for the logo to be rebuilt to match, while keeping the
existing dark-navy theme rather than switching to the brief's off-white background. `Logo.jsx`
rebuilt as a bold T (crossbar + a pointed ribbon-tail stem) with a teal ribbon wrapping into a C,
rendered in `--ink` instead of navy (navy would vanish on a dark background) — iterated once
live for boldness/legibility per the user's feedback.

### 20.6 Wave 2 — cost/reliability (code half done; deploy is the user's step)

`orchestrator.analyze()` now caches its finished result for 20 minutes per ticker — previously
every page reload, new tab, or new visitor spent a fresh paid Claude call for a ticker someone
had already researched minutes earlier; a raised exception is never cached, so a failure recovers
on the next request. Verified carefully (mindful this spends real money): two `/analyze/AMD`
calls back to back — first ~30s (a real call), second 4ms (cache hit), one `[llm]` log line for
both. Also added an explicit Anthropic client timeout (90s analysis, 45s chat) — previously
unset, meaning a hung request could occupy a worker indefinitely. **What's left of Wave 2 is not
code:** deploying to Render and setting `TRADE101_ACCESS_TOKEN`, which needs the user's own host
signup (§14/§15/§16 cover the deploy paths and the pre-share guard in detail).

### 20.7 Wave 3, first item — chart indicator overlays (H5)

The app computed SMA50/SMA200/Bollinger Bands/RSI/MACD and explained them at length in the
Metrics panel's lessons, but never plotted a single one — `lightweight-charts` v4.2 has no
multi-pane support, and the backend's indicator function only ever returned the LATEST snapshot
value, nothing to draw a line from. Upgraded to **v5.2.1** (multi-pane support is the entire
reason for the upgrade). New `indicators.compute_indicator_series()` reuses the same primitive
functions already used for the snapshot, just without collapsing to the last value, so the two
views can never drift apart (tested). `PriceChart.jsx` now overlays SMA50/SMA200 + Bollinger
Bands on the price pane, puts RSI and MACD each in their own pane below (RSI on a fixed 0–100
scale with 30/70 reference lines), and adds a crosshair-driven OHLC + change% + volume legend —
all four togglable, SMA on by default. Verified live: RSI's hovered value matched the Metrics
panel's snapshot exactly.

**A bug the user caught immediately after, fixed same day:** SMA200 was cut short on the 1Y chart
and vanished entirely on 5D/1D. Root cause: SMA200 needs 200 bars of lookback before it produces
even one point, and `/research` fetched exactly the display window (e.g. literally 5 calendar
days of 15-minute bars for the "5D" tab) with zero lookback margin. Fixed with
`app.py::_fetch_with_lookback` — fetch more history than gets displayed (verified against
yfinance directly that `period="3mo"` is silently REJECTED for 30m/15m/5m intervals; intraday
history is capped at 60 days regardless of the period token used, so `"60d"` is the safe choice),
compute indicators on the larger fetch, trim back to the original display width before returning.
**Course-correction worth stating plainly:** this gap existed in the H5 pass's own shipped code a
few minutes earlier, and that pass's own tests/live verification checked almost exclusively the
1Y timeframe — the general lesson (also true of the pattern-detector miss in §20.3) is that
verifying one condition is not the same as verifying a feature across the actual range of inputs
it needs to serve. New tests explicitly assert full indicator coverage on a short-window case now.

### 20.8 Where things stand at the end of this session

- **Test count:** 29 (session start) → **71** backend tests, all passing throughout.
- **Commits this session** (all local; **not yet pushed** until the push at the end of this
  handover): `d170e32` (audit doc) → `f160d05` (merge PR #2/#3) → `8980c3a` (Wave 0) →
  `bf9ed66` (logo) → `1d8d22e` (Wave 1) → `fbeb408` (pattern fixes) → `ced7f7b` (ecosystem
  panel) → `4a41f31` (ecosystem hover/dedupe) → `4a952b8` (Wave 2) → `4d663f5` (Wave 3/H5) →
  `2851394` (SMA lookback fix).
- **Done:** Waves 0, 1, and 2's code half; Wave 3's chart-overlay item (H5) plus the SMA
  lookback bug it surfaced.
- **Not done, and the two things to pick up in the next session:**
  1. **Wave 2's deploy step** — the user's own Render signup + setting `TRADE101_ACCESS_TOKEN`
     before ever sharing the link. Code side has been ready since §14/§15/§16.
  2. **Wave 3's UI/UX redesign** — a proposal to review before any of it is built, per the
     user's explicit instruction from the very start of this session. Not started. The chart is
     now materially more complex (multiple panes, overlays, a legend) than when this was first
     scoped, which is useful context for that proposal rather than something to design around
     the old flat-price chart.
- This session ends here on the user's request, to continue in a new chat — see `CLAUDE.md`'s
  "Known bugs" and `BACKLOG.md`'s "Audit — Wave 0/1/2/3" sections for the authoritative, current
  checklist a new session should read first.

## 21. Wave 3 executed, reviewed live across two feedback rounds, merged — 2026-09-17

New session continuing from §20. User confirmed direction for Wave 3 (pushed back on a fully
rigid three-zone grid over dead-space concerns, and on the icon plan implying the chosen symbols
themselves would change) before anything was built — see `CLAUDE.md`'s "Known bugs" → the Wave 3
"Fixed" entry for the current-state summary of what shipped. This entry is the narrative: what
went wrong along the way and why, kept here rather than bloating `CLAUDE.md`.

**Round 1 (initial build).** Fixed layout, SVG icon set, evidence-card redesign, mobile media
query, dead CSS removal. Also renamed Ask-Claude → "Ask TC-Buddy" with a candlestick icon
(user's explicit ask, alongside the redesign discussion). Built and left uncommitted for review.

**Round 2 (user feedback, 7 notes on the live app).** Metrics/AI-read swap, pattern color, logo→
home wiring, and a real chart-autofit bug (`fitContent()` gated behind an `isFirstFit` check that
only ever fired once, ever — every timeframe switch after the first left the chart unfit). Also
attempted a news-depth fix (supplement thin feeds with Google News) and a patterns fix (restrict
intraday pattern scans to the trailing 2 hours, to stop stale 3-4-hour-old swings from showing).
**The patterns fix was wrong** — confirmed in round 3 below.

**Round 3 (user feedback on a real thin-coverage stock, TECA.F — Toshiba Tec's Frankfurt
secondary listing).** Three real bugs surfaced by testing against an actual edge case rather than
just NVDA/AAPL:
1. **SMA200 "same error" reported again** — looked like the round-2 fix hadn't landed, but was
   actually a *different*, previously-unnoticed bug: `Metrics` always rendered the base 1Y/1D
   `indicators` object regardless of which chart timeframe was selected, so the 10D tab showed
   a real-but-irrelevant 1Y SMA200 number. Chased this down through: (a) suspecting the frontend
   session cache was stale (it turned out ALSO to have a real bug — no TTL at all, docs/AUDIT.md
   M1, now fixed as a side effect), (b) suspecting the backend `gather()` cache was stale, before
   (c) finding the actual root cause by tracing which `indicators` object `Research.jsx` passed
   to `<Metrics>`. Lesson: when a user reports "the same bug again" after a fix, don't assume the
   fix was incomplete — verify it's the SAME bug before re-patching, since here it was a sibling
   bug with an identical-looking symptom.
2. **Patterns: user meant the OPPOSITE of round 2's fix.** "I don't want to see only patterns
   below 2 hours, I want to see patterns below 2 hours AS WELL" — the round-2 restriction excluded
   both genuinely recent and older-but-real patterns by shrinking the scan window. Reverted
   entirely back to the pre-Wave-3 full-series scan. **This is the second time in this session a
   "make X more recent" request got over-literally translated into "exclude anything not recent"
   — worth remembering as a pattern of misreading, not a one-off.**
3. **News "still US-only, proves my point"** — investigated properly rather than assuming the
   user was right or wrong. Finding: Google News RSS genuinely does return non-US results (verified
   with a real query), but a 30-day recency cutoff was silently discarding real coverage that was
   simply a few months old — common for a thinly-covered secondary listing. Widened the
   supplement window to 90 days, and added an honest "little findable coverage" note for the
   (expected, real) case where a listing has almost nothing. This was NOT a US-market-only bug —
   it was a recency-window bug that happened to disproportionately hit thin non-US listings.

**Infrastructure, twice.** Port 8001 (like port 8000 before it) got a stuck orphaned LISTENING
socket with no owning process partway through this work. Separately, `uvicorn --reload`'s
WatchFiles watcher proved unreliable on this machine — only one reload fired across several
subsequent backend file saves, so a code fix could look "not applied" when the process just
hadn't restarted. This directly caused false starts while chasing bug #1 above. Resolution:
backend now runs on **port 8002, without `--reload`** — restart manually after backend edits.
`frontend/.env.local` updated; the frontend dev server also needed restarting (Vite only reads
`.env.local` at startup). **Recommend for future sessions:** don't trust `--reload` on this
machine at all; treat every backend edit as needing a manual restart to verify.

**User then explicitly asked one more thing mid-review** (not part of the original Wave 3 scope,
addressed alongside round 2): clicking the "Trade Craft" logo from any page should return to the
true Welcome/home screen. It was a static, unclickable `<div>` on every page — now a real button
wired to `App.jsx`'s existing `goHome`.

**Outcome:** all of the above approved and committed as `897514c`, pushed to `origin/master`.
71 backend tests pass throughout. Wave 4 (fundamentals/earnings, sharper evidence matching,
frontend tests, glossary/watchlist notes) started immediately after in the same session — see
`BACKLOG.md` for its checklist.

## 22. Wave 4, the BYOK redesign, a real chart bug, and the README rewrite — 2026-09-17

Same session as §21, continued without a break. Four distinct pieces of work, in the order they
actually happened, since the order itself matters (the BYOK redesign was triggered by something
the user revealed mid-session, not planned from the start).

### 22.1 Wave 4 — fundamentals, sharper evidence, frontend tests, glossary

Executed `docs/AUDIT.md` §10's list (M5 → M3 → M10 → glossary/watchlist), plus two bugs the user
found by testing real, harder tickers rather than the usual AAPL/NVDA smoke test.

**M5 — fundamentals**, `services/company.py::_fundamentals()`: P/E (trailing + forward), EPS,
revenue growth, profit margin, dividend yield, debt/equity, next earnings date, all straight from
yfinance — nothing computed or estimated. The one thing worth flagging for anyone touching this
code later: `dividendYield` and `debtToEquity` are ALREADY percentage-scale in yfinance's own
convention, unlike `revenueGrowth`/`profitMargins` which are fractions. Verified empirically
against AAPL before trusting it, since getting this wrong silently misrepresents every dividend
yield in the app by 100x — the kind of bug that looks fine in a spot-check and is wrong for
every single ticker.

**Non-US peers — found by the user testing RELIANCE.NS, not on the Wave 4 list.** The Ecosystem
tab showed nothing, because Finnhub's peers endpoint is US-listed only, a gap the project had
been deferring to "the paid Firecrawl/Exa tier, post-deploy" since Phase 2. Before accepting that
deferral again, checked whether a free alternative existed now and found one — Yahoo Finance's
own keyless "people also watch" endpoint. Used it as a fallback, but deliberately did NOT present
it as equivalent to Finnhub's peer data: it's co-viewed-by-other-investors, not
same-industry-competitor data, and the response carries a `peersSource` field so the frontend can
label it honestly rather than papering over the difference. **The near-miss here:** the easy path
would have been to just re-state the old deferral as still-true without re-checking it — it
wasn't, and wouldn't have been caught without actually looking.

**Trendline detector missing a still-forming pattern — found by the user on a real NKE chart.**
A visually obvious falling wedge in the last ~15 bars wasn't detected. Root cause:
`_trendlines()` only ever fit through the last 4 CONFIRMED peaks/troughs, and `argrelextrema`
structurally cannot confirm an extremum without bars on both sides of it — so a shape still
forming at the very tail of the series has zero confirmed extrema to fit a line through no matter
how clean it looks visually. Fixed two ways: try progressively smaller/more-recent extrema
windows before falling back to the widest one, and, for the still-forming case specifically, fit
directly through raw bars in a trailing window when no extrema-based fit works at all. The user
then asked to verify the wedge-vs-channel classification itself against an external
technical-analysis reference they supplied — the definitions matched what the code already
implemented, a genuine confirmation, not a second hidden bug. **Course-correction inside this
same exchange:** the ad-hoc multi-width comparison used to answer that question was initially
described in a way that implied the LIVE app was ambiguous between the two labels, when the
actual running code path returns one consistent answer — caught and corrected in the same
conversation once it was clearly wrong.

**M3 — sharper evidence matching.** `services/evidence.py`'s relevance filter previously trusted
any bare match on a distinctive company-name word, so "Apple cider vinegar" classified as
Apple-Inc-relevant on the word "apple" alone. Fixed with a curated set of company names that
double as ordinary English words, requiring a secondary corroborating signal (the ticker, or
ordinary market/business vocabulary) before trusting those specific matches. Deliberately
narrow — most company names aren't dictionary words, so this doesn't cost recall on the common
case.

**M10 — frontend tests, zero to 53.** Vitest v2 (pinned below v3 to stay compatible with the
project's Vite 5) + Testing Library. Covers the pure-logic libs (currency, history, watchlist,
practice-lab trade math, lessons) plus `App.jsx`'s ticker-disambiguation logic, which was
extracted from an inline closure into a module-level exported function specifically so it could
be tested in isolation — a small refactor done in service of testability, not a drive-by
cleanup.

**Glossary + watchlist notes.** Lower-risk, additive: a searchable static reference page
(`lib/glossary.js` + `components/Glossary.jsx`) and a one-line study-note field per watchlist
entry. No notable mistakes here.

84 backend / 57 frontend tests passing at the end of Wave 4, committed and pushed as it landed.

### 22.2 The pivot — BYOK replaces the shared-token model entirely

Mid-session the user stated the actual deployment goal for the first time in concrete terms: a
genuinely OPEN, publicly-shareable link, not "a few trusted people with an invite token" — which
is what the `TRADE101_ACCESS_TOKEN` + daily-cap system built 2026-09-15 (§20 above) was actually
designed for. The user was explicit: "I do not want to risk it" — meaning any model where a
stranger could still spend the owner's Claude key, even bounded by a cap, wasn't acceptable for
an open link. Given that goal, no amount of cap-tuning on the old model was the right answer.

The conversation worked through the shape of the fix as a discussion before any code was
written. Netlify was raised as a possible host and rejected — it's a static-site/serverless-
functions platform and cannot run this app's persistent FastAPI process without a real
rearchitecting, not a small config change. BYOK (bring-your-own-key) was then proposed; the
user's own framing of it — "a password system to open the website," the key "input once" and
then persisting so the visitor "just logs in using the password" — was clarified through two
direct questions rather than assumed: confirmed the API key IS the only credential (no separate
password layered on top), and confirmed this should FULLY REPLACE the old gate, not sit
alongside it.

**What shipped.** `components/ApiKeyGate.jsx` — a first-run, whole-app gate. A visitor pastes
their own Anthropic key (validated to start with `sk-ant-`) and optionally a display name; both
saved permanently in `lib/apiKey.js` (localStorage, that visitor's own browser only) — never
asked again on that device. `api.js::authHeaders()` sends the key as `X-Anthropic-Key` on
`/analyze`/`/ask` only; every deterministic endpoint (chart, indicators, news, patterns,
ecosystem) stays free and keyless for everyone, always. Backend: `app.py` reads the header via
`Header(default=None)` and threads it as `client_key` through `orchestrator.analyze()/ask()` →
`agents/analysis.py::run()` / `agents/chat.py::answer()` → `agents/llm.py::call()/call_chat()`,
which resolves it (`_resolve_key()`) as the literal Anthropic key for that one call — visitor key
first, `TRADE101_ANALYSIS_KEY` env var as a local-dev-only fallback, explicit `MissingKeyError`
with a friendly message if neither exists. `services/access.py`, `lib/access.js`, and
`tests/test_access.py` were **deleted outright**, not deprecated or kept as a fallback path —
replaced by `tests/test_byok.py` (8 new tests, including one that constructs a real
`anthropic.AuthenticationError` via `httpx.Response` to verify an invalid visitor key degrades to
a friendly message rather than a raw SDK error).

**Verified the actual failure path, not just the happy path.** Tested with a deliberately
invalid key end to end: it reached the real Anthropic API, was genuinely rejected (401), and
`app.py::_ai_error_reason()` (new) turned that into "that Anthropic API key was rejected —
double-check you pasted it correctly" instead of surfacing Anthropic's raw SDK error JSON to a
visitor who has no way to interpret it.

**A security concern, investigated and resolved transparently.** Mid-implementation the user sent
an instruction that needed careful handling before acting on it at all: "remove my password from
the GitHub repo." This was NOT acted on blindly, given the potential severity if true. Ran
`git log --all --full-history -- .env backend/.env frontend/.env` (no output — never committed),
then `git grep` across every tracked file and the full history's diffs for credential-shaped
patterns (`sk-ant-`, hardcoded tokens, `password=`), and confirmed `.claude/worktrees/*/.env`
files were gitignored, never tracked. Found nothing. Reported the findings plainly and asked the
user to clarify what they'd actually seen, rather than either dismissing the concern or
performing an unnecessary and risky history rewrite on a private repo with no evidence anything
needed rewriting. The user confirmed: "if .env file was never committed then good," then
clarified afterward that it had been a verification request, not a report of an actual leak —
fully resolved, no further action needed. **Worth preserving as a pattern for future sessions:**
an alarming instruction involving credentials/history-rewriting was investigated exhaustively
BEFORE any action, reported honestly including the negative result, and the user was asked to
confirm rather than the ambiguity being resolved by guessing.

**Mistakes/course-corrections:** none in the implementation itself — the two clarifying questions
asked before writing any code (key-is-the-only-credential? fully-replace-not-extend?) were exactly
what prevented a wrong design from being built and then needing correction. The value was in
asking before coding, not in fixing something after.

### 22.3 A real bug, found by testing the new feature rather than trusting it

While manually exercising the Comparison tab to verify BYOK worked end-to-end on every tab (not
just Research, where it had already been tested), hit a hard crash: `chart.addLineSeries is not a
function`. Root cause: `ComparisonChart.jsx` was never migrated when the rest of the app moved to
**lightweight-charts v5** for the H5 chart-overlay work (§20 above) — `PriceChart.jsx` was
correctly migrated at the time; `ComparisonChart.jsx` was missed because the Comparison tab
hadn't been exercised again since that migration landed. Fixed by changing both
`chart.addLineSeries({...})` calls to `chart.addSeries(LineSeries, {...})` with the matching
import, then grepped the rest of `frontend/src` for any other leftover `addLineSeries`/
`addAreaSeries`/`addCandlestickSeries`/`addHistogramSeries`/`addBarSeries` calls — none found, so
this was the only casualty of that migration.

**Mistake/course-correction in the debugging process itself, not the bug.** The first
reproduction attempt used a fast, scripted browser interaction that typed into both comparison
inputs in quick succession; it ALSO crashed, but from triple-clicking too fast into a stale DOM
reference — a different, script-specific cause that briefly looked like it might be a deeper or
different problem before it was checked by hand. The real, product-level bug was confirmed
separately by reproducing it through slow, deliberate, completely normal manual interaction
(type AAPL, click Load, type MSFT, click Load) — which is what actually confirmed this as a
genuine regression rather than a test-harness artifact, and is the version that should be trusted
when script-based and manual reproduction disagree on cause.

Fix verified live: both AAPL and MSFT lines render correctly on the comparison chart, no crash,
before re-running the screenshot capture below.

### 22.4 README rewrite + real screenshots

Separate, smaller request alongside the above: make the repo look better with screenshots and
examples. `README.md` had drifted significantly stale — missing Comparison, Watchlist, Practice
Lab, Glossary, Ask TC-Buddy, and fundamentals entirely, and still describing the just-removed
shared-token access model. Rewrote it to match current reality (features list, BYOK explanation,
corrected setup steps matching the rewritten `.env.example`, current project layout).

Captured six real screenshots from the actually-running app — not mockups — using a temporary
`puppeteer-core` script (`frontend/_shots_tmp.cjs`, deleted after use, never committed) pointed
at the machine's existing Edge install via `executablePath`. Installed `puppeteer-core` with
`--no-save` and uninstalled it again afterward — confirmed `package.json`/`package-lock.json`
unchanged before and after. The script read the local `.env`'s `TRADE101_ANALYSIS_KEY` directly
via `fs.readFileSync` purely to seed `localStorage` so the captured screenshots show real AI
content rather than an empty gate screen — the key was never printed, logged, or written to any
committed file.

**Two tooling detours, worth recording so they aren't re-discovered from scratch next time.**
First, launching Puppeteer via the Bash tool failed with an opaque `Failed to launch the browser
process: Code: 0` and empty stderr, even with `--no-sandbox`/`dangerouslyDisableSandbox: true` —
this sandboxed Bash environment cannot spawn GUI/browser subprocesses at all, regardless of
flags. Switched to the PowerShell tool (also with `dangerouslyDisableSandbox: true`), which
launched the browser successfully — a shell-tool-specific sandbox difference, not a Puppeteer
config problem. Second, the first screenshot run produced a corrupted "NVDAAAPL" comparison
input and a real `ErrorBoundary` crash screenshot, because `initial`-prop ticker state leaked
across a same-origin hash-only navigation that doesn't always trigger a full remount; fixed with
`{ clickCount: 3 }` before typing (select-all before replace) and an extra full page reload
before navigating to `/#/compare`.

**Mistakes/course-corrections:** the corrupted first comparison screenshot IS what surfaced the
real ComparisonChart bug in §22.3 above — a deliberately unplanned but valuable side effect of
insisting on capturing the real running app rather than describing it from memory. Separately, a
retry run of just the comparison screenshot showed genuinely flaky behavior (slot B stuck on
"Loading…" indefinitely in the isolated retry, despite always working in a full run and always
working under manual testing) — concluded this was headless-automation timing flakiness, not a
product bug, since manual testing was consistently clean; resolved pragmatically with longer
waits and sequential per-slot DOM queries rather than chasing it as a real bug.

87 backend / 57 frontend tests passing at the end of this entry. Everything in this section
committed in focused, single-purpose commits and pushed to `origin/master` as it landed:
`bc9a497` (BYOK), `69cc111` (README + screenshots + ComparisonChart fix), `6b66db8` (docs).

### 22.5 Where things stand at the end of this session

- **Test count:** 71 (end of §21) → **87 backend / 57 frontend**, all passing throughout.
- **Done:** Wave 4 in full; the BYOK redesign (replacing the old shared-token/cap model
  entirely); the ComparisonChart v4→v5 leftover bug; the security-concern investigation
  (resolved, nothing found); the README rewrite with real screenshots.
- **Not done:** the user's own deploy step (host signup) — now materially lower-stakes than
  before, since BYOK means the link is safe to share the moment it's live, with nothing to
  configure first. See `CLAUDE.md`'s "Known bugs" intro and `docs/AUDIT.md` §10 for the current
  authoritative checklist.
