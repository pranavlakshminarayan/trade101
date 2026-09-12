# Trade101 — Complete Conversation Handover (turn-by-turn)

This is a faithful, chronological reconstruction of the **entire chat** that produced Trade101 — every user request (with their own key phrasings preserved), what I did in response, every decision, and the way we operated. It complements the structured summary in [`HANDOVER.md`](HANDOVER.md). A new chat can read this top-to-bottom and know exactly what happened and why.

- **Repo:** https://github.com/pranavlakshminarayan/trade101 (public, branch `master`)
- **Local:** `C:\Users\prana\Documents\Claude Code\Trading idea`
- **User:** Pranav — student, beginning trader, trades on Moomoo (finds it button-heavy). GitHub `pranavlakshminarayan`, email workspace.sonic@gmail.com. Windows 11, Git Bash, Anaconda Python 3.12.7.
- **Status (2026-09-12):** MVP complete (M0–M5), pushed to GitHub. Next = Phase 2 (`BACKLOG.md`).

> The single guardrail that never changed across the whole chat: **the tool describes and teaches; it never gives buy/sell advice.** Numbers are exact (deterministic code); every AI claim is sourced; if a source is unreachable, say so — never fabricate. The goal is to **extract and make sense of data**, not read labels back.

---

## HOW WE OPERATED (the working style — important for continuity)

- **Verify, then report.** Nearly every build step ended with a real check (run the tests, hit the endpoint, look at the browser DOM/screenshot) before I claimed it worked. I reported failures honestly with the actual output.
- **Honest pushback.** When the user's instruction had a technical flaw (e.g. "one agent per subsystem"), I said so and proposed a better shape, then let them decide. I never silently overrode them; their words always won.
- **Cost-conscious.** The AI calls spend the user's Claude key. Once keys were live I minimized browser test-loads, verified at the data level (curl) where possible, and flagged when a test spent a call. We switched the model Opus→**Sonnet** to save money.
- **Incremental + committed.** Work went in milestones (M0–M5), each git-committed with a clear message. Design was locked in a spec before code (brainstorming → spec → plan → build).
- **Design iterated visually.** Layout/branding were worked out as live HTML mockups (v1→v5) via the brainstorming skill's visual-companion server, then rebuilt in React.
- **Faithful to the guardrails.** Deterministic code for numbers; agents only for judgment; everything sourced; never "buy/sell".
- **Attribution:** commits end with `Co-Authored-By: Claude …`.

---

## THE THREE PHASES (one continuous session)

1. **Yahoo Finance MCP connector** (a *separate* folder, `…\yfinance-mcp`).
2. **AAPL September-event study** (a published analysis Artifact dashboard).
3. **Trade101** — the personal research + learning app (THIS repo). ~90% of the chat.

---

## TURN-BY-TURN LOG

### Phase 1 — Yahoo Finance MCP connector

**U1 — "can i integrate yahoo finance to claude?"**
Me: Explained the options — (a) a local Python script using `yfinance` in Claude Code, (b) a custom **MCP connector** for live use in chat, (c) ad-hoc web fetches. Asked what the actual goal was.

**U2 — "we can use claude code with Yahoo finance… build a Claude code MCP and integrate Yahoo Finance… as a live connector. Explain the steps and build together."** (model set to `claude-opus-4-8`)
Me: Laid out the shape (local MCP server over stdio, register with `claude mcp add`) and a 5-step table. Checked env (Python 3.12.7; `mcp`/`yfinance` not installed). Created `C:\Users\prana\Documents\Claude Code\yfinance-mcp` with a `.venv`, installed `mcp[cli]` + `yfinance` (backgrounded). Wrote `server.py` with tools `get_quote`, `get_history`, `get_financials`, `compare_tickers`. Steps 4–5 (register/restart) flagged as the user's to run (interactive).

**U3 (mid-turn) — "create a subfolder named Yahoo Finance… execute the first step."**
Me: Install finished. Discovered a gotcha: `mcp` **2.x** renamed `FastMCP` → use `from mcp.server.mcpserver import MCPServer` (the `.tool()` decorator and `.run()` are unchanged). Fixed the import, tested `get_quote` live (MSFT ≈ $495.77), confirmed the stdio server starts clean, wrote a README. Kept the folder name `yfinance-mcp` (a space in "Yahoo Finance" would complicate the `claude mcp add` path) and explained why. Step 1 done.

**U4 — "did you execute all the 5 steps?"**
Me: Honest — did **1–3**; **4–5** (register, restart, verify) are the user's to run in an interactive terminal. Gave the exact `claude mcp add yfinance -- <venv python> <server.py>`.

**U5 — shared a screenshot (an Anthropic-IPO chat answer) captioned "this is the error returned".**
Me: Pointed out that's **not** an MCP error — it's an unrelated chat answer. Asked where they ran the command and what the terminal printed.

**U6 — pasted a PowerShell error: `claude` is not recognized.**
Me: Located the CLI at `C:\Users\prana\.local\bin\claude.exe` (not on PATH). Gave a full-path command plus a permanent PATH fix (`[Environment]::SetEnvironmentVariable(...)`).

**U7 — "i ran all the commands."**
Me: Verified myself with `claude mcp list` → **`yfinance … ✔ Connected`**. Explained the current session won't show the tools (it started before registration) — a fresh session will. Saved a memory note.

**U8 — "can you set this up as a new customised connector."**
Me: Explained "connector" spans different surfaces. Found Claude Desktop installed. Asked (AskUserQuestion) which surface; user answered **"all three"** + "claude connector". Delivered: **(1) Claude Code** re-scoped to user config (`✔ Connected`); **(2) Claude Desktop** — built `dist/yfinance.mcpb` Desktop Extension (manifest_version 0.3, points at the venv python), sent the file; **(3) claude.ai web** — made `server.py` dual-mode (stdio default; `MCP_TRANSPORT=http` serves `streamable_http_app()` via uvicorn), wrote `requirements.txt`; noted it needs public hosting the user does themselves (unauthenticated endpoint caveat). Updated README + memory.

### Phase 2 — AAPL September-event study (Wall Street trader)

**U9 — "use the yahoo finance integrator skill… research AAPL around Apple's September keynote over the past 4 years… act as a Wall Street trader."** Questions: drivers before/after the event; previous years' trends/stats; average fluctuations; RSI & bullish metrics at each launch; how long it stays in profit and when it dips.
Me: The MCP tools were now live in the session. Pulled the live AAPL quote via the connector ($319.97), then ran the heavy study with a Python script on the same `yfinance` engine (avoiding dumping thousands of bars into context). Studied the four keynotes (iPhone 14/15/16/17, 2022–2025): pre-run-up, event-day, T+1…T+30, RSI(14), SMA50/200, volatility, peak/dip timing. Findings: **sell-the-news** — muted event day (avg −0.56%), reliable day-after dip (−1.43%), recovery to ~+6.6% peak near session 21, +2.45% by T+30; RSI entering ≈ **48.6 (neutral, NOT overbought — myth-busted)**; trend (above 200-DMA) mattered more than RSI. Loaded `artifact-design` + `dataviz` skills, validated a categorical palette with the dataviz script, and **published an interactive dashboard Artifact** (trading-desk dark theme): https://claude.ai/code/artifact/8123b4b3-88db-495b-80f1-5bfe7530b5bb . Gave a written trader's readout answering every question, with a "historical analysis, not advice" disclaimer.

**U10 — "cross validate this to the Apple products sale post the keynote… compare sales vs stock over the last 4 years."**
Me: Honest data reality up front — Yahoo has **no unit sales**, and Apple **stopped reporting iPhone units in 2018**. Used **iPhone-segment revenue** for the December launch quarter (fiscal Q1), verified from **SEC 8-Ks** (WebSearch/WebFetch). Finding: at the **extremes the two agree** (iPhone 14 weak sales −8% + weak stock; iPhone 17 record +23% + strong stock), but the **middle inverts** — the stock trades the *anticipated demand narrative* (e.g. the "Apple Intelligence" run-up), and the actual sales print lands months later. Added a **"Sales vs Stock"** panel and republished the artifact.

**U11 — "I want the stock variations with sales only in the month of September over the last 4 years, in alignment to the launch."**
Me: Flagged that clean September-only new-product sales don't exist; used the **September-ending fiscal Q4** iPhone revenue as the honest proxy. Computed September-only stock stats. Finding: **September-quarter iPhone sales rose every year (steady)** while the September **stock move swung −12.5% to +10.8%** → the month's stock is **decoupled** from actual sales (macro + anticipation). Added a **"September in isolation"** panel; cited the SEC sources.

### Phase 3 — Building Trade101 (this repo)

**U12 — the big vision** (paraphrased faithfully): build his own dashboard/website using the web + Yahoo Finance + research to **watch metrics and make his own decisions**; AI to read **bullish/bearish trend cycles** and pattern shapes ("3 mountains = bearish, 3 valleys = bullish"); a **learning platform** because videos/courses never worked for him — he's **hands-on**. Zerodha-clean but a notch more pro than **Moomoo** (too many buttons). **Chrome-style tabs** (Home/Research, Comparison, History). Detailed Research view layout (live chart top-left, indicators below, AI momentum read top-right with sourced why, learn-the-metric panel + annotated pattern, news + financials, ecosystem chain like NVDA→TSMC→AI buyers). Strong **DISCLAIMER**: don't rush, don't hallucinate, he's a student, it's a **data-analytics model that scrapes the web and helps him learn metrics** — not a buy/sell oracle. "**USE RELEVANT CONNECTORS, PLUGINS AND SKILLS.**" "**DID YOU UNDERSTAND?**"
Me: Invoked the **brainstorming** skill. Confirmed understanding by mirroring the vision, gave honest reads (real-time data limits; automated pattern detection is noisy; premium sources are paywalled/ToS-limited; AI narrates+sources, never predicts; this needs a **real local app with a backend**, not an Artifact). Flagged **scope** (≈6 subsystems) and proposed decomposition + **MVP-first** (single-stock Research view). Working folder set to `Trading idea`.

**U13 — clarifications** (with the folder attached): Zerodha/Moomoo were just calibration; wants **pattern recognition shown visually** (screenshot with drawn lines) when explaining a metric; accepts delayed data but wants the most recent updates and to "duplicate the Yahoo chart"; **global markets** (USA, China, Singapore, S.Korea, HK, Japan, India); local app fine; **wants an agent for each of the 6 subsystems** (agentic workflow); phased build; store in `Trading idea`.
Me: Reshaped "6 agents" honestly → **hybrid**: deterministic code for the *numbers* (can't be hallucinated) + specialist **agents** for the *judgment* (news/analysis/ecosystem) under an orchestrator. Asked via AskUserQuestion; user chose **Hybrid** ("a mix of agents and LLM is good… I do not want to hallucinate the numbers").

**U14 — accepted the visual companion** ("sure that works").
Me: Read the visual-companion guide, started the mockup server (Windows background), rendered **v1** (`research-layout.html`) — the described Research view with numbered zones.

**U15 — "swap 5 and 6 [annotated-pattern ↔ news]… tell me your suggestions on the visual representation."**
Me: Rendered **v2** with the swap + 5 design suggestions (draw pattern lines on the live chart; "cockpit" above the fold; contextual click-to-learn; AI confidence + always-visible evidence; strict red/green-for-price-only color discipline), plus a verbal brainstorm.

**U16 — more feedback**: add S&P/NASDAQ **index learning** in the ecosystem; agrees too many blocks; **pattern via a button** (top-right) → a slide-out panel + **magnifier lens** (shared an image); **merge the metric analyzer + learning** (click a metric → its lesson, Esc to close); a **references box** at the bottom (all links); an **"Ask Claude" chatbot** (unsure now/later); ecosystem flexible.
Me: Server had auto-stopped; no image was saved (the tool records clicks, not images) — built from the clear written description. Restarted the server, rendered **v3** (pattern button + slide-out panel + magnifier shown open; merged metrics+learning; index learning; references box; Ask-Claude tagged Phase 2; flexible ecosystem). Recommended **Ask Claude = Phase 2** (reserve the seam now). Saved `trade101-project.md` memory.

**U17 — shared two references** (a Head-&-Shoulders magnifier chart, and an Apple product page for "simple and appealing"): wants very interactive/appealing UI; **section 2+4 on the left, news on the right**; **flexible, not rigid** — if the momentum block is long, push metrics below the chart and move news to fill the space.
Me: Acknowledged both references; built **v4** in the Apple-clean direction (light, airy) with a fluid left/right layout.

**U18 — more references** (Gemini page, Claude page, two palette examples "Stock Trading Slate" + "Crypto Wallet Dark", and a **hex-cube logo image**; fintech-palette links): keep **RSI/metric symbols like real apps**; airy is good but **white doesn't suit** — wants a dark fintech palette; a **Gemini/Claude-style welcome page** → research view; a news **"What it means"** inference tab (Trade101's own reasoning about how news affects the stock); brand name **Trade101**, plus the logo.
Me: Derived the **Trade101 dark palette** from the logo (navy/teal/green). Restarted the server, built **v5** (dark palette; welcome page + research view; standard metric symbols like `RSI (14)`, `MACD (12,26,9)`; the news Feed + "What it means" tab). Saved memory + MEMORY.md.

**U19 — "the logo sucks"** + a detailed logo spec (isometric data-cube; 2×2 panels: dark-blue bar chart, dark-green candlesticks, bold white "1" and "0" = "10"; teal-blue + olive-green faceted sides; light-grey circuit background). Colours are a small part — revisit later; **design the MVP with these, upgrade next phase**.
Me: Parked logo/colours. Surfaced the real dependency (the agents need their **own Claude API key**, billed per use). Stated the MVP scope default (US-first, NVDA as the dev example). Asked (AskUserQuestion) the **tech stack**; user chose **FastAPI + React** (over all-Python/NiceGUI and desktop/Tauri).

**U20 — build clarifications**: can M3 switch to **Firecrawl** later? use TradingView's free sources; is there a **scraping agent** (efficient)?; the overview looks good; make **separate API keys per task named `Trade101-<Task>`**.
Me: Confirmed the news provider is **pluggable** (Firecrawl swap = one line, `TRADE101_NEWS_PROVIDER`). Explained the efficient scraping split (the agent *decides & judges*; deterministic tools *fetch* — the LLM never parses raw HTML). Corrected two things honestly: **TradingView's free offering is its charting library (Lightweight-Charts) + widgets, not a free data feed**, and **"Microsoft Money" is discontinued** → data sources are a pluggable slot (Yahoo now; Stooq/Alpha Vantage/Finnhub later). Adopted the named-keys convention. Wrote the full **design spec** to `docs/superpowers/specs/2026-09-09-trade101-design.md`, self-reviewed, sent it, asked for review.

**U21 — approved the spec** ("looks good to me for now"); build the MVP on **real-time work** (NVDA is a trial; will test another stock for a true test); generate the logo from the description; kickstart. **The GitHub push is the END step.**
Me: Confirmed real-time & ticker-agnostic + the GitHub finale. Tried to generate the logo (invoked `generate-image`) — it needs an **OpenRouter key** which isn't configured; told the user how to add it themselves (never paste it to me), noted it doesn't block the build. The `writing-plans` skill wasn't installed → I authored the **implementation plan** directly (6 runnable milestones), sent it, asked to start M0+M1.

**U22 — "GO!"**
Me: Built **M0** (git init; `.gitignore` ignoring `.env`/`.venv`/`.superpowers`/`data`; `.env.example` with named keys; backend/frontend skeletons) + **M1** (`services/marketdata.py` via yfinance any-market; `services/indicators.py` = RSI/MACD/SMA/EMA/Bollinger in pure pandas, exact & unit-tested; `app.py` `/health` + `/research/{ticker}`; tests). Installed deps (backgrounded).

*(background install done)* — Ran **9 tests pass**. Started the server and hit `/research` live on **NVDA / MSFT / RELIANCE.NS** (multi-market — proved nothing is hardcoded to NVDA) + a clean **404** on a bad ticker. Committed **M0+M1**.

**U23 — "Go go, keep rolling"** — push to GitHub at the very end with setup instructions.
Me: Built **M2** (hand-built Vite+React, not a scaffold: `styles.css` dark Trade101 palette, `api.js`, `lessons.js`, `Logo`, `PriceChart` (Lightweight-Charts candles+volume), `Metrics`, `Welcome`, `Research`, `App`). npm install (backgrounded). Started both servers, verified in the browser (Welcome → NVDA research view → live chart → click-to-learn RSI lesson → **no console errors**). Committed **M2**.

**U24 — "how do i test it?"** + PowerShell **WinError 10013** (port 8000 already in use).
Me: The background backend I'd started was squatting on 8000 → killed it, told the user to re-run.

**U25 — `npm run dev` → PowerShell execution-policy error** (`npm.ps1` blocked).
Me: The frontend was already running (mine, on 5173) → just open it. The backend uses `python.exe` (no PS issue). Gave the two fixes: `npm.cmd run dev`, or `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

*(Between M2 and here, M3 was built — the AI narration. Sequence: I reported M2, said M3 needs keys + a news provider, asked which (AskUserQuestion). User asked for the difference between Finnhub/Exa/Firecrawl; I explained and recommended **Finnhub (free) + SEC EDGAR**. User: "the free one is good… build the trial and test it… my task is NOT to read labels and give answers, it is **extract data and make sense of it**… create a new text file with all the additional features and phase 2/3 work." I created `BACKLOG.md`, invoked the `claude-api` skill (read the Python SDK — adaptive thinking + `output_config.effort`, model ids), and built **M3**: `services/news.py` (Finnhub company news + SEC EDGAR filings, pluggable via `TRADE101_NEWS_PROVIDER`), `agents/llm.py`, `agents/analysis.py` (the sense-making engine — synthesise signals, sourced, never advise), `agents/orchestrator.py`, a **citation guard**, `GET /analyze/{ticker}` (separate from `/research` so the chart never blocks on the AI; degrades to `available:false` with no key), frontend **AiRead** + **NewsPanel** (Feed / "What it means"), and `.env` loading via `python-dotenv`. Committed M3; verified graceful degradation.)*

**U26 — tested MU (Micron); the AI momentum read worked great; listed flaws:** (1) won't always know the ticker → **type the company name, you resolve it, disambiguate if several**; (2) blocks still rigid → **flexible layout that fills gaps**; (3) the **top strip is missing**; (4) the Technical Snapshot is redundant → **merge its facts into the metric click-to-learn** (fact first, then a better lesson); (5) the **chart doesn't reload → auto-refresh every 5–10 min**; (6) add a **line chart** condensed to ~10 days for intraday.
Me: The "polish pass" — added **name→ticker `/search`** (Yahoo search) + a **disambiguation picker**; restored the **top strip**; **removed the standalone snapshot**, folding facts into the metric lessons (improved copy); **auto-refresh every 7 min**; a **Candles/Line toggle**; reorganised the layout (metrics below the chart, news on the right). Committed. Then fixed a line-chart bug — Yahoo has no `10d` period (it jumps 5d→1mo) → fetch `1mo`/`30m` and slice ~10 sessions. Committed.

**U27 — layout still not flexible enough** (the news should fill the empty space under the metrics on the **left**); wants **line-chart timeframe options** like a real app: **1Y · 1M · 10D · 5D · 1D (24h/intraday)**; **line color follows direction** (Tesla example: red over 5D, green over 10D); patterns must apply to **all** tabs.
Me: Moved **news into the left column**; built the full **timeframe row** (1Y/1M/10D/5D/1D for both Candles and Line, each fetching the right granularity); **directional line color** (green if the window is up, red if down — proved AAPL red over 5D, green over 1M). Committed.

**U28 — more**: move **ecosystem + references up under the news** to fill space; render **news items as boxed cards** (Google-News style, darker contrast); make **references descriptive links** (headline/filing, not repeated "Yahoo"); then **move on to M4**.
Me: Moved ecosystem+references into the left column; **boxed news cards**; **descriptive reference links** (used the headline as link text via the orchestrator). Committed. Then started **M4**: `services/patterns.py` (Head-&-Shoulders ±, triple/double top & bottom via `scipy` extrema; labeled points, neckline, rich explanations), `GET /patterns` (any timeframe → applies across all chart tabs), an amber **on-chart overlay** + description panel. Committed M4 (patterns). *(Installed `scipy`.)*

**U29 — pattern feedback**: don't show top **and** bottom together — a **selector** (click 1 → triple top, click other → triple bottom); each pattern needs a **real learning explanation** (what it means · momentum inference · what traders typically do); the layout must be a **true masonry** ("move blocks left or right wherever there's space… reduce scrolling"); and a **loading widget** while it scrapes.
Me: **Pattern selector** (▲/▼ tabs; only the chosen pattern draws); **enriched explanations** (an `EXPL` dict: what it is · inference · what traders do · caveat, educational not advice); a **self-balancing JS masonry** (measures each block's height and sends flow blocks to the shorter column — verified balance ≈ 1618 vs 1819 px, with ecosystem+refs auto-flowing right under the tall AI read and news to the left); a **loading widget** (spinner + "Scraping & analysing…"). Committed. Verified live (masonry balanced, no console errors, spinner shows).

**U30 — two asks**: the **browser back button** doesn't work (a friend can't navigate back) → make it part of the tool; and **switch the model Opus→Sonnet** (stop wasting money on trials).
Me: Added **History-API routing** — navigating pushes state, browser back/forward work, and `#TICKER` in the URL loads that stock (**shareable links** — verified NVDA → back → welcome). Switched the **default model to `claude-sonnet-5`** (override via `TRADE101_MODEL`). Then built **M4 ecosystem panel** with real data: `services/company.py` + `GET /ecosystem` (sector, industry, **beta with a "what beta means for this stock" note**, market cap, **Finnhub peers as clickable chips**). Committed. Verified: NVDA → Technology/Semiconductors, $5.42T, peers AVGO/MU/AMD…, `#NVDA` URL, back button works.

**U31 — non-US by name (no suffix)** + build **M5** + **complete the History tab** (list of searched companies each with a two-line inference of the search).
Me: Name resolution already handled non-US (allianz→ALV.DE, samsung→005930.KS, toyota→TM, tencent→0700.HK) — I only fixed the misleading "needs a suffix" **copy** (welcome text, chips, 404 message). Built the **History tab** (`lib/history.js` localStorage; `History.jsx`; saves every analysed stock with its 2-line AI takeaway; list shows ticker · name · momentum · time + summary; each card reopens the stock; Clear-all + empty state; wired into the tabs + welcome rail). **M5 tests:** `tests/test_patterns.py` (triple top/bottom, H&S, no-pattern-on-trend) + `tests/test_app.py` (endpoint smoke + graceful degradation) — **16 passing**. Verified live: NVDA saved with its summary, History renders it. Wrote the comprehensive **README** (setup + run for both, `.env`, the PowerShell npm note). Checked `gh` (authed as pranavlakshminarayan). Safety-scanned (only `.env.example` tracked; no real keys anywhere in history). Asked (AskUserQuestion) **public vs private** → **Public**. `gh repo create trade101 --public --source=. --push` → **live**. Verified remote HEAD matches local, 42 files, `.env` not tracked. Updated memory.

**U32 — "give me a short description that I can put as a message."**
Me: Gave a short shareable blurb (what Trade101 is + the repo link).

**U33 — "generate a complete handover chat… include every single line… to the md file."**
Me: Wrote this document.

---

## CURRENT STATE (verified)

- **MVP complete (M0–M5)**, public on GitHub, 12 commits, branch `master`, 16 tests passing.
- **Endpoints:** `/health`, `/search?q=`, `/research/{ticker}?period&interval`, `/analyze/{ticker}` (AI; degrades w/o key), `/patterns/{ticker}`, `/ecosystem/{ticker}`.
- **Frontend features:** name search + picker (any market), live chart (candles/line, 1Y/1M/10D/5D/1D, auto-refresh, directional line color), metrics with click-to-learn (fact + lesson), pattern overlay + selector, AI momentum read (Sonnet, sourced), news Feed + "What it means", ecosystem (beta/sector/peers), References (descriptive), History (localStorage, 2-line takeaways), self-balancing masonry, browser back + `#TICKER` links, loading spinner.
- **Model:** default `claude-sonnet-5` (`TRADE101_MODEL` overrides). Keys in root `.env` (git-ignored): `TRADE101_ANALYSIS_KEY` (Claude), `TRADE101_NEWS_KEY` (free Finnhub).

## HOW TO RUN (two terminals)
```
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000
# frontend (from frontend/)
npm run dev        # if PowerShell blocks npm: npm.cmd run dev, or Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Open http://127.0.0.1:5173. Tests: `cd backend && .venv/Scripts/python.exe -m pytest -q`.

## GOTCHAS (learned the hard way)
- PowerShell blocks `npm` ("running scripts is disabled") → `npm.cmd` or set the execution policy.
- Pin servers to `127.0.0.1` (IPv6 `::1` binding broke browser fetches); API base is `http://127.0.0.1:8000`.
- WinError 10013 = port already in use → kill the stray process on 8000/5173 before restarting.
- Each `/analyze` call spends the user's Claude key — verify at the data level (curl) where possible; be sparing in the browser.
- HMR can re-mount React and re-fire `/analyze`; scaled browser-emulation viewports throw off click coordinates.
- Chart-pattern detection is a **heuristic learning aid** (returns "none" when nothing clean) — never present it as a signal.
- `mcp` 2.x (Phase-1 connector) uses `MCPServer`, not `FastMCP`.

## NEXT — Phase 2 (see `BACKLOG.md` + `docs/trade101-phase-2-recommendations.txt`)
- **Ask Claude** chat over the research bundle (UI seam reserved).
- **Comparison** tab (two stocks side by side).
- Deeper non-US sourcing via **Firecrawl** (provider already pluggable via `TRADE101_NEWS_PROVIDER`); broader premium sourcing (Exa).
- Richer pattern library + step-by-step teaching replay; the real **data-cube logo** (needs an OpenRouter key); desktop packaging.
- **North-star (never drop):** extract and make sense of data; teach understanding; **never advise.**
