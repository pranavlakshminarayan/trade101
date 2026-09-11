# Trade101

A personal stock-research **and learning** app. Type a **company name** (any market) → Trade101 pulls live prices, computes indicators, detects chart patterns, gathers news + filings, and **explains the momentum with sourced reasoning** — so you learn to read the market on real stocks.

> **It never tells you to buy or sell.** Numbers are exact (deterministic code); every AI opinion is source-backed. It's a data-analytics + learning tool, not a signal generator. Data is delayed ~15 min.


## What it does now

A research page for any company in any major market, plus a learning layer around it.

**Research** — live chart, exact indicators, chart patterns, a sourced AI momentum read
where every claim links to the evidence it rests on, filtered company news, fundamentals,
five style lenses, and a typed ecosystem graph.

**Learning** — Guided Study (commit your own read before the AI's is revealed),
retrospective replay (read a hidden window of the stock's own history), and a journal of
your hypotheses — not your trades.

**Workspace** — side-by-side comparison, a watchlist that reports information events
rather than prompting you to act, and an optional practice lab for hypothetical positions.

Trade101 describes and teaches. It never says buy, sell or hold, never gives a price
target, and never states a claim it cannot source.

📄 **[docs/EXECUTION-REPORT.md](docs/EXECUTION-REPORT.md)** — what is built, what needs
testing, and known gaps.

### API endpoints

| | |
|---|---|
| `/research/{ticker}` | quote, indicators, OHLCV, as-of + staleness |
| `/analyze/{ticker}` | sourced AI read (degrades without a key) |
| `/lenses/{ticker}` | five deterministic style lenses |
| `/fundamentals/{ticker}` | earnings, revenue, margins, cash flow, valuation |
| `/graph/{ticker}` | typed, sourced ecosystem relationships |
| `/replay/{ticker}` · `/replay/{ticker}/reveal` | hidden-window exercise |
| `/compare?tickers=A,B` | rebased side-by-side, no ranking |
| `/journal` · `/watchlist` · `/practice` | the learning layer |
| `/usage` | AI spend by feature, key, model and ticker |
| `/patterns` · `/ecosystem` · `/search` · `/history` · `/cache` · `/health` | |


## Features
- **Search by name, any market** — "samsung", "toyota", "allianz" → pick from the matches (US, China, Japan, Korea, HK, Singapore, India, Europe).
- **Live chart** — candlesticks or line, timeframes 1Y · 1M · 10D · 5D · 1D (intraday), auto-refreshes every 7 min. Line color follows direction.
- **Metrics + learning** — RSI, MACD, SMA 50/200, Bollinger, volume — tap any to learn it *on this stock*.
- **Chart patterns** — head & shoulders, triple/double top & bottom, drawn on the chart with a plain-English lesson (heuristic learning aid).
- **AI momentum read** — bullish/bearish + confidence, synthesised from the indicators + news, fully sourced.
- **News** — feed + a "What it means" inference.
- **Ecosystem & index** — sector, industry, beta, market cap, peer companies (clickable).
- **History** — every stock you study, saved with a two-line takeaway.
- Browser back/forward + `#TICKER` shareable links.

## Stack
- **Backend:** Python · FastAPI · yfinance · pandas · scipy · Anthropic (Claude). Deterministic services + AI agents.
- **Frontend:** React · Vite · Lightweight-Charts.

---

## Setup

### 0. Prerequisites
- **Python 3.11+** and **Node 18+**.
- Two API keys (free/cheap): a **Claude API key** ([console.anthropic.com](https://console.anthropic.com/settings/keys)) and a free **Finnhub key** ([finnhub.io](https://finnhub.io/register)).

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv/Scripts/python.exe -m pip install -r requirements.txt
# macOS/Linux:
# source .venv/bin/activate && pip install -r requirements.txt
```

### 2. Environment
Copy the template to `.env` in the **project root** and fill in your keys:
```bash
cp .env.example .env
```
```
TRADE101_ANALYSIS_KEY=sk-ant-...      # Claude API key (AI momentum read + news)
TRADE101_NEWS_KEY=...                 # free Finnhub key (news + peers)
# TRADE101_MODEL=claude-sonnet-5      # default; use claude-opus-5 for max depth
```
The app runs without keys too — you just lose the AI narration/news (chart, indicators, patterns still work).

### 3. Frontend
```bash
cd frontend
npm install
```

---

## Run

Open **two terminals**:

**Backend:**
```bash
cd backend
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000   # Windows
# uvicorn app:app --reload --port 8000                              # macOS/Linux
```

**Frontend:**
```bash
cd frontend
npm run dev
```
Open **http://127.0.0.1:5173**.

> **Windows / PowerShell:** if `npm` is blocked with *"running scripts is disabled"*, either run `npm.cmd run dev`, or once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

## Test
```bash
cd backend
.venv/Scripts/python.exe -m pytest -q
```

## Project layout
```
backend/    FastAPI app, services (marketdata, indicators, patterns, news,
            company, search), agents (orchestrator, analysis), tests
frontend/   React + Vite app (Welcome, Research, History, chart, components)
docs/       design spec + implementation plan
```

## Disclaimer
Historical/technical analysis and educational explanations only — **not financial advice**, not a recommendation to trade. Data is delayed. Chart-pattern detection is a heuristic aid that fails often. Do your own research.
