Trade101 — Product and Technical Recommendations
Updated: 2026-09-10

> Tracked as **Phase 1.5 — Trust and coherence** in `BACKLOG.md` (inserted ahead of Phase 2
> depth work). See `CLAUDE.md` for current status.

PRODUCT POSITIONING

Trade101's differentiator should be active market learning, not a larger
technical-indicator dashboard and not an AI stock-tip product.

The desired learner loop is:
1. Observe the chart and evidence.
2. Form an interpretation or hypothesis.
3. Reveal Trade101's evidence-backed explanation, including conflicts.
4. Identify what could disprove the interpretation.
5. Return later and compare the read with the outcome.

The product must describe evidence and uncertainty, never tell the user to
buy, sell, hold, copy a trader, or expect a profit.


CURRENT MVP: WHAT IS WORKING

- Clear search-to-research workflow.
- Deterministic indicator calculations are separated from AI narration.
- The chart can remain usable if AI narration fails.
- Contextual metric lessons, chart patterns, history, references, and a
  company/peer panel provide a good initial learning foundation.
- Delayed data is already visibly labelled.


HIGHEST-PRIORITY FIXES (DO THESE BEFORE ADDING MANY FEATURES)

1. Evidence quality and source relevance

The app must not let an AI narrative make company-specific claims from broad,
unrelated articles. In a live NVDA review, unrelated stories were returned in
the company-news feed and still appeared in the narrative context.

Implement an evidence pipeline:
- Classify fetched articles as company-specific, supply-chain, sector, macro,
  or irrelevant.
- Exclude irrelevant articles before the AI analysis call.
- Give every claim an ID, source URL, published date, category, and supporting
  excerpt.
- Render the citation immediately next to the claim, not only in a long list
  of references.
- Label output as Fact, Interpretation, or Unknown/insufficient evidence.
- If there is no relevant company news, state that clearly and withhold a
  company-catalyst explanation.
- Add tests that intentionally supply irrelevant or unsupported content and
  ensure the analysis is rejected or downgraded.

Important: a non-empty source string is not evidence validation. This problem
is solved primarily by data filtering and validation code, not by adding more
AI agents or API keys.

2. Timeframe integrity

When a user switches the chart between 1Y, 1M, 10D, 5D, and 1D, all dependent
panels must use the same context or be explicitly marked otherwise.

- Show a shared label: timeframe, bar interval, data timestamp, and whether
  values are adjusted.
- Recompute relevant indicators and pattern detection for the chosen
  timeframe, or retain daily analysis with an explicit "daily analysis" label.
- Do not call an intraday 50-bar moving average "SMA 50-day".
- Keep the price used in the chart and the price used in indicator calculations
  consistent; otherwise explain adjusted versus unadjusted price data.

3. Coverage truthfulness

Search may find global listings, but data quality is not uniform. Display
coverage badges per company:
- Price/chart: supported, delayed, or unavailable.
- Company news: supported, limited, or unavailable.
- Official filings: supported, limited, or unavailable.
- Fundamentals: supported, limited, or unavailable.

Avoid marketing every market as equivalently researched until appropriate
licensed sources and country-specific adapters are implemented.


ARCHITECTURE AND DATA RECOMMENDATIONS

Gemini's recommendations are sound, with this order of execution:

1. Keep the current deterministic-service-plus-AI design.
   The AI should receive a compact, curated evidence bundle rather than raw
   news results. The deterministic backend owns prices, indicators, timestamps,
   source metadata, and evidence validation.

2. Add caching before scaling traffic.
   Start with a small cache abstraction and TTLs. Redis is appropriate when
   multiple users/processes need shared caching; a local in-memory or SQLite
   cache is sufficient for an early single-user prototype. Cache market bars,
   company profiles, news results, and completed analysis bundles separately.

3. Use a provider abstraction for market data.
   Do not replace Yahoo data with an institutional provider in one large rewrite.
   Keep a MarketDataProvider interface, then add an adapter for the chosen
   professional provider. Select a provider based on target exchanges, allowed
   redistribution, historical data, real-time entitlement, and cost.

4. Add WebSockets only when a real-time feed justifies them.
   A WebSocket connection cannot make delayed source data real-time. For the
   current education-oriented MVP, polling/cached refreshes are reasonable.
   Use real-time streaming only after obtaining a licensed real-time feed and
   designing clear reconnect, stale-data, and market-closed states.

5. Preserve graceful degradation.
   Prices and charts should render if AI, news, filing, ecosystem, or search
   sources fail. Each unavailable panel should say what failed, what remains
   usable, and whether retrying may help.


PRODUCT FEATURES: RECOMMENDED ORDER

Phase 1.5 — Trust and coherence
- Evidence relevance filter, claim-level citations, evidence tests.
- Shared timeframe/as-of labels across chart, metrics, patterns, and AI read.
- Provider coverage badges and robust error/stale-data states.
- Cache abstraction and API response caching.
- Visible educational/not-financial-advice notice near the momentum narrative,
  not only at the bottom of the app.
- Confirm API keys remain backend-only; do not expose them in Vite variables,
  browser bundles, URLs, client logs, or committed files.

Phase 2 — Learning engine
- Guided Study Mode: observe, predict, reveal, challenge, revisit.
- More tooltips, but favor short contextual prompts over tooltip overload.
- Learning journal: save the learner's hypothesis and evidence, not a virtual
  trade recommendation.
- Retrospective replay: hide a historical outcome until the learner submits a
  read, then reveal what followed with no claim of predictability.
- Company fundamentals: earnings date, results versus estimates, revenue,
  margins, cash flow, valuation context, and primary filing links.

Phase 2.5 — Style lenses, not "styles to copy"
- Trend lens: trend structure, relative strength, volume confirmation.
- Swing lens: momentum, volatility, recent catalyst context.
- Mean-reversion lens: range and volatility context, strongly caveated.
- Long-term lens: fundamentals, earnings, valuation, competitive position.
- Event-driven lens: earnings, filings, guidance, and macro sensitivity.

For every lens, show what it considers, what it does not consider, conflicting
evidence, and its failure modes. Do not ship a day-trading lens until a licensed
real-time data source is available; delayed data creates false precision.

Phase 3 — Research workspace
- Complete Comparison: choose two or more companies; normalize price charts;
  compare indicators, earnings/fundamentals, news evidence, peers, and time
  windows. Never reduce the output to "which is better."
- Watchlist: track companies, research updates, source coverage, and learner
  notes. Alerts should be phrased as information events (earnings filed, price
  crossed a selected level, new filing), not trade prompts.
- Optional simulated portfolio: make it a separate practice lab with explicit
  delayed/hypothetical performance and learning reflections. Do not make it the
  primary action of a beginner-facing educational app.
- Light mode, contrast checks, keyboard navigation, and responsive layout.

Phase 4 — Supply-chain and market ecosystem intelligence
- Replace the present peer list with a sourced relationship graph.
- Each edge needs relationship type (supplier, customer, partner, competitor,
  investor, index constituent), source, date, confidence, and materiality.
- Distinguish public companies from private companies.
- State that a business relationship can be a research hypothesis, not proof of
  a stock-price effect.
- ETF view should display verified holdings and weights. An ETF does not
  automatically rise merely because a company in a possible supply chain grows.


API KEYS AND AGENTS

The current two-key configuration is appropriate for the current MVP:

TRADE101_ANALYSIS_KEY=...    # Claude narration
TRADE101_NEWS_KEY=...        # Finnhub news and peers

Do not add separate AI agents or separate Claude API keys merely to improve
sourcing. First implement the evidence pipeline above. One carefully bounded
analysis call is easier to evaluate, cache, secure, and debug.

Add a new key only when a real integration has been implemented and tested:

TRADE101_SEARCH_PROVIDER=none
TRADE101_SEARCH_KEY=          # optional, future research/search provider
TRADE101_MARKET_DATA_PROVIDER=yahoo
TRADE101_MARKET_DATA_KEY=     # optional, future licensed data provider
TRADE101_CACHE_URL=           # optional, Redis connection when needed

Never commit the real .env file. Maintain only .env.example in Git with empty
values and explanations.


DEFINITION OF DONE FOR THE NEXT RELEASE

A completed "Trust & Learning" release should let a learner open a company and:
- See exactly what timeframe and data timestamp every conclusion refers to.
- See only relevant company, sector, supply-chain, or macro evidence.
- Open a citation and understand why it supports a displayed statement.
- See uncertainty when source coverage is poor.
- Form their own interpretation before seeing the AI synthesis.
- Leave with a saved learning note, not a trading instruction.

This sequence protects Trade101's most valuable promise: it helps people learn
how to reason about markets rather than outsourcing that reasoning to an AI.
